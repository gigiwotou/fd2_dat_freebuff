#ifndef FD2_INPUT_H
#define FD2_INPUT_H

#include "fd2/types.h"
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

/* ---- Input State ---- */
struct fd2_input {
    bool  pressed[FD2_ACTION_COUNT];  /* Just pressed this frame (edge) */
    bool  held[FD2_ACTION_COUNT];     /* Currently held down */
    bool  released[FD2_ACTION_COUNT]; /* Just released this frame (edge) */

    /* Raw key state for diagnostic/debug */
    int   last_keycode;               /* Last SDL key event code */
    int   last_scancode;              /* Last SDL scan code */
    bool  key_states[512];            /* Raw key state (indexed by scancode) */
};

/* ---- Functions ---- */

void fd2_input_init(fd2_input_t* input);
void fd2_input_process_event(fd2_input_t* input, const void* sdl_event);
void fd2_input_begin_frame(fd2_input_t* input);
bool fd2_action_pressed(const fd2_input_t* input, fd2_action_t action);
bool fd2_action_held(const fd2_input_t* input, fd2_action_t action);
bool fd2_action_released(const fd2_input_t* input, fd2_action_t action);
bool fd2_input_any_pressed(const fd2_input_t* input);
bool fd2_key_held(const fd2_input_t* input, int scancode);
bool fd2_key_pressed(const fd2_input_t* input, int scancode);
fd2_action_t fd2_input_map_scancode(int scancode);

#ifdef __cplusplus
}
#endif

#endif /* FD2_INPUT_H */
