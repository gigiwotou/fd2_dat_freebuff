/**
 * Phase 4 Test - Plot System
 * Tests dialog, NPC, and event systems.
 */

#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include "fd2/types.h"
#include "fd2/dialog.h"
#include "fd2/npc.h"
#include "fd2/event_system.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int test_dialog_system(void) {
    printf("[TEST] Dialog System... ");

    fd2_dialog_box_t box;
    if (fd2_dialog_init(&box) < 0) {
        printf("FAIL (init)\n");
        return -1;
    }

    /* Create test dialog data */
    u8 test_data[] = "Hello, welcome to FD2!|Start Game;Continue Game;Quit\nThis is a test dialog.\nThird line of text.\0";

    int count = fd2_dialog_load_from_dat(&box, test_data, sizeof(test_data));
    if (count < 1) {
        printf("FAIL (load, got %d entries)\n", count);
        fd2_dialog_shutdown(&box);
        return -1;
    }

    if (fd2_dialog_start(&box, 0) < 0) {
        printf("FAIL (start)\n");
        fd2_dialog_shutdown(&box);
        return -1;
    }

    const fd2_dialog_entry_t* entry = fd2_dialog_get_current(&box);
    if (!entry || entry->has_choices != true || entry->choice_count != 3) {
        printf("FAIL (entry: has_choices=%d, count=%d)\n",
               entry ? entry->has_choices : -1,
               entry ? entry->choice_count : -1);
        fd2_dialog_shutdown(&box);
        return -1;
    }

    /* Test typing animation */
    for (int i = 0; i < 50; i++) {
        bool done = fd2_dialog_update(&box, false);
        if (done) break;
    }

    fd2_dialog_shutdown(&box);
    printf("PASS (loaded %d entries, choices working)\n", count);
    return 0;
}

static int test_npc_system(void) {
    printf("[TEST] NPC System... ");

    fd2_npc_system_t sys;
    if (fd2_npc_system_init(&sys) < 0) {
        printf("FAIL (init)\n");
        return -1;
    }

    int npc0 = fd2_npc_create(&sys, 10, 15, 0, 0, 0);
    int npc1 = fd2_npc_create(&sys, 12, 15, 1, 1, 0);
    int npc2 = fd2_npc_create(&sys, 14, 15, 2, 2, 1);

    if (npc0 < 0 || npc1 < 0 || npc2 < 0) {
        printf("FAIL (create)\n");
        fd2_npc_system_shutdown(&sys);
        return -1;
    }

    /* Test position lookup */
    int found = fd2_npc_find_at(&sys, 10, 15);
    if (found != npc0) {
        printf("FAIL (find_at: got %d expected %d)\n", found, npc0);
        fd2_npc_system_shutdown(&sys);
        return -1;
    }

    /* Test script initialization */
    int script_npc_count = fd2_npc_init_from_script(&sys, 99);
    if (script_npc_count < 5) {
        printf("FAIL (script init: got %d NPCs)\n", script_npc_count);
        fd2_npc_system_shutdown(&sys);
        return -1;
    }

    /* Test update */
    fd2_npc_system_update(&sys, 60);

    fd2_npc_system_shutdown(&sys);
    printf("PASS (created %d NPCs, script init works)\n", script_npc_count);
    return 0;
}

static int test_event_system(void) {
    printf("[TEST] Event System... ");

    fd2_event_system_t sys;
    if (fd2_event_system_init(&sys) < 0) {
        printf("FAIL (init)\n");
        return -1;
    }

    /* Test flag operations */
    fd2_event_set_flag(&sys, 0, true);
    fd2_event_set_flag(&sys, 1, false);

    if (!fd2_event_get_flag(&sys, 0) || fd2_event_get_flag(&sys, 1)) {
        printf("FAIL (flags)\n");
        fd2_event_system_shutdown(&sys);
        return -1;
    }

    fd2_event_clear_all_flags(&sys);
    if (fd2_event_get_flag(&sys, 0)) {
        printf("FAIL (clear flags)\n");
        fd2_event_system_shutdown(&sys);
        return -1;
    }

    /* Test trigger creation */
    u16 params[] = {1, 2, 3};
    int trig0 = fd2_event_create_trigger(&sys, 10, 15, 0, FD2_EVENT_DIALOG_START, params, 3);
    int trig1 = fd2_event_create_trigger(&sys, 20, 25, 1, FD2_EVENT_BATTLE_START, NULL, 0);
    int trig2 = fd2_event_create_trigger(&sys, 30, 35, 2, FD2_EVENT_SCENE_PLAY, params, 1);

    if (trig0 < 0 || trig1 < 0 || trig2 < 0) {
        printf("FAIL (create trigger)\n");
        fd2_event_system_shutdown(&sys);
        return -1;
    }

    /* Test trigger activation */
    int triggered = fd2_event_check_triggers(&sys, 10, 15);
    if (triggered != 1) {
        printf("FAIL (check triggers: got %d expected 1)\n", triggered);
        fd2_event_system_shutdown(&sys);
        return -1;
    }

    const fd2_event_trigger_t* triggered_trig = fd2_event_get_triggered(&sys, 0);
    if (!triggered_trig || !triggered_trig->triggered) {
        printf("FAIL (get triggered)\n");
        fd2_event_system_shutdown(&sys);
        return -1;
    }

    /* Test condition flag */
    sys.triggers[1].condition_flag = 5;
    fd2_event_set_flag(&sys, 5, true);
    triggered = fd2_event_check_triggers(&sys, 20, 25);
    if (triggered != 1) {
        printf("FAIL (condition flag)\n");
        fd2_event_system_shutdown(&sys);
        return -1;
    }

    fd2_event_system_shutdown(&sys);
    printf("PASS (flags, triggers, conditions working)\n");
    return 0;
}

static int test_integration(void) {
    printf("[TEST] Integration (Dialog+NPC+Event)... ");

    fd2_dialog_box_t dialog;
    fd2_dialog_init(&dialog);

    fd2_npc_system_t npc_sys;
    fd2_npc_system_init(&npc_sys);

    fd2_event_system_t event_sys;
    fd2_event_system_init(&event_sys);

    /* Simulate opening scene setup */
    u8 test_dialog_data[] = "Welcome to the battlefield!\nYour adventure begins here.\0";
    fd2_dialog_load_from_dat(&dialog, test_dialog_data, sizeof(test_dialog_data));

    fd2_npc_init_from_script(&npc_sys, 99);

    u16 params[] = {0};
    fd2_event_create_trigger(&event_sys, 10, 10, 0, FD2_EVENT_DIALOG_START, params, 1);

    /* Simulate player movement triggering event */
    int triggered = fd2_event_check_triggers(&event_sys, 10, 10);
    if (triggered == 0) {
        printf("FAIL (no trigger)\n");
        fd2_dialog_shutdown(&dialog);
        fd2_npc_system_shutdown(&npc_sys);
        fd2_event_system_shutdown(&event_sys);
        return -1;
    }

    const fd2_event_trigger_t* trig = fd2_event_get_triggered(&event_sys, 0);
    if (!trig || trig->action != FD2_EVENT_DIALOG_START) {
        printf("FAIL (wrong trigger action)\n");
        fd2_dialog_shutdown(&dialog);
        fd2_npc_system_shutdown(&npc_sys);
        fd2_event_system_shutdown(&event_sys);
        return -1;
    }

    /* Start dialog from triggered event */
    fd2_dialog_start(&dialog, 0);
    const fd2_dialog_entry_t* entry = fd2_dialog_get_current(&dialog);
    if (!entry) {
        printf("FAIL (dialog not started)\n");
        fd2_dialog_shutdown(&dialog);
        fd2_npc_system_shutdown(&npc_sys);
        fd2_event_system_shutdown(&event_sys);
        return -1;
    }

    fd2_dialog_shutdown(&dialog);
    fd2_npc_system_shutdown(&npc_sys);
    fd2_event_system_shutdown(&event_sys);

    printf("PASS (all systems integrated)\n");
    return 0;
}

/* ---- Main ---- */

#ifdef _WIN32
#undef main
#endif

int main(int argc, char* argv[]) {
    (void)argc; (void)argv;

    printf("=== FD2 Phase 4: Plot System Test ===\n\n");

    int failures = 0;

    failures += test_dialog_system();
    failures += test_npc_system();
    failures += test_event_system();
    failures += test_integration();

    printf("\n=== Results: %d failures ===\n", failures);
    return failures > 0 ? 1 : 0;
}
