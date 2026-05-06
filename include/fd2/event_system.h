#ifndef FD2_EVENT_SYSTEM_H
#define FD2_EVENT_SYSTEM_H

#include "fd2/types.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ---- Event Trigger System ----
 * Based on IDA sub_135DD - Event trigger system.
 * Manages event flags, triggers, and effects from FDFIELD.DAT.
 */

#define FD2_EVENT_FLAG_COUNT 64
#define FD2_EVENT_TRIGGER_MAX 128

typedef enum {
    FD2_EVENT_NONE = 0,
    FD2_EVENT_DIALOG_START,
    FD2_EVENT_NPC_MOVE,
    FD2_EVENT_ITEM_GET,
    FD2_EVENT_FLAG_SET,
    FD2_EVENT_MAP_CHANGE,
    FD2_EVENT_BATTLE_START,
    FD2_EVENT_SCENE_PLAY,
    FD2_EVENT_CUTSCENE_PLAY,
    FD2_EVENT_CUSTOM
} fd2_event_action_t;

typedef struct {
    s16  trigger_x;
    s16  trigger_y;
    s16  trigger_radius;
    u8   event_id;
    u8   condition_flag;
    u8   action;              /* fd2_event_action_t */
    u16  action_param[3];
    bool triggered;
} fd2_event_trigger_t;

typedef struct {
    bool      flags[FD2_EVENT_FLAG_COUNT];
    int       flag_count;

    fd2_event_trigger_t triggers[FD2_EVENT_TRIGGER_MAX];
    int                 trigger_count;

    int       last_triggered_event;
} fd2_event_system_t;

/* Initialize event system */
int  fd2_event_system_init(fd2_event_system_t* sys);
void fd2_event_system_shutdown(fd2_event_system_t* sys);

/* Flag operations */
bool fd2_event_get_flag(const fd2_event_system_t* sys, int flag_id);
void fd2_event_set_flag(fd2_event_system_t* sys, int flag_id, bool value);
void fd2_event_clear_all_flags(fd2_event_system_t* sys);

/* Create an event trigger */
int  fd2_event_create_trigger(fd2_event_system_t* sys,
                              s16 trigger_x, s16 trigger_y,
                              u8 event_id, u8 action,
                              const u16* params, int param_count);

/* Check if player is near any trigger */
int  fd2_event_check_triggers(fd2_event_system_t* sys,
                              s16 player_x, s16 player_y);

/* Get triggered event info */
const fd2_event_trigger_t* fd2_event_get_triggered(const fd2_event_system_t* sys, int event_id);

/* Reset all triggered events */
void fd2_event_reset_triggered(fd2_event_system_t* sys);

#ifdef __cplusplus
}
#endif

#endif /* FD2_EVENT_SYSTEM_H */
