#ifndef FD2_INPUT_H
#define FD2_INPUT_H

#include <stdint.h>
#include <stdbool.h>
#include "fd2_decoder.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================
 * FD2 Input System
 *
 * Translates SDL2 keyboard events into game-level input actions.
 * The original game (sub_10620) reads the BIOS keyboard buffer at
 * 0x41A/0x41C to check for pending keystrokes.
 *
 * We abstract this into a simple action-pressed / action-held model.
 * ======================================================================== */

/* ---- Game Actions ---- */
typedef enum {
    FD2_ACTION_NONE = 0,

    /* Movement */
    FD2_ACTION_UP,
    FD2_ACTION_DOWN,
    FD2_ACTION_LEFT,
    FD2_ACTION_RIGHT,

    /* Buttons */
    FD2_ACTION_A,         /* Punch (low) */
    FD2_ACTION_B,         /* Kick (low) */
    FD2_ACTION_C,         /* Punch (high) */
    FD2_ACTION_D,         /* Kick (high) */

    /* System */
    FD2_ACTION_START,     /* Enter/Space - confirm */
    FD2_ACTION_X,         /* X key - cancel/exit menu */
    FD2_ACTION_COIN,      /* Insert coin (for future use) */
    FD2_ACTION_ESCAPE,    /* Back/quit */
    FD2_ACTION_DEBUG_GRID, /* G key - toggle debug grid overlay */

    FD2_ACTION_COUNT
} fd2_action_t;

/* ---- Input State ---- */
typedef struct fd2_input {
    bool  pressed[FD2_ACTION_COUNT];  /* Just pressed this frame (edge) */
    bool  held[FD2_ACTION_COUNT];     /* Currently held down */
    bool  released[FD2_ACTION_COUNT]; /* Just released this frame (edge) */

    /* Raw key state for diagnostic/debug */
    int   last_keycode;               /* Last SDL key event code */
    int   last_scancode;              /* Last SDL scan code */
    bool  key_states[512];            /* Raw key state (indexed by scancode) */
} fd2_input_t;

/* ---- Functions ---- */

/*
 * Initialize input state to all-released.
 */
void fd2_input_init(fd2_input_t* input);

/*
 * Process an SDL event and update input state.
 * Call this for every SDL_Event in the frame.
 */
void fd2_input_process_event(fd2_input_t* input, const void* sdl_event);

/*
 * Call at the start of each frame to clear per-frame state
 * (pressed/released edges). Held state persists.
 */
void fd2_input_begin_frame(fd2_input_t* input);

/*
 * Check if an action was just pressed this frame (edge trigger).
 */
bool fd2_action_pressed(const fd2_input_t* input, fd2_action_t action);

/*
 * Check if an action is currently held down.
 */
bool fd2_action_held(const fd2_input_t* input, fd2_action_t action);

/*
 * Check if an action was just released this frame (edge trigger).
 */
bool fd2_action_released(const fd2_input_t* input, fd2_action_t action);

/*
 * Check if ANY key is pressed (equivalent to sub_10620).
 * Returns true if there is any pending input.
 */
bool fd2_input_any_pressed(const fd2_input_t* input);

/*
 * Check if a specific raw key is currently held down.
 * Index is SDL scancode.
 */
bool fd2_key_held(const fd2_input_t* input, int scancode);

/*
 * Check if a specific raw key was just pressed this frame.
 * Index is SDL scancode.
 */
bool fd2_key_pressed(const fd2_input_t* input, int scancode);

/*
 * Get the action that maps to an SDL scancode.
 * Used internally by process_event, exposed for testing.
 */
fd2_action_t fd2_input_map_scancode(int scancode);

#ifdef __cplusplus
}
#endif

#endif /* FD2_INPUT_H */
