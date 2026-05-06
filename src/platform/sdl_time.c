/**
 * SDL2 Time Platform Implementation
 * Timer functions using SDL_GetTicks.
 */

#define _GNU_SOURCE
#include "fd2/platform_time.h"
#include "fd2/types.h"
#include <SDL2/SDL.h>

static u32 sdl_time_get_ticks_ms(void) {
    return SDL_GetTicks();
}

static u64 sdl_time_get_ticks_us(void) {
    return (u64)SDL_GetTicks() * 1000;
}

static void sdl_time_delay_ms(u32 ms) {
    SDL_Delay(ms);
}

static void sdl_time_delay_us(u32 us) {
    SDL_Delay(us / 1000);
}

static const fd2_time_iface_t g_sdl_time_iface = {
    .get_ticks_ms = sdl_time_get_ticks_ms,
    .get_ticks_us = sdl_time_get_ticks_us,
    .delay_ms     = sdl_time_delay_ms,
    .delay_us     = sdl_time_delay_us,
};

const fd2_time_iface_t* fd2_platform_get_time(void) {
    return &g_sdl_time_iface;
}
