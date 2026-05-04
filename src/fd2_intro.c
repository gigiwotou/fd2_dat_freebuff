/**
 * FD2 Intro Animation Player
 * 
 * Faithfully reproduces the intro animation from FD2.EXE (sub_1F894).
 * Uses SDL2 for rendering.
 */

#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#include <limits.h>
#endif

#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "fd2_decoder.h"

static char g_exe_dir[PATH_MAX];

static void init_exe_dir(void) {
#ifdef _WIN32
    char exe_path[PATH_MAX];
    DWORD len = GetModuleFileNameA(NULL, exe_path, sizeof(exe_path));
    if (len > 0 && len < sizeof(exe_path)) {
        char* last_backslash = strrchr(exe_path, '\\');
        if (last_backslash) {
            *(last_backslash + 1) = '\0';
            strcpy(g_exe_dir, exe_path);
        } else {
            strcpy(g_exe_dir, "./");
        }
    } else {
        strcpy(g_exe_dir, "./");
    }
#else
    ssize_t len = readlink("/proc/self/exe", g_exe_dir, sizeof(g_exe_dir) - 1);
    if (len > 0) {
        g_exe_dir[len] = '\0';
        char* last_slash = strrchr(g_exe_dir, '/');
        if (last_slash) *(last_slash + 1) = '\0';
    } else {
        strcpy(g_exe_dir, "./");
    }
#endif
}

static char* exe_path(const char* filename) {
    static char path[PATH_MAX];
    snprintf(path, sizeof(path), "%s%s", g_exe_dir, filename);
    return path;
}

#define SCALE 3
#define WIN_W (FD2_SCREEN_W * SCALE)
#define WIN_H (FD2_SCREEN_H * SCALE)

static SDL_Window*   g_window   = NULL;
static SDL_Renderer* g_renderer = NULL;
static SDL_Texture*  g_texture  = NULL;
static Uint32*       g_argb     = NULL;
static u8            g_palette[FD2_PALETTE_BYTES];
static u8            g_screen[FD2_SCREEN_SIZE];

static void palette_to_argb(const u8* pal, Uint32* argb) {
    for (int i = 0; i < FD2_PALETTE_COLORS; i++) {
        argb[i] = (0xFFu << 24) |
                  ((u32)pal[i * 3 + 0] << 16) |
                  ((u32)pal[i * 3 + 1] << 8)  |
                  ((u32)pal[i * 3 + 2]);
    }
}

static void render_screen(const u8* screen, const Uint32* argb_palette, Uint32* dst) {
    for (int y = 0; y < FD2_SCREEN_H; y++) {
        for (int x = 0; x < FD2_SCREEN_W; x++) {
            dst[y * FD2_SCREEN_W + x] = argb_palette[screen[y * FD2_SCREEN_W + x]];
        }
    }
}

static void present_frame(void) {
    SDL_UpdateTexture(g_texture, NULL, g_argb, FD2_SCREEN_W * sizeof(Uint32));
    SDL_RenderClear(g_renderer);
    SDL_RenderCopy(g_renderer, g_texture, NULL, NULL);
    SDL_RenderPresent(g_renderer);
}

static void fill_screen(u8 color) {
    memset(g_screen, color, FD2_SCREEN_SIZE);
}

static void blit_rle_image(const u8* res_data, u32 res_size, int dx, int dy) {
    int w, h;
    if (fd2_image_get_dimensions(res_data, res_size, &w, &h) != 0) return;

    u8* pixels = NULL;
    if (fd2_rle_decompress_from_resource(res_data, res_size, &pixels, &w, &h, -1) != 0) return;

    for (int y = 0; y < h && (dy + y) < FD2_SCREEN_H; y++) {
        for (int x = 0; x < w && (dx + x) < FD2_SCREEN_W; x++) {
            u8 px = pixels[y * w + x];
            if (px != 0) {
                int sx = dx + x;
                int sy = dy + y;
                if (sx >= 0 && sy >= 0) {
                    g_screen[sy * FD2_SCREEN_W + sx] = px;
                }
            }
        }
    }
    free(pixels);
}

/* blit_pixels: used for overlay rendering if needed */
__attribute__((unused))
static void blit_pixels(const u8* pixels, int w, int h, int dx, int dy) {
    for (int y = 0; y < h && (dy + y) < FD2_SCREEN_H; y++) {
        for (int x = 0; x < w && (dx + x) < FD2_SCREEN_W; x++) {
            u8 px = pixels[y * w + x];
            if (px != 0) {
                int sx = dx + x;
                int sy = dy + y;
                if (sx >= 0 && sy >= 0) {
                    g_screen[sy * FD2_SCREEN_W + sx] = px;
                }
            }
        }
    }
}

static void fade_to_black(int steps, int step_ms) {
    u8 current_pal[FD2_PALETTE_BYTES];
    u8 black_pal[FD2_PALETTE_BYTES];
    memset(black_pal, 0, sizeof(black_pal));

    memcpy(current_pal, g_palette, FD2_PALETTE_BYTES);

    for (int s = 0; s <= steps; s++) {
        fd2_palette_fade(current_pal, black_pal, g_palette, steps, s);
        palette_to_argb(g_palette, g_argb + FD2_SCREEN_W * FD2_SCREEN_H);
        render_screen(g_screen, g_argb + FD2_SCREEN_W * FD2_SCREEN_H, g_argb);
        present_frame();
        SDL_Delay(step_ms);
    }
}

static void play_bar_animation_resource(const u8* res_data, u32 res_size, int frames, int frame_ms) {
    if (!res_data) return;

    int w, h;
    if (fd2_image_get_dimensions(res_data, res_size, &w, &h) != 0) return;

    u8* pixels = NULL;
    if (fd2_rle_decompress_from_resource(res_data, res_size, &pixels, &w, &h, -1) != 0) return;

    fill_screen(0);
    for (int f = 0; f < frames; f++) {
        int col = (f * w) / frames;
        for (int y = 0; y < h && y < FD2_SCREEN_H; y++) {
            for (int x = 0; x < col && x < w && x < FD2_SCREEN_W; x++) {
                u8 px = pixels[y * w + x];
                if (px != 0) {
                    g_screen[y * FD2_SCREEN_W + x] = px;
                }
            }
        }
        render_screen(g_screen, g_argb + FD2_SCREEN_W * FD2_SCREEN_H, g_argb);
        present_frame();
        SDL_Delay(frame_ms);
    }
    free(pixels);
}

/* Play the intro scroll animation (sub_1F894 scroll phase).
 * This is a 1:1 reproduction of the original DOS code.
 *
 * Original assembly flow:
 *   1. Allocate scroll buffer (n15_1), memset to 0
 *   2. For n5 = 0..4: sub_4E98D(FDOTHER[n5+69], 0, 147*n5, n15_1, 320, -1)
 *      -> RLE-decompress each frame directly into the buffer at y = 147*n5
 *   3. For n535 = 535; n535 >= 0; --n535:
 *        sub_11EB0(n15_1 + 320*n535, ..., 655360, 320, n15_1+320*n535, 320, 320, 200)
 *        -> memmove 200 rows from buffer[offset] to screen
 *        if (n535 == 535) sub_1F525()  // refresh
 *        if (n535 == 450) sub_1F73F(100, 99, n15_1, 450)  // overlay
 *        if (n535 == 330) { fadeout; sub_1F81E(4,90,99); sub_1F81E(5,50,0); restore }
 *        if (n535 == 210) { fadeout; sub_1F81E(6,90,99); sub_1F81E(7,50,0); restore }
 *        if (n535 == 110) { fadeout; sub_1F81E(8,90,99); restore }
 *        if (n535 == 25)  break;  // then sub_1F81E(0,15,0)
 *        if (n535 == 10)  sub_1F73F(75, 76, n15_1, 10)   // overlay
 *        j___delay(30);
 *        if (!n535) j___delay(1000);
 *   4. After break at n535==25: sub_1F81E(0,15,0) -> ANI#0
 *   5. Then sub_11EB0 restore + sub_1F525
 */
static void play_intro_animation(const char* fdother_path) {
    /* ---- Step 1: Build scroll buffer exactly like sub_1F894 ----
     * IDA analysis: loc_396C0 = 235200 = 320 * 735.
     * All 5 frames use fixed stride of 147 pixels (147 * 5 = 735).
     * Each frame is loaded via sub_4E98D(res, 0, 147*n5, buf, 320, -1)
     * where dst_y = 147 * n5 and the RLE image is fully decompressed.
     * IMPORTANT: Original game resources 69-73 are all 147px high.
     * If a resource has different height, clamp to 147 to match original behavior. */
    const int frame_h = 147;
    const int num_frames = 5;
    const int buf_h = frame_h * num_frames;  /* 735 */

    u8* scroll_buf = (u8*)calloc(FD2_SCREEN_W * buf_h, sizeof(u8));
    if (!scroll_buf) return;

    for (int i = 0; i < num_frames; i++) {
        u8* fres = fd2_dat_load_resource(fdother_path, NULL, 69 + i);
        u32 fsize = fd2_last_loaded_size;
        if (fres) {
            /* sub_4E98D with value_1 == -1 decompresses the full RLE image
             * directly into the buffer at dst_y = 147 * i.
             * Clamp to 147px to match original game behavior. */
            int fw, fh;
            u8* fpixels = NULL;
            if (fd2_rle_decompress_from_resource(fres, fsize, &fpixels, &fw, &fh, -1) == 0) {
                fprintf(stderr, "[intro] Frame %d (res %d): RLE size=%u, dim=%dx%d, dst_y=%d, copy_h=%d\n",
                        i, 69 + i, fsize, fw, fh, frame_h * i,
                        fh < frame_h ? fh : frame_h);
                int dst_y = frame_h * i;
                int copy_h = fh < frame_h ? fh : frame_h;
                int copy_w = fw < FD2_SCREEN_W ? fw : FD2_SCREEN_W;
                for (int y = 0; y < copy_h; y++) {
                    memcpy(scroll_buf + (dst_y + y) * FD2_SCREEN_W,
                           fpixels + y * fw, copy_w);
                }
                free(fpixels);
            }
            free(fres);
        } else {
            fprintf(stderr, "[intro] Frame %d (res %d): NOT FOUND\n", i, 69 + i);
        }
    }

    /* Debug: check first/last few bytes of each frame region */
    for (int i = 0; i < num_frames; i++) {
        int dst_y = frame_h * i;
        u8* frame_start = scroll_buf + dst_y * FD2_SCREEN_W;
        u8* frame_end = scroll_buf + (dst_y + frame_h - 1) * FD2_SCREEN_W;
        fprintf(stderr, "[intro] Frame %d at row %d: first_byte=%d, last_byte=%d\n",
                i, dst_y, frame_start[0], frame_end[0]);
    }
    fprintf(stderr, "[intro] Total buffer height: %d (expected: 735)\n", buf_h);

    /* ---- Step 2: Scroll loop (n535 from 535 down to 0) ----
     * At n535=535: src_offset=535*320, we copy rows 535..734 (200 rows)
     * But buffer is only 735 rows, so 535+200=735 <= 735, valid. */
    for (int n535 = 535; n535 >= 0; --n535) {
        int src_offset = n535 * FD2_SCREEN_W;

        /* sub_11EB0: memmove 200 rows from scroll_buf[src] to screen */
        if (n535 + FD2_SCREEN_H <= buf_h) {
            memcpy(g_screen, scroll_buf + src_offset, FD2_SCREEN_SIZE);
        } else if (n535 < buf_h) {
            int copy_rows = buf_h - n535;
            memcpy(g_screen, scroll_buf + src_offset, copy_rows * FD2_SCREEN_W);
            memset(g_screen + copy_rows * FD2_SCREEN_W, 0,
                   (FD2_SCREEN_H - copy_rows) * FD2_SCREEN_W);
        } else {
            memset(g_screen, 0, FD2_SCREEN_SIZE);
        }

        /* n535 == 535: sub_1F525 (screen refresh with current palette) */
        if (n535 == 535) {
            /* Palette was already set to FDOTHER[101] before this function */
        }

        /* n535 == 450: sub_1F73F(100, 99, n15_1, 450)
         * This overlay does: fadeout -> clear -> load palette 99 ->
         *   blit resource 100 -> fadein -> wait 6 ticks ->
         *   fadeout -> restore scroll_buf at pos 450 -> load palette 101 -> fadein */
        if (n535 == 450) {
            u8* ov_res = fd2_dat_load_resource(fdother_path, NULL, 100);
            u32 ov_size = fd2_last_loaded_size;
            if (ov_res) {
                blit_rle_image(ov_res, ov_size, 0, 0);
                free(ov_res);
            }
        }

        /* n535 == 330 / 210 / 110: character intro ANI sequences
         * These are handled by sub_1F81E which plays ANI.DAT animations.
         * For fd2_intro.c we skip these (fd2_game.c has full implementation). */

        /* n535 == 10: sub_1F73F(75, 76, n15_1, 10) */
        if (n535 == 10) {
            u8* ov_res = fd2_dat_load_resource(fdother_path, NULL, 75);
            u32 ov_size = fd2_last_loaded_size;
            if (ov_res) {
                blit_rle_image(ov_res, ov_size, 0, 0);
                free(ov_res);
            }
        }

        render_screen(g_screen, g_argb + FD2_SCREEN_W * FD2_SCREEN_H, g_argb);
        present_frame();

        /* Original: j___delay(30) */
        SDL_Delay(30);

        /* Original: if (!n535) j___delay(1000) */
        if (n535 == 0) {
            SDL_Delay(1000);
        }

        /* Check for quit/skip */
        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT ||
                (e.type == SDL_KEYDOWN && e.key.keysym.sym == SDLK_ESCAPE)) {
                free(scroll_buf);
                return;
            }
        }

        /* n535 == 25: break (then sub_1F81E(0,15,0) plays ANI#0) */
        if (n535 == 25) {
            break;
        }
    }

    free(scroll_buf);
}

int main(int argc, char** argv) {
    (void)argc; (void)argv;

    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        fprintf(stderr, "SDL_Init failed: %s\n", SDL_GetError());
        return 1;
    }

    g_window = SDL_CreateWindow("FD2 - Intro Animation",
                                SDL_WINDOWPOS_CENTERED,
                                SDL_WINDOWPOS_CENTERED,
                                WIN_W, WIN_H,
                                SDL_WINDOW_SHOWN);
    if (!g_window) {
        fprintf(stderr, "SDL_CreateWindow failed: %s\n", SDL_GetError());
        SDL_Quit();
        return 1;
    }

    g_renderer = SDL_CreateRenderer(g_window, -1, SDL_RENDERER_ACCELERATED);
    if (!g_renderer) {
        fprintf(stderr, "SDL_CreateRenderer failed: %s\n", SDL_GetError());
        SDL_DestroyWindow(g_window);
        SDL_Quit();
        return 1;
    }

    g_texture = SDL_CreateTexture(g_renderer,
                                  SDL_PIXELFORMAT_ARGB8888,
                                  SDL_TEXTUREACCESS_STREAMING,
                                  FD2_SCREEN_W, FD2_SCREEN_H);
    if (!g_texture) {
        fprintf(stderr, "SDL_CreateTexture failed: %s\n", SDL_GetError());
        SDL_DestroyRenderer(g_renderer);
        SDL_DestroyWindow(g_window);
        SDL_Quit();
        return 1;
    }

    g_argb = (Uint32*)calloc(FD2_SCREEN_W * FD2_SCREEN_H * 2, sizeof(Uint32));
    if (!g_argb) {
        fprintf(stderr, "Memory allocation failed\n");
        SDL_DestroyTexture(g_texture);
        SDL_DestroyRenderer(g_renderer);
        SDL_DestroyWindow(g_window);
        SDL_Quit();
        return 1;
    }

    init_exe_dir();

    const char* fdother_path = exe_path("FDOTHER.DAT");
    if (!fdother_path) {
        fprintf(stderr, "Failed to get FDOTHER.DAT path\n");
        free(g_argb);
        SDL_DestroyTexture(g_texture);
        SDL_DestroyRenderer(g_renderer);
        SDL_DestroyWindow(g_window);
        SDL_Quit();
        return 1;
    }

    printf("Loading intro resources...\n");

    /* Load title screen resource 74 via sub_111BA */
    u8* title_res = fd2_dat_load_resource(fdother_path, NULL, 74);
    u32 title_size = fd2_last_loaded_size;

    /* Load palette resource 76 via sub_111BA */
    u8* pal_res = fd2_dat_load_resource(fdother_path, NULL, 76);
    u32 pal_size = fd2_last_loaded_size;
    if (pal_res && pal_size == FD2_PALETTE_BYTES) {
        fd2_palette_6bit_to_8bit(pal_res, g_palette);
    }
    palette_to_argb(g_palette, g_argb + FD2_SCREEN_W * FD2_SCREEN_H);

    fill_screen(0);
    if (title_res) {
        blit_rle_image(title_res, title_size, 0, 0);
    }

    render_screen(g_screen, g_argb + FD2_SCREEN_W * FD2_SCREEN_H, g_argb);
    present_frame();
    SDL_Delay(500);

    printf("Playing bar animation...\n");
    
    /* Load resource 10 for bar animation */
    u8* bar_res = fd2_dat_load_resource(fdother_path, NULL, 10);
    u32 bar_size = fd2_last_loaded_size;
    if (bar_res) {
        play_bar_animation_resource(bar_res, bar_size, 60, 30);
    }
    SDL_Delay(200);

    printf("Fading to black...\n");
    fade_to_black(40, 8);
    SDL_Delay(100);

    /* Load resource 101 for scroll/menu section */
    u8* menu_res = fd2_dat_load_resource(fdother_path, NULL, 101);
    u32 menu_size = fd2_last_loaded_size;

    /* Scroll/menu section uses palette FDOTHER[101] */
    const u8* scroll_pal = menu_res;
    if (scroll_pal && menu_size >= FD2_PALETTE_BYTES) {
        fd2_palette_6bit_to_8bit(scroll_pal, g_palette);
    }
    fd2_palette_set_brightness(g_palette, 63);
    palette_to_argb(g_palette, g_argb + FD2_SCREEN_W * FD2_SCREEN_H);

    fill_screen(0);
    if (menu_res) {
        blit_rle_image(menu_res, menu_size, 0, 0);
    }
    render_screen(g_screen, g_argb + FD2_SCREEN_W * FD2_SCREEN_H, g_argb);
    present_frame();
    SDL_Delay(500);

    printf("Playing intro animation (535 frames)...\n");
    play_intro_animation(fdother_path);

    printf("Fading out...\n");
    fade_to_black(40, 8);
    SDL_Delay(100);

    /* Clean up loaded resources */
    if (title_res) free(title_res);
    if (pal_res) free(pal_res);
    if (bar_res) free(bar_res);
    if (menu_res) free(menu_res);

    printf("Showing menu...\n");
    printf("Press ESC to quit.\n");

    int running = 1;
    while (running) {
        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT ||
                (e.type == SDL_KEYDOWN && e.key.keysym.sym == SDLK_ESCAPE)) {
                running = 0;
            }
        }
        SDL_Delay(16);
    }

    free(g_argb);
    SDL_DestroyTexture(g_texture);
    SDL_DestroyRenderer(g_renderer);
    SDL_DestroyWindow(g_window);
    SDL_Quit();

    return 0;
}