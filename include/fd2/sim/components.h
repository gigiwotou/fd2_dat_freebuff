#ifndef FD2_SIM_COMPONENTS_H
#define FD2_SIM_COMPONENTS_H

#include "fd2/types.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ---- Sprite Component ----
 * Position on map, direction, animation frame, icon ID.
 * Mirrors original game character position logic.
 */
typedef struct {
    s16  tile_x;
    s16  tile_y;
    s16  prev_tile_x;
    s16  prev_tile_y;
    u8   direction;
    u8   anim_frame;
    u8   anim_timer;
    u8   icon_id;
    u8   palette_offset;
    u8   facing;
    bool moving;
    u8   move_progress;
} fd2_sprite_comp_t;

/* ---- Stats Component ----
 * Character HP/MP/attributes. Mirrors original battle data.
 */
typedef struct {
    u16  hp;
    u16  max_hp;
    u16  mp;
    u16  max_mp;
    u8   str;
    u8   def;
    u8   agi;
    u8   int_;
    u8   level;
    u8   class_id;
    u8   status_flags;
    u8   exp[4];
    s16  action_order;
} fd2_stats_comp_t;

/* ---- NPC Component ----
 * Script binding, event flags, dialog IDs.
 * Used for plot scenes (sub_3231B, sub_1366A).
 */
typedef struct {
    u16  script_id;
    u8   event_flags[8];
    u8   dialog_id;
    u8   npc_type;
    u8   trigger_radius;
    u8   patrol_points[8];
    u8   patrol_count;
    u8   current_patrol;
    bool activated;
    u8   behavior;
} fd2_npc_comp_t;

/* ---- Map Component ----
 * Tile-based map data, terrain info, spawn points.
 * Mirrors original FDFIELD/FDSHAP data.
 */
typedef struct {
    s16  map_id;
    u8*  layout_data;
    u8*  control_data;
    u8*  spawn_data;
    u16  map_width;
    u16  map_height;
    s16  scroll_x;
    s16  scroll_y;
    u8   terrain_id;
} fd2_map_comp_t;

/* ---- Battle Component ----
 * Battle state, turn info, action queue.
 * Mirrors original battle logic (sub_1F525).
 */
typedef struct {
    u16  battle_id;
    u8   turn;
    u8   phase;
    u8   current_actor;
    u8   action_queue[FD2_MAX_ENTITIES];
    u8   action_count;
    u8   selected_action;
    u8   selected_target;
    bool in_action;
    u8   damage_shake;
    s8   damage_value;
    u8   anim_playing;
    u8   anim_frame;
} fd2_battle_comp_t;

/* ---- Tag Component ----
 * String tag for entity lookup.
 */
typedef struct {
    char name[32];
} fd2_tag_comp_t;

#ifdef __cplusplus
}
#endif

#endif /* FD2_SIM_COMPONENTS_H */
