/**
 * FD2 Game Core Implementation
 *
 * Main game loop and state machine. Based on the original game's flow:
 *   sub_25BF4 (main) → sub_1F894 (intro) → sub_117E7 (game state machine)
 *
 * The state machine drives the game through:
 *   INIT → INTRO → MENU → CHAR_SELECT → BATTLE → VICTORY → ...
 */

#define _GNU_SOURCE
#include "fd2_game.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#endif

/* ---- Forward declarations for built-in states ---- */
static void state_init_enter(fd2_game_t* game);
static fd2_state_t state_init_update(fd2_game_t* game);
static void state_init_exit(fd2_game_t* game);

static void state_intro_enter(fd2_game_t* game);
static fd2_state_t state_intro_update(fd2_game_t* game);
static void state_intro_exit(fd2_game_t* game);

static void state_menu_enter(fd2_game_t* game);
static fd2_state_t state_menu_update(fd2_game_t* game);
static void state_menu_exit(fd2_game_t* game);

static void state_demo_enter(fd2_game_t* game);
static fd2_state_t state_demo_update(fd2_game_t* game);
static void state_demo_exit(fd2_game_t* game);

static void state_char_select_enter(fd2_game_t* game);
static fd2_state_t state_char_select_update(fd2_game_t* game);
static void state_char_select_exit(fd2_game_t* game);

static void state_battle_enter(fd2_game_t* game);
static fd2_state_t state_battle_update(fd2_game_t* game);
static void state_battle_exit(fd2_game_t* game);

static void state_victory_enter(fd2_game_t* game);
static fd2_state_t state_victory_update(fd2_game_t* game);
static void state_victory_exit(fd2_game_t* game);

static void state_continue_enter(fd2_game_t* game);
static fd2_state_t state_continue_update(fd2_game_t* game);
static void state_continue_exit(fd2_game_t* game);

static void state_game_over_enter(fd2_game_t* game);
static fd2_state_t state_game_over_update(fd2_game_t* game);
static void state_game_over_exit(fd2_game_t* game);

/* ---- Built-in State Operations Table ---- */
static const fd2_state_ops_t builtin_states[FD2_STATE_COUNT] = {
    [FD2_STATE_NONE]         = { NULL, NULL, NULL },
    [FD2_STATE_INIT]         = { state_init_enter, state_init_update, state_init_exit },
    [FD2_STATE_INTRO]        = { state_intro_enter, state_intro_update, state_intro_exit },
    [FD2_STATE_MENU]         = { state_menu_enter, state_menu_update, state_menu_exit },
    [FD2_STATE_DEMO]         = { state_demo_enter, state_demo_update, state_demo_exit },
    [FD2_STATE_CHAR_SELECT]  = { state_char_select_enter, state_char_select_update, state_char_select_exit },
    [FD2_STATE_BATTLE]       = { state_battle_enter, state_battle_update, state_battle_exit },
    [FD2_STATE_VICTORY]      = { state_victory_enter, state_victory_update, state_victory_exit },
    [FD2_STATE_CONTINUE]     = { state_continue_enter, state_continue_update, state_continue_exit },
    [FD2_STATE_GAME_OVER]    = { state_game_over_enter, state_game_over_update, state_game_over_exit },
    [FD2_STATE_QUIT]         = { NULL, NULL, NULL },
};

/* ---- Utility ---- */

static void find_data_dir(fd2_game_t* game, const char* argv0) {
    /* Try to find game data directory.
     * Search order:
     *   1. Explicit path (if argv0 is provided and is a directory)
     *   2. EXE directory (where the .exe file is located)
     *   3. ./game/ (relative to CWD)
     */
    
    /* If an explicit data directory was passed, use it */
    if (argv0 && argv0[0]) {
        /* Check if it's a directory path (not a filename) */
        snprintf(game->data_dir, sizeof(game->data_dir), "%s", argv0);
        return;
    }

#ifdef _WIN32
    /* Try exe directory using Windows API */
    char exe_path[PATH_MAX];
    DWORD len = GetModuleFileNameA(NULL, exe_path, sizeof(exe_path));
    if (len > 0 && len < sizeof(exe_path)) {
        /* Remove the executable filename to get the directory */
        char* backslash = strrchr(exe_path, '\\');
        if (backslash) {
            *(backslash + 1) = '\0';
            snprintf(game->data_dir, sizeof(game->data_dir), "%s", exe_path);
            return;
        }
    }
#endif

    /* Fallback: use current directory */
    snprintf(game->data_dir, sizeof(game->data_dir), ".");
}

const char* fd2_game_data_path(fd2_game_t* game, const char* filename) {
    if (!game || !filename) return NULL;

    static char path_buf[768];
    snprintf(path_buf, sizeof(path_buf), "%s/%s", game->data_dir, filename);
    return path_buf;
}

void fd2_game_request_quit(fd2_game_t* game) {
    if (game) game->running = 0;
}

/* ---- State Registration ---- */

void fd2_game_register_state(fd2_game_t* game, fd2_state_t state,
                              const fd2_state_ops_t* ops) {
    if (!game || state < 0 || state >= FD2_STATE_COUNT || !ops) return;
    game->state_ops[state] = ops;
}

/* ---- Lifecycle ---- */

int fd2_game_init(fd2_game_t* game, const char* data_dir) {
    if (!game) return -1;

    memset(game, 0, sizeof(*game));

    /* Find data directory */
    find_data_dir(game, data_dir);

    /* Initialize SDL — try video+audio first, fall back to video only */
    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO | SDL_INIT_TIMER) < 0) {
        fprintf(stderr, "fd2_game_init: SDL_Init with audio failed: %s, trying video only\n", SDL_GetError());
        if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_TIMER) < 0) {
            fprintf(stderr, "fd2_game_init: SDL_Init video-only failed: %s\n", SDL_GetError());
            return -1;
        }
    }

    /* Initialize subsystems */
    if (fd2_render_init(&game->render, FD2_RENDER_SCALE) != 0) {
        fprintf(stderr, "fd2_game_init: render init failed\n");
        SDL_Quit();
        return -1;
    }

    if (fd2_audio_init(&game->audio) != 0) {
        fprintf(stderr, "fd2_game_init: audio init failed (non-fatal)\n");
        /* Audio failure is non-fatal */
    }

    fd2_input_init(&game->input);

    if (fd2_resources_init(&game->resources, game->data_dir) != 0) {
        fprintf(stderr, "fd2_game_init: resources init failed\n");
        fd2_audio_shutdown(&game->audio);
        fd2_render_shutdown(&game->render);
        SDL_Quit();
        return -1;
    }

    /* Register built-in states */
    for (int i = 0; i < FD2_STATE_COUNT; i++) {
        if (builtin_states[i].update) {
            game->state_ops[i] = &builtin_states[i];
        }
    }

    /* Start in INIT state */
    game->current_state = FD2_STATE_INIT;
    game->next_state    = FD2_STATE_NONE;
    game->running       = 1;
    game->frame_count   = 0;
    game->last_tick     = SDL_GetTicks();

    printf("fd2_game_init: initialized (data_dir=%s)\n", game->data_dir);
    return 0;
}

int fd2_game_run(fd2_game_t* game) {
    if (!game || !game->running) return -1;

    /* Enter the initial state (enter is only called on transitions,
     * so the first state needs explicit entry) */
    {
        const fd2_state_ops_t* init_ops = game->state_ops[game->current_state];
        if (init_ops && init_ops->enter) {
            init_ops->enter(game);
        }
    }

    const int TARGET_FPS = 60;
    const u32 FRAME_TIME = 1000 / TARGET_FPS;

    while (game->running && game->current_state != FD2_STATE_QUIT) {
        u32 frame_start = SDL_GetTicks();

        /* ---- Input ---- */
        fd2_input_begin_frame(&game->input);

        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) {
                game->running = 0;
                break;
            }
            if (e.type == SDL_KEYDOWN && e.key.keysym.sym == SDLK_F11) {
                fd2_render_toggle_fullscreen(&game->render);
                continue;
            }
            fd2_input_process_event(&game->input, &e);
        }

        if (!game->running) break;

        /* ---- State Update ---- */
        const fd2_state_ops_t* ops = game->state_ops[game->current_state];
        if (ops && ops->update) {
            fd2_state_t next = ops->update(game);

            /* State transition? */
            if (next != game->current_state && next != FD2_STATE_NONE) {
                /* Exit current state */
                if (ops->exit) {
                    ops->exit(game);
                }
                game->state_data = NULL;

                /* Enter new state */
                game->current_state = next;
                const fd2_state_ops_t* new_ops = game->state_ops[next];
                if (new_ops && new_ops->enter) {
                    new_ops->enter(game);
                }
            }
        }

        /* ---- Frame pacing ---- */
        game->frame_count++;
        u32 frame_elapsed = SDL_GetTicks() - frame_start;
        if (frame_elapsed < FRAME_TIME) {
            SDL_Delay(FRAME_TIME - frame_elapsed);
        }

        game->last_tick = SDL_GetTicks();
    }

    /* Exit final state */
    if (game->current_state != FD2_STATE_QUIT && game->current_state != FD2_STATE_NONE) {
        const fd2_state_ops_t* ops = game->state_ops[game->current_state];
        if (ops && ops->exit) {
            ops->exit(game);
        }
    }

    return 0;
}

void fd2_game_shutdown(fd2_game_t* game) {
    if (!game) return;

    fd2_resources_shutdown(&game->resources);
    fd2_audio_shutdown(&game->audio);
    fd2_render_shutdown(&game->render);
    SDL_Quit();

    memset(game, 0, sizeof(*game));
}

/* ========================================================================
 * Built-in State Implementations
 * ======================================================================== */

/* ---- INIT State ----
 * Load essential resources, then transition to INTRO.
 * Based on sub_25BF4: load FDOTHER resources 0-6, FDTXT, malloc screen/palette.
 */

typedef struct {
    int load_step;       /* 0..N: which DAT file to load next */
    int load_failures;
} state_init_data_t;

static void state_init_enter(fd2_game_t* game) {
    state_init_data_t* data = (state_init_data_t*)calloc(1, sizeof(state_init_data_t));
    game->state_data = data;
    data->load_step = 0;

    /* Show loading screen */
    fd2_render_fill_screen(&game->render, 0);
    fd2_render_present(&game->render);
    printf("state_init: loading resources...\n");
}

static fd2_state_t state_init_update(fd2_game_t* game) {
    state_init_data_t* data = (state_init_data_t*)game->state_data;
    if (!data) return FD2_STATE_QUIT;

    /* Load all essential DAT files at once.
     * Could be spread across frames for a loading bar, but for now
     * we do it in one shot.
     */
    if (data->load_step == 0) {
        /* Load FDOTHER first (needed for intro) */
        if (fd2_resources_load_dat(&game->resources, FD2_DAT_FDOTHER) != 0) {
            fprintf(stderr, "state_init: FATAL: cannot load FDOTHER.DAT\n");
            return FD2_STATE_QUIT;
        }

        /* Load other essential files (non-fatal if missing) */
        fd2_resources_load_dat(&game->resources, FD2_DAT_FDTXT);
        fd2_resources_load_dat(&game->resources, FD2_DAT_BG);
        fd2_resources_load_dat(&game->resources, FD2_DAT_FIGANI);
        fd2_resources_load_dat(&game->resources, FD2_DAT_TAI);
        fd2_resources_load_dat(&game->resources, FD2_DAT_ANI);

        data->load_step = 1;
    }

    /* All loaded, transition to intro */
    printf("state_init: resources loaded, starting intro\n");
    return FD2_STATE_INTRO;
}

static void state_init_exit(fd2_game_t* game) {
    free(game->state_data);
    game->state_data = NULL;
}

/* ---- INTRO State ----
 * Opening animation sequence.
 * 1:1 match of sub_1F894 flow:
 *   Phase 0: Title screen (FDOTHER 74) → fade in → wait 30 ticks → fade out
 *   Phase 1: ANI#3 (intro cinematic, 90ms) → fade out
 *   Phase 2: Scroll (FDOTHER 69-73, 535→0) with ANI/overlay at positions
 *            330(ANI#4+5), 210(ANI#6+7), 110(skip), 450(overlay), 10(overlay), 25(ANI#0)
 *   Phase 3: Fade to black
 *   Phase 4: ANI#1 (menu intro, 15ms)
 *   Phase 5: Fade in menu background
 *   Phase 6: → transition to MENU state
 *
 * NOTE: ANI.DAT index mapping (from sub_20421 / sub_1F81E in sub_1F894):
 *   Index 0: 51 frames (main logo — played at scroll pos 25)
 *   Index 1: 26 frames (menu intro — played in Phase 4)
 *   Index 2: 28 frames (character intro A)
 *   Index 3: 12 frames (intro cinematic — played in Phase 1)
 *   Index 4: 35 frames (character intro — scroll pos 330, 1st ANI)
 *   Index 5: 12 frames (character name — scroll pos 330, 2nd ANI)
 *   Index 6: 17 frames (character intro — scroll pos 210, 1st ANI)
 *   Index 7: 12 frames (character name — scroll pos 210, 2nd ANI)
 *   Index 8: OUT OF BOUNDS — original calls at scroll pos 110, skip
 *
 * Animation playback order from sub_1F894:
 *   Phase 1:  sub_20421(3, 90, 1)  — ANI#3, FDOTHER[99] palette, 90ms
 *   Scroll 330: sub_1F882 + sub_1F81E(4,90,99) + sub_1F81E(5,50,0)
 *   Scroll 210: sub_1F882 + sub_1F81E(6,90,99) + sub_1F81E(7,50,0)
 *   Scroll 110: sub_1F882 + sub_1F81E(8,90,99)  (ANI#8 OOB, skip)
 *   Scroll 25:  sub_1F81E(0,15,0)  — ANI#0, FDOTHER[0] palette, 15ms
 *   Phase 4:  sub_20421(1, 15, 1)  — ANI#1, 15ms
 */

typedef struct {
    int  phase;
    int  phase_frame;

    /* AFM animation context for ANI.DAT playback */
    fd2_afm_t* afm;           /* Heap-allocated (64KB+ buffers inside) */
    u8*        ani_data;      /* Raw AFM data (allocated separately, needs explicit free) */
    int        ani_resource;  /* Which ANI.DAT resource is playing */
    int        ani_frame_delay; /* ms per AFM frame */

    /* Scroll animation buffer */
    u8*  scroll_buf;          /* 320 * 735 bytes */
    int  scroll_total_h;     /* Total height of scroll buffer */
    int  scroll_pos;         /* Current scroll position (535→25) */

    /* Scroll ANI sub-state (for playing character intros at positions 330/210/110) */
    int  scroll_ani_step;    /* 0=idle, 1=start_ani, 2=play_ani, 3=restore_scroll */
    int  scroll_ani_queue[3];/* Queue of ANI resource IDs to play */
    int  scroll_ani_queue_len;/* Number of ANIs in queue */
    int  scroll_ani_queue_idx;/* Current index in queue */
    int  scroll_ani_delay[3]; /* ms per frame for each ANI in queue */
    int  scroll_ani_palette[3]; /* FDOTHER palette resource per ANI in queue (-1=none) */
    bool scroll_ani_needs_fadeout; /* Whether to fade-out before ANI sequence */
    bool scroll_ani_after_end;    /* True for pos 25: after ANI, continue to pos 10 overlay */

    /* Overlay sub-state (sub_1F73F at scroll positions 450 and 10) */
    int  overlay_step;          /* 0=idle, 1=fadeout+draw, 2=wait, 3=fadeout+restore */
    int  overlay_image_res;     /* FDOTHER image resource to display */
    int  overlay_palette_res;   /* FDOTHER palette resource */
    int  overlay_wait;          /* Tick counter for overlay step 2 wait */
} state_intro_data_t;

/* Helper: play one frame of an ANI.DAT AFM animation.
 * Returns: 0 = frame decoded and presented, 1 = animation done, -1 = error */
static int intro_play_ani_frame(fd2_game_t* game, state_intro_data_t* data) {
    if (!data->afm) return -1;

    if (fd2_afm_is_done(data->afm)) {
        return 1;  /* Animation finished */
    }

    if (fd2_afm_decode_next_frame(data->afm) != 0) {
        return 1;  /* Decode error or finished */
    }

    /* Apply AFM palette and frame to screen */
    fd2_render_set_palette_6bit(&game->render, fd2_afm_get_palette(data->afm));
    fd2_render_blit_afm(&game->render, fd2_afm_get_frame(data->afm), -1);
    fd2_render_present(&game->render);

    /* Pump events so the window doesn't freeze during animation */
    SDL_Event e;
    while (SDL_PollEvent(&e)) {
        if (e.type == SDL_QUIT) return -2;  /* Signal quit */
    }

    return 0;
}

/* ---- Helper: load ANI.DAT AFM data directly from file (with index lookup) ----
 * ANI.DAT has a special index structure: after the LLLLLL magic (6 bytes),
 * there are N 4-byte entries where each entry points to the actual AFM data.
 * Index table starts at offset 0x06.
 * To get ANI#N: read 4 bytes at offset (0x06 + N*4) to get the AFM offset,
 *              then read from that offset (173 byte header + frames).
 * This replicates sub_20421's fseek(4*a5 + 6, 0) and fseek(*(DWORD*)buf, 0).
 */
static int load_ani_afm_from_file(const char* ani_path, int ani_index,
                                   u8** out_data, u32* out_size) {
    if (!ani_path || !out_data || !out_size) return -1;
    if (ani_index < 0) {
        fprintf(stderr, "intro: invalid ANI index %d\n", ani_index);
        return -1;
    }
    
    FILE* f = fopen(ani_path, "rb");
    if (!f) {
        fprintf(stderr, "intro: cannot open ANI.DAT: %s\n", ani_path);
        return -1;
    }
    
    /* ANI.DAT index lookup: offset = 0x06 + index * 4 */
    fseek(f, 0x06 + ani_index * 4, SEEK_SET);
    u32 afm_offset = 0;
    if (fread(&afm_offset, 4, 1, f) != 1) {
        fprintf(stderr, "intro: cannot read ANI.DAT index %d\n", ani_index);
        fclose(f);
        return -1;
    }
    
    /* Seek to the AFM data */
    if (fseek(f, afm_offset, SEEK_SET) != 0) {
        fprintf(stderr, "intro: cannot seek to AFM offset 0x%X\n", afm_offset);
        fclose(f);
        return -1;
    }
    
    /* Read AFM header (173 bytes) */
    u8 header[FD2_AFM_HEADER_SIZE];
    if (fread(header, 1, FD2_AFM_HEADER_SIZE, f) != FD2_AFM_HEADER_SIZE) {
        fprintf(stderr, "intro: cannot read AFM header for ANI#%d\n", ani_index);
        fclose(f);
        return -1;
    }
    
    /* Verify AFM signature */
    if (memcmp(header, "AFM", 3) != 0) {
        fprintf(stderr, "intro: ANI#%d has invalid AFM signature\n", ani_index);
        fclose(f);
        return -1;
    }
    
    /* Get frame count from header offset 0xA5 */
    u16 frame_count = (u16)header[0xA5] | ((u16)header[0xA6] << 8);
    
    /* Calculate total size: header + all frames */
    u8 frame_hdr[FD2_AFM_FRAME_HDR];
    u32 total_size = FD2_AFM_HEADER_SIZE;
    
    for (u16 i = 0; i < frame_count; i++) {
        if (fread(frame_hdr, FD2_AFM_FRAME_HDR, 1, f) != 1) {
            fprintf(stderr, "intro: cannot read frame header %d\n", i);
            fclose(f);
            return -1;
        }
        u16 frame_size = (u16)frame_hdr[0] | ((u16)frame_hdr[1] << 8);
        total_size += FD2_AFM_FRAME_HDR + frame_size;
        
        /* Seek past frame data */
        if (fseek(f, frame_size, SEEK_CUR) != 0) {
            fprintf(stderr, "intro: cannot seek past frame %d\n", i);
            fclose(f);
            return -1;
        }
    }
    
    /* Allocate buffer */
    u8* afm_data = (u8*)malloc(total_size);
    if (!afm_data) {
        fprintf(stderr, "intro: cannot allocate AFM buffer (%u bytes)\n", total_size);
        fclose(f);
        return -1;
    }
    
    /* Seek back and read all data */
    fseek(f, afm_offset, SEEK_SET);
    if (fread(afm_data, 1, total_size, f) != total_size) {
        fprintf(stderr, "intro: cannot read full AFM data\n");
        free(afm_data);
        fclose(f);
        return -1;
    }
    
    fclose(f);
    
    *out_data = afm_data;
    *out_size = total_size;
    
    printf("intro: loaded ANI#%d from file (offset=0x%X, %u frames, %u bytes)\n",
           ani_index, afm_offset, frame_count, total_size);
    return 0;
}

/* Helper: start playing an ANI.DAT AFM animation */
static int intro_start_ani(fd2_game_t* game, state_intro_data_t* data,
                           int ani_index, int frame_delay_ms) {
    /* Free previous AFM context and its data */
    if (data->afm) {
        /* The AFM data was allocated separately, need to free it */
        /* Check if there's stored pointer to free */
        if (data->ani_data) {
            free(data->ani_data);
            data->ani_data = NULL;
        }
        free(data->afm);
        data->afm = NULL;
    }

    /* Get ANI.DAT path from resource manager */
    const char* ani_path = fd2_resources_dat_path(&game->resources, FD2_DAT_ANI);
    if (!ani_path) {
        fprintf(stderr, "intro: cannot get ANI.DAT path\n");
        return -1;
    }

    /* Load AFM data directly from file (with proper index lookup) */
    u8* afm_data = NULL;
    u32 afm_size = 0;
    
    if (load_ani_afm_from_file(ani_path, ani_index, &afm_data, &afm_size) != 0) {
        fprintf(stderr, "intro: failed to load ANI#%d from ANI.DAT\n", ani_index);
        return -1;
    }

    /* Allocate and initialize AFM context */
    data->afm = (fd2_afm_t*)calloc(1, sizeof(fd2_afm_t));
    if (!data->afm) {
        free(afm_data);
        return -1;
    }

    fd2_afm_init(data->afm);
    if (fd2_afm_open(data->afm, afm_data, afm_size) != 0) {
        fprintf(stderr, "intro: failed to open AFM for ANI#%d\n", ani_index);
        free(afm_data);
        free(data->afm);
        data->afm = NULL;
        return -1;
    }

    /* Store the allocated data pointer for later cleanup */
    data->ani_data = afm_data;
    data->ani_resource = ani_index;
    data->ani_frame_delay = frame_delay_ms;

    printf("intro: playing ANI#%d (%u frames, %dms delay)\n",
           ani_index, data->afm->total_frames, frame_delay_ms);
    return 0;
}

/* Helper: build scroll buffer from FDOTHER resources 69-73 */
static void intro_build_scroll_buffer(fd2_game_t* game, state_intro_data_t* data) {
    /* IDA sub_1F894: loc_396C0 = 235200 = 320 * 735.
     * All 5 frames use fixed stride of 147 pixels (147 * 5 = 735).
     * Each frame is loaded via sub_4E98D(res, 0, 147*n5, buf, 320, -1)
     * where dst_y = 147 * n5 and the RLE image is fully decompressed.
     * IMPORTANT: Original game resources 69-73 are all 147px high.
     * If a resource has different height, clamp to 147 to match original behavior.
     * The scroll loop copies 200 rows from buf[n535*320] to screen,
     * with n535 ranging from 535 down to 0.
     * At n535=535: shows rows 535..734 (the bottom portion of frames 4-5). */
    const int frame_h = 147;
    const int num_frames = 5;
    data->scroll_total_h = frame_h * num_frames;  /* 735 */
    data->scroll_buf = (u8*)calloc(FD2_SCREEN_W * data->scroll_total_h, sizeof(u8));
    if (!data->scroll_buf) return;

    for (int i = 0; i < num_frames; i++) {
        u32 fsize;
        const u8* fres = fd2_resources_get(&game->resources, FD2_DAT_FDOTHER, 69 + i, &fsize);
        if (fres) {
            int fw, fh;
            u8* fpixels = NULL;
            if (fd2_rle_decompress_from_resource(fres, fsize, &fpixels, &fw, &fh) == 0) {
                int dst_y = frame_h * i;
                /* Clamp to 147px to match original game behavior.
                 * If resource height differs from 147, only copy 147 rows. */
                int copy_h = fh < frame_h ? fh : frame_h;
                int copy_w = fw < FD2_SCREEN_W ? fw : FD2_SCREEN_W;
                fprintf(stderr, "[intro] Frame %d (res %d): RLE size=%u, dim=%dx%d, dst_y=%d, copy_h=%d\n",
                        i, 69 + i, fsize, fw, fh, dst_y, copy_h);
                for (int y = 0; y < copy_h; y++) {
                    memcpy(data->scroll_buf + (dst_y + y) * FD2_SCREEN_W,
                           fpixels + y * fw, copy_w);
                }
                /* Print first and last byte of this frame for debugging */
                fprintf(stderr, "[intro] Frame %d: first_byte=%d, last_byte=%d\n",
                        i, data->scroll_buf[dst_y * FD2_SCREEN_W],
                        data->scroll_buf[(dst_y + copy_h - 1) * FD2_SCREEN_W]);
                free(fpixels);
            }
        } else {
            fprintf(stderr, "[intro] Frame %d (res %d): NOT FOUND\n", i, 69 + i);
        }
    }
    fprintf(stderr, "[intro] Total buffer height: %d (expected: 735)\n", data->scroll_total_h);
}

static void state_intro_enter(fd2_game_t* game) {
    state_intro_data_t* data = (state_intro_data_t*)calloc(1, sizeof(state_intro_data_t));
    game->state_data = data;
    data->phase = 0;
    data->phase_frame = 0;
    data->afm = NULL;
    data->ani_data = NULL;
    data->scroll_buf = NULL;

    /* ---- Phase 0: Show title screen (sub_1F894 start) ---- */

    /* Load palette from FDOTHER resource 76 (original: sub_111BA(FDOTHER_DAT,76)) */
    u32 pal_size;
    const u8* pal_res = fd2_resources_get(&game->resources, FD2_DAT_FDOTHER, 76, &pal_size);
    if (pal_res && pal_size == FD2_PALETTE_BYTES) {
        fd2_render_set_palette_6bit(&game->render, pal_res);
    }

    /* Decompress title image (FDOTHER resource 74) and blit to screen */
    u32 title_size;
    const u8* title_res = fd2_resources_get(&game->resources, FD2_DAT_FDOTHER, 74, &title_size);
    fd2_render_fill_screen(&game->render, 0);
    if (title_res) {
        fd2_render_blit_rle(&game->render, title_res, title_size, 0, 0);
    }

    /* Start with brightness 0 (black) — will fade in on first update */
    fd2_render_set_brightness(&game->render, 0);
    fd2_render_present(&game->render);
}

static fd2_state_t state_intro_update(fd2_game_t* game) {
    state_intro_data_t* data = (state_intro_data_t*)game->state_data;
    if (!data) return FD2_STATE_QUIT;

    /* ESC always quits */
    if (fd2_action_pressed(&game->input, FD2_ACTION_ESCAPE)) {
        return FD2_STATE_QUIT;
    }

    /* Any other key skips remaining intro phases (jumps to menu) */
    if (fd2_input_any_pressed(&game->input) && data->phase < 5) {
        if (data->ani_data) { free(data->ani_data); data->ani_data = NULL; }
        if (data->afm) { free(data->afm); data->afm = NULL; }
        if (data->scroll_buf) { free(data->scroll_buf); data->scroll_buf = NULL; }
        data->scroll_ani_step = 0;
        return FD2_STATE_MENU;
    }

    switch (data->phase) {
        /* ---- Phase 0: Title screen fade-in + wait + fade-out ----
         * Original: sub_1F525 (fade in) → sub_17AA9(1) → sub_17AA9(30) → sub_1F882 (fade out) */
        case 0:
        {
            if (data->phase_frame == 0) {
                /* Fade in from black (sub_1F525: 64 steps, 2ms each) */
                fd2_render_fade_from_black(&game->render, 64, 2);
            }
            data->phase_frame++;
            /* Wait ~30 ticks after fade-in (sub_17AA9(1) + sub_17AA9(30)) */
            if (data->phase_frame >= 30 + 64) {
                /* Fade out to black (sub_1F882: 64 steps, 2ms each) */
                fd2_render_fade_to_black(&game->render, 64, 2);
                printf("intro: phase 0 done (title faded out), starting Phase 1 (ANI#3)\n");
                data->phase = 1;
                data->phase_frame = 0;
            }
            break;
        }

        /* ---- Phase 1: ANI#3 intro cinematic ----
         * Original: load FDOTHER[99] palette → clear screen → sub_20421(3, 90, 1)
         *   → sub_1F882 (fade out) → clear → load FDOTHER[101] → brightness 0
         * ANI#3 has 12 frames, 90ms delay, interruptible (a3=1). */
        case 1:
        {
            if (data->phase_frame == 0) {
                /* Load FDOTHER[99] as palette (sub_111BA("FDOTHER.DAT", FDOTHER_DAT, 99)) */
                u32 pal_size;
                const u8* pal_res = fd2_resources_get(
                    &game->resources, FD2_DAT_FDOTHER, 99, &pal_size);
                if (pal_res && pal_size == FD2_PALETTE_BYTES) {
                    fd2_render_set_palette_6bit(&game->render, pal_res);
                }

                /* Clear screen, set brightness to 0 (sub_11D40(0,255,0)).
                 * Screen appears black even though palette is set, because
                 * brightness=0 zeroes the palette. AFM playback will
                 * override the palette each frame via set_palette_6bit. */
                fd2_render_fill_screen(&game->render, 0);
                fd2_render_set_brightness(&game->render, 0);
                fd2_render_present(&game->render);

                /* Start ANI#3 playback (sub_20421(3, 90, 1)) */
                intro_start_ani(game, data, 3, 90);
            }

            int result = intro_play_ani_frame(game, data);
            if (result == -2) return FD2_STATE_QUIT;
            if (result != 0) {
                /* ANI#3 finished — fade out, then prepare scroll phase.
                 * Original: sub_1F882 (fade out) after sub_20421 returns. */
                if (data->ani_data) { free(data->ani_data); data->ani_data = NULL; }
                if (data->afm) { free(data->afm); data->afm = NULL; }
                fd2_render_fade_to_black(&game->render, 64, 2);
                printf("intro: ANI#3 done (faded out), starting scroll (phase 2)\n");
                data->phase = 2;
                data->phase_frame = 0;
                return FD2_STATE_INTRO;
            }

            SDL_Delay(data->ani_frame_delay);
            data->phase_frame++;
            break;
        }

        /* ---- Phase 2: Scroll animation (535→0) ----
         * Original: for (n535 = 535; n535 >= 0; --n535) { ... if (n535==25) special }
         * Scroll buffer from FDOTHER 69-73 (5 images × 147 rows = 735h)
         * FDOTHER[101] palette, FDOTHER[7] used for scroll palette.
         * ANI sub-state at positions 330, 210, 110, 25.
         * Overlay sub-state (sub_1F73F) at positions 450, 10. */
        case 2:
        {
            /* Initialization: only run once (phase_frame == 0 means first entry) */
            if (data->phase_frame == 0) {
                printf("intro: phase 2 init (scroll buffer setup)\n");
                
                /* Original after ANI#3: memset(655360,0,64000) → sub_111BA(101) →
                 * sub_11D40(0,255,64) → build scroll → sub_4E381 → malloc overlay */
                fd2_render_fill_screen(&game->render, 0);

                /* Load FDOTHER[101] as palette (original: FDOTHER_DAT = sub_111BA(101)) */
                u32 pal_size;
                const u8* pal_res = fd2_resources_get(
                    &game->resources, FD2_DAT_FDOTHER, 101, &pal_size);
                if (pal_res && pal_size == FD2_PALETTE_BYTES) {
                    fd2_render_set_palette_6bit(&game->render, pal_res);
                }

                /* Set brightness to 64 (sub_11D40(0, 255, 64)) */
                fd2_render_set_brightness(&game->render, 64);

                /* Build scroll buffer from FDOTHER 69-73 */
                intro_build_scroll_buffer(game, data);

                if (!data->scroll_buf) {
                    fprintf(stderr, "intro ERROR: scroll buffer allocation failed!\n");
                    data->phase = 3;
                    data->phase_frame = 0;
                    break;
                }
                printf("intro: scroll buffer built, size %dx%d\n",
                       FD2_SCREEN_W, data->scroll_total_h);

                /* Set initial state */
                data->scroll_pos = 535;
                data->phase_frame = 1;  /* Mark init complete */
                data->scroll_ani_needs_fadeout = false;
                data->scroll_ani_after_end = false;
                data->overlay_step = 0;
                data->scroll_ani_step = 0;

                /* Show first scroll frame and fade in (sub_1F525 at n535==535) */
                int pos = data->scroll_pos;
                for (int y = 0; y < FD2_SCREEN_H && (pos + y) < data->scroll_total_h; y++) {
                    memcpy(game->render.screen + y * FD2_SCREEN_W,
                           data->scroll_buf + (pos + y) * FD2_SCREEN_W,
                           FD2_SCREEN_W);
                }
                fd2_render_fade_from_black(&game->render, 64, 2);

                printf("intro: scroll started from pos 535, entering main loop\n");
                /* Don't break - continue to scroll processing */
            }

            /* ---- Overlay sub-state (sub_1F73F at scroll positions 450 and 10) ----
             * sub_1F73F flow: fade out → draw image+palette → fade in → wait 6 ticks →
             *                 fade out → restore scroll+palette → fade in */
            if (data->overlay_step != 0) {
                printf("intro: overlay_step=%d (image=%d)\n", data->overlay_step, data->overlay_image_res);
                switch (data->overlay_step) {
                    case 1: /* Fade out + draw overlay image */
                    {
                        printf("intro: overlay step 1 - fade out and draw\n");
                        fd2_render_fade_to_black(&game->render, 64, 2);
                        fd2_render_fill_screen(&game->render, 0);

                        /* Load overlay palette */
                        u32 pal_size;
                        const u8* pal_res = fd2_resources_get(
                            &game->resources, FD2_DAT_FDOTHER,
                            data->overlay_palette_res, &pal_size);
                        if (pal_res && pal_size == FD2_PALETTE_BYTES) {
                            fd2_render_set_palette_6bit(&game->render, pal_res);
                        }

                        /* Load overlay image */
                        u32 ov_size;
                        const u8* ov_res = fd2_resources_get(
                            &game->resources, FD2_DAT_FDOTHER,
                            data->overlay_image_res, &ov_size);
                        if (ov_res) {
                            fd2_render_blit_rle(&game->render, ov_res, ov_size, 0, 0);
                        }

                        fd2_render_fade_from_black(&game->render, 64, 2);
                        data->overlay_step = 2;
                        data->overlay_wait = 0;
                        break;
                    }
                    case 2: /* Wait a few ticks (sub_17AA9(1) + sub_17AA9(6)) */
                    {
                        data->overlay_wait++;
                        if (data->overlay_wait >= 7) {
                            data->overlay_step = 3;
                        }
                        break;
                    }
                    case 3: /* Fade out + restore scroll + fade in */
                    {
                        fd2_render_fade_to_black(&game->render, 64, 2);

                        /* Restore scroll buffer at current position */
                        int pos = data->scroll_pos;
                        if (data->scroll_buf) {
                            fd2_render_fill_screen(&game->render, 0);
                            for (int y = 0; y < FD2_SCREEN_H && (pos + y) < data->scroll_total_h; y++) {
                                memcpy(game->render.screen + y * FD2_SCREEN_W,
                                       data->scroll_buf + (pos + y) * FD2_SCREEN_W,
                                       FD2_SCREEN_W);
                            }
                        }

                        /* Restore FDOTHER[101] palette */
                        u32 pal_size;
                        const u8* pal_res = fd2_resources_get(
                            &game->resources, FD2_DAT_FDOTHER, 101, &pal_size);
                        if (pal_res && pal_size == FD2_PALETTE_BYTES) {
                            fd2_render_set_palette_6bit(&game->render, pal_res);
                        }

                        fd2_render_fade_from_black(&game->render, 64, 2);
                        data->overlay_step = 0;
                        data->scroll_pos--;  /* Advance past the overlay trigger position */
                        
                        /* If this was the overlay at pos 10 (after ANI#0), transition to phase 3 */
                        if (data->scroll_ani_after_end && data->scroll_pos == 9) {
                            printf("intro: final overlay done, going to phase 3\n");
                            if (data->scroll_buf) {
                                free(data->scroll_buf);
                                data->scroll_buf = NULL;
                            }
                            data->phase = 3;
                            data->phase_frame = 0;
                        }
                        break;
                    }
                }
                return FD2_STATE_INTRO;
            }

            /* ---- ANI sub-state (character intros at scroll positions 330/210/110/25) ----
             * Original flow at pos 330/210:
             *   sub_1F882 (fade out) → sub_1F81E(ani1, 90, 99) → sub_1F81E(ani2, 50, 0)
             *   → restore scroll + fade in
             * At pos 110: sub_1F882 → sub_1F81E(8,90,99) (ANI#8 OOB → skip)
             * At pos 25: sub_1F81E(0, 15, 0) — then break loop
             *
             * sub_1F81E(ani_id, delay, palette_res):
             *   if palette_res>=0: clear → load FDOTHER[palette_res] as palette → brightness 0
             *   sub_20421(ani_id, delay, 0) → sub_1F882 (fade out)
             */
            if (data->scroll_ani_step != 0) {
                switch (data->scroll_ani_step) {
                    case 1: /* Fade out + start ANI playback (sub_1F882 + sub_1F81E) */
                    {
                        /* Fade out first (only at positions 330/210/110, not 25) */
                        if (data->scroll_ani_needs_fadeout) {
                            fd2_render_fade_to_black(&game->render, 64, 2);
                            data->scroll_ani_needs_fadeout = false;
                        }

                        int ani_id = data->scroll_ani_queue[data->scroll_ani_queue_idx];
                        int palette_res = data->scroll_ani_palette[data->scroll_ani_queue_idx];
                        int delay_ms = data->scroll_ani_delay[data->scroll_ani_queue_idx];

                        /* sub_1F81E: clear screen → set palette → brightness 0.
                         * set_brightness(0) here matches sub_11D40(0,255,0) in original.
                         * Unlike the fade_from_black cases, this is intentional: the
                         * screen should be black until AFM starts writing frames,
                         * and AFM's set_palette_6bit will override each frame. */
                        fd2_render_fill_screen(&game->render, 0);

                        if (palette_res >= 0) {
                            u32 pal_size;
                            const u8* pal_res = fd2_resources_get(
                                &game->resources, FD2_DAT_FDOTHER, palette_res, &pal_size);
                            if (pal_res && pal_size == FD2_PALETTE_BYTES) {
                                fd2_render_set_palette_6bit(&game->render, pal_res);
                            }
                        }

                        fd2_render_set_brightness(&game->render, 0);
                        fd2_render_present(&game->render);

                        /* Start the ANI animation (sub_20421) */
                        if (intro_start_ani(game, data, ani_id, delay_ms) == 0) {
                            data->scroll_ani_step = 2;
                        } else {
                            /* ANI not found — skip to next in queue */
                            data->scroll_ani_queue_idx++;
                            if (data->scroll_ani_queue_idx >= data->scroll_ani_queue_len) {
                                data->scroll_ani_step = 3;
                            }
                        }
                        break;
                    }

                    case 2: /* Play one ANI frame */
                    {
                        int result = intro_play_ani_frame(game, data);
                        if (result == -2) return FD2_STATE_QUIT;

                        if (result != 0) {
                            /* ANI finished — fade out (sub_1F882), advance queue */
                            if (data->ani_data) { free(data->ani_data); data->ani_data = NULL; }
                            if (data->afm) { free(data->afm); data->afm = NULL; }
                            fd2_render_fade_to_black(&game->render, 64, 2);
                            data->scroll_ani_queue_idx++;

                            if (data->scroll_ani_queue_idx >= data->scroll_ani_queue_len) {
                                data->scroll_ani_step = 3;  /* All ANIs done */
                            } else {
                                data->scroll_ani_step = 1;  /* Start next ANI */
                            }
                        } else {
                            SDL_Delay(data->ani_frame_delay);
                        }
                        break;
                    }

                    case 3: /* Restore scroll buffer + fade in (LABEL_13/LABEL_14) */
                    {
                        /* LABEL_13/LABEL_14: After any ANI finishes.
                         * Original: sub_11EB0(...) → sub_111BA(101) →
                         *           sub_1F525() → goto LABEL_25.
                         * LABEL_25 ends with --n535, so we must decrement
                         * scroll_pos here to avoid re-triggering the same
                         * ANI position on the next frame. */
                        int pos = data->scroll_pos;
                        if (data->scroll_buf) {
                            fd2_render_fill_screen(&game->render, 0);
                            for (int y = 0; y < FD2_SCREEN_H && (pos + y) < data->scroll_total_h; y++) {
                                memcpy(game->render.screen + y * FD2_SCREEN_W,
                                       data->scroll_buf + (pos + y) * FD2_SCREEN_W,
                                       FD2_SCREEN_W);
                            }
                        }

                        /* Load FDOTHER[101] palette (scroll palette) */
                        u32 pal_size;
                        const u8* pal_res = fd2_resources_get(
                            &game->resources, FD2_DAT_FDOTHER, 101, &pal_size);
                        if (pal_res && pal_size == FD2_PALETTE_BYTES) {
                            fd2_render_set_palette_6bit(&game->render, pal_res);
                        }

                        /* Fade in from black (sub_1F525). */
                        fd2_render_fade_from_black(&game->render, 64, 2);

                        data->scroll_ani_step = 0;
                        data->scroll_ani_queue_len = 0;
                        data->scroll_ani_queue_idx = 0;
                        /* Decrement scroll_pos to match original's --n535
                         * after LABEL_25. This prevents re-triggering ANI
                         * at the same position on next frame. */
                        data->scroll_pos--;
                        printf("intro: ANI at pos %d done, resuming scroll at pos %d\n",
                               pos, data->scroll_pos);
                        break;
                    }
                }
                return FD2_STATE_INTRO;
            }

            /* ---- Normal scroll processing ---- */

            int pos = data->scroll_pos;
            if (pos < 0) {
                /* Scroll done */
                printf("intro: scroll done at pos %d, fading to black\n", pos);
                data->phase = 3;
                data->phase_frame = 0;
                break;
            }

            /* Check if scroll_buf is valid */
            if (!data->scroll_buf) {
                fprintf(stderr, "intro ERROR: scroll_buf is NULL at pos %d\n", pos);
                data->phase = 3;
                data->phase_frame = 0;
                break;
            }

            /* Copy 320x200 from scroll buffer at offset pos */
            for (int y = 0; y < FD2_SCREEN_H && (pos + y) < data->scroll_total_h; y++) {
                memcpy(game->render.screen + y * FD2_SCREEN_W,
                       data->scroll_buf + (pos + y) * FD2_SCREEN_W,
                       FD2_SCREEN_W);
            }

            /* ---- Debug: report scroll position periodically ---- */
            if ((pos % 25) == 0) {
                printf("intro: scroll pos %d (overlay_step=%d, scroll_ani_step=%d)\n",
                       pos, data->overlay_step, data->scroll_ani_step);
            }

            /* ---- Overlay triggers at positions 450 and 10 (sub_1F73F) ---- */
            if (pos == 450) {
                /* sub_1F73F(100, 99, n15_1, 450): overlay image 100, palette 99 */
                printf("intro: TRIGGERING OVERLAY at pos 450 (image=%d, palette=%d)\n", 100, 99);
                data->overlay_image_res = 100;
                data->overlay_palette_res = 99;
                data->overlay_step = 1;
                break;
            }
            if (pos == 10) {
                /* sub_1F73F(75, 76, n15_1, 10): overlay image 75, palette 76 */
                data->overlay_image_res = 75;
                data->overlay_palette_res = 76;
                data->overlay_step = 1;
                /* Don't decrement scroll_pos here - overlay_step 3 will do it */
                break;
            }

            /* ---- ANI triggers at positions 330, 210, 110, 25 ----
             * Original flow (sub_1F894 scroll loop):
             *   pos 330: sub_1F882 → sub_1F81E(4,90,99) → sub_1F81E(5,50,0) → restore
             *   pos 210: sub_1F882 → sub_1F81E(6,90,99) → sub_1F81E(7,50,0) → restore
             *   pos 110: sub_1F882 → sub_1F81E(8,90,99) → restore (ANI#8 OOB, skip)
             *   pos 25:  sub_1F81E(0,15,0) → break (end of scroll loop, go to Phase 3)
             */
            if ((pos == 330 || pos == 210 || pos == 110 || pos == 25)
                && data->scroll_ani_step == 0) {
                if (pos == 330) {
                    data->scroll_ani_queue[0] = 4;
                    data->scroll_ani_queue[1] = 5;
                    data->scroll_ani_queue_len = 2;
                    data->scroll_ani_palette[0] = 99;  /* FDOTHER[99] palette */
                    data->scroll_ani_palette[1] = 0;   /* FDOTHER[0] palette */
                    data->scroll_ani_delay[0] = 90;   /* First ANI: 90ms */
                    data->scroll_ani_delay[1] = 50;   /* Second ANI: 50ms */
                    data->scroll_ani_needs_fadeout = true;
                    data->scroll_ani_after_end = false;  /* Normal: continue scroll */
                } else if (pos == 210) {
                    data->scroll_ani_queue[0] = 6;
                    data->scroll_ani_queue[1] = 7;
                    data->scroll_ani_queue_len = 2;
                    data->scroll_ani_palette[0] = 99;  /* FDOTHER[99] palette */
                    data->scroll_ani_palette[1] = 0;   /* FDOTHER[0] palette */
                    data->scroll_ani_delay[0] = 90;
                    data->scroll_ani_delay[1] = 50;
                    data->scroll_ani_needs_fadeout = true;
                    data->scroll_ani_after_end = false;  /* Normal: continue scroll */
                } else if (pos == 110) {
                    /* Original: sub_1F882 (fade out) → sub_1F81E(8,90,99)
                     * (ANI#8 OOB, fails immediately) → LABEL_14 (restore scroll
                     * + fade in). Visual effect: brief fade-to-black pause.
                     * Trigger ANI sub-state with ANI#8 (which will fail to load,
                     * causing immediate step 3 = restore + fade in). */
                    data->scroll_ani_queue[0] = 8;
                    data->scroll_ani_queue_len = 1;
                    data->scroll_ani_palette[0] = 99;
                    data->scroll_ani_delay[0] = 90;
                    data->scroll_ani_needs_fadeout = true;
                    data->scroll_ani_after_end = false;  /* Normal: continue scroll */
                } else { /* pos == 25 */
                    /* sub_1F81E(0, 15, 0): ANI#0 with FDOTHER[0] palette, 15ms delay.
                     * After ANI#0 finishes, continue scrolling to pos 10 overlay,
                     * then transition to phase 3. */
                    data->scroll_ani_queue[0] = 0;
                    data->scroll_ani_queue_len = 1;
                    data->scroll_ani_palette[0] = 0;   /* FDOTHER[0] palette */
                    data->scroll_ani_delay[0] = 15;
                    data->scroll_ani_needs_fadeout = false;  /* No fade-out at pos 25 */
                    data->scroll_ani_after_end = true;   /* Continue to pos 10 overlay */
                }
                data->scroll_ani_queue_idx = 0;
                data->scroll_ani_step = 1;
                printf("intro: scroll pos %d — triggering ANI queue[%d] len=%d%s\n",
                       pos, data->scroll_ani_queue[0], data->scroll_ani_queue_len,
                       data->scroll_ani_after_end ? " (END SCROLL)" : "");
                break;
            }

            fd2_render_present(&game->render);

            /* Pump events during scroll */
            {
                SDL_Event e;
                while (SDL_PollEvent(&e)) {
                    if (e.type == SDL_QUIT) return FD2_STATE_QUIT;
                }
            }

            /* Delay 30ms per frame (original: j___delay(30)) */
            SDL_Delay(30);

            /* 1-second pause at scroll pos 0 (original: if (!n535) j___delay(1000)) */
            if (data->scroll_pos == 0) {
                SDL_Delay(1000);
            }

            data->scroll_pos--;
            break;
        }

        /* ---- Phase 3: Fade to reddish-black (sub_2DF01 with base 0x3F,0,0) ---- */
        case 3:
        {
            if (data->scroll_buf) {
                free(data->scroll_buf);
                data->scroll_buf = NULL;
            }

            /* Fade to reddish-black over 40 steps, 8ms each.
             * Original: sub_2DF01(0, 255, n40, 0x3F, 0, 0) — fades to a
             * uniform (63,0,0) red instead of pure black, giving a warm tint. */
            fd2_render_fade_to_color(&game->render, 40, 8, 0x3F, 0, 0);

            /* Wait 100ms */
            SDL_Delay(100);

            printf("intro: fade to black done, starting ANI#1\n");
            data->phase = 4;
            data->phase_frame = 0;
            break;
        }

        /* ---- Phase 4: ANI#1 menu intro ----
         * Original: load FDOTHER[7] (image) + FDOTHER[8] (palette) →
         *   clear screen → brightness 0 → sub_20421(1, 15, 1) */
        case 4:
        {
            if (data->phase_frame == 0) {
                /* Load FDOTHER[8] as palette (original: FDOTHER_DAT = sub_111BA(8)) */
                u32 pal_size;
                const u8* pal_res = fd2_resources_get(
                    &game->resources, FD2_DAT_FDOTHER, 8, &pal_size);
                if (pal_res && pal_size == FD2_PALETTE_BYTES) {
                    fd2_render_set_palette_6bit(&game->render, pal_res);
                }

                /* Clear screen, set brightness to 0 */
                fd2_render_fill_screen(&game->render, 0);
                fd2_render_set_brightness(&game->render, 0);
                fd2_render_present(&game->render);

                intro_start_ani(game, data, 1, 15);
            }

            int result = intro_play_ani_frame(game, data);
            if (result == -2) return FD2_STATE_QUIT;
            if (result != 0) {
                if (data->ani_data) { free(data->ani_data); data->ani_data = NULL; }
                if (data->afm) { free(data->afm); data->afm = NULL; }
                printf("intro: ANI#1 (menu intro) done, fading in menu\n");
                data->phase = 5;
                data->phase_frame = 0;
                return FD2_STATE_INTRO;
            }

            SDL_Delay(data->ani_frame_delay);
            data->phase_frame++;
            break;
        }

        /* ---- Phase 5: Fade in menu background ----
         * Original after ANI#1: sub_11DF2(0,255,64) (add 64 to palette) →
         *   sub_16886(FDOTHER[7]) (draw menu image) →
         *   sub_2DF01 fade from (56,60,63) to full palette over 40 steps, 8ms each */
        case 5:
        {
            /* Load FDOTHER[8] as palette (original: FDOTHER_DAT = sub_111BA(8)) */
            u32 pal5_size;
            const u8* pal5_res = fd2_resources_get(
                &game->resources, FD2_DAT_FDOTHER, 8, &pal5_size);
            if (pal5_res && pal5_size == FD2_PALETTE_BYTES) {
                fd2_render_set_palette_6bit(&game->render, pal5_res);
            }

            /* sub_11DF2(0, 255, 64): add 64 to every palette entry in 6-bit space.
             * Since 64 > 63, every entry clamps to 63 = max brightness.
             * This creates a "whitened" palette as the fade target, so the
             * menu background appears slightly brighter than normal. */
            fd2_render_palette_add_6bit(&game->render, 64);

            /* Draw FDOTHER[7] as menu background image
             * (original: sub_16886(FDOTHER[7]) draws to screen) */
            fd2_render_fill_screen(&game->render, 0);
            u32 res7_size;
            const u8* res7 = fd2_resources_get(&game->resources, FD2_DAT_FDOTHER, 7, &res7_size);
            if (res7) {
                fd2_render_blit_rle(&game->render, res7, res7_size, 0, 0);
            }

            /* Fade from dim cool-blue (0x38,0x3C,0x3F) to full brightened palette
             * over 40 steps, 8ms each (sub_2DF01 ascending: n40_1=0..40).
             * The base color (56,60,63) in 6-bit is a dark cool blue-gray,
             * giving the fade-in a characteristic cold tint instead of pure black. */
            fd2_render_fade_from_color(&game->render, 40, 8, 0x38, 0x3C, 0x3F);

            data->phase = 6;
            data->phase_frame = 0;
            break;
        }

        /* ---- Phase 6: Done — transition to MENU ---- */
        case 6:
            return FD2_STATE_MENU;

        default:
            return FD2_STATE_MENU;
    }

    return FD2_STATE_INTRO;
}

static void state_intro_exit(fd2_game_t* game) {
    state_intro_data_t* data = (state_intro_data_t*)game->state_data;
    if (data) {
        if (data->ani_data) free(data->ani_data);
        if (data->afm) free(data->afm);
        if (data->scroll_buf) free(data->scroll_buf);
        free(data);
    }
    game->state_data = NULL;
}

/* ---- MENU State ----
 * Main menu. Based on sub_1FF79 (draws menu items) and the input loop
 * in sub_1F894 (up/down/select with blink animation).
 *
 * Menu items use FDOTHER resources 1-6:
 *   Resources 1,3,5 = unselected items (1P, VS, Demo)
 *   Resources 2,4,6 = selected items (1P, VS, Demo)
 *
 * The number of visible items depends on game mode (n100):
 *   n100=2 → 1 item only (1P)
 *   n100=3 → 2 items (1P, VS)
 *   n100=4 → 3 items (1P, VS, Demo)
 *
 * Menu items are drawn at fixed screen positions:
 *   Item 0 (1P):  y_offset = 707969  → row ~1105 * 320 / ... → pixel offset
 *   Item 1 (VS):  y_offset = 710849
 *   Item 2 (Demo): y_offset = 713729
 *
 * Selected item blinks 4 times (80ms on/off) before confirming.
 */

typedef struct {
    int  menu_selection;   /* 0=1P, 1=VS, 2=Demo */
    int  num_items;         /* Number of visible menu items (2-4) */
    int  blink_timer;       /* For blink animation after selection */
    int  blink_count;       /* How many blink cycles completed */
    bool selected;          /* True once player hits Start on an item */
    bool blink_visible;     /* True = show selected item, False = hide */
} state_menu_data_t;

/* Draw the menu. Matches sub_1FF79.
 *   selection: -1 = draw without highlight, 0..2 = highlight that item
 *   num_items: how many items to show (2-4)
 */
static void menu_draw(fd2_game_t* game, int selection, int num_items) {
    /* Draw menu background (FDOTHER 101) */
    u32 menu_size;
    const u8* menu_res = fd2_resources_get(&game->resources, FD2_DAT_FDOTHER, 101, &menu_size);
    fd2_render_fill_screen(&game->render, 0);
    if (menu_res) {
        fd2_render_blit_rle(&game->render, menu_res, menu_size, 0, 0);
    }

    /* Draw menu items.
     * sub_1FF79 uses sub_16886 to decompress resources at specific Y offsets.
     * The resources are:
     *   FDOTHER[1] = 1P unselected,  FDOTHER[2] = 1P selected
     *   FDOTHER[3] = VS unselected,  FDOTHER[4] = VS selected
     *   FDOTHER[5] = Demo unselected, FDOTHER[6] = Demo selected
     *
     * Y offsets (from sub_1FF79 / sub_16886):
     *   Item 0: 707969 = 320*2212 + 49 → row 2212 is out of screen range...
     *   Actually these are memory addresses. 707969 / 320 = 2212.4 — that's the
     *   resource offset, not screen position. sub_16886 decompresses RLE data
     *   from the DAT file directly to the video buffer at a given Y offset.
     *   For now, we blit each item at estimated screen positions.
     */

    /* Menu item positions from original sub_1FF79 / sub_16886.
     * Video buffer offsets: 707969, 710849, 713729
     * Minus 655360 (video base) = 52609, 55489, 58369
     * 52609 / 320 = 164 remainder 49  → y=164, x=49
     * 55489 / 320 = 173 remainder 49  → y=173, x=49
     * 58369 / 320 = 182 remainder 49  → y=182, x=49
     */
    static const int item_x = 49;
    static const int item_y[3] = { 164, 173, 182 };

    /* Draw each visible item */
    for (int i = 0; i < num_items && i < 3; i++) {
        int unselected_res = 1 + i * 2;  /* 1, 3, 5 */
        int selected_res   = 2 + i * 2;  /* 2, 4, 6 */

        int res_idx = (i == selection) ? selected_res : unselected_res;

        u32 item_size;
        const u8* item_res = fd2_resources_get(&game->resources, FD2_DAT_FDOTHER, res_idx, &item_size);
        if (item_res) {
            /* Center the item horizontally */
            u8* pixels = NULL;
            int w, h;
            if (fd2_rle_decompress_from_resource(item_res, item_size, &pixels, &w, &h) == 0) {
                fd2_render_blit(&game->render, pixels, w, h, item_x, item_y[i]);
                free(pixels);
            }
        }
    }

    fd2_render_present(&game->render);
}

static void state_menu_enter(fd2_game_t* game) {
    state_menu_data_t* data = (state_menu_data_t*)calloc(1, sizeof(state_menu_data_t));
    game->state_data = data;
    data->menu_selection = 0;
    data->num_items = 3;    /* Default: show all 3 items */
    data->blink_timer = 0;
    data->blink_count = 0;
    data->selected = false;
    data->blink_visible = true;

    /* Set up palette for menu */
    u32 pal_size;
    const u8* pal_res = fd2_resources_get(&game->resources, FD2_DAT_FDOTHER, 7, &pal_size);
    if (pal_res && pal_size == FD2_PALETTE_BYTES) {
        fd2_render_set_palette_6bit(&game->render, pal_res);
    }
    fd2_render_set_brightness(&game->render, 56);  /* 0x38 from original */

    /* Draw initial menu with selection on first item */
    menu_draw(game, 0, data->num_items);

    printf("state_menu: entered\n");
}

static fd2_state_t state_menu_update(fd2_game_t* game) {
    state_menu_data_t* data = (state_menu_data_t*)game->state_data;
    if (!data) return FD2_STATE_QUIT;

    /* ESC returns to intro (or quits) */
    if (fd2_action_pressed(&game->input, FD2_ACTION_ESCAPE)) {
        return FD2_STATE_QUIT;
    }

    /* If we're in the blink-after-selection state */
    if (data->selected) {
        data->blink_timer++;

        /* Blink every ~80ms (about 5 frames at 60fps) */
        if (data->blink_timer >= 5) {
            data->blink_timer = 0;
            data->blink_visible = !data->blink_visible;
            data->blink_count++;

            /* Draw with or without selected item */
            menu_draw(game, data->blink_visible ? data->menu_selection : -1,
                      data->num_items);
        }

        /* After 4 full blink cycles (8 half-cycles), confirm selection */
        if (data->blink_count >= 8) {
            /* Dispatch based on selection */
            switch (data->menu_selection) {
                case 0:  /* 1 Player */
                    game->game_mode = 0;
                    return FD2_STATE_CHAR_SELECT;
                case 1:  /* VS Mode */
                    game->game_mode = 1;
                    return FD2_STATE_CHAR_SELECT;
                case 2:  /* Demo */
                    game->game_mode = 2;
                    return FD2_STATE_DEMO;
                default:
                    game->game_mode = 0;
                    return FD2_STATE_CHAR_SELECT;
            }
        }

        return FD2_STATE_MENU;
    }

    /* Normal menu navigation */
    if (fd2_action_pressed(&game->input, FD2_ACTION_UP)) {
        data->menu_selection = (data->menu_selection - 1 + data->num_items) % data->num_items;
        menu_draw(game, data->menu_selection, data->num_items);
    }
    if (fd2_action_pressed(&game->input, FD2_ACTION_DOWN)) {
        data->menu_selection = (data->menu_selection + 1) % data->num_items;
        menu_draw(game, data->menu_selection, data->num_items);
    }

    /* Start button confirms selection → blink animation */
    if (fd2_action_pressed(&game->input, FD2_ACTION_START) ||
        fd2_action_pressed(&game->input, FD2_ACTION_A)) {
        data->selected = true;
        data->blink_timer = 0;
        data->blink_count = 0;
        data->blink_visible = true;
        /* Original: sub_25A96(1, 1) — play selection sound */
    }

    return FD2_STATE_MENU;
}

static void state_menu_exit(fd2_game_t* game) {
    free(game->state_data);
    game->state_data = NULL;
}

/* ---- DEMO State ----
 * Demo/attract mode. Placeholder.
 */
static void state_demo_enter(fd2_game_t* game) {
    (void)game;
    printf("state_demo: entered (placeholder)\n");
}

static fd2_state_t state_demo_update(fd2_game_t* game) {
    if (fd2_action_pressed(&game->input, FD2_ACTION_ESCAPE) ||
        fd2_input_any_pressed(&game->input)) {
        return FD2_STATE_MENU;
    }
    return FD2_STATE_DEMO;
}

static void state_demo_exit(fd2_game_t* game) {
    (void)game;
}

/* ---- CHAR_SELECT State ----
 * Character selection. Placeholder.
 */
static void state_char_select_enter(fd2_game_t* game) {
    game->state_data = NULL;

    /* Load character select resources */
    fd2_resources_load_dat(&game->resources, FD2_DAT_FDSHAP);
    fd2_resources_load_dat(&game->resources, FD2_DAT_TAI);

    fd2_render_fill_screen(&game->render, 0);
    fd2_render_present(&game->render);

    printf("state_char_select: entered (placeholder)\n");
}

static fd2_state_t state_char_select_update(fd2_game_t* game) {
    if (fd2_action_pressed(&game->input, FD2_ACTION_ESCAPE)) {
        return FD2_STATE_MENU;
    }
    if (fd2_action_pressed(&game->input, FD2_ACTION_START)) {
        /* Select character and start battle */
        return FD2_STATE_BATTLE;
    }
    return FD2_STATE_CHAR_SELECT;
}

static void state_char_select_exit(fd2_game_t* game) {
    (void)game;
}

/* ---- BATTLE State ----
 * In-game fight. Based on sub_10010.
 * Placeholder: just shows a black screen.
 */
static void state_battle_enter(fd2_game_t* game) {
    /* Load battle resources */
    fd2_resources_load_dat(&game->resources, FD2_DAT_FDFIELD);
    fd2_resources_load_dat(&game->resources, FD2_DAT_FDSHAP);
    fd2_resources_load_dat(&game->resources, FD2_DAT_FIGANI);
    fd2_resources_load_dat(&game->resources, FD2_DAT_DATO);

    fd2_render_fill_screen(&game->render, 0);
    fd2_render_present(&game->render);

    printf("state_battle: entered (placeholder)\n");
}

static fd2_state_t state_battle_update(fd2_game_t* game) {
    if (fd2_action_pressed(&game->input, FD2_ACTION_ESCAPE)) {
        return FD2_STATE_MENU;
    }
    return FD2_STATE_BATTLE;
}

static void state_battle_exit(fd2_game_t* game) {
    (void)game;
}

/* ---- VICTORY State ----
 * Round/match result. Placeholder.
 */
static void state_victory_enter(fd2_game_t* game) { (void)game; }
static fd2_state_t state_victory_update(fd2_game_t* game) {
    (void)game;
    return FD2_STATE_MENU;
}
static void state_victory_exit(fd2_game_t* game) { (void)game; }

/* ---- CONTINUE State ----
 * Continue screen. Placeholder.
 */
static void state_continue_enter(fd2_game_t* game) { (void)game; }
static fd2_state_t state_continue_update(fd2_game_t* game) {
    if (fd2_action_pressed(&game->input, FD2_ACTION_START)) {
        return FD2_STATE_CHAR_SELECT;
    }
    return FD2_STATE_GAME_OVER;
}
static void state_continue_exit(fd2_game_t* game) { (void)game; }

/* ---- GAME_OVER State ----
 * Game over screen. Placeholder.
 */
static void state_game_over_enter(fd2_game_t* game) { (void)game; }
static fd2_state_t state_game_over_update(fd2_game_t* game) {
    (void)game;
    return FD2_STATE_MENU;
}
static void state_game_over_exit(fd2_game_t* game) { (void)game; }
