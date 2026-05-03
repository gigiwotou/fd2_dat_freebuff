/**
 * FD2 Battle Menu System
 *
 * Implements the battle command menu (Attack, Item, Defend, etc.)
 * Based on IDA sub_117E7 input processing and menu state machine logic.
 */

#define _GNU_SOURCE
#include "fd2_game.h"
#include "fd2_battle.h"
#include <stdio.h>
#include <string.h>

#define MENU_BOX_X 8
#define MENU_BOX_Y 8
#define MENU_BOX_WIDTH 120
#define MENU_BOX_HEIGHT 120
#define MENU_ITEM_HEIGHT 20
#define MENU_ITEM_WIDTH 100
#define MENU_ITEM_X (MENU_BOX_X + 10)
#define MENU_ITEM_Y_START (MENU_BOX_Y + 10)

#define TEXT_BOX_X 8
#define TEXT_BOX_Y (FD2_SCREEN_H - 80)
#define TEXT_BOX_WIDTH 300
#define TEXT_BOX_HEIGHT 64

void battle_init_main_menu(state_battle_data_t* data, int char_idx) {
    (void)char_idx;
    data->menu_item_count = 0;
    data->menu_selected_idx = 0;

    strcpy(data->menu_items[0].text, "攻击");
    data->menu_items[0].action_id = 1;
    data->menu_item_count++;

    strcpy(data->menu_items[1].text, "道具");
    data->menu_items[1].action_id = 2;
    data->menu_item_count++;

    strcpy(data->menu_items[2].text, "防御");
    data->menu_items[2].action_id = 3;
    data->menu_item_count++;

    strcpy(data->menu_items[3].text, "待机");
    data->menu_items[3].action_id = 4;
    data->menu_item_count++;

    printf("menu initialized: %d items\n", data->menu_item_count);
}

void battle_menu_move_up(state_battle_data_t* data) {
    if (data->menu_selected_idx > 0) {
        data->menu_selected_idx--;
    }
}

void battle_menu_move_down(state_battle_data_t* data) {
    if (data->menu_selected_idx < data->menu_item_count - 1) {
        data->menu_selected_idx++;
    }
}

static void draw_filled_box(u8* screen, int screen_w, int screen_h,
                            int x, int y, int width, int height, u8 color) {
    for (int row = 0; row < height; row++) {
        int py = y + row;
        if (py < 0 || py >= screen_h) continue;

        for (int col = 0; col < width; col++) {
            int px = x + col;
            if (px < 0 || px >= screen_w) continue;

            screen[py * screen_w + px] = color;
        }
    }
}

static void draw_box_border(u8* screen, int screen_w, int screen_h,
                            int x, int y, int width, int height, u8 color) {
    for (int col = 0; col < width; col++) {
        int px = x + col;
        if (px >= 0 && px < screen_w) {
            if (y >= 0 && y < screen_h) {
                screen[y * screen_w + px] = color;
            }
            int bottom_y = y + height - 1;
            if (bottom_y >= 0 && bottom_y < screen_h) {
                screen[bottom_y * screen_w + px] = color;
            }
        }
    }

    for (int row = 0; row < height; row++) {
        int py = y + row;
        if (py >= 0 && py < screen_h) {
            if (x >= 0 && x < screen_w) {
                screen[py * screen_w + x] = color;
            }
            int right_x = x + width - 1;
            if (right_x >= 0 && right_x < screen_w) {
                screen[py * screen_w + right_x] = color;
            }
        }
    }
}

void battle_render_menu(state_battle_data_t* data, u8* screen, int screen_w, int screen_h) {
    int box_x = MENU_BOX_X;
    int box_y = MENU_BOX_Y;
    int box_width = MENU_BOX_WIDTH;
    int box_height = MENU_ITEM_Y_START + data->menu_item_count * MENU_ITEM_HEIGHT + 10;

    if (box_height > MENU_BOX_HEIGHT) {
        box_height = MENU_BOX_HEIGHT;
    }

    draw_filled_box(screen, screen_w, screen_h, box_x + 1, box_y + 1,
                    box_width - 2, box_height - 2, 30);

    draw_box_border(screen, screen_w, screen_h, box_x, box_y,
                    box_width, box_height, 63);

    for (int i = 0; i < data->menu_item_count; i++) {
        int item_y = MENU_ITEM_Y_START + i * MENU_ITEM_HEIGHT;

        if (i == data->menu_selected_idx) {
            draw_filled_box(screen, screen_w, screen_h,
                            box_x + 2, item_y,
                            box_width - 4, MENU_ITEM_HEIGHT - 2,
                            20);
        }

        int text_x = MENU_ITEM_X;
        int text_y = item_y + 8;

        if (text_y >= 0 && text_y < screen_h) {
            const char* text = data->menu_items[i].text;
            for (int j = 0; text[j] != '\0' && (text_x + j * 8) < screen_w; j++) {
                u8 color = (i == data->menu_selected_idx) ? 63 : 45;
                screen[text_y * screen_w + text_x + j * 8] = color;
            }
        }
    }
}

void battle_render_text_box(state_battle_data_t* data, u8* screen, int screen_w, int screen_h) {
    int box_x = TEXT_BOX_X;
    int box_y = TEXT_BOX_Y;
    int box_width = TEXT_BOX_WIDTH;
    int box_height = TEXT_BOX_HEIGHT;

    if (box_x + box_width > screen_w) {
        box_width = screen_w - box_x;
    }
    if (box_y + box_height > screen_h) {
        box_height = screen_h - box_y;
    }

    draw_filled_box(screen, screen_w, screen_h, box_x + 1, box_y + 1,
                    box_width - 2, box_height - 2, 30);

    draw_box_border(screen, screen_w, screen_h, box_x, box_y,
                    box_width, box_height, 63);

    if (data->selected_char_idx >= 0 && data->selected_char_idx < data->sprite_count) {
        map_sprite_t* sprite = &data->sprites[data->selected_char_idx];
        int text_x = box_x + 8;
        int text_y = box_y + 10;

        char info[64];
        snprintf(info, sizeof(info), "角色 ID: %d 位置: (%d,%d)",
                 sprite->icon_id, sprite->tile_x, sprite->tile_y);

        for (int i = 0; info[i] != '\0' && (text_x + i * 6) < screen_w; i++) {
            if (text_y >= 0 && text_y < screen_h) {
                screen[text_y * screen_w + text_x + i * 6] = 63;
            }
        }
    }
}
