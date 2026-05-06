/**
 * SDL2 Input Platform Implementation
 * Adapts SDL2 events to the fd2_input_t action system.
 */

#define _GNU_SOURCE
#include "fd2/platform_input.h"
#include "fd2/types.h"
#include "fd2_input.h"
#include <SDL2/SDL.h>
#include <stdlib.h>
#include <string.h>

static int sdl_input_init(fd2_input_t** out_input) {
    fd2_input_t* input = (fd2_input_t*)calloc(1, sizeof(fd2_input_t));
    if (!input) return -1;

    fd2_input_init(input);
    *out_input = input;
    return 0;
}

static void sdl_input_shutdown(fd2_input_t* input) {
    free(input);
}

static fd2_action_t scancode_to_action(int scancode) {
    switch (scancode) {
        case SDL_SCANCODE_UP:    return FD2_ACTION_UP;
        case SDL_SCANCODE_DOWN:  return FD2_ACTION_DOWN;
        case SDL_SCANCODE_LEFT:  return FD2_ACTION_LEFT;
        case SDL_SCANCODE_RIGHT: return FD2_ACTION_RIGHT;

        case SDL_SCANCODE_Z:
        case SDL_SCANCODE_A:     return FD2_ACTION_A;
        case SDL_SCANCODE_X:
        case SDL_SCANCODE_S:     return FD2_ACTION_B;
        case SDL_SCANCODE_C:     return FD2_ACTION_C;
        case SDL_SCANCODE_D:     return FD2_ACTION_D;

        case SDL_SCANCODE_RETURN:
        case SDL_SCANCODE_SPACE: return FD2_ACTION_START;
        case SDL_SCANCODE_TAB:   return FD2_ACTION_COIN;
        case SDL_SCANCODE_ESCAPE:return FD2_ACTION_ESCAPE;
        case SDL_SCANCODE_G:     return FD2_ACTION_DEBUG_GRID;

        default: return FD2_ACTION_NONE;
    }
}

static void sdl_input_process_event(fd2_input_t* input, void* platform_event) {
    SDL_Event* event = (SDL_Event*)platform_event;

    if (event->type == SDL_KEYDOWN) {
        int scancode = event->key.keysym.scancode;
        input->last_scancode = scancode;
        input->last_keycode = event->key.keysym.sym;
        input->key_states[scancode] = true;

        fd2_action_t action = scancode_to_action(scancode);
        if (action != FD2_ACTION_NONE && !input->held[action]) {
            input->pressed[action] = true;
        }
        input->held[action] = true;
    }

    if (event->type == SDL_KEYUP) {
        int scancode = event->key.keysym.scancode;
        input->key_states[scancode] = false;

        fd2_action_t action = scancode_to_action(scancode);
        if (action != FD2_ACTION_NONE) {
            input->held[action] = false;
            input->released[action] = true;
        }
    }
}

static void sdl_input_begin_frame(fd2_input_t* input) {
    fd2_input_begin_frame(input);
}

static void sdl_input_end_frame(fd2_input_t* input) {
    memset(input->pressed, 0, sizeof(input->pressed));
    memset(input->released, 0, sizeof(input->released));
}

static bool sdl_input_is_action_held(fd2_input_t* input, fd2_action_t action) {
    return fd2_action_held(input, action);
}

static bool sdl_input_is_action_pressed(fd2_input_t* input, fd2_action_t action) {
    return fd2_action_pressed(input, action);
}

static bool sdl_input_is_action_released(fd2_input_t* input, fd2_action_t action) {
    return fd2_action_released(input, action);
}

static bool sdl_input_is_any_pressed(fd2_input_t* input) {
    return fd2_input_any_pressed(input);
}

static const fd2_input_iface_t g_sdl_input_iface = {
    .init               = sdl_input_init,
    .shutdown           = sdl_input_shutdown,
    .process_event      = sdl_input_process_event,
    .begin_frame        = sdl_input_begin_frame,
    .end_frame          = sdl_input_end_frame,
    .is_action_held     = sdl_input_is_action_held,
    .is_action_pressed  = sdl_input_is_action_pressed,
    .is_action_released = sdl_input_is_action_released,
    .is_any_pressed     = sdl_input_is_any_pressed,
};

const fd2_input_iface_t* fd2_platform_get_input(void) {
    return &g_sdl_input_iface;
}
