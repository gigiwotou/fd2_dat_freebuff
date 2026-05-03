/**
 * FD2 Battle Character Selection System
 *
 * Based on IDA sub_12C0D (find character at cursor) and sub_34894 (check char valid).
 * 
 * Original assembly analysis:
 * - sub_12C0D: Loops through character array (80 bytes per char at dword_53A45)
 *   Compares char[0] (x) and char[1] (y) with cursor position (qword_53AB1)
 *   Calls sub_34894 to check if char[5] & 1 == 0 (valid)
 * - sub_34894: Returns (char_data[80 * idx + 5] & 1)
 */

#define _GNU_SOURCE
#include "fd2_game.h"
#include "fd2_battle.h"
#include <stdio.h>

/*
 * Check if character at index is valid.
 * Based on IDA sub_34894: return (char_data[80 * idx + 5] & 1)
 * In our implementation, flag field indicates empty/invalid slot.
 */
int battle_check_char_valid(state_battle_data_t* data, int char_idx) {
    if (char_idx < 0 || char_idx >= data->sprite_count) {
        return 1;
    }

    map_sprite_t* sprite = &data->sprites[char_idx];

    /* Original: byte at offset 5, bit 0 indicates invalid/empty */
    if (!sprite->loaded || sprite->pixels == NULL) {
        return 1;
    }

    return 0;
}

/*
 * Find character at cursor position.
 * Based on IDA sub_12C0D:
 *   for (i = 0; i < char_count; i++) {
 *     if (char[i].x == cursor_x && char[i].y == cursor_y && !sub_34894(i))
 *       return i;
 *   }
 *   return -1;
 */
int battle_find_char_at_cursor(state_battle_data_t* data) {
    for (int i = 0; i < data->sprite_count; i++) {
        map_sprite_t* sprite = &data->sprites[i];

        /* Compare position with cursor */
        if (sprite->tile_x == data->cursor_x && sprite->tile_y == data->cursor_y) {
            /* Check if character is valid (not empty/invalid slot) */
            if (!battle_check_char_valid(data, i)) {
                return i;
            }
        }
    }

    return -1;
}
