#ifndef FD2_NPC_H
#define FD2_NPC_H

#include "fd2/types.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ---- NPC System ----
 * Based on IDA sub_13185 - NPC/character initialization.
 * Manages NPC state, behavior, and interaction with player.
 */

#define FD2_NPC_MAX 32

typedef struct {
    s16  map_x;            /* Map tile X */
    s16  map_y;            /* Map tile Y */
    u8   direction;        /* 0=down, 1=up, 2=left, 3=right */
    u8   sprite_id;        /* Icon ID from FDICON.B24 */
    u8   dialog_id;        /* Dialog entry ID */
    u8   behavior;         /* 0=static, 1=patrol, 2=follow, 3=event_trigger */
    u8   event_id;         /* Event trigger ID */
    u8   patrol_route[8];  /* Patrol points */
    u8   patrol_count;
    u8   patrol_index;
    bool activated;        /* Has this NPC been interacted with? */
    bool visible;          /* Is this NPC visible? */
} fd2_npc_t;

typedef struct {
    fd2_npc_t npcs[FD2_NPC_MAX];
    int       npc_count;
    int       active_npc;  /* Currently selected NPC index */
} fd2_npc_system_t;

/* Initialize NPC system */
int  fd2_npc_system_init(fd2_npc_system_t* sys);
void fd2_npc_system_shutdown(fd2_npc_system_t* sys);

/* Create an NPC */
int  fd2_npc_create(fd2_npc_system_t* sys,
                    s16 map_x, s16 map_y,
                    u8 sprite_id, u8 dialog_id, u8 behavior);

/* Get NPC by index */
fd2_npc_t* fd2_npc_get(fd2_npc_system_t* sys, int index);
const fd2_npc_t* fd2_npc_get_c(const fd2_npc_system_t* sys, int index);

/* Find NPC at map position */
int  fd2_npc_find_at(const fd2_npc_system_t* sys, s16 map_x, s16 map_y);

/* Update all NPCs (movement, patrol, triggers) */
void fd2_npc_system_update(fd2_npc_system_t* sys, u32 tick);

/* Render NPCs to screen buffer */
void fd2_npc_system_render(const fd2_npc_system_t* sys,
                           u8* screen, int screen_w, int screen_h,
                           s16 scroll_x, s16 scroll_y);

/* Initialize NPCs from script (sub_13185 logic) */
int  fd2_npc_init_from_script(fd2_npc_system_t* sys, int script_id);

#ifdef __cplusplus
}
#endif

#endif /* FD2_NPC_H */
