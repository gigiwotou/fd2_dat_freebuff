/**
 * FD2 Battle Info Panel
 * 
 * 基于 IDA Pro MCP 分析:
 * - sub_12D7B: 显示角色信息 (调用 sub_12CEA)
 * - sub_12CEA: 定位并显示角色信息面板
 * - sub_173E7/sub_1741C: 菜单/信息UI渲染
 */

#include "fd2_game.h"
#include "fd2_battle.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <string.h>

/* 信息面板位置 */
#define INFO_PANEL_X    180
#define INFO_PANEL_Y    10
#define INFO_PANEL_W    140
#define INFO_PANEL_H    100

/* 文字颜色 */
#define COLOR_WHITE     63
#define COLOR_YELLOW    62
#define COLOR_GREEN     48
#define COLOR_RED       16
#define COLOR_BLUE      44
#define COLOR_CYAN      47
#define COLOR_GRAY      15
#define COLOR_BLACK     0

/* 字体大小 */
#define FONT_W          8
#define FONT_H          8

/* ========================================================================
 * 简易字体渲染 - 使用 FD2 的字体系统
 * ======================================================================== */
static void draw_char(u8* screen, int screen_w, int screen_h, int x, int y, int c, u8 color) {
    if (x < 0 || y < 0 || x >= screen_w || y >= screen_h) return;
    
    /* 使用简单的 8x8 字体点阵
       这里使用一个简化的实现，只显示 ASCII 字符的基本形状 */
    for (int row = 0; row < FONT_H; row++) {
        for (int col = 0; col < FONT_W; col++) {
            int px = x + col;
            int py = y + row;
            if (px >= 0 && px < screen_w && py >= 0 && py < screen_h) {
                /* 简单的字符点阵，这里用填充代替实际字体 */
                if (c >= 32 && c < 127) {
                    screen[py * screen_w + px] = color;
                }
            }
        }
    }
}

static void draw_string(u8* screen, int screen_w, int screen_h, int x, int y, const char* str, u8 color) {
    if (!str || !screen) return;
    
    int cx = x;
    int cy = y;
    int len = strlen(str);
    
    for (int i = 0; i < len; i++) {
        char c = str[i];
        if (c == '\n') {
            cx = x;
            cy += FONT_H;
        } else if (c == '\t') {
            cx += FONT_W * 4;
        } else {
            draw_char(screen, screen_w, screen_h, cx, cy, c, color);
            cx += FONT_W;
        }
    }
}

static void draw_rect(u8* screen, int screen_w, int screen_h, int x, int y, int w, int h, u8 color) {
    for (int row = 0; row < h; row++) {
        for (int col = 0; col < w; col++) {
            int px = x + col;
            int py = y + row;
            if (px >= 0 && px < screen_w && py >= 0 && py < screen_h) {
                screen[py * screen_w + px] = color;
            }
        }
    }
}

static void draw_rect_border(u8* screen, int screen_w, int screen_h, int x, int y, int w, int h, u8 color) {
    /* Top border */
    for (int i = 0; i < w; i++) {
        int px = x + i;
        if (px >= 0 && px < screen_w && y >= 0 && y < screen_h) {
            screen[y * screen_w + px] = color;
        }
    }
    /* Bottom border */
    for (int i = 0; i < w; i++) {
        int px = x + i;
        int py = y + h - 1;
        if (px >= 0 && px < screen_w && py >= 0 && py < screen_h) {
            screen[py * screen_w + px] = color;
        }
    }
    /* Left border */
    for (int i = 0; i < h; i++) {
        int py = y + i;
        if (x >= 0 && x < screen_w && py >= 0 && py < screen_h) {
            screen[py * screen_w + x] = color;
        }
    }
    /* Right border */
    for (int i = 0; i < h; i++) {
        int py = y + i;
        int px = x + w - 1;
        if (px >= 0 && px < screen_w && py >= 0 && py < screen_h) {
            screen[py * screen_w + px] = color;
        }
    }
}

static void draw_filled_rect_with_border(u8* screen, int screen_w, int screen_h, int x, int y, int w, int h, u8 bg, u8 border) {
    /* Background */
    draw_rect(screen, screen_w, screen_h, x, y, w, h, bg);
    /* Border */
    draw_rect_border(screen, screen_w, screen_h, x, y, w, h, border);
}

/* ========================================================================
 * battle_render_char_info - 渲染角色信息面板
 * 
 * 基于 IDA sub_12D7B -> sub_12CEA 的逻辑
 * 显示选中角色的:
 * - 名称/编号
 * - HP (当前/最大)
 * - MP (当前/最大)
 * - 等级
 * - 职业/类型
 * - 位置
 * ======================================================================== */
void battle_render_char_info(state_battle_data_t* data, fd2_game_t* game, int char_idx) {
    if (!data || !game || char_idx < 0 || char_idx >= data->total_char_count) {
        return;
    }
    
    u8* screen = game->render.screen;
    if (!screen) return;
    
    battle_char_data_t* ch = &data->char_data[char_idx];
    
    /* 绘制背景面板 */
    draw_filled_rect_with_border(screen, FD2_SCREEN_W, FD2_SCREEN_H,
                                 INFO_PANEL_X, INFO_PANEL_Y, INFO_PANEL_W, INFO_PANEL_H,
                                 COLOR_BLACK, COLOR_WHITE);
    
    /* 角色名称 */
    char name_buf[64];
    snprintf(name_buf, sizeof(name_buf), "Char #%d", char_idx);
    draw_string(screen, FD2_SCREEN_W, FD2_SCREEN_H,
                INFO_PANEL_X + 5, INFO_PANEL_Y + 3,
                name_buf, COLOR_YELLOW);
    
    /* 职业/类型 */
    char type_buf[32];
    const char* type_str = "Unknown";
    if (ch->char_type == 0) type_str = "Ally";
    else if (ch->char_type == 1) type_str = "Enemy";
    else if (ch->char_type == 2) type_str = "NPC";
    else if (ch->char_type == 23) type_str = "Special";
    else if (ch->char_type == 30) type_str = "Boss";
    
    snprintf(type_buf, sizeof(type_buf), "Type: %s", type_str);
    draw_string(screen, FD2_SCREEN_W, FD2_SCREEN_H,
                INFO_PANEL_X + 5, INFO_PANEL_Y + 14,
                type_buf, COLOR_CYAN);
    
    /* 等级 */
    char level_buf[32];
    snprintf(level_buf, sizeof(level_buf), "Lv: %d", ch->direction);
    draw_string(screen, FD2_SCREEN_W, FD2_SCREEN_H,
                INFO_PANEL_X + 5, INFO_PANEL_Y + 25,
                level_buf, COLOR_GREEN);
    
    /* HP */
    char hp_buf[32];
    /* 使用 icon_id 作为当前 HP, icon_id_alt 作为最大 HP 的近似值 */
    int current_hp = ch->icon_id;
    int max_hp = ch->icon_id_alt;
    if (max_hp <= 0) max_hp = 100;
    snprintf(hp_buf, sizeof(hp_buf), "HP: %d/%d", current_hp, max_hp);
    draw_string(screen, FD2_SCREEN_W, FD2_SCREEN_H,
                INFO_PANEL_X + 5, INFO_PANEL_Y + 36,
                hp_buf, COLOR_GREEN);
    
    /* MP */
    char mp_buf[32];
    snprintf(mp_buf, sizeof(mp_buf), "MP: %d/%d", 
             ch->portrait_id, ch->portrait_id > 0 ? ch->portrait_id * 2 : 50);
    draw_string(screen, FD2_SCREEN_W, FD2_SCREEN_H,
                INFO_PANEL_X + 5, INFO_PANEL_Y + 47,
                mp_buf, COLOR_BLUE);
    
    /* 位置 */
    char pos_buf[32];
    snprintf(pos_buf, sizeof(pos_buf), "Pos: (%d,%d)", ch->tile_x, ch->tile_y);
    draw_string(screen, FD2_SCREEN_W, FD2_SCREEN_H,
                INFO_PANEL_X + 5, INFO_PANEL_Y + 58,
                pos_buf, COLOR_GRAY);
    
    /* 状态标志 */
    char status_buf[32];
    if (ch->death_flag) {
        snprintf(status_buf, sizeof(status_buf), "Status: DEAD");
        draw_string(screen, FD2_SCREEN_W, FD2_SCREEN_H,
                    INFO_PANEL_X + 5, INFO_PANEL_Y + 69,
                    status_buf, COLOR_RED);
    } else if ((ch->active_byte & 1) != 0) {
        snprintf(status_buf, sizeof(status_buf), "Status: INACTIVE");
        draw_string(screen, FD2_SCREEN_W, FD2_SCREEN_H,
                    INFO_PANEL_X + 5, INFO_PANEL_Y + 69,
                    status_buf, COLOR_GRAY);
    } else {
        snprintf(status_buf, sizeof(status_buf), "Status: ALIVE");
        draw_string(screen, FD2_SCREEN_W, FD2_SCREEN_H,
                    INFO_PANEL_X + 5, INFO_PANEL_Y + 69,
                    status_buf, COLOR_GREEN);
    }
    
    /* 图标ID */
    char icon_buf[32];
    snprintf(icon_buf, sizeof(icon_buf), "Icon: %d", ch->icon_id);
    draw_string(screen, FD2_SCREEN_W, FD2_SCREEN_H,
                INFO_PANEL_X + 5, INFO_PANEL_Y + 80,
                icon_buf, COLOR_GRAY);
}

/* ========================================================================
 * battle_render_info_panel - 如果有选中角色则渲染信息面板
 * ======================================================================== */
void battle_render_info_panel(state_battle_data_t* data, fd2_game_t* game) {
    if (!data || !game) return;
    
    if (data->selected_char_idx >= 0 && data->selected_char_idx < data->total_char_count) {
        battle_render_char_info(data, game, data->selected_char_idx);
    }
}
