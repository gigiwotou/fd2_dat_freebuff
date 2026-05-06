#ifndef FD2_PLATFORM_INPUT_H
#define FD2_PLATFORM_INPUT_H

#include "fd2/types.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ---- Input State ---- */
typedef struct {
    bool actions[FD2_ACTION_COUNT];
    bool actions_pressed[FD2_ACTION_COUNT];
    bool actions_released[FD2_ACTION_COUNT];
} fd2_input_state_t;

/* ---- Input Interface ---- */

typedef struct {
    int (*init)(fd2_input_t** out_input);
    void (*shutdown)(fd2_input_t* input);

    void (*process_event)(fd2_input_t* input, void* platform_event);
    void (*begin_frame)(fd2_input_t* input);
    void (*end_frame)(fd2_input_t* input);

    bool (*is_action_held)(fd2_input_t* input, fd2_action_t action);
    bool (*is_action_pressed)(fd2_input_t* input, fd2_action_t action);
    bool (*is_action_released)(fd2_input_t* input, fd2_action_t action);
    bool (*is_any_pressed)(fd2_input_t* input);
} fd2_input_iface_t;

/* Get the platform input interface (implemented by platform/sdl_input.c) */
const fd2_input_iface_t* fd2_platform_get_input(void);

#ifdef __cplusplus
}
#endif

#endif /* FD2_PLATFORM_INPUT_H */
