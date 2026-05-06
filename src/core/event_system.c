/**
 * FD2 Event System Implementation
 * Based on IDA sub_135DD - Event trigger system.
 */

#define _GNU_SOURCE
#include "fd2/event_system.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

int fd2_event_system_init(fd2_event_system_t* sys) {
    if (!sys) return -1;

    memset(sys, 0, sizeof(*sys));
    sys->flag_count = FD2_EVENT_FLAG_COUNT;
    sys->trigger_count = 0;
    sys->last_triggered_event = -1;

    return 0;
}

void fd2_event_system_shutdown(fd2_event_system_t* sys) {
    if (!sys) return;
    memset(sys, 0, sizeof(*sys));
}

bool fd2_event_get_flag(const fd2_event_system_t* sys, int flag_id) {
    if (!sys || flag_id < 0 || flag_id >= FD2_EVENT_FLAG_COUNT) return false;
    return sys->flags[flag_id];
}

void fd2_event_set_flag(fd2_event_system_t* sys, int flag_id, bool value) {
    if (!sys || flag_id < 0 || flag_id >= FD2_EVENT_FLAG_COUNT) return;
    sys->flags[flag_id] = value;
}

void fd2_event_clear_all_flags(fd2_event_system_t* sys) {
    if (!sys) return;
    memset(sys->flags, 0, sizeof(sys->flags));
}

int fd2_event_create_trigger(fd2_event_system_t* sys,
                             s16 trigger_x, s16 trigger_y,
                             u8 event_id, u8 action,
                             const u16* params, int param_count) {
    if (!sys || sys->trigger_count >= FD2_EVENT_TRIGGER_MAX) return -1;

    fd2_event_trigger_t* trigger = &sys->triggers[sys->trigger_count];
    memset(trigger, 0, sizeof(*trigger));

    trigger->trigger_x = trigger_x;
    trigger->trigger_y = trigger_y;
    trigger->trigger_radius = 1;
    trigger->event_id = event_id;
    trigger->action = action;
    trigger->triggered = false;

    if (params && param_count > 0) {
        int copy_count = param_count < 3 ? param_count : 3;
        memcpy(trigger->action_param, params, copy_count * sizeof(u16));
    }

    int index = sys->trigger_count;
    sys->trigger_count++;

    return index;
}

int fd2_event_check_triggers(fd2_event_system_t* sys,
                             s16 player_x, s16 player_y) {
    if (!sys) return -1;

    int triggered_count = 0;

    for (int i = 0; i < sys->trigger_count; i++) {
        fd2_event_trigger_t* trigger = &sys->triggers[i];
        if (trigger->triggered) continue;

        /* Check if player is within trigger radius */
        s16 dx = player_x - trigger->trigger_x;
        s16 dy = player_y - trigger->trigger_y;

        if (dx < 0) dx = -dx;
        if (dy < 0) dy = -dy;

        if (dx <= trigger->trigger_radius && dy <= trigger->trigger_radius) {
            /* Check condition flag */
            if (trigger->condition_flag > 0 &&
                !fd2_event_get_flag(sys, trigger->condition_flag)) {
                continue;
            }

            trigger->triggered = true;
            sys->last_triggered_event = trigger->event_id;
            triggered_count++;

            printf("[EVENT] Trigger %d at (%d,%d) activated (action=%d)\n",
                   trigger->event_id, trigger->trigger_x, trigger->trigger_y,
                   trigger->action);
        }
    }

    return triggered_count;
}

const fd2_event_trigger_t* fd2_event_get_triggered(const fd2_event_system_t* sys, int event_id) {
    if (!sys || event_id < 0) return NULL;

    for (int i = 0; i < sys->trigger_count; i++) {
        if (sys->triggers[i].event_id == event_id && sys->triggers[i].triggered) {
            return &sys->triggers[i];
        }
    }

    return NULL;
}

void fd2_event_reset_triggered(fd2_event_system_t* sys) {
    if (!sys) return;

    for (int i = 0; i < sys->trigger_count; i++) {
        sys->triggers[i].triggered = false;
    }

    sys->last_triggered_event = -1;
}
