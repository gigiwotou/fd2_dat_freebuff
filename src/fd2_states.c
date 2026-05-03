/**
 * FD2 Simple States
 *
 * INIT, DEMO, CHAR_SELECT, VICTORY, GAME_OVER states.
 * These are placeholder/simple states.
 */

#define _GNU_SOURCE
#include "fd2_game.h"
#include "fd2_states.h"
#include "fd2_map_loader.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int load_step;
    int load_failures;
} state_init_data_t;

void state_init_enter(fd2_game_t* game) {
    state_init_data_t* data = (state_init_data_t*)calloc(1, sizeof(state_init_data_t));
    game->state_data = data;
    data->load_step = 0;

    fd2_render_fill_screen(&game->render, 0);
    fd2_render_present(&game->render);
    printf("state_init: loading resources...\n");
}

fd2_state_t state_init_update(fd2_game_t* game) {
    state_init_data_t* data = (state_init_data_t*)game->state_data;
    if (!data) return FD2_STATE_QUIT;

    if (data->load_step == 0) {
        if (fd2_resources_load_dat(&game->resources, FD2_DAT_FDOTHER) != 0) {
            fprintf(stderr, "state_init: FATAL: cannot load FDOTHER.DAT\n");
            return FD2_STATE_QUIT;
        }

        fd2_resources_load_dat(&game->resources, FD2_DAT_FDTXT);
        fd2_resources_load_dat(&game->resources, FD2_DAT_BG);
        fd2_resources_load_dat(&game->resources, FD2_DAT_FIGANI);
        fd2_resources_load_dat(&game->resources, FD2_DAT_TAI);
        fd2_resources_load_dat(&game->resources, FD2_DAT_ANI);

        data->load_step = 1;
    }

    printf("state_init: resources loaded, starting intro\n");
    return FD2_STATE_INTRO;
}

void state_init_exit(fd2_game_t* game) {
    free(game->state_data);
    game->state_data = NULL;
}

void state_demo_enter(fd2_game_t* game) {
    (void)game;
    printf("state_demo: entered (placeholder)\n");
}

fd2_state_t state_demo_update(fd2_game_t* game) {
    if (fd2_action_pressed(&game->input, FD2_ACTION_ESCAPE) ||
        fd2_input_any_pressed(&game->input)) {
        return FD2_STATE_MENU;
    }
    return FD2_STATE_DEMO;
}

void state_demo_exit(fd2_game_t* game) {
    (void)game;
}

void state_char_select_enter(fd2_game_t* game) {
    game->state_data = NULL;

    fd2_resources_load_dat(&game->resources, FD2_DAT_FDSHAP);
    fd2_resources_load_dat(&game->resources, FD2_DAT_TAI);

    fd2_render_fill_screen(&game->render, 0);
    fd2_render_present(&game->render);

    printf("state_char_select: entered (placeholder)\n");
}

fd2_state_t state_char_select_update(fd2_game_t* game) {
    if (fd2_action_pressed(&game->input, FD2_ACTION_ESCAPE)) {
        return FD2_STATE_MENU;
    }
    if (fd2_action_pressed(&game->input, FD2_ACTION_START)) {
        return FD2_STATE_BATTLE;
    }
    return FD2_STATE_CHAR_SELECT;
}

void state_char_select_exit(fd2_game_t* game) {
    (void)game;
}

void state_victory_enter(fd2_game_t* game) { (void)game; }
fd2_state_t state_victory_update(fd2_game_t* game) {
    (void)game;
    return FD2_STATE_MENU;
}
void state_victory_exit(fd2_game_t* game) { (void)game; }

void state_game_over_enter(fd2_game_t* game) { (void)game; }
fd2_state_t state_game_over_update(fd2_game_t* game) {
    (void)game;
    return FD2_STATE_MENU;
}
void state_game_over_exit(fd2_game_t* game) { (void)game; }
