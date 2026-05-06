/**
 * SDL2 Video Platform Implementation
 * Implements fd2_video_iface_t using SDL2 renderer.
 */

#define _GNU_SOURCE
#include "fd2/platform_video.h"
#include "fd2/types.h"
#include <SDL2/SDL.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

struct fd2_video {
    SDL_Window*   window;
    SDL_Renderer* renderer;
    SDL_Texture*  texture;
    Uint32*       argb_buffer;
    u8            screen[FD2_SCREEN_SIZE];
    u8            palette[FD2_PALETTE_BYTES];
    int           scale;
    int           fullscreen;
};

static void palette_to_argb(const u8* pal, Uint32* argb) {
    for (int i = 0; i < FD2_PALETTE_COLORS; i++) {
        argb[i] = (0xFFu << 24) |
                  ((u32)pal[i * 3 + 0] << 16) |
                  ((u32)pal[i * 3 + 1] << 8)  |
                  ((u32)pal[i * 3 + 2]);
    }
}

static void render_screen(const u8* screen, const Uint32* argb_palette, Uint32* dst) {
    for (int i = 0; i < FD2_SCREEN_SIZE; i++) {
        dst[i] = argb_palette[screen[i]];
    }
}

static int sdl_video_init(fd2_video_t** out_video, int width, int height, int scale, const char* title) {
    fd2_video_t* video = (fd2_video_t*)calloc(1, sizeof(fd2_video_t));
    if (!video) return -1;

    video->scale = scale;

    video->window = SDL_CreateWindow(title,
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
        width * scale, height * scale,
        SDL_WINDOW_SHOWN);
    if (!video->window) {
        fprintf(stderr, "sdl_video: SDL_CreateWindow failed: %s\n", SDL_GetError());
        free(video);
        return -1;
    }

    video->renderer = SDL_CreateRenderer(video->window, -1, SDL_RENDERER_ACCELERATED);
    if (!video->renderer) {
        fprintf(stderr, "sdl_video: SDL_CreateRenderer failed: %s\n", SDL_GetError());
        SDL_DestroyWindow(video->window);
        free(video);
        return -1;
    }

    video->texture = SDL_CreateTexture(video->renderer,
        SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_STREAMING,
        width, height);
    if (!video->texture) {
        fprintf(stderr, "sdl_video: SDL_CreateTexture failed: %s\n", SDL_GetError());
        SDL_DestroyRenderer(video->renderer);
        SDL_DestroyWindow(video->window);
        free(video);
        return -1;
    }

    video->argb_buffer = (Uint32*)calloc(FD2_SCREEN_SIZE, sizeof(Uint32));
    if (!video->argb_buffer) {
        fprintf(stderr, "sdl_video: cannot allocate ARGB buffer\n");
        SDL_DestroyTexture(video->texture);
        SDL_DestroyRenderer(video->renderer);
        SDL_DestroyWindow(video->window);
        free(video);
        return -1;
    }

    memset(video->screen, 0, FD2_SCREEN_SIZE);
    memset(video->palette, 0, FD2_PALETTE_BYTES);
    palette_to_argb(video->palette, video->argb_buffer);

    *out_video = video;
    return 0;
}

static void sdl_video_shutdown(fd2_video_t* video) {
    if (!video) return;
    if (video->argb_buffer) free(video->argb_buffer);
    if (video->texture) SDL_DestroyTexture(video->texture);
    if (video->renderer) SDL_DestroyRenderer(video->renderer);
    if (video->window) SDL_DestroyWindow(video->window);
    free(video);
}

static void sdl_video_set_palette(fd2_video_t* video, const u8* palette_8bit) {
    memcpy(video->palette, palette_8bit, FD2_PALETTE_BYTES);
    palette_to_argb(palette_8bit, video->argb_buffer);
}

static void sdl_video_set_brightness(fd2_video_t* video, int brightness_0_to_63) {
    u8 temp_pal[FD2_PALETTE_BYTES];
    memcpy(temp_pal, video->palette, FD2_PALETTE_BYTES);
    for (int i = 0; i < FD2_PALETTE_BYTES; i++) {
        temp_pal[i] = (u8)((int)video->palette[i] * brightness_0_to_63 / 63);
    }
    palette_to_argb(temp_pal, video->argb_buffer);
}

static void sdl_video_upload_screen(fd2_video_t* video, const u8* screen_buffer) {
    memcpy(video->screen, screen_buffer, FD2_SCREEN_SIZE);
}

static void sdl_video_present(fd2_video_t* video) {
    render_screen(video->screen, video->argb_buffer, video->argb_buffer);

    SDL_UpdateTexture(video->texture, NULL, video->argb_buffer,
        FD2_SCREEN_W * sizeof(Uint32));
    SDL_RenderClear(video->renderer);
    SDL_RenderCopy(video->renderer, video->texture, NULL, NULL);
    SDL_RenderPresent(video->renderer);
}

static void sdl_video_fill_screen(fd2_video_t* video, u8 color) {
    memset(video->screen, color, FD2_SCREEN_SIZE);
}

static void sdl_video_blit(fd2_video_t* video, const u8* pixels, int w, int h, int dx, int dy) {
    for (int y = 0; y < h && (dy + y) < FD2_SCREEN_H; y++) {
        for (int x = 0; x < w && (dx + x) < FD2_SCREEN_W; x++) {
            int sx = dx + x;
            int sy = dy + y;
            if (sx >= 0 && sy >= 0) {
                video->screen[sy * FD2_SCREEN_W + sx] = pixels[y * w + x];
            }
        }
    }
}

static void sdl_video_blit_trans(fd2_video_t* video, const u8* pixels, int w, int h,
                                  int dx, int dy, u8 transparent) {
    for (int y = 0; y < h && (dy + y) < FD2_SCREEN_H; y++) {
        for (int x = 0; x < w && (dx + x) < FD2_SCREEN_W; x++) {
            u8 px = pixels[y * w + x];
            if (px != transparent) {
                int sx = dx + x;
                int sy = dy + y;
                if (sx >= 0 && sy >= 0) {
                    video->screen[sy * FD2_SCREEN_W + sx] = px;
                }
            }
        }
    }
}

static void sdl_video_toggle_fullscreen(fd2_video_t* video) {
    video->fullscreen = !video->fullscreen;
    SDL_SetWindowFullscreen(video->window,
        video->fullscreen ? SDL_WINDOW_FULLSCREEN_DESKTOP : 0);
}

static void sdl_video_process_events(fd2_video_t* video) {
    (void)video;
    /* Events are handled by input system */
}

static const fd2_video_iface_t g_sdl_video_iface = {
    .init              = sdl_video_init,
    .shutdown          = sdl_video_shutdown,
    .set_palette       = sdl_video_set_palette,
    .set_brightness    = sdl_video_set_brightness,
    .upload_screen     = sdl_video_upload_screen,
    .present           = sdl_video_present,
    .fill_screen       = sdl_video_fill_screen,
    .blit              = sdl_video_blit,
    .blit_trans        = sdl_video_blit_trans,
    .toggle_fullscreen = sdl_video_toggle_fullscreen,
    .process_events    = sdl_video_process_events,
    .width             = FD2_SCREEN_W,
    .height            = FD2_SCREEN_H,
    .scale             = 3,
};

const fd2_video_iface_t* fd2_platform_get_video(void) {
    return &g_sdl_video_iface;
}
