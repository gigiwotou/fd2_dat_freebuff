/**
 * FD2 MENU State
 *
 * Main menu. Based on sub_1FF79 (draws menu items) and the input loop
 * in sub_1F894 (up/down/select with blink animation).
 */

#define _GNU_SOURCE
#include "fd2_game.h"
#include "fd2_menu.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

typedef struct {
    int  menu_selection;
    int  num_items;
    int  blink_timer;
    int  blink_count;
    bool selected;
    bool blink_visible;
} state_menu_data_t;

static void menu_draw(fd2_game_t* game, int selection, int num_items) {
    static const int item_x = 129;
    static const int item_y[3] = { 164, 173, 182 };

    u32 dat_size;
    const u8* dat = fd2_resources_get(&game->resources, FD2_DAT_FDOTHER, 6, &dat_size);
    if (!dat || dat_size < 14) {
        printf("menu_draw: FDOTHER #6 not available (%u bytes)\n", dat_size);
        return;
    }

    if (dat[0] != 'L' || dat[1] != 'L' || dat[2] != 'L' ||
        dat[3] != 'L' || dat[4] != 'L' || dat[5] != 'L') {
        printf("menu_draw: FDOTHER #6 invalid magic header\n");
        return;
    }

    u32 sub_count = dat[6] | (dat[7] << 8) | (dat[8] << 16) | (dat[9] << 24);
    const u8* offset_table = dat + 6;

    if (sub_count < 7) {
        printf("menu_draw: FDOTHER #6 has only %u sub-resources (need 7)\n", sub_count);
        return;
    }

    int i;

    {
        int sub_idx = 0;
        const u8* off_ptr = offset_table + sub_idx * 4;
        u32 offset = off_ptr[0] | (off_ptr[1] << 8) | (off_ptr[2] << 16) | (off_ptr[3] << 24);
        if (offset >= dat_size) {
            printf("menu_draw: bg sub_idx=0 offset out of range (%u >= %u)\n", offset, dat_size);
            return;
        }
        const u8* sub_data = dat + offset;

        int w = sub_data[0] | (sub_data[1] << 8);
        int h = sub_data[2] | (sub_data[3] << 8);
        if (w > 0 && h > 0 && w <= 320 && h <= 200) {
            u32 rle_size;
            if (sub_idx + 1 <= sub_count) {
                const u8* next_off = offset_table + (sub_idx + 1) * 4;
                u32 next_offset = next_off[0] | (next_off[1] << 8) | (next_off[2] << 16) | (next_off[3] << 24);
                rle_size = next_offset - offset - 4;
            } else {
                rle_size = dat_size - offset - 4;
            }

            const u8* rle_data = sub_data + 4;
            u8* pixels = (u8*)calloc(w * h, sizeof(u8));
            if (fd2_rle_decompress(rle_data, rle_size, pixels, w, h) == 0) {
                fd2_render_blit(&game->render, pixels, w, h, 0, 0);
            }
            free(pixels);
        }
    }

    for (i = 0; i < num_items && i < 3; i++) {
        int sub_idx;
        if (i == 0) {
            sub_idx = (selection == 0) ? 2 : 1;
        } else if (i == 1) {
            sub_idx = (selection == 1) ? 4 : 3;
        } else {
            sub_idx = (selection == 2) ? 6 : 5;
        }
        int dx = item_x;
        int dy = item_y[i];

        if (sub_idx > sub_count) continue;

        const u8* off_ptr = offset_table + sub_idx * 4;
        u32 offset = off_ptr[0] | (off_ptr[1] << 8) | (off_ptr[2] << 16) | (off_ptr[3] << 24);
        if (offset >= dat_size) {
            printf("menu_draw: sub[%d] offset out of range (%u >= %u)\n", sub_idx, offset, dat_size);
            continue;
        }
        const u8* sub_data = dat + offset;

        int w = sub_data[0] | (sub_data[1] << 8);
        int h = sub_data[2] | (sub_data[3] << 8);
        if (w <= 0 || h <= 0 || w > 320 || h > 200) {
            printf("menu_draw: sub[%d] invalid size %dx%d\n", sub_idx, w, h);
            continue;
        }

        u32 rle_size;
        if (sub_idx + 1 <= sub_count) {
            const u8* next_off = offset_table + (sub_idx + 1) * 4;
            u32 next_offset = next_off[0] | (next_off[1] << 8) | (next_off[2] << 16) | (next_off[3] << 24);
            rle_size = next_offset - offset - 4;
        } else {
            rle_size = dat_size - offset - 4;
        }

        const u8* rle_data = sub_data + 4;

        u8* pixels = (u8*)calloc(w * h, sizeof(u8));
        if (fd2_rle_decompress(rle_data, rle_size, pixels, w, h) == 0) {
            fd2_render_blit(&game->render, pixels, w, h, dx, dy);
        }
        free(pixels);
    }

    fd2_render_present(&game->render);
}

void state_menu_enter(fd2_game_t* game) {
    state_menu_data_t* data = (state_menu_data_t*)calloc(1, sizeof(state_menu_data_t));
    game->state_data = data;
    data->menu_selection = 0;
    data->num_items = 3;
    data->blink_timer = 0;
    data->blink_count = 0;
    data->selected = false;
    data->blink_visible = true;

    u32 pal_size;
    const u8* pal_res = fd2_resources_get(&game->resources, FD2_DAT_FDOTHER, 7, &pal_size);
    if (pal_res && pal_size == FD2_PALETTE_BYTES) {
        fd2_render_set_palette_6bit(&game->render, pal_res);
    }
    fd2_render_set_brightness(&game->render, 56);

    menu_draw(game, 0, data->num_items);

    printf("state_menu: entered (intro music continues playing)\n");
}

fd2_state_t state_menu_update(fd2_game_t* game) {
    state_menu_data_t* data = (state_menu_data_t*)game->state_data;
    if (!data) return FD2_STATE_QUIT;

    if (fd2_action_pressed(&game->input, FD2_ACTION_ESCAPE)) {
        return FD2_STATE_INTRO;
    }

    if (data->selected) {
        data->blink_timer++;

        if (data->blink_timer >= 5) {
            data->blink_timer = 0;
            data->blink_visible = !data->blink_visible;
            data->blink_count++;

            menu_draw(game, data->blink_visible ? data->menu_selection : -1,
                      data->num_items);
        }

        if (data->blink_count >= 8) {
            switch (data->menu_selection) {
                case 0:
                    game->game_mode = 0;
                    game->map_index = 32;
                    printf("[MENU] Starting 1P story mode - Map 32\n");
                    return FD2_STATE_BATTLE;
                case 1:
                    game->game_mode = 1;
                    game->map_index = 0;
                    return FD2_STATE_BATTLE;
                case 2:
                    printf("[MENU] Continue - loading battle save\n");
                    return FD2_STATE_CONTINUE;
                default:
                    game->game_mode = 0;
                    game->map_index = 0;
                    return FD2_STATE_BATTLE;
            }
        }

        return FD2_STATE_MENU;
    }

    if (fd2_action_pressed(&game->input, FD2_ACTION_UP)) {
        data->menu_selection = (data->menu_selection - 1 + data->num_items) % data->num_items;
        menu_draw(game, data->menu_selection, data->num_items);
    }
    if (fd2_action_pressed(&game->input, FD2_ACTION_DOWN)) {
        data->menu_selection = (data->menu_selection + 1) % data->num_items;
        menu_draw(game, data->menu_selection, data->num_items);
    }

    if (fd2_action_pressed(&game->input, FD2_ACTION_START) ||
        fd2_action_pressed(&game->input, FD2_ACTION_A)) {
        data->selected = true;
        data->blink_timer = 0;
        data->blink_count = 0;
        data->blink_visible = true;
    }

    return FD2_STATE_MENU;
}

void state_menu_exit(fd2_game_t* game) {
    free(game->state_data);
    game->state_data = NULL;
}
