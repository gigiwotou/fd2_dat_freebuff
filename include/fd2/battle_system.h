#ifndef FD2_BATTLE_SYSTEM_H
#define FD2_BATTLE_SYSTEM_H

#include "fd2/types.h"
#include "fd2/sim/entity.h"
#include "fd2/event_system.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ---- Battle System ----
 * Based on IDA sub_1F525 - Battle main loop.
 * Turn-based tactical combat with menu-driven actions.
 */

#define FD2_BATTLE_MAX_UNITS 32
#define FD2_BATTLE_MAP_W 64
#define FD2_BATTLE_MAP_H 64

/* Battle phases */
typedef enum {
    FD2_BATTLE_PHASE_INIT = 0,
    FD2_BATTLE_PHASE_PLAYER_TURN,
    FD2_BATTLE_PHASE_ENEMY_TURN,
    FD2_BATTLE_PHASE_ACTION_SELECT,
    FD2_BATTLE_PHASE_TARGET_SELECT,
    FD2_BATTLE_PHASE_ACTION_EXECUTE,
    FD2_BATTLE_PHASE_ANIMATION,
    FD2_BATTLE_PHASE_RESULT,
    FD2_BATTLE_PHASE_VICTORY,
    FD2_BATTLE_PHASE_DEFEAT,
} fd2_battle_phase_t;

/* Battle actions */
typedef enum {
    FD2_BATTLE_ACTION_NONE = 0,
    FD2_BATTLE_ACTION_ATTACK,
    FD2_BATTLE_ACTION_MAGIC,
    FD2_BATTLE_ACTION_ITEM,
    FD2_BATTLE_ACTION_DEFEND,
    FD2_BATTLE_ACTION_WAIT,
    FD2_BATTLE_ACTION_ESCAPE,
    FD2_BATTLE_ACTION_SKILL,
    FD2_BATTLE_ACTION_COUNT
} fd2_battle_action_t;

/* Battle unit (character/enemy) */
typedef struct {
    entity_id_t entity_id;
    s16         map_x;
    s16         map_y;
    u8          team;              /* 0=player, 1=enemy */
    u8          unit_type;         /* class/monster type */
    u8          level;
    s16         hp;
    s16         max_hp;
    s16         mp;
    s16         max_mp;
    u8          str;               /* Strength */
    u8          def;               /* Defense */
    u8          agi;               /* Agility */
    u8          int_;              /* Intelligence */
    u8          luck;              /* Luck (crit rate) */
    bool        alive;
    bool        acted_this_turn;
    bool        selected;
    u8          ai_behavior;       /* 0=attack nearest, 1=attack weakest, 2=defend, 3=flee */
    s16         action_order;      /* Turn order (based on AGI) */
} fd2_battle_unit_t;

/* Battle state */
typedef struct {
    fd2_battle_phase_t phase;
    int                turn_number;
    int                current_unit_index;
    int                selected_action;
    int                selected_target;
    bool               player_phase;

    fd2_battle_unit_t  units[FD2_BATTLE_MAX_UNITS];
    int                unit_count;
    int                player_count;
    int                enemy_count;

    u8                 terrain_map[FD2_BATTLE_MAP_W * FD2_BATTLE_MAP_H];
    int                map_width;
    int                map_height;

    /* Damage calculation results */
    s16                last_damage;
    bool               last_critical;
    bool               last_miss;
    u8                 damage_animation;

    /* Menu state */
    int                menu_cursor;
    bool               menu_open;
    bool               targeting;

    /* Battle end conditions */
    bool               battle_ended;
    int                victory_condition;  /* 0=all enemies dead, 1=boss dead, 2=survive N turns */
    int                result;              /* 0=ongoing, 1=victory, 2=defeat, 3=escaped */
} fd2_battle_t;

/* Initialize battle system */
int  fd2_battle_init(fd2_battle_t* battle);
void fd2_battle_shutdown(fd2_battle_t* battle);

/* Add a unit to the battle */
int  fd2_battle_add_unit(fd2_battle_t* battle,
                         s16 map_x, s16 map_y,
                         u8 team, u8 unit_type, u8 level);

/* Set battle map data */
void fd2_battle_set_map(fd2_battle_t* battle, const u8* terrain, int width, int height);

/* Update battle state machine */
void fd2_battle_update(fd2_battle_t* battle, fd2_event_system_t* event_sys,
                       bool action_pressed, int input_x, int input_y);

/* ---- Turn Management ---- */
void fd2_battle_start_turn(fd2_battle_t* battle);
void fd2_battle_end_turn(fd2_battle_t* battle);
void fd2_battle_calculate_action_order(fd2_battle_t* battle);

/* ---- Action Execution ---- */
void fd2_battle_execute_action(fd2_battle_t* battle, int unit_idx,
                               fd2_battle_action_t action, int target_idx);

/* ---- Damage Calculation ---- */
s16  fd2_battle_calc_damage(const fd2_battle_unit_t* attacker,
                            const fd2_battle_unit_t* defender,
                            bool* out_critical, bool* out_miss);

/* ---- AI ---- */
void fd2_battle_ai_select_action(fd2_battle_t* battle, int unit_idx,
                                 fd2_battle_action_t* out_action, int* out_target);

/* ---- Query ---- */
int  fd2_battle_find_unit_at(const fd2_battle_t* battle, s16 map_x, s16 map_y);
int  fd2_battle_find_nearest_enemy(const fd2_battle_t* battle, int unit_idx);
int  fd2_battle_find_weakest_enemy(const fd2_battle_t* battle, int unit_idx);

/* ---- Check End Conditions ---- */
int  fd2_battle_check_end(fd2_battle_t* battle);

#ifdef __cplusplus
}
#endif

#endif /* FD2_BATTLE_SYSTEM_H */
