/**
 * FD2 Input System Implementation
 *
 * Translates SDL2 keyboard events into game-level input actions.
 * The original game (sub_10620) reads the BIOS keyboard buffer at
 * 0x41A/0x41C to check for pending keystrokes.
 */

#include "fd2_input.h"
#include <SDL2/SDL.h>
#include <string.h>
#include <stdbool.h>

/* ---- Key Mapping ----
 *
 * Original game uses a 2-player arcade layout:
 *   P1: Arrow keys + Z/X/C/V (or A/S/D/F)
 *   P2: WASD + J/K/L/; (not used initially)
 *   System: Enter, Esc, Tab (coin)
 */
fd2_action_t fd2_input_map_scancode(int scancode) {
    switch (scancode) {
        /* Movement - Player 1 */
        case SDL_SCANCODE_UP:     return FD2_ACTION_UP;
        case SDL_SCANCODE_DOWN:   return FD2_ACTION_DOWN;
        case SDL_SCANCODE_LEFT:   return FD2_ACTION_LEFT;
        case SDL_SCANCODE_RIGHT:  return FD2_ACTION_RIGHT;

        /* Buttons - Player 1 */
        case SDL_SCANCODE_Z:      return FD2_ACTION_A;  /* Punch low */
        case SDL_SCANCODE_X:      return FD2_ACTION_B;  /* Kick low */
        case SDL_SCANCODE_C:      return FD2_ACTION_C;  /* Punch high */
        case SDL_SCANCODE_V:      return FD2_ACTION_D;  /* Kick high */

        /* Alternative button layout */
        case SDL_SCANCODE_A:      return FD2_ACTION_A;
        case SDL_SCANCODE_S:      return FD2_ACTION_B;
        case SDL_SCANCODE_D:      return FD2_ACTION_C;
        case SDL_SCANCODE_F:      return FD2_ACTION_D;

        /* System */
        case SDL_SCANCODE_RETURN:
        case SDL_SCANCODE_SPACE:  return FD2_ACTION_START;
        case SDL_SCANCODE_ESCAPE: return FD2_ACTION_ESCAPE;
        case SDL_SCANCODE_TAB:    return FD2_ACTION_COIN;

        default:                  return FD2_ACTION_NONE;
    }
}

/* ---- Lifecycle ---- */

void fd2_input_init(fd2_input_t* input) {
    if (!input) return;
    memset(input, 0, sizeof(*input));
}

/* ---- Frame Processing ---- */

void fd2_input_begin_frame(fd2_input_t* input) {
    if (!input) return;
    /* Clear edge-triggered states for this frame */
    memset(input->pressed, 0, sizeof(input->pressed));
    memset(input->released, 0, sizeof(input->released));
}

void fd2_input_process_event(fd2_input_t* input, const void* sdl_event) {
    if (!input || !sdl_event) return;

    const SDL_Event* e = (const SDL_Event*)sdl_event;
    if (e->type != SDL_KEYDOWN && e->type != SDL_KEYUP) return;
    if (e->key.repeat) return;  /* Ignore key repeat */

    int scancode = e->key.keysym.scancode;
    
    /* Track raw key state */
    if (scancode >= 0 && scancode < 512) {
        input->key_states[scancode] = (e->type == SDL_KEYDOWN);
    }

    fd2_action_t action = fd2_input_map_scancode(scancode);
    if (action == FD2_ACTION_NONE || action >= FD2_ACTION_COUNT) return;

    input->last_keycode  = e->key.keysym.sym;
    input->last_scancode = scancode;

    if (e->type == SDL_KEYDOWN) {
        if (!input->held[action]) {
            input->pressed[action] = true;
        }
        input->held[action] = true;
    } else { /* SDL_KEYUP */
        input->held[action] = false;
        input->released[action] = true;
    }
}

/* ---- Query ---- */

bool fd2_action_pressed(const fd2_input_t* input, fd2_action_t action) {
    if (!input || action <= FD2_ACTION_NONE || action >= FD2_ACTION_COUNT) return false;
    return input->pressed[action];
}

bool fd2_action_held(const fd2_input_t* input, fd2_action_t action) {
    if (!input || action <= FD2_ACTION_NONE || action >= FD2_ACTION_COUNT) return false;
    return input->held[action];
}

bool fd2_action_released(const fd2_input_t* input, fd2_action_t action) {
    if (!input || action <= FD2_ACTION_NONE || action >= FD2_ACTION_COUNT) return false;
    return input->released[action];
}

bool fd2_input_any_pressed(const fd2_input_t* input) {
    if (!input) return false;
    for (int i = 1; i < FD2_ACTION_COUNT; i++) {
        if (input->pressed[i]) return true;
    }
    return false;
}

bool fd2_key_held(const fd2_input_t* input, int scancode) {
    if (!input || scancode < 0 || scancode >= 512) return false;
    return input->key_states[scancode];
}

bool fd2_key_pressed(const fd2_input_t* input, int scancode) {
    /* For pressed, we need to check if it was just pressed this frame
     * We can approximate this by checking if it's held and wasn't held before */
    if (!input || scancode < 0 || scancode >= 512) return false;
    return input->key_states[scancode];
}
