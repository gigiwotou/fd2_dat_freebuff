#ifndef FD2_RENDER_H
#define FD2_RENDER_H

#include "fd2_decoder.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================
 * FD2 Rendering Pipeline
 *
 * Manages the 320x200 indexed-color screen buffer and SDL2 presentation.
 * The original game writes to a VGA mode 13h framebuffer (0xA0000).
 * We replicate this with an 8-bit indexed buffer + palette → SDL2 texture.
 *
 * Flow: game code → g_screen[indexed] → palette lookup → ARGB → SDL
 * ======================================================================== */

#define FD2_RENDER_SCALE  3   /* Default window scale factor */

/* ---- Render State ---- */
typedef struct fd2_render {
    /* SDL2 objects */
    void*   window;       /* SDL_Window* */
    void*   renderer;     /* SDL_Renderer* */
    void*   texture;      /* SDL_Texture* (STREAMING, ARGB8888) */

    /* Screen buffer (320x200, 8-bit indexed) */
    u8      screen[FD2_SCREEN_SIZE];
    u8      palette[FD2_PALETTE_BYTES];  /* Current 8-bit RGB palette */

    /* ARGB conversion buffer (palette lookup result) */
    u32*    argb;         /* FD2_SCREEN_W * FD2_SCREEN_H * sizeof(u32) */
    u32*    argb_palette; /* 256-entry palette as ARGB8888 */

    /* Configuration */
    int     scale;        /* Window scale (1-5) */
    int     window_w;     /* Actual window width */
    int     window_h;     /* Actual window height */

    /* State */
    bool    initialized;
    bool    fullscreen;
} fd2_render_t;

/* ---- Lifecycle ---- */

/*
 * Initialize the rendering system: create window, renderer, texture.
 * scale: window scale factor (1-5). Use FD2_RENDER_SCALE for default.
 * Returns 0 on success, -1 on failure.
 */
int fd2_render_init(fd2_render_t* render, int scale);

/*
 * Shut down and free all rendering resources.
 */
void fd2_render_shutdown(fd2_render_t* render);

/* ---- Screen Buffer Operations ---- */

/*
 * Fill the screen buffer with a single color index.
 */
void fd2_render_fill_screen(fd2_render_t* render, u8 color);

/*
 * Blit an 8-bit indexed image onto the screen buffer.
 * Transparent pixels (index 0) are skipped.
 */
void fd2_render_blit(fd2_render_t* render,
                     const u8* pixels, int w, int h,
                     int dx, int dy);

/*
 * Blit an image, treating color_index as transparent instead of 0.
 */
void fd2_render_blit_trans(fd2_render_t* render,
                           const u8* pixels, int w, int h,
                           int dx, int dy, u8 transparent);

/*
 * Decompress an RLE resource and blit it directly to screen.
 * Convenience function combining fd2_rle_decompress_from_resource + blit.
 * Returns 0 on success, -1 on failure.
 */
int fd2_render_blit_rle(fd2_render_t* render,
                        const u8* res_data, u32 res_size,
                        int dx, int dy);

/*
 * Set a single pixel in the screen buffer.
 */
void fd2_render_plot(fd2_render_t* render, int x, int y, u8 color);

/* ---- Palette Operations ---- */

/*
 * Set the palette from 6-bit VGA data (converts to 8-bit internally).
 */
void fd2_render_set_palette_6bit(fd2_render_t* render, const u8* pal_6bit);

/*
 * Set the palette from 8-bit RGB data.
 */
void fd2_render_set_palette_8bit(fd2_render_t* render, const u8* pal_8bit);

/*
 * Apply brightness to the current palette (0=black, 63=full).
 */
void fd2_render_set_brightness(fd2_render_t* render, int brightness);

/*
 * Fade the palette between two states over multiple steps.
 * src/dst: 8-bit RGB palette arrays (768 bytes each)
 * steps: total number of fade steps
 * current: current step (0..steps)
 */
void fd2_render_fade_palette(fd2_render_t* render,
                             const u8* src, const u8* dst,
                             int steps, int current);

/*
 * Fade the screen to black over the given number of steps.
 * Each step takes step_ms milliseconds.
 * Checks for quit events during fade.
 */
void fd2_render_fade_to_black(fd2_render_t* render, int steps, int step_ms);

/*
 * Fade the screen from black (brightness 0) to full (brightness 63).
 * Matches sub_1F525: brightness ramps from 0 to 64 over 64 steps.
 * Each step takes step_ms milliseconds.
 * Checks for quit events during fade.
 */
void fd2_render_fade_from_black(fd2_render_t* render, int steps, int step_ms);

/*
 * Fade the current palette to a uniform color over the given number of steps.
 * Matches sub_2DF01 with descending step counter (e.g. Phase 3 fade-out).
 * base_r6/g6/b6: 6-bit VGA color values (0-63) to fade towards.
 * Each step takes step_ms milliseconds.
 */
void fd2_render_fade_to_color(fd2_render_t* render, int steps, int step_ms,
                               int base_r6, int base_g6, int base_b6);

/*
 * Fade from a uniform color to the current palette over the given number of steps.
 * Matches sub_2DF01 with ascending step counter (e.g. Phase 5 fade-in).
 * base_r6/g6/b6: 6-bit VGA color values (0-63) to fade from.
 * Each step takes step_ms milliseconds.
 */
void fd2_render_fade_from_color(fd2_render_t* render, int steps, int step_ms,
                                 int base_r6, int base_g6, int base_b6);

/*
 * Add a 6-bit value to every palette entry (sub_11DF2).
 * Produces a brightened/whitened palette.
 */
void fd2_render_palette_add_6bit(fd2_render_t* render, int add_6bit);

/*
 * Blit an AFM animation frame into the screen buffer.
 * Copies the AFM frame (320x200 indexed) directly to the screen.
 * transparent: color index to skip (0 = skip black, -1 = no transparency).
 */
void fd2_render_blit_afm(fd2_render_t* render, const u8* afm_frame,
                         int transparent);

/* ---- Presentation ---- */

/*
 * Convert the indexed screen buffer + palette to ARGB and present.
 * This is the final step each frame: palette lookup → texture → render.
 */
void fd2_render_present(fd2_render_t* render);

/*
 * Toggle fullscreen mode.
 */
void fd2_render_toggle_fullscreen(fd2_render_t* render);

#ifdef __cplusplus
}
#endif

#endif /* FD2_RENDER_H */
