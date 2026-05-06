/**
 * Modern Game Framework Implementation
 * Integrates all Phase 1-6 systems into a unified framework.
 */

#define _GNU_SOURCE
#include "fd2/game_framework.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

static void render_title_screen(fd2_game_framework_t* game) {
    /* Clear screen */
    memset(game->screen, 0, FD2_SCREEN_SIZE);

    /* Draw title text area */
    for (int y = 80; y < 120; y++) {
        for (int x = 40; x < 280; x++) {
            if (y == 80 || y == 119 || x == 40 || x == 279) {
                game->screen[y * FD2_SCREEN_W + x] = 60;
            } else {
                game->screen[y * FD2_SCREEN_W + x] = 0;
            }
        }
    }

    /* Title text placeholder */
    for (int i = 0; i < 12; i++) {
        int x = 100 + i * 10;
        int y = 95;
        for (int cy = 0; cy < 8; cy++) {
            for (int cx = 0; cx < 8; cx++) {
                int px = x + cx;
                int py = y + cy;
                if (px >= 0 && px < FD2_SCREEN_W && py >= 0 && py < FD2_SCREEN_H) {
                    game->screen[py * FD2_SCREEN_W + px] = 255;
                }
            }
        }
    }

    /* Blink "Press Start" */
    if (game->frame_count % 60 < 40) {
        for (int i = 0; i < 10; i++) {
            int x = 110 + i * 10;
            int y = 105;
            for (int cy = 0; cy < 7; cy++) {
                int px = x;
                int py = y + cy;
                if (px >= 0 && px < FD2_SCREEN_W && py >= 0 && py < FD2_SCREEN_H) {
                    game->screen[py * FD2_SCREEN_W + px] = 200;
                }
            }
        }
    }
}

static void render_battle_screen(fd2_game_framework_t* game) {
    /* Clear screen */
    memset(game->screen, 0, FD2_SCREEN_SIZE);

    /* Draw terrain grid */
    for (int y = 0; y < FD2_SCREEN_H; y += 16) {
        for (int x = 0; x < FD2_SCREEN_W; x++) {
            if (x < FD2_SCREEN_W && y < FD2_SCREEN_H) {
                game->screen[y * FD2_SCREEN_W + x] = 30;
            }
        }
    }
    for (int x = 0; x < FD2_SCREEN_W; x += 16) {
        for (int y = 0; y < FD2_SCREEN_H; y++) {
            if (y < FD2_SCREEN_H) {
                game->screen[y * FD2_SCREEN_W + x] = 30;
            }
        }
    }

    /* Draw battle units */
    for (int i = 0; i < game->battle.unit_count; i++) {
        const fd2_battle_unit_t* unit = &game->battle.units[i];
        if (!unit->alive) continue;

        int sx = unit->map_x * 16;
        int sy = unit->map_y * 16;

        if (sx >= 0 && sx < FD2_SCREEN_W - 16 && sy >= 0 && sy < FD2_SCREEN_H - 24) {
            u8 color = (unit->team == 0) ? 100 : 200;

            for (int dy = 0; dy < 16; dy++) {
                for (int dx = 0; dx < 16; dx++) {
                    int px = sx + dx;
                    int py = sy + dy;
                    if (px < FD2_SCREEN_W && py < FD2_SCREEN_H) {
                        game->screen[py * FD2_SCREEN_W + px] = color;
                    }
                }
            }
        }
    }

    /* Draw action menu if player turn */
    if (game->battle.player_phase && game->battle.phase == FD2_BATTLE_PHASE_PLAYER_TURN) {
        for (int y = 160; y < 195; y++) {
            for (int x = 10; x < 150; x++) {
                game->screen[y * FD2_SCREEN_W + x] = (y == 160 || y == 194 || x == 10 || x == 149) ? 60 : 0;
            }
        }

        /* Menu cursor */
        const char* actions[] = {"ATK", "MAG", "ITM", "DEF", "RUN"};
        for (int i = 0; i < 5; i++) {
            if (game->battle.menu_cursor == i) {
                int x = 20;
                int y = 165 + i * 6;
                game->screen[y * FD2_SCREEN_W + x] = 255;
            }
        }
    }
}

int fd2_game_framework_init(fd2_game_framework_t* game,
                            const char* data_dir,
                            const char* mods_dir) {
    if (!game) return -1;

    memset(game, 0, sizeof(*game));

    /* Initialize core systems */
    fd2_entity_mgr_init(&game->entity_mgr);
    fd2_event_bus_init(&game->event_bus);
    fd2_dialog_init(&game->dialog);
    fd2_npc_system_init(&game->npc_system);
    fd2_event_system_init(&game->event_system);
    fd2_battle_init(&game->battle);
    fd2_mod_mgr_init(&game->mod_mgr, mods_dir ? mods_dir : "mods");

    /* Set game state */
    game->state = FD2_GS_INIT;
    game->running = true;
    game->frame_count = 0;
    game->tick_count = 0;

    /* Store paths */
    if (data_dir) {
        snprintf(game->data_dir, sizeof(game->data_dir), "%s", data_dir);
    }
    if (mods_dir) {
        snprintf(game->mods_dir, sizeof(game->mods_dir), "%s", mods_dir);
    }

    /* Set MOD API references */
    fd2_mod_set_entity_mgr(&game->entity_mgr);
    fd2_mod_set_event_bus(&game->event_bus);

    /* Initialize palette (default) */
    memset(game->palette, 0, FD2_PALETTE_BYTES);

    printf("[FRAMEWORK] Initialized successfully\n");
    return 0;
}

void fd2_game_framework_shutdown(fd2_game_framework_t* game) {
    if (!game) return;

    fd2_battle_shutdown(&game->battle);
    fd2_mod_mgr_shutdown(&game->mod_mgr);
    fd2_event_system_shutdown(&game->event_system);
    fd2_npc_system_shutdown(&game->npc_system);
    fd2_dialog_shutdown(&game->dialog);
    fd2_event_bus_shutdown(&game->event_bus);
    fd2_entity_mgr_init(&game->entity_mgr);  /* Reset entities */

    memset(game, 0, sizeof(*game));
    printf("[FRAMEWORK] Shutdown complete\n");
}

void fd2_game_framework_update(fd2_game_framework_t* game,
                               const fd2_input_iface_t* input,
                               fd2_input_t* input_state,
                               const fd2_video_iface_t* video,
                               fd2_video_t* video_state,
                               const fd2_audio_iface_t* audio,
                               fd2_audio_t* audio_state) {
    if (!game || !game->running) return;

    (void)video; (void)video_state;
    (void)audio; (void)audio_state;

    game->frame_count++;

    /* Process input */
    if (input && input_state) {
        input->begin_frame(input_state);
    }

    /* State-specific update */
    switch (game->state) {
        case FD2_GS_INIT:
            /* Transition to title */
            fd2_game_framework_set_state(game, FD2_GS_TITLE);
            break;

        case FD2_GS_TITLE:
            if (input && input_state && input->is_action_pressed(input_state, FD2_ACTION_START)) {
                fd2_game_framework_set_state(game, FD2_GS_MENU);
            }
            break;

        case FD2_GS_MENU:
            if (input && input_state) {
                if (input->is_action_pressed(input_state, FD2_ACTION_UP)) {
                    /* Menu up */
                }
                if (input->is_action_pressed(input_state, FD2_ACTION_DOWN)) {
                    /* Menu down */
                }
                if (input->is_action_pressed(input_state, FD2_ACTION_START)) {
                    /* Start battle */
                    fd2_game_framework_set_state(game, FD2_GS_BATTLE);

                    /* Initialize a test battle */
                    fd2_battle_add_unit(&game->battle, 5, 5, 0, 1, 10);
                    fd2_battle_add_unit(&game->battle, 15, 15, 1, 1, 8);
                }
                if (input->is_action_pressed(input_state, FD2_ACTION_ESCAPE)) {
                    game->running = false;
                }
            }
            break;

        case FD2_GS_BATTLE:
            if (input && input_state) {
                bool action_pressed = input->is_action_pressed(input_state, FD2_ACTION_A);
                int input_x = 0;
                if (input->is_action_pressed(input_state, FD2_ACTION_LEFT)) input_x = -1;
                if (input->is_action_pressed(input_state, FD2_ACTION_RIGHT)) input_x = 1;

                fd2_battle_update(&game->battle, &game->event_system,
                                 action_pressed, input_x, 0);

                if (input->is_action_pressed(input_state, FD2_ACTION_ESCAPE)) {
                    game->battle.battle_ended = true;
                }
            }

            if (game->battle.battle_ended) {
                fd2_battle_shutdown(&game->battle);
                fd2_battle_init(&game->battle);
                fd2_game_framework_set_state(game, FD2_GS_MENU);
            }
            break;

        case FD2_GS_DIALOG:
            if (input && input_state) {
                bool advance = input->is_action_pressed(input_state, FD2_ACTION_A);
                bool done = fd2_dialog_update(&game->dialog, advance);
                if (done) {
                    fd2_game_framework_set_state(game, game->prev_state);
                }
            }
            break;

        case FD2_GS_GAME_OVER:
            if (input && input_state && input->is_action_pressed(input_state, FD2_ACTION_START)) {
                fd2_game_framework_set_state(game, FD2_GS_MENU);
            }
            break;

        case FD2_GS_QUIT:
            game->running = false;
            break;

        default:
            break;
    }

    /* Process event bus */
    fd2_event_bus_process(&game->event_bus);
    fd2_event_bus_advance_tick(&game->event_bus);

    /* Process MOD updates */
    fd2_mod_mgr_update(&game->mod_mgr);

    /* Clear per-frame input */
    if (input && input_state) {
        input->end_frame(input_state);
    }
}

void fd2_game_framework_render(fd2_game_framework_t* game) {
    if (!game) return;

    switch (game->state) {
        case FD2_GS_TITLE:
            render_title_screen(game);
            break;

        case FD2_GS_MENU:
            render_title_screen(game);  /* Reuse title as menu placeholder */
            break;

        case FD2_GS_BATTLE:
            render_battle_screen(game);
            break;

        case FD2_GS_DIALOG:
            /* Render underlying state */
            fd2_game_framework_render(game);
            /* Render dialog on top */
            fd2_dialog_render(&game->dialog, game->screen, FD2_SCREEN_W, FD2_SCREEN_H);
            break;

        default:
            memset(game->screen, 0, FD2_SCREEN_SIZE);
            break;
    }
}

void fd2_game_framework_set_state(fd2_game_framework_t* game, fd2_game_state_t state) {
    if (!game) return;

    game->prev_state = game->state;
    game->state = state;

    printf("[FRAMEWORK] State changed: %d -> %d\n", game->prev_state, state);
}

fd2_game_state_t fd2_game_framework_get_state(const fd2_game_framework_t* game) {
    return game ? game->state : FD2_GS_INIT;
}
