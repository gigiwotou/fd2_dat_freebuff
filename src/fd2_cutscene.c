/**
 * FD2 CUTSCENE State
 *
 * Cutscene playback (sub_1366A + sub_15F84).
 * Plays a sequence of scenes that tell the story.
 */

#define _GNU_SOURCE
#include "fd2_game.h"
#include "fd2_cutscene.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void state_cutscene_enter(fd2_game_t* game) {
    scene_player_t* player = &game->scene_player;
    scene_player_init(player);
    
    game->cutscene_index = 0;
    
    if (game->cutscene_count > 0) {
        int first_scene = game->cutscene_sequence[0];
        scene_player_play(player, first_scene);
        printf("state_cutscene: entered, playing scene %d (map=%d)\n", 
               first_scene, game->map_index);
    } else {
        printf("state_cutscene: entered, no scenes to play\n");
    }
}

fd2_state_t state_cutscene_update(fd2_game_t* game) {
    scene_player_t* player = &game->scene_player;
    
    if (fd2_action_pressed(&game->input, FD2_ACTION_START) ||
        fd2_action_pressed(&game->input, FD2_ACTION_A) ||
        fd2_action_pressed(&game->input, FD2_ACTION_ESCAPE)) {
        scene_player_skip(player);
    }
    
    bool scene_done = scene_player_update(player, 16);
    
    scene_player_render(player, game->render.screen, FD2_SCREEN_W, FD2_SCREEN_H);
    fd2_render_present(&game->render);
    
    if (scene_done) {
        game->cutscene_index++;
        if (game->cutscene_index < game->cutscene_count) {
            int next_scene = game->cutscene_sequence[game->cutscene_index];
            printf("state_cutscene: playing next scene %d\n", next_scene);
            scene_player_play(player, next_scene);
        } else {
            printf("state_cutscene: all scenes done, transitioning to battle (map=%d)\n",
                   game->map_index);
            return FD2_STATE_BATTLE;
        }
    }
    
    return FD2_STATE_CUTSCENE;
}

void state_cutscene_exit(fd2_game_t* game) {
    scene_player_shutdown(&game->scene_player);
    printf("state_cutscene: exited\n");
}
