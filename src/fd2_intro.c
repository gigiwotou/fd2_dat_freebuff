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
    if (fd2_rle_decompress_from_resource(res_data, res_size, &pixels, &w, &h) != 0) return;

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

static void play_bar_animation(const fd2_dat_t* dat, int frames, int frame_ms) {
    u32 size;
    const u8* res = fd2_dat_get_resource(dat, 10, &size);
    if (!res) return;

    int w, h;
    if (fd2_image_get_dimensions(res, size, &w, &h) != 0) return;

    u8* pixels = NULL;
    if (fd2_rle_decompress_from_resource(res, size, &pixels, &w, &h) != 0) return;

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

static void play_intro_animation(const fd2_dat_t* dat) {
    int frame_heights[5] = {147, 147, 147, 147, 200};
    int total_h = 0;
    for (int i = 0; i < 5; i++) total_h += frame_heights[i];

    u32 size_99;
    const u8* res_99 = fd2_dat_get_resource(dat, 99, &size_99);
    u8* pixels_99 = NULL;
    int w_99 = 0, h_99 = 0;
    if (res_99) {
        fd2_rle_decompress_from_resource(res_99, size_99, &pixels_99, &w_99, &h_99);
    }

    u8* anim_buffer = (u8*)calloc(FD2_SCREEN_W * total_h, sizeof(u8));
    int row_offset = 0;
    for (int i = 0; i < 5; i++) {
        u32 fsize;
        const u8* fres = fd2_dat_get_resource(dat, 69 + i, &fsize);
        if (fres) {
            int fw, fh;
            u8* fpixels = NULL;
            if (fd2_rle_decompress_from_resource(fres, fsize, &fpixels, &fw, &fh) == 0) {
                int copy_h = fh < frame_heights[i] ? fh : frame_heights[i];
                int copy_w = fw < FD2_SCREEN_W ? fw : FD2_SCREEN_W;
                for (int y = 0; y < copy_h; y++) {
                    memcpy(anim_buffer + (row_offset + y) * FD2_SCREEN_W,
                           fpixels + y * fw, copy_w);
                }
                free(fpixels);
            }
        }
        row_offset += frame_heights[i];
    }

    for (int frame = 535; frame >= 25; frame--) {
        int src_row = frame;
        if (src_row + 200 <= total_h) {
            for (int y = 0; y < 200; y++) {
                memcpy(g_screen + y * FD2_SCREEN_W,
                       anim_buffer + (src_row + y) * FD2_SCREEN_W,
                       FD2_SCREEN_W);
            }
        }

        if (frame == 450 && pixels_99) {
            blit_pixels(pixels_99, w_99, h_99, 0, 0);
        }

        if (frame == 25 && pixels_99) {
            blit_pixels(pixels_99, w_99, h_99, 0, 0);
        }

        render_screen(g_screen, g_argb + FD2_SCREEN_W * FD2_SCREEN_H, g_argb);
        present_frame();

        SDL_Delay(5);

        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT ||
                (e.type == SDL_KEYDOWN && e.key.keysym.sym == SDLK_ESCAPE)) {
                free(anim_buffer);
                free(pixels_99);
                return;
            }
        }
    }

    SDL_Delay(1000);

    free(anim_buffer);
    free(pixels_99);
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

    fd2_dat_t dat;
    if (fd2_dat_load(&dat, exe_path("FDOTHER.DAT")) != 0) {
        fprintf(stderr, "Failed to load FDOTHER.DAT from %s\n", g_exe_dir);
        free(g_argb);
        SDL_DestroyTexture(g_texture);
        SDL_DestroyRenderer(g_renderer);
        SDL_DestroyWindow(g_window);
        SDL_Quit();
        return 1;
    }

    printf("Loading intro resources...\n");

    u32 title_size;
    const u8* title_res = fd2_dat_get_resource(&dat, 74, &title_size);

    /* Title screen uses palette FDOTHER[76] (original: sub_111BA(76)) */
    u32 pal_size;
    const u8* pal_res = fd2_dat_get_resource(&dat, 76, &pal_size);
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
    play_bar_animation(&dat, 60, 30);
    SDL_Delay(200);

    printf("Fading to black...\n");
    fade_to_black(40, 8);
    SDL_Delay(100);

    u32 menu_size;
    const u8* menu_res = fd2_dat_get_resource(&dat, 101, &menu_size);

    /* Scroll/menu section uses palette FDOTHER[101] (original: sub_111BA(101)) */
    const u8* scroll_pal = fd2_dat_get_resource(&dat, 101, &pal_size);
    if (scroll_pal && pal_size == FD2_PALETTE_BYTES) {
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
    play_intro_animation(&dat);

    printf("Fading out...\n");
    fade_to_black(40, 8);
    SDL_Delay(100);

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

    fd2_dat_free(&dat);
    free(g_argb);
    SDL_DestroyTexture(g_texture);
    SDL_DestroyRenderer(g_renderer);
    SDL_DestroyWindow(g_window);
    SDL_Quit();

    return 0;
}