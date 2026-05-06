/**
 * Phase 5 Test - Battle System
 * Tests battle state machine, damage calculation, AI, and turn management.
 */

#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include "fd2/types.h"
#include "fd2/battle_system.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static int test_battle_init(void) {
    printf("[TEST] Battle Init... ");

    fd2_battle_t battle;
    if (fd2_battle_init(&battle) < 0) {
        printf("FAIL (init)\n");
        return -1;
    }

    if (battle.phase != FD2_BATTLE_PHASE_INIT ||
        battle.unit_count != 0 ||
        battle.turn_number != 0) {
        printf("FAIL (state incorrect)\n");
        fd2_battle_shutdown(&battle);
        return -1;
    }

    fd2_battle_shutdown(&battle);
    printf("PASS\n");
    return 0;
}

static int test_add_units(void) {
    printf("[TEST] Add Units... ");

    fd2_battle_t battle;
    fd2_battle_init(&battle);

    /* Add player units */
    int p0 = fd2_battle_add_unit(&battle, 5, 5, 0, 1, 5);
    int p1 = fd2_battle_add_unit(&battle, 6, 5, 0, 2, 6);
    int p2 = fd2_battle_add_unit(&battle, 7, 5, 0, 1, 4);

    /* Add enemy units */
    int e0 = fd2_battle_add_unit(&battle, 20, 20, 1, 3, 5);
    int e1 = fd2_battle_add_unit(&battle, 21, 20, 1, 4, 7);
    int e2 = fd2_battle_add_unit(&battle, 22, 20, 1, 3, 3);

    if (p0 < 0 || p1 < 0 || p2 < 0 || e0 < 0 || e1 < 0 || e2 < 0) {
        printf("FAIL (add units)\n");
        fd2_battle_shutdown(&battle);
        return -1;
    }

    if (battle.unit_count != 6 || battle.player_count != 3 || battle.enemy_count != 3) {
        printf("FAIL (counts: units=%d, players=%d, enemies=%d)\n",
               battle.unit_count, battle.player_count, battle.enemy_count);
        fd2_battle_shutdown(&battle);
        return -1;
    }

    /* Verify stats */
    fd2_battle_unit_t* unit = &battle.units[0];
    if (unit->team != 0 || unit->map_x != 5 || unit->alive != true) {
        printf("FAIL (unit 0 data)\n");
        fd2_battle_shutdown(&battle);
        return -1;
    }

    fd2_battle_shutdown(&battle);
    printf("PASS (added 6 units: 3 players, 3 enemies)\n");
    return 0;
}

static int test_damage_calculation(void) {
    printf("[TEST] Damage Calculation... ");

    fd2_battle_t battle;
    fd2_battle_init(&battle);

    fd2_battle_add_unit(&battle, 0, 0, 0, 1, 10);
    fd2_battle_add_unit(&battle, 10, 10, 1, 1, 5);

    fd2_battle_unit_t* attacker = &battle.units[0];
    fd2_battle_unit_t* defender = &battle.units[1];

    /* Set deterministic stats */
    attacker->str = 20;
    attacker->luck = 10;
    defender->def = 10;
    defender->agi = 10;

    /* Test multiple damage calculations */
    int total_damage = 0;
    int crit_count = 0;
    int miss_count = 0;

    for (int i = 0; i < 100; i++) {
        bool critical, miss;
        s16 damage = fd2_battle_calc_damage(attacker, defender, &critical, &miss);

        total_damage += damage;
        if (critical) crit_count++;
        if (miss) miss_count++;

        /* Verify damage is positive */
        if (damage < 0) {
            printf("FAIL (negative damage: %d)\n", damage);
            fd2_battle_shutdown(&battle);
            return -1;
        }

        /* Critical damage should be higher */
        if (critical && damage < (attacker->str * 2 - defender->def)) {
            printf("FAIL (critical damage too low: %d)\n", damage);
            fd2_battle_shutdown(&battle);
            return -1;
        }
    }

    /* Average damage should be reasonable */
    int avg_damage = total_damage / 100;
    int expected_base = attacker->str * 2 - defender->def;  /* 30 */

    if (avg_damage < expected_base / 2 || avg_damage > expected_base * 2) {
        printf("FAIL (avg damage %d out of range, expected ~%d)\n",
               avg_damage, expected_base);
        fd2_battle_shutdown(&battle);
        return -1;
    }

    /* Should have some criticals (~20% chance with luck=10) */
    if (crit_count < 5 || crit_count > 40) {
        printf("FAIL (crit count %d out of expected range 5-40)\n", crit_count);
        fd2_battle_shutdown(&battle);
        return -1;
    }

    fd2_battle_shutdown(&battle);
    printf("PASS (avg dmg=%d, crits=%d/100, misses=%d/100)\n",
           avg_damage, crit_count, miss_count);
    return 0;
}

static int test_turn_management(void) {
    printf("[TEST] Turn Management... ");

    fd2_battle_t battle;
    fd2_battle_init(&battle);

    /* Add units with different AGI */
    fd2_battle_add_unit(&battle, 0, 0, 0, 1, 5);
    battle.units[0].agi = 5;

    fd2_battle_add_unit(&battle, 0, 0, 1, 1, 5);
    battle.units[1].agi = 10;  /* Enemy has higher AGI */

    fd2_battle_add_unit(&battle, 0, 0, 0, 1, 5);
    battle.units[2].agi = 15;  /* Player has highest AGI */

    fd2_battle_calculate_action_order(&battle);

    /* Verify unit 2 (AGI=15) goes first */
    if (battle.units[0].agi != 15) {
        printf("FAIL (action order: unit 0 AGI=%d, expected 15)\n", battle.units[0].agi);
        fd2_battle_shutdown(&battle);
        return -1;
    }

    /* Start first turn */
    fd2_battle_start_turn(&battle);
    if (battle.turn_number != 1) {
        printf("FAIL (turn number: %d, expected 1)\n", battle.turn_number);
        fd2_battle_shutdown(&battle);
        return -1;
    }

    fd2_battle_shutdown(&battle);
    printf("PASS\n");
    return 0;
}

static int test_action_execution(void) {
    printf("[TEST] Action Execution... ");

    fd2_battle_t battle;
    fd2_battle_init(&battle);

    fd2_battle_add_unit(&battle, 0, 0, 0, 1, 10);
    fd2_battle_add_unit(&battle, 10, 10, 1, 1, 5);

    battle.units[0].str = 20;
    battle.units[1].def = 10;
    battle.units[1].hp = 50;

    /* Execute attack */
    fd2_battle_execute_action(&battle, 0, FD2_BATTLE_ACTION_ATTACK, 1);

    if (battle.last_damage <= 0) {
        printf("FAIL (no damage dealt)\n");
        fd2_battle_shutdown(&battle);
        return -1;
    }

    /* Verify HP was reduced */
    if (battle.units[1].hp >= 50) {
        printf("FAIL (HP not reduced: %d)\n", battle.units[1].hp);
        fd2_battle_shutdown(&battle);
        return -1;
    }

    /* Test defend action */
    fd2_battle_t battle2;
    fd2_battle_init(&battle2);
    fd2_battle_add_unit(&battle2, 0, 0, 0, 1, 5);
    battle2.units[0].def = 10;

    fd2_battle_execute_action(&battle2, 0, FD2_BATTLE_ACTION_DEFEND, -1);
    if (battle2.units[0].def != 20) {
        printf("FAIL (defend didn't double DEF: %d)\n", battle2.units[0].def);
        fd2_battle_shutdown(&battle);
        fd2_battle_shutdown(&battle2);
        return -1;
    }

    fd2_battle_shutdown(&battle);
    fd2_battle_shutdown(&battle2);
    printf("PASS\n");
    return 0;
}

static int test_ai(void) {
    printf("[TEST] AI System... ");

    fd2_battle_t battle;
    fd2_battle_init(&battle);

    /* Player unit */
    fd2_battle_add_unit(&battle, 0, 0, 0, 1, 5);

    /* Enemy units with different behaviors */
    fd2_battle_add_unit(&battle, 10, 10, 1, 1, 5);
    battle.units[1].ai_behavior = 0;  /* Attack nearest */

    fd2_battle_add_unit(&battle, 20, 20, 1, 1, 5);
    battle.units[2].ai_behavior = 1;  /* Attack weakest */

    fd2_battle_add_unit(&battle, 15, 15, 1, 1, 5);
    battle.units[3].ai_behavior = 2;  /* Defend when low HP */
    battle.units[3].hp = battle.units[3].max_hp / 4;  /* Low HP */

    /* Test AI action selection */
    fd2_battle_action_t action;
    int target;

    /* Enemy 0: Should attack nearest (player at 0,0) */
    fd2_battle_ai_select_action(&battle, 1, &action, &target);
    if (action != FD2_BATTLE_ACTION_ATTACK || target != 0) {
        printf("FAIL (AI 0: action=%d, target=%d)\n", action, target);
        fd2_battle_shutdown(&battle);
        return -1;
    }

    /* Enemy 1: Should attack weakest (also player at 0,0) */
    fd2_battle_ai_select_action(&battle, 2, &action, &target);
    if (action != FD2_BATTLE_ACTION_ATTACK) {
        printf("FAIL (AI 1: action=%d)\n", action);
        fd2_battle_shutdown(&battle);
        return -1;
    }

    /* Enemy 2: Low HP should defend */
    fd2_battle_ai_select_action(&battle, 3, &action, &target);
    if (action != FD2_BATTLE_ACTION_DEFEND) {
        printf("FAIL (AI 2: action=%d, expected DEFEND)\n", action);
        fd2_battle_shutdown(&battle);
        return -1;
    }

    fd2_battle_shutdown(&battle);
    printf("PASS\n");
    return 0;
}

static int test_battle_end(void) {
    printf("[TEST] Battle End Conditions... ");

    fd2_battle_t battle;
    fd2_battle_init(&battle);

    fd2_battle_add_unit(&battle, 0, 0, 0, 1, 5);
    fd2_battle_add_unit(&battle, 10, 10, 1, 1, 5);

    /* Kill enemy */
    battle.units[1].alive = false;
    battle.units[1].hp = 0;
    battle.enemy_count--;

    int result = fd2_battle_check_end(&battle);
    if (result != 1 || battle.result != 1) {
        printf("FAIL (victory not detected: result=%d)\n", result);
        fd2_battle_shutdown(&battle);
        return -1;
    }

    /* Test defeat */
    fd2_battle_t battle2;
    fd2_battle_init(&battle2);

    fd2_battle_add_unit(&battle2, 0, 0, 0, 1, 5);
    fd2_battle_add_unit(&battle2, 10, 10, 1, 1, 5);

    battle2.units[0].alive = false;
    battle2.units[0].hp = 0;
    battle2.player_count--;

    result = fd2_battle_check_end(&battle2);
    if (result != 2 || battle2.result != 2) {
        printf("FAIL (defeat not detected: result=%d)\n", result);
        fd2_battle_shutdown(&battle);
        fd2_battle_shutdown(&battle2);
        return -1;
    }

    fd2_battle_shutdown(&battle);
    fd2_battle_shutdown(&battle2);
    printf("PASS\n");
    return 0;
}

/* ---- Main ---- */

#ifdef _WIN32
#undef main
#endif

int main(int argc, char* argv[]) {
    (void)argc; (void)argv;

    srand((unsigned int)time(NULL));

    printf("=== FD2 Phase 5: Battle System Test ===\n\n");

    int failures = 0;

    failures += test_battle_init();
    failures += test_add_units();
    failures += test_damage_calculation();
    failures += test_turn_management();
    failures += test_action_execution();
    failures += test_ai();
    failures += test_battle_end();

    printf("\n=== Results: %d failures ===\n", failures);
    return failures > 0 ? 1 : 0;
}
