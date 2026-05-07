/**
 * FD2 Rendering Pipeline Implementation
 *
 * Manages the 320x200 indexed-color screen buffer and SDL2 presentation.
 * The original game writes to VGA mode 13h framebuffer (0xA0000).
 */

#include "fd2_render.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ---- Internal Helpers ---- */

static void update_argb_palette(fd2_render_t* render) {
    for (int i = 0; i < FD2_PALETTE_COLORS; i++) {
        render->argb_palette[i] =
            (0xFFu << 24) |
            ((u32)render->palette[i * 3 + 0] << 16) |
            ((u32)render->palette[i * 3 + 1] << 8)  |
            ((u32)render->palette[i * 3 + 2]);
    }
}

static void screen_to_argb(const fd2_render_t* render) {
    for (int i = 0; i < FD2_SCREEN_SIZE; i++) {
        render->argb[i] = render->argb_palette[render->screen[i]];
    }
}

/* ---- Lifecycle ---- */

int fd2_render_init(fd2_render_t* render, int scale) {
    if (!render) return -1;

    memset(render, 0, sizeof(*render));
    render->scale = (scale < 1) ? 1 : (scale > 5) ? 5 : scale;
    render->window_w = FD2_SCREEN_W * render->scale;
    render->window_h = FD2_SCREEN_H * render->scale;

    /* Allocate ARGB buffers */
    render->argb = (u32*)calloc(FD2_SCREEN_SIZE, sizeof(u32));
    render->argb_palette = (u32*)calloc(FD2_PALETTE_COLORS, sizeof(u32));
    if (!render->argb || !render->argb_palette) {
        fprintf(stderr, "fd2_render_init: failed to allocate buffers\n");
        free(render->argb);
        free(render->argb_palette);
        return -1;
    }

    /* Create window */
    SDL_Window* win = SDL_CreateWindow(
        "Flame Dragon 2",
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
        render->window_w, render->window_h,
        SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE);
    if (!win) {
        fprintf(stderr, "fd2_render_init: SDL_CreateWindow failed: %s\n", SDL_GetError());
        free(render->argb);
        free(render->argb_palette);
        return -1;
    }
    render->window = win;

    /* Create renderer - 移除VSYNC避免阻塞 */
    SDL_Renderer* ren = SDL_CreateRenderer(win, -1,
        SDL_RENDERER_ACCELERATED);
    if (!ren) {
        fprintf(stderr, "fd2_render_init: SDL_CreateRenderer failed: %s\n", SDL_GetError());
        SDL_DestroyWindow(win);
        free(render->argb);
        free(render->argb_palette);
        return -1;
    }
    render->renderer = ren;

    /* Set logical size so SDL handles scaling for us */
    SDL_RenderSetLogicalSize(ren, FD2_SCREEN_W, FD2_SCREEN_H);

    /* Create streaming texture */
    SDL_Texture* tex = SDL_CreateTexture(ren,
        SDL_PIXELFORMAT_ARGB8888,
        SDL_TEXTUREACCESS_STREAMING,
        FD2_SCREEN_W, FD2_SCREEN_H);
    if (!tex) {
        fprintf(stderr, "fd2_render_init: SDL_CreateTexture failed: %s\n", SDL_GetError());
        SDL_DestroyRenderer(ren);
        SDL_DestroyWindow(win);
        free(render->argb);
        free(render->argb_palette);
        return -1;
    }
    render->texture = tex;

    /* Palette and screen already zeroed by the memset above */
    /* 初始化默认调色板 - 使用灰度渐变用于测试 */
    for (int i = 0; i < FD2_PALETTE_COLORS; i++) {
        render->palette[i * 3 + 0] = (u8)i;  /* R */
        render->palette[i * 3 + 1] = (u8)i;  /* G */
        render->palette[i * 3 + 2] = (u8)i;  /* B */
    }
    update_argb_palette(render);
    
    printf("[RENDER] Initialized with grayscale palette\n");

    render->initialized = true;
    return 0;
}

void fd2_render_shutdown(fd2_render_t* render) {
    if (!render || !render->initialized) return;

    if (render->texture)    SDL_DestroyTexture((SDL_Texture*)render->texture);
    if (render->renderer)   SDL_DestroyRenderer((SDL_Renderer*)render->renderer);
    if (render->window)     SDL_DestroyWindow((SDL_Window*)render->window);
    free(render->argb);
    free(render->argb_palette);

    memset(render, 0, sizeof(*render));
}

/* ---- Screen Buffer ---- */

void fd2_render_fill_screen(fd2_render_t* render, u8 color) {
    if (!render) return;
    memset(render->screen, color, FD2_SCREEN_SIZE);
}

void fd2_render_blit(fd2_render_t* render,
                     const u8* pixels, int w, int h,
                     int dx, int dy) {
    if (!render || !pixels) return;
    fd2_render_blit_trans(render, pixels, w, h, dx, dy, 0);
}

void fd2_render_blit_trans(fd2_render_t* render,
                           const u8* pixels, int w, int h,
                           int dx, int dy, u8 transparent) {
    if (!render || !pixels) return;

    for (int y = 0; y < h; y++) {
        int sy = dy + y;
        if (sy < 0 || sy >= FD2_SCREEN_H) continue;

        for (int x = 0; x < w; x++) {
            int sx = dx + x;
            if (sx < 0 || sx >= FD2_SCREEN_W) continue;

            u8 px = pixels[y * w + x];
            if (px != transparent) {
                render->screen[sy * FD2_SCREEN_W + sx] = px;
            }
        }
    }
}

int fd2_render_blit_rle(fd2_render_t* render,
                        const u8* res_data, u32 res_size,
                        int dx, int dy) {
    if (!render || !res_data) return -1;

    u8* pixels = NULL;
    int w = 0, h = 0;
    if (fd2_rle_decompress_from_resource(res_data, res_size, &pixels, &w, &h, -1) != 0) {
        return -1;
    }

    fd2_render_blit(render, pixels, w, h, dx, dy);
    free(pixels);
    return 0;
}

void fd2_render_plot(fd2_render_t* render, int x, int y, u8 color) {
    if (!render) return;
    if (x < 0 || x >= FD2_SCREEN_W || y < 0 || y >= FD2_SCREEN_H) return;
    render->screen[y * FD2_SCREEN_W + x] = color;
}

/* ---- Palette ---- */

void fd2_render_set_palette_6bit(fd2_render_t* render, const u8* pal_6bit) {
    if (!render || !pal_6bit) return;
    fd2_palette_6bit_to_8bit(pal_6bit, render->palette);
    update_argb_palette(render);
}

void fd2_render_set_palette_8bit(fd2_render_t* render, const u8* pal_8bit) {
    if (!render || !pal_8bit) return;
    memcpy(render->palette, pal_8bit, FD2_PALETTE_BYTES);
    update_argb_palette(render);
}

void fd2_render_set_brightness(fd2_render_t* render, int brightness) {
    if (!render) return;
    fd2_palette_set_brightness(render->palette, brightness);
    update_argb_palette(render);
}

void fd2_render_fade_palette(fd2_render_t* render,
                             const u8* src, const u8* dst,
                             int steps, int current) {
    if (!render) return;
    fd2_palette_fade(src, dst, render->palette, steps, current);
    update_argb_palette(render);
}

void fd2_render_fade_to_black(fd2_render_t* render, int steps, int step_ms) {
    if (!render) return;

    u8 src_pal[FD2_PALETTE_BYTES];
    u8 black_pal[FD2_PALETTE_BYTES];
    memset(black_pal, 0, sizeof(black_pal));
    memcpy(src_pal, render->palette, FD2_PALETTE_BYTES);

    for (int s = 0; s <= steps; s++) {
        fd2_render_fade_palette(render, src_pal, black_pal, steps, s);
        fd2_render_present(render);

        /* Pump events during fade so the app doesn't freeze */
        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) return;
        }

        SDL_Delay(step_ms);
    }
}

void fd2_render_fade_from_black(fd2_render_t* render, int steps, int step_ms) {
    if (!render) return;

    u8 dst_pal[FD2_PALETTE_BYTES];
    u8 black_pal[FD2_PALETTE_BYTES];
    memset(black_pal, 0, sizeof(black_pal));
    memcpy(dst_pal, render->palette, FD2_PALETTE_BYTES);

    for (int s = 0; s <= steps; s++) {
        fd2_render_fade_palette(render, black_pal, dst_pal, steps, s);
        fd2_render_present(render);

        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) return;
        }

        SDL_Delay(step_ms);
    }
}

void fd2_render_fade_to_color(fd2_render_t* render, int steps, int step_ms,
                               int base_r6, int base_g6, int base_b6) {
    if (!render) return;

    /* Build base palette: every color = (base_r6, base_g6, base_b6) in 8-bit */
    u8 base_pal[FD2_PALETTE_BYTES];
    u8 src_pal[FD2_PALETTE_BYTES];
    {
        u8 r8 = (u8)((base_r6 << 2) | (base_r6 >> 4));
        u8 g8 = (u8)((base_g6 << 2) | (base_g6 >> 4));
        u8 b8 = (u8)((base_b6 << 2) | (base_b6 >> 4));
        for (int i = 0; i < FD2_PALETTE_COLORS; i++) {
            base_pal[i * 3 + 0] = r8;
            base_pal[i * 3 + 1] = g8;
            base_pal[i * 3 + 2] = b8;
        }
    }
    memcpy(src_pal, render->palette, FD2_PALETTE_BYTES);

    /* Fade from src to base: step goes 0→steps (sub_2DF01 descending counter) */
    for (int s = 0; s <= steps; s++) {
        fd2_render_fade_palette(render, src_pal, base_pal, steps, s);
        fd2_render_present(render);

        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) return;
        }

        SDL_Delay(step_ms);
    }
}

void fd2_render_fade_from_color(fd2_render_t* render, int steps, int step_ms,
                                 int base_r6, int base_g6, int base_b6) {
    if (!render) return;

    /* Build base palette: every color = (base_r6, base_g6, base_b6) in 8-bit */
    u8 base_pal[FD2_PALETTE_BYTES];
    u8 dst_pal[FD2_PALETTE_BYTES];
    {
        u8 r8 = (u8)((base_r6 << 2) | (base_r6 >> 4));
        u8 g8 = (u8)((base_g6 << 2) | (base_g6 >> 4));
        u8 b8 = (u8)((base_b6 << 2) | (base_b6 >> 4));
        for (int i = 0; i < FD2_PALETTE_COLORS; i++) {
            base_pal[i * 3 + 0] = r8;
            base_pal[i * 3 + 1] = g8;
            base_pal[i * 3 + 2] = b8;
        }
    }
    memcpy(dst_pal, render->palette, FD2_PALETTE_BYTES);

    /* Fade from base to dst: step goes 0→steps (sub_2DF01 ascending counter) */
    for (int s = 0; s <= steps; s++) {
        fd2_render_fade_palette(render, base_pal, dst_pal, steps, s);
        fd2_render_present(render);

        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) return;
        }

        SDL_Delay(step_ms);
    }
}

void fd2_render_palette_add_6bit(fd2_render_t* render, int add_6bit) {
    if (!render) return;
    fd2_palette_add_6bit(render->palette, add_6bit);
    update_argb_palette(render);
}

void fd2_render_blit_afm(fd2_render_t* render, const u8* afm_frame,
                         int transparent) {
    if (!render || !afm_frame) return;

    for (int i = 0; i < FD2_SCREEN_SIZE; i++) {
        u8 px = afm_frame[i];
        if (transparent < 0 || px != (u8)transparent) {
            render->screen[i] = px;
        }
    }
}


/* ---- Presentation ---- */

void fd2_render_present(fd2_render_t* render) {
    if (!render || !render->initialized) {
        return;
    }

    /* 处理SDL事件防止窗口锁死 */
    SDL_Event event;
    while (SDL_PollEvent(&event)) {
        if (event.type == SDL_QUIT) {
            return;
        }
    }

    screen_to_argb(render);
    SDL_UpdateTexture((SDL_Texture*)render->texture, NULL,
                      render->argb, FD2_SCREEN_W * sizeof(u32));
    SDL_RenderClear((SDL_Renderer*)render->renderer);
    SDL_RenderCopy((SDL_Renderer*)render->renderer,
                   (SDL_Texture*)render->texture, NULL, NULL);
    SDL_RenderPresent((SDL_Renderer*)render->renderer);
}

void fd2_render_toggle_fullscreen(fd2_render_t* render) {
    if (!render || !render->initialized) return;

    render->fullscreen = !render->fullscreen;
    SDL_SetWindowFullscreen((SDL_Window*)render->window,
                            render->fullscreen ? SDL_WINDOW_FULLSCREEN_DESKTOP : 0);
}
