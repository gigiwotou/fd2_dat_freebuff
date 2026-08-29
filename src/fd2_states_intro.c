/**
 * FD2 INTRO State
 *
 * Opening animation sequence.
 * 1:1 match of sub_1F894 flow:
 *   Phase 0: Title screen (FDOTHER 74) -> fade in -> wait 30 ticks -> fade out
 *   Phase 1: ANI#3 (intro cinematic, 90ms) -> fade out
 *   Phase 2: Scroll (FDOTHER 69-73, 535->0) with ANI/overlay at positions
 *   Phase 3: Fade to black
 *   Phase 4: ANI#1 (menu intro, 15ms)
 *   Phase 5: Fade in menu background
 *   Phase 6: -> transition to MENU state
 */

#define _GNU_SOURCE
#include "fd2_game.h"
#include "fd2_intro.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

typedef struct {
    int  phase;
    int  phase_frame;

    fd2_afm_t* afm;
    u8*        ani_data;
    int        ani_resource;
    int        ani_frame_delay;

    u8*  scroll_buf;
    int  scroll_total_h;
    int  scroll_pos;

    int  scroll_ani_step;
    int  scroll_ani_queue[3];
    int  scroll_ani_queue_len;
    int  scroll_ani_queue_idx;
    int  scroll_ani_delay[3];
    int  scroll_ani_palette[3];
    bool scroll_ani_needs_fadeout;
    bool scroll_ani_after_end;

    int  overlay_step;
    int  overlay_image_res;
    int  overlay_palette_res;
    int  overlay_wait;

    int  palette_flash_trigger_idx;
    int  palette_flash_frame_count;
    bool palette_flash_active;
} state_intro_data_t;

static int intro_play_ani_frame(fd2_game_t* game, state_intro_data_t* data) {
    if (!data->afm) return -1;

    if (fd2_afm_is_done(data->afm)) {
        return 1;
    }

    if (fd2_afm_decode_next_frame(data->afm) != 0) {
        return 1;
    }

    fd2_render_set_palette_6bit(&game->render, fd2_afm_get_palette(data->afm));
    fd2_render_blit_afm(&game->render, fd2_afm_get_frame(data->afm), -1);
    fd2_render_present(&game->render);

    SDL_Event e;
    while (SDL_PollEvent(&e)) {
        if (e.type == SDL_QUIT) return -2;
    }

    return 0;
}

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

    fseek(f, 0x06 + ani_index * 4, SEEK_SET);
    u32 afm_offset = 0;
    if (fread(&afm_offset, 4, 1, f) != 1) {
        fprintf(stderr, "intro: cannot read ANI.DAT index %d\n", ani_index);
        fclose(f);
        return -1;
    }

    if (fseek(f, afm_offset, SEEK_SET) != 0) {
        fprintf(stderr, "intro: cannot seek to AFM offset 0x%X\n", afm_offset);
        fclose(f);
        return -1;
    }

    u8 header[FD2_AFM_HEADER_SIZE];
    if (fread(header, 1, FD2_AFM_HEADER_SIZE, f) != FD2_AFM_HEADER_SIZE) {
        fprintf(stderr, "intro: cannot read AFM header for ANI#%d\n", ani_index);
        fclose(f);
        return -1;
    }

    if (memcmp(header, "AFM", 3) != 0) {
        fprintf(stderr, "intro: ANI#%d has invalid AFM signature\n", ani_index);
        fclose(f);
        return -1;
    }

    u16 frame_count = (u16)header[0xA5] | ((u16)header[0xA6] << 8);

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

        if (fseek(f, frame_size, SEEK_CUR) != 0) {
            fprintf(stderr, "intro: cannot seek past frame %d\n", i);
            fclose(f);
            return -1;
        }
    }

    u8* afm_data = (u8*)malloc(total_size);
    if (!afm_data) {
        fprintf(stderr, "intro: cannot allocate AFM buffer (%u bytes)\n", total_size);
        fclose(f);
        return -1;
    }

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

static int intro_start_ani(fd2_game_t* game, state_intro_data_t* data,
                           int ani_index, int frame_delay_ms) {
    if (data->afm) {
        if (data->ani_data) {
            free(data->ani_data);
            data->ani_data = NULL;
        }
        free(data->afm);
        data->afm = NULL;
    }

    const char* ani_path = fd2_resources_dat_path(&game->resources, FD2_DAT_ANI);
    if (!ani_path) {
        fprintf(stderr, "intro: cannot get ANI.DAT path\n");
        return -1;
    }

    u8* afm_data = NULL;
    u32 afm_size = 0;

    if (load_ani_afm_from_file(ani_path, ani_index, &afm_data, &afm_size) != 0) {
        fprintf(stderr, "intro: failed to load ANI#%d from ANI.DAT\n", ani_index);
        return -1;
    }

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

    data->ani_data = afm_data;
    data->ani_resource = ani_index;
    data->ani_frame_delay = frame_delay_ms;

    printf("intro: playing ANI#%d (%u frames, %dms delay)\n",
           ani_index, data->afm->total_frames, frame_delay_ms);
    return 0;
}

static void intro_build_scroll_buffer(fd2_game_t* game, state_intro_data_t* data) {
    const int frame_h = 147;
    const int num_frames = 5;
    data->scroll_total_h = frame_h * num_frames;
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
                int copy_h = fh < frame_h ? fh : frame_h;
                int copy_w = fw < FD2_SCREEN_W ? fw : FD2_SCREEN_W;
                fprintf(stderr, "[intro] Frame %d (res %d): RLE size=%u, dim=%dx%d, dst_y=%d, copy_h=%d\n",
                        i, 69 + i, fsize, fw, fh, dst_y, copy_h);
                for (int y = 0; y < copy_h; y++) {
                    memcpy(data->scroll_buf + (dst_y + y) * FD2_SCREEN_W,
                           fpixels + y * fw, copy_w);
                }
                fprintf(stderr, "[intro] Frame %d: first_byte=%d, last_byte=%d\n",
                        i, data->scroll_buf[dst_y * FD2_SCREEN_W],
                        data->scroll_buf[(dst_y + copy_h - 1) * FD2_SCREEN_W + copy_w - 1]);
                free(fpixels);
            }
        } else {
            fprintf(stderr, "[intro] Frame %d (res %d): NOT FOUND\n", i, 69 + i);
        }
    }
    fprintf(stderr, "[intro] Total buffer height: %d (expected: 735)\n", data->scroll_total_h);
}

void state_intro_enter(fd2_game_t* game) {
    state_intro_data_t* data = (state_intro_data_t*)calloc(1, sizeof(state_intro_data_t));
    game->state_data = data;
    data->phase = 0;
    data->phase_frame = 0;
    data->afm = NULL;
    data->ani_data = NULL;
    data->scroll_buf = NULL;

    const char* fdmus_path = fd2_resources_dat_path(&game->resources, FD2_DAT_FDMUS);
    fd2_audio_set_fdmus_path(&game->audio, fdmus_path);

    fd2_audio_play_music(&game->audio, 11, -1);

    u32 pal_size;
    const u8* pal_res = fd2_resources_get(&game->resources, FD2_DAT_FDOTHER, 76, &pal_size);
    if (pal_res && pal_size == FD2_PALETTE_BYTES) {
        fd2_render_set_palette_6bit(&game->render, pal_res);
    }

    u32 title_size;
    const u8* title_res = fd2_resources_get(&game->resources, FD2_DAT_FDOTHER, 74, &title_size);
    fd2_render_fill_screen(&game->render, 0);
    if (title_res) {
        fd2_render_blit_rle(&game->render, title_res, title_size, 0, 0);
    }

    fd2_render_set_brightness(&game->render, 64);
    fd2_render_present(&game->render);
}

fd2_state_t state_intro_update(fd2_game_t* game) {
    state_intro_data_t* data = (state_intro_data_t*)game->state_data;
    if (!data) return FD2_STATE_QUIT;

    if (fd2_action_pressed(&game->input, FD2_ACTION_ESCAPE) ||
        fd2_input_any_pressed(&game->input)) {
        if (data->ani_data) { free(data->ani_data); data->ani_data = NULL; }
        if (data->afm) { free(data->afm); data->afm = NULL; }
        if (data->scroll_buf) { free(data->scroll_buf); data->scroll_buf = NULL; }
        data->scroll_ani_step = 0;
        return FD2_STATE_MENU;
    }

    switch (data->phase) {
        case 0:
        {
            if (data->phase_frame == 0) {
                fd2_render_fade_from_black(&game->render, 64, 2);
            }
            data->phase_frame++;
            if (data->phase_frame >= 30 + 64) {
                fd2_render_fade_to_black(&game->render, 64, 2);
                printf("intro: phase 0 done (title faded out), starting Phase 1 (ANI#3)\n");
                data->phase = 1;
                data->phase_frame = 0;
            }
            break;
        }

        case 1:
        {
            if (data->phase_frame == 0) {
                u32 pal_size;
                const u8* pal_res = fd2_resources_get(
                    &game->resources, FD2_DAT_FDOTHER, 99, &pal_size);
                if (pal_res && pal_size == FD2_PALETTE_BYTES) {
                    fd2_render_set_palette_6bit(&game->render, pal_res);
                }

                fd2_render_fill_screen(&game->render, 0);
                fd2_render_set_brightness(&game->render, 0);
                fd2_render_present(&game->render);

                intro_start_ani(game, data, 3, 90);
            }

            int result = intro_play_ani_frame(game, data);
            if (result == -2) return FD2_STATE_QUIT;
            if (result != 0) {
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

        case 2:
        {
            if (data->phase_frame == 0) {
                printf("intro: phase 2 init (scroll buffer setup)\n");

                fd2_render_fill_screen(&game->render, 0);

                u32 pal_size;
                const u8* pal_res = fd2_resources_get(
                    &game->resources, FD2_DAT_FDOTHER, 100, &pal_size);
                if (pal_res && pal_size == FD2_PALETTE_BYTES) {
                    fd2_render_set_palette_6bit(&game->render, pal_res);
                }

                fd2_render_set_brightness(&game->render, 64);

                intro_build_scroll_buffer(game, data);

                if (!data->scroll_buf) {
                    fprintf(stderr, "intro ERROR: scroll buffer allocation failed!\n");
                    data->phase = 3;
                    data->phase_frame = 0;
                    break;
                }
                printf("intro: scroll buffer built, size %dx%d\n",
                       FD2_SCREEN_W, data->scroll_total_h);

                data->scroll_pos = 535;
                data->phase_frame = 1;
                data->scroll_ani_needs_fadeout = false;
                data->scroll_ani_after_end = false;
                data->overlay_step = 0;
                data->scroll_ani_step = 0;

                int pos = data->scroll_pos;
                for (int y = 0; y < FD2_SCREEN_H && (pos + y) < data->scroll_total_h; y++) {
                    memcpy(game->render.screen + y * FD2_SCREEN_W,
                           data->scroll_buf + (pos + y) * FD2_SCREEN_W,
                           FD2_SCREEN_W);
                }
                fd2_render_fade_from_black(&game->render, 64, 2);

                printf("intro: scroll started from pos 535, entering main loop\n");
            }

            if (data->overlay_step != 0) {
                printf("intro: overlay_step=%d (image=%d)\n", data->overlay_step, data->overlay_image_res);
                switch (data->overlay_step) {
                    case 1:
                    {
                        printf("intro: overlay step 1 - fade out and draw\n");
                        fd2_render_fade_to_black(&game->render, 64, 2);
                        fd2_render_fill_screen(&game->render, 0);

                        u32 pal_size;
                        const u8* pal_res = fd2_resources_get(
                            &game->resources, FD2_DAT_FDOTHER,
                            data->overlay_palette_res, &pal_size);
                        if (pal_res && pal_size == FD2_PALETTE_BYTES) {
                            fd2_render_set_palette_6bit(&game->render, pal_res);
                        }

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
                    case 2:
                    {
                        data->overlay_wait++;
                        if (data->overlay_wait >= 7) {
                            data->overlay_step = 3;
                        }
                        break;
                    }
                    case 3:
                    {
                        fd2_render_fade_to_black(&game->render, 64, 2);

                        int pos = data->scroll_pos;
                        if (data->scroll_buf) {
                            fd2_render_fill_screen(&game->render, 0);
                            for (int y = 0; y < FD2_SCREEN_H && (pos + y) < data->scroll_total_h; y++) {
                                memcpy(game->render.screen + y * FD2_SCREEN_W,
                                       data->scroll_buf + (pos + y) * FD2_SCREEN_W,
                                       FD2_SCREEN_W);
                            }
                        }

                        u32 pal_size;
                        const u8* pal_res = fd2_resources_get(
                            &game->resources, FD2_DAT_FDOTHER, 102, &pal_size);
                        if (pal_res && pal_size == FD2_PALETTE_BYTES) {
                            fd2_render_set_palette_6bit(&game->render, pal_res);
                        }

                        fd2_render_fade_from_black(&game->render, 64, 2);
                        data->overlay_step = 0;
                        data->scroll_pos--;

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

            static const int flash_triggers[] = {
                520, 490, 460, 430, 400, 370, 340, 310, 280, 250, 220, 190,
                160, 130, 100, 80, 60, 40, 20, 10
            };
            static const int num_flash_triggers = sizeof(flash_triggers) / sizeof(flash_triggers[0]);

            int pos = data->scroll_pos;

            if (data->palette_flash_trigger_idx < num_flash_triggers) {
                int next_trigger = flash_triggers[data->palette_flash_trigger_idx];
                if (pos <= next_trigger + 5 && pos >= next_trigger - 5) {
                    printf("intro: palette check - pos=%d, next_trigger=%d (idx %d/%d), active=%d, count=%d\n",
                           pos, next_trigger, data->palette_flash_trigger_idx + 1, num_flash_triggers,
                           data->palette_flash_active, data->palette_flash_frame_count);
                }
                if (pos == next_trigger) {
                    u32 pal_size;
                    const u8* dark_pal = fd2_resources_get(
                        &game->resources, FD2_DAT_FDOTHER, 102, &pal_size);
                    if (dark_pal && pal_size == FD2_PALETTE_BYTES) {
                        fd2_render_set_palette_6bit(&game->render, dark_pal);
                        printf("intro: >>> palette flash TRIGGER at pos %d (trigger %d/%d) <<<\n",
                               pos, data->palette_flash_trigger_idx + 1, num_flash_triggers);
                        data->palette_flash_active = true;
                        data->palette_flash_frame_count = 0;
                        data->palette_flash_trigger_idx++;
                    } else {
                        printf("intro: WARNING - dark palette resource not found or wrong size!\n");
                        data->palette_flash_trigger_idx++;
                    }
                }
            }

            if (data->palette_flash_active && data->palette_flash_frame_count >= 11) {
                u32 pal_size;
                const u8* normal_pal = fd2_resources_get(
                    &game->resources, FD2_DAT_FDOTHER, 101, &pal_size);
                if (normal_pal && pal_size == FD2_PALETTE_BYTES) {
                    fd2_render_set_palette_6bit(&game->render, normal_pal);
                    printf("intro: palette flash RESTORE after %d frames\n", data->palette_flash_frame_count);
                    data->palette_flash_active = false;
                    data->palette_flash_frame_count = 0;
                }
            }

            data->palette_flash_frame_count++;

            if (data->scroll_ani_step != 0) {
                switch (data->scroll_ani_step) {
                    case 1:
                    {
                        if (data->scroll_ani_needs_fadeout) {
                            fd2_render_fade_to_black(&game->render, 64, 2);
                            data->scroll_ani_needs_fadeout = false;
                        }

                        int ani_id = data->scroll_ani_queue[data->scroll_ani_queue_idx];
                        int palette_res = data->scroll_ani_palette[data->scroll_ani_queue_idx];
                        int delay_ms = data->scroll_ani_delay[data->scroll_ani_queue_idx];

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

                        if (intro_start_ani(game, data, ani_id, delay_ms) == 0) {
                            data->scroll_ani_step = 2;
                        } else {
                            data->scroll_ani_queue_idx++;
                            if (data->scroll_ani_queue_idx >= data->scroll_ani_queue_len) {
                                data->scroll_ani_step = 3;
                            }
                        }
                        break;
                    }

                    case 2:
                    {
                        int result = intro_play_ani_frame(game, data);
                        if (result == -2) return FD2_STATE_QUIT;

                        if (result != 0) {
                            if (data->ani_data) { free(data->ani_data); data->ani_data = NULL; }
                            if (data->afm) { free(data->afm); data->afm = NULL; }
                            fd2_render_fade_to_black(&game->render, 64, 2);
                            data->scroll_ani_queue_idx++;

                            if (data->scroll_ani_queue_idx >= data->scroll_ani_queue_len) {
                                data->scroll_ani_step = 3;
                            } else {
                                data->scroll_ani_step = 1;
                            }
                        } else {
                            SDL_Delay(data->ani_frame_delay);
                        }
                        break;
                    }

                    case 3:
                    {
                        if (data->scroll_buf) {
                            fd2_render_fill_screen(&game->render, 0);
                            for (int y = 0; y < FD2_SCREEN_H && (pos + y) < data->scroll_total_h; y++) {
                                memcpy(game->render.screen + y * FD2_SCREEN_W,
                                       data->scroll_buf + (pos + y) * FD2_SCREEN_W,
                                       FD2_SCREEN_W);
                            }
                        }

                        u32 pal_size;
                        const u8* pal_res = fd2_resources_get(
                            &game->resources, FD2_DAT_FDOTHER, 102, &pal_size);
                        if (pal_res && pal_size == FD2_PALETTE_BYTES) {
                            fd2_render_set_palette_6bit(&game->render, pal_res);
                        }

                        fd2_render_fade_from_black(&game->render, 64, 2);

                        data->scroll_ani_step = 0;
                        data->scroll_ani_queue_len = 0;
                        data->scroll_ani_queue_idx = 0;
                        data->scroll_pos--;
                        printf("intro: ANI at pos %d done, resuming scroll at pos %d\n",
                               pos, data->scroll_pos);
                        break;
                    }
                }
                return FD2_STATE_INTRO;
            }

            pos = data->scroll_pos;
            if (pos < 0) {
                printf("intro: scroll done at pos %d, fading to black\n", pos);
                data->phase = 3;
                data->phase_frame = 0;
                break;
            }

            if (!data->scroll_buf) {
                fprintf(stderr, "intro ERROR: scroll_buf is NULL at pos %d\n", pos);
                data->phase = 3;
                data->phase_frame = 0;
                break;
            }

            for (int y = 0; y < FD2_SCREEN_H && (pos + y) < data->scroll_total_h; y++) {
                memcpy(game->render.screen + y * FD2_SCREEN_W,
                       data->scroll_buf + (pos + y) * FD2_SCREEN_W,
                       FD2_SCREEN_W);
            }

            if ((pos % 25) == 0) {
                printf("intro: scroll pos %d (overlay_step=%d, scroll_ani_step=%d)\n",
                       pos, data->overlay_step, data->scroll_ani_step);
            }

            if (pos == 450) {
                printf("intro: TRIGGERING OVERLAY at pos 450 (image=%d, palette=%d)\n", 99, 98);
                data->overlay_image_res = 100;
                data->overlay_palette_res = 99;
                data->overlay_step = 1;
                break;
            }
            if (pos == 10) {
                data->overlay_image_res = 75;
                data->overlay_palette_res = 76;
                data->overlay_step = 1;
                break;
            }

            if ((pos == 330 || pos == 210 || pos == 110 || pos == 25)
                && data->scroll_ani_step == 0) {
                if (pos == 330) {
                    data->scroll_ani_queue[0] = 5;
                    data->scroll_ani_queue[1] = 6;
                    data->scroll_ani_queue_len = 2;
                    data->scroll_ani_palette[0] = 100;
                    data->scroll_ani_palette[1] = 1;
                    data->scroll_ani_delay[0] = 90;
                    data->scroll_ani_delay[1] = 50;
                    data->scroll_ani_needs_fadeout = true;
                    data->scroll_ani_after_end = false;
                } else if (pos == 210) {
                    data->scroll_ani_queue[0] = 7;
                    data->scroll_ani_queue[1] = 8;
                    data->scroll_ani_queue_len = 2;
                    data->scroll_ani_palette[0] = 100;
                    data->scroll_ani_palette[1] = 1;
                    data->scroll_ani_delay[0] = 90;
                    data->scroll_ani_delay[1] = 50;
                    data->scroll_ani_needs_fadeout = true;
                    data->scroll_ani_after_end = false;
                } else if (pos == 110) {
                    data->scroll_ani_queue[0] = 9;
                    data->scroll_ani_queue_len = 1;
                    data->scroll_ani_palette[0] = 100;
                    data->scroll_ani_delay[0] = 90;
                    data->scroll_ani_needs_fadeout = true;
                    data->scroll_ani_after_end = false;
                } else {
                    data->scroll_ani_queue[0] = 1;
                    data->scroll_ani_queue_len = 1;
                    data->scroll_ani_palette[0] = 1;
                    data->scroll_ani_delay[0] = 15;
                    data->scroll_ani_needs_fadeout = false;
                    data->scroll_ani_after_end = true;
                }
                data->scroll_ani_queue_idx = 0;
                data->scroll_ani_step = 1;
                printf("intro: scroll pos %d - triggering ANI queue[%d] len=%d%s\n",
                       pos, data->scroll_ani_queue[0], data->scroll_ani_queue_len,
                       data->scroll_ani_after_end ? " (END SCROLL)" : "");
                break;
            }

            fd2_render_present(&game->render);

            {
                SDL_Event e;
                while (SDL_PollEvent(&e)) {
                    if (e.type == SDL_QUIT) return FD2_STATE_QUIT;
                }
            }

            SDL_Delay(30);

            if (data->scroll_pos == 0) {
                SDL_Delay(1000);
            }

            data->scroll_pos--;
            break;
        }

        case 3:
        {
            if (data->scroll_buf) {
                free(data->scroll_buf);
                data->scroll_buf = NULL;
            }

            fd2_render_fade_to_color(&game->render, 40, 8, 0x3F, 0, 0);

            SDL_Delay(100);

            printf("intro: fade to black done, starting ANI#1\n");
            data->phase = 4;
            data->phase_frame = 0;
            break;
        }

        case 4:
        {
            if (data->phase_frame == 0) {
                u32 pal_size;
                const u8* pal_res = fd2_resources_get(
                    &game->resources, FD2_DAT_FDOTHER, 9, &pal_size);
                if (pal_res && pal_size == FD2_PALETTE_BYTES) {
                    fd2_render_set_palette_6bit(&game->render, pal_res);
                }

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

        case 5:
        {
            u32 pal5_size;
            const u8* pal5_res = fd2_resources_get(
                &game->resources, FD2_DAT_FDOTHER, 9, &pal5_size);
            if (pal5_res && pal5_size == FD2_PALETTE_BYTES) {
                fd2_render_set_palette_6bit(&game->render, pal5_res);
            }

            fd2_render_palette_add_6bit(&game->render, 64);

            fd2_render_fill_screen(&game->render, 0);

            fd2_render_fade_from_color(&game->render, 40, 8, 0x38, 0x3C, 0x3F);

            data->phase = 6;
            data->phase_frame = 0;
            break;
        }

        case 6:
            return FD2_STATE_MENU;

        default:
            return FD2_STATE_MENU;
    }

    return FD2_STATE_INTRO;
}

void state_intro_exit(fd2_game_t* game) {
    state_intro_data_t* data = (state_intro_data_t*)game->state_data;
    if (data) {
        if (data->ani_data) free(data->ani_data);
        if (data->afm) free(data->afm);
        if (data->scroll_buf) free(data->scroll_buf);
        free(data);
    }
    game->state_data = NULL;
}
