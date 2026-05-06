/**
 * FD2 CONTINUE State
 *
 * Load battle save and enter battle state.
 * Based on IDA sub_10010 and sub_25EBB Continue option handling.
 */

#define _GNU_SOURCE
#include "fd2_game.h"
#include "fd2_continue.h"
#include "fd2_save_load.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    battle_save_data_t save_data;
    int load_step;
    int load_failure;
    int num_fighters;
    u8 char_positions[64][2];
    u8 char_icons[64];
} state_continue_data_t;

void state_continue_enter(fd2_game_t* game) {
    state_continue_data_t* data = (state_continue_data_t*)calloc(1, sizeof(state_continue_data_t));
    game->state_data = data;
    data->load_step = 0;
    data->load_failure = 0;

    const char* save_path = fd2_game_data_path(game, "FD2.SAV");
    if (!save_path) {
        fprintf(stderr, "state_continue: cannot get save path\n");
        data->load_failure = 1;
        return;
    }

    if (load_battle_save(save_path, &data->save_data) != 0) {
        fprintf(stderr, "state_continue: failed to load battle save\n");
        data->load_failure = 1;
        return;
    }

    int num_chars = data->save_data.n6_0;
    if (num_chars > 0 && num_chars <= 64) {
        data->num_fighters = num_chars;
        for (int i = 0; i < num_chars; i++) {
            u8* char_data = data->save_data.char_data + i * BATTLE_SAVE_CHAR_DATA_SIZE;
            data->char_positions[i][0] = char_data[0];
            data->char_positions[i][1] = char_data[1];
            data->char_icons[i] = char_data[7];
            /* Copy full 80-byte char data for battle state */
            memcpy(game->save_char_full_data[i], char_data, BATTLE_SAVE_CHAR_DATA_SIZE);
            fprintf(stderr, "  char[%d]: x=%d, y=%d, icon_id=%d, death_flag=%d, active_mask=0x%02X\n",
                   i, char_data[0], char_data[1], char_data[7], char_data[39], char_data[26]);
        }
    } else {
        data->num_fighters = 0;
    }

    game->map_index = data->save_data.n17;
    game->num_fighters = data->save_data.n6_0;
    game->current_fighter = 0;
    game->game_mode = data->save_data.n17;

    game->from_save = 1;
    game->save_char_count = data->num_fighters;
    memcpy(game->save_char_positions, data->char_positions, sizeof(game->save_char_positions));
    memcpy(game->save_char_icons, data->char_icons, sizeof(game->save_char_icons));

    printf("state_continue: save loaded, entering battle (map=%d, chars=%d)\n",
           data->save_data.n17, data->save_data.n6_0);
}

fd2_state_t state_continue_update(fd2_game_t* game) {
    state_continue_data_t* data = (state_continue_data_t*)game->state_data;
    if (!data) return FD2_STATE_MENU;

    if (data->load_failure) {
        fd2_render_fill_screen(&game->render, 0);
        fd2_render_present(&game->render);
        return FD2_STATE_MENU;
    }

    return FD2_STATE_BATTLE;
}

void state_continue_exit(fd2_game_t* game) {
    state_continue_data_t* data = (state_continue_data_t*)game->state_data;
    if (data) {
        free(data);
    }
    game->state_data = NULL;
}
