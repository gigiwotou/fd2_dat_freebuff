/**
 * Battle System Implementation
 * Based on IDA sub_1F525 - Battle main loop.
 * Turn-based tactical combat with menu-driven actions.
 */

#define _GNU_SOURCE
#include "fd2/battle_system.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

/* ---- Initialization ---- */

int fd2_battle_init(fd2_battle_t* battle) {
    if (!battle) return -1;

    memset(battle, 0, sizeof(*battle));
    battle->phase = FD2_BATTLE_PHASE_INIT;
    battle->turn_number = 0;
    battle->unit_count = 0;
    battle->player_count = 0;
    battle->enemy_count = 0;
    battle->result = 0;
    battle->menu_cursor = 0;
    battle->victory_condition = 0;

    memset(battle->terrain_map, 0, sizeof(battle->terrain_map));
    battle->map_width = FD2_BATTLE_MAP_W;
    battle->map_height = FD2_BATTLE_MAP_H;

    return 0;
}

void fd2_battle_shutdown(fd2_battle_t* battle) {
    if (!battle) return;
    memset(battle, 0, sizeof(*battle));
}

int fd2_battle_add_unit(fd2_battle_t* battle,
                        s16 map_x, s16 map_y,
                        u8 team, u8 unit_type, u8 level) {
    if (!battle || battle->unit_count >= FD2_BATTLE_MAX_UNITS) return -1;

    fd2_battle_unit_t* unit = &battle->units[battle->unit_count];
    memset(unit, 0, sizeof(*unit));

    unit->map_x = map_x;
    unit->map_y = map_y;
    unit->team = team;
    unit->unit_type = unit_type;
    unit->level = level;
    unit->alive = true;
    unit->acted_this_turn = false;
    unit->ai_behavior = (team == 1) ? 0 : 255;  /* Enemies use AI, players don't */

    /* Base stats based on level and unit_type */
    unit->max_hp = 50 + level * 10 + unit_type * 5;
    unit->hp = unit->max_hp;
    unit->max_mp = 10 + level * 5;
    unit->mp = unit->max_mp;
    unit->str = 5 + level * 2;
    unit->def = 3 + level * 2;
    unit->agi = 5 + level;
    unit->int_ = 5 + level * 2;
    unit->luck = 3 + (level / 2);

    int index = battle->unit_count;
    battle->unit_count++;

    if (team == 0) battle->player_count++;
    else battle->enemy_count++;

    return index;
}

void fd2_battle_set_map(fd2_battle_t* battle, const u8* terrain, int width, int height) {
    if (!battle || !terrain) return;

    battle->map_width = (width < FD2_BATTLE_MAP_W) ? width : FD2_BATTLE_MAP_W;
    battle->map_height = (height < FD2_BATTLE_MAP_H) ? height : FD2_BATTLE_MAP_H;

    memcpy(battle->terrain_map, terrain,
           battle->map_width * battle->map_height);
}

/* ---- Turn Management ---- */

static int compare_action_order(const void* a, const void* b) {
    const fd2_battle_unit_t* ua = (const fd2_battle_unit_t*)a;
    const fd2_battle_unit_t* ub = (const fd2_battle_unit_t*)b;
    return ub->action_order - ua->action_order;  /* Higher AGI goes first */
}

void fd2_battle_calculate_action_order(fd2_battle_t* battle) {
    if (!battle) return;

    /* Calculate action order based on AGI + random factor */
    for (int i = 0; i < battle->unit_count; i++) {
        fd2_battle_unit_t* unit = &battle->units[i];
        if (!unit->alive) {
            unit->action_order = 0;
            continue;
        }
        unit->action_order = unit->agi + (rand() % 5);
    }

    /* Sort units by action order */
    qsort(battle->units, battle->unit_count,
          sizeof(fd2_battle_unit_t), compare_action_order);
}

void fd2_battle_start_turn(fd2_battle_t* battle) {
    if (!battle) return;

    battle->turn_number++;
    printf("[BATTLE] Turn %d started\n", battle->turn_number);

    /* Reset acted flags for all alive units */
    for (int i = 0; i < battle->unit_count; i++) {
        fd2_battle_unit_t* unit = &battle->units[i];
        if (unit->alive) {
            unit->acted_this_turn = false;
        }
    }

    fd2_battle_calculate_action_order(battle);

    /* Find first alive unit */
    battle->current_unit_index = 0;
    while (battle->current_unit_index < battle->unit_count &&
           !battle->units[battle->current_unit_index].alive) {
        battle->current_unit_index++;
    }

    if (battle->current_unit_index < battle->unit_count) {
        fd2_battle_unit_t* unit = &battle->units[battle->current_unit_index];
        if (unit->team == 0) {
            battle->phase = FD2_BATTLE_PHASE_PLAYER_TURN;
            battle->player_phase = true;
        } else {
            battle->phase = FD2_BATTLE_PHASE_ENEMY_TURN;
            battle->player_phase = false;
        }
    }
}

void fd2_battle_end_turn(fd2_battle_t* battle) {
    if (!battle) return;

    battle->units[battle->current_unit_index].acted_this_turn = true;

    /* Find next alive unit */
    battle->current_unit_index++;
    while (battle->current_unit_index < battle->unit_count &&
           !battle->units[battle->current_unit_index].alive) {
        battle->current_unit_index++;
    }

    if (battle->current_unit_index >= battle->unit_count) {
        /* All units have acted, start new turn */
        fd2_battle_start_turn(battle);
    } else {
        fd2_battle_unit_t* unit = &battle->units[battle->current_unit_index];
        if (unit->team == 0) {
            battle->phase = FD2_BATTLE_PHASE_PLAYER_TURN;
            battle->player_phase = true;
        } else {
            battle->phase = FD2_BATTLE_PHASE_ENEMY_TURN;
            battle->player_phase = false;
        }
    }
}

/* ---- Damage Calculation ----
 * Based on original game formula (IDA analysis):
 * Damage = (Attacker.STR * 2 - Defender.DEF) * Random(0.8, 1.2)
 * Critical hit: 10% chance, damage * 2
 * Miss: Based on AGI difference
 */

s16 fd2_battle_calc_damage(const fd2_battle_unit_t* attacker,
                           const fd2_battle_unit_t* defender,
                           bool* out_critical, bool* out_miss) {
    if (!attacker || !defender) return 0;

    *out_critical = false;
    *out_miss = false;

    /* Miss calculation: if defender AGI > attacker AGI * 2, chance to miss */
    if (defender->agi > attacker->agi * 2) {
        int miss_chance = (defender->agi - attacker->agi * 2) * 5;
        if ((rand() % 100) < miss_chance) {
            *out_miss = true;
            return 0;
        }
    }

    /* Base damage */
    s16 base_damage = (s16)(attacker->str * 2) - (s16)defender->def;
    if (base_damage < 1) base_damage = 1;

    /* Random factor (0.8 to 1.2) */
    int random_factor = 80 + (rand() % 41);
    s16 damage = (s16)((base_damage * random_factor) / 100);

    /* Critical hit (based on luck) */
    int crit_chance = attacker->luck * 2;
    if ((rand() % 100) < crit_chance) {
        damage *= 2;
        *out_critical = true;
    }

    /* Minimum damage is 1 */
    if (damage < 1) damage = 1;

    return damage;
}

/* ---- Action Execution ---- */

void fd2_battle_execute_action(fd2_battle_t* battle, int unit_idx,
                               fd2_battle_action_t action, int target_idx) {
    if (!battle || unit_idx < 0 || unit_idx >= battle->unit_count) return;

    fd2_battle_unit_t* attacker = &battle->units[unit_idx];
    if (!attacker->alive) return;

    battle->selected_action = action;
    battle->selected_target = target_idx;

    switch (action) {
        case FD2_BATTLE_ACTION_ATTACK:
            if (target_idx >= 0 && target_idx < battle->unit_count) {
                fd2_battle_unit_t* defender = &battle->units[target_idx];
                if (defender->alive) {
                    bool critical, miss;
                    s16 damage = fd2_battle_calc_damage(attacker, defender, &critical, &miss);

                    if (miss) {
                        battle->last_damage = 0;
                        battle->last_miss = true;
                        battle->last_critical = false;
                        printf("[BATTLE] %s attacked but MISSED!\n",
                               attacker->team == 0 ? "Player" : "Enemy");
                    } else {
                        defender->hp -= damage;
                        battle->last_damage = damage;
                        battle->last_miss = false;
                        battle->last_critical = critical;

                        if (defender->hp <= 0) {
                            defender->hp = 0;
                            defender->alive = false;
                            printf("[BATTLE] %s defeated %s! (DMG=%d%s)\n",
                                   attacker->team == 0 ? "Player" : "Enemy",
                                   defender->team == 0 ? "player unit" : "enemy unit",
                                   damage, critical ? " CRIT!" : "");
                        } else {
                            printf("[BATTLE] %s hit %s for %d damage%s\n",
                                   attacker->team == 0 ? "Player" : "Enemy",
                                   defender->team == 0 ? "player unit" : "enemy unit",
                                   damage, critical ? " CRIT!" : "");
                        }
                    }

                    battle->damage_animation = 8;
                }
            }
            break;

        case FD2_BATTLE_ACTION_DEFEND:
            attacker->def *= 2;  /* Double defense for this turn */
            printf("[BATTLE] %s is defending!\n",
                   attacker->team == 0 ? "Player" : "Enemy");
            break;

        case FD2_BATTLE_ACTION_WAIT:
            printf("[BATTLE] %s is waiting.\n",
                   attacker->team == 0 ? "Player" : "Enemy");
            break;

        default:
            break;
    }
}

/* ---- AI ---- */

void fd2_battle_ai_select_action(fd2_battle_t* battle, int unit_idx,
                                 fd2_battle_action_t* out_action, int* out_target) {
    if (!battle || unit_idx < 0 || unit_idx >= battle->unit_count) {
        *out_action = FD2_BATTLE_ACTION_WAIT;
        *out_target = -1;
        return;
    }

    fd2_battle_unit_t* unit = &battle->units[unit_idx];
    if (!unit->alive) {
        *out_action = FD2_BATTLE_ACTION_WAIT;
        *out_target = -1;
        return;
    }

    /* AI behavior based on unit's AI type */
    switch (unit->ai_behavior) {
        case 0:  /* Attack nearest enemy */
            *out_action = FD2_BATTLE_ACTION_ATTACK;
            *out_target = fd2_battle_find_nearest_enemy(battle, unit_idx);
            break;

        case 1:  /* Attack weakest enemy */
            *out_action = FD2_BATTLE_ACTION_ATTACK;
            *out_target = fd2_battle_find_weakest_enemy(battle, unit_idx);
            break;

        case 2:  /* Defend */
            if (unit->hp < unit->max_hp / 2) {
                *out_action = FD2_BATTLE_ACTION_DEFEND;
            } else {
                *out_action = FD2_BATTLE_ACTION_ATTACK;
                *out_target = fd2_battle_find_nearest_enemy(battle, unit_idx);
            }
            break;

        case 3:  /* Flee when low HP */
            if (unit->hp < unit->max_hp / 3) {
                *out_action = FD2_BATTLE_ACTION_WAIT;
            } else {
                *out_action = FD2_BATTLE_ACTION_ATTACK;
                *out_target = fd2_battle_find_nearest_enemy(battle, unit_idx);
            }
            break;

        default:
            *out_action = FD2_BATTLE_ACTION_ATTACK;
            *out_target = fd2_battle_find_nearest_enemy(battle, unit_idx);
            break;
    }

    if (*out_target < 0) {
        *out_action = FD2_BATTLE_ACTION_WAIT;
    }
}

/* ---- Query Functions ---- */

int fd2_battle_find_unit_at(const fd2_battle_t* battle, s16 map_x, s16 map_y) {
    if (!battle) return -1;

    for (int i = 0; i < battle->unit_count; i++) {
        if (battle->units[i].alive &&
            battle->units[i].map_x == map_x &&
            battle->units[i].map_y == map_y) {
            return i;
        }
    }

    return -1;
}

int fd2_battle_find_nearest_enemy(const fd2_battle_t* battle, int unit_idx) {
    if (!battle || unit_idx < 0 || unit_idx >= battle->unit_count) return -1;

    const fd2_battle_unit_t* unit = &battle->units[unit_idx];
    int nearest_idx = -1;
    int nearest_dist = 9999;

    for (int i = 0; i < battle->unit_count; i++) {
        if (i == unit_idx) continue;
        if (!battle->units[i].alive) continue;
        if (battle->units[i].team == unit->team) continue;

        s16 dx = battle->units[i].map_x - unit->map_x;
        s16 dy = battle->units[i].map_y - unit->map_y;
        if (dx < 0) dx = -dx;
        if (dy < 0) dy = -dy;
        int dist = dx + dy;

        if (dist < nearest_dist) {
            nearest_dist = dist;
            nearest_idx = i;
        }
    }

    return nearest_idx;
}

int fd2_battle_find_weakest_enemy(const fd2_battle_t* battle, int unit_idx) {
    if (!battle || unit_idx < 0 || unit_idx >= battle->unit_count) return -1;

    const fd2_battle_unit_t* unit = &battle->units[unit_idx];
    int weakest_idx = -1;
    int weakest_hp = 9999;

    for (int i = 0; i < battle->unit_count; i++) {
        if (i == unit_idx) continue;
        if (!battle->units[i].alive) continue;
        if (battle->units[i].team == unit->team) continue;

        if (battle->units[i].hp < weakest_hp) {
            weakest_hp = battle->units[i].hp;
            weakest_idx = i;
        }
    }

    return weakest_idx;
}

/* ---- End Condition Check ---- */

int fd2_battle_check_end(fd2_battle_t* battle) {
    if (!battle) return 0;

    int player_alive = 0;
    int enemy_alive = 0;

    for (int i = 0; i < battle->unit_count; i++) {
        if (battle->units[i].alive) {
            if (battle->units[i].team == 0) player_alive++;
            else enemy_alive++;
        }
    }

    if (enemy_alive == 0) {
        battle->result = 1;  /* Victory */
        battle->battle_ended = true;
        printf("[BATTLE] VICTORY! All enemies defeated.\n");
        return 1;
    }

    if (player_alive == 0) {
        battle->result = 2;  /* Defeat */
        battle->battle_ended = true;
        printf("[BATTLE] DEFEAT! All units lost.\n");
        return 2;
    }

    return 0;  /* Battle continues */
}

/* ---- Main Update ---- */

void fd2_battle_update(fd2_battle_t* battle, fd2_event_system_t* event_sys,
                       bool action_pressed, int input_x, int input_y) {
    if (!battle || battle->battle_ended) return;

    (void)event_sys;
    (void)input_y;

    if (battle->phase == FD2_BATTLE_PHASE_INIT) {
        fd2_battle_start_turn(battle);
        return;
    }

    if (battle->damage_animation > 0) {
        battle->damage_animation--;
        if (battle->damage_animation == 0) {
            fd2_battle_end_turn(battle);
            fd2_battle_check_end(battle);
        }
        return;
    }

    if (battle->player_phase) {
        /* Player turn: wait for input */
        if (action_pressed) {
            if (!battle->targeting) {
                /* Select action */
                battle->targeting = true;
                battle->menu_cursor = FD2_BATTLE_ACTION_ATTACK;
            } else {
                /* Execute action */
                fd2_battle_unit_t* current_unit = &battle->units[battle->current_unit_index];
                int target = fd2_battle_find_nearest_enemy(battle, battle->current_unit_index);
                fd2_battle_execute_action(battle, battle->current_unit_index,
                                          (fd2_battle_action_t)battle->menu_cursor, target);
                battle->targeting = false;
            }
        }

        if (input_x != 0 && battle->targeting) {
            battle->menu_cursor += input_x;
            if (battle->menu_cursor < FD2_BATTLE_ACTION_ATTACK)
                battle->menu_cursor = FD2_BATTLE_ACTION_COUNT - 1;
            if (battle->menu_cursor >= FD2_BATTLE_ACTION_COUNT)
                battle->menu_cursor = FD2_BATTLE_ACTION_ATTACK;
        }
    } else {
        /* Enemy turn: AI decides */
        fd2_battle_action_t ai_action;
        int ai_target;
        fd2_battle_ai_select_action(battle, battle->current_unit_index,
                                    &ai_action, &ai_target);
        fd2_battle_execute_action(battle, battle->current_unit_index,
                                  ai_action, ai_target);
    }
}
