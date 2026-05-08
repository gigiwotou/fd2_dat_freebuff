/**
 * FD2 Battle Info Panel - 原游戏UI实现
 * 
 * 基于 IDA Pro MCP 逆向分析:
 * 
 * 函数调用链:
 * sub_12D7B -> sub_12CEA -> sub_11CAC -> sub_11EEE -> sub_4E22A/sub_4E016
 * 
 * sub_11CAC(a1, a2, a3, a4, a5):
 *   - sub_3702F(a1, a2, a3, a4, 32) 准备数据
 *   - sub_1297D(v5) 处理数据
 *   - if(!a5) sub_4E31C()
 *   - sub_11EEE(dword_53A49+32904, 456, 13, 8, n9, n34) 渲染文字
 *   - v6 = sub_122DC()
 *   - sub_127A9(v6) 渲染信息
 *   - sub_1ACF3(dword_53A49+32904, 456) 绘制边框
 *   - return sub_11EB0(656644, 320, dword_53A49+32904, 456, 312, 192)
 * 
 * sub_11EEE - 文字渲染:
 *   - 从 FDOTHER.DAT 加载16x16字体
 *   - 从 dword_53A6D 获取字符数据表
 *   - 每个字符宽16像素
 *   - 调用 sub_4E22A 或 sub_4E016 blit字符
 * 
 * sub_11EB0 - 帧缓冲拷贝:
 *   - dst: 0xA0504 (VGA屏幕)
 *   - dst_pitch: 320
 *   - src: dword_53A49+32904
 *   - src_pitch: 456
 *   - w: 312, h: 192
 */

#include "fd2_game.h"
#include "fd2_battle.h"
#include "fd2_decoder.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* ========================================================================
 * 原游戏信息面板常量
 * ======================================================================== */

/* 内部渲染缓冲区 (模拟 dword_53A49 + 32904) */
#define PANEL_BUF_PITCH    456
#define PANEL_W            312
#define PANEL_H            192

/* 字体尺寸 (FDOTHER.DAT 16x16) */
#define FONT_W             16
#define FONT_H             16
#define FONT_LINE_H        18

/* 屏幕映射位置 (312x192 面板映射到 320x200 屏幕) */
#define PANEL_SCREEN_X     4
#define PANEL_SCREEN_Y     4

/* 颜色定义 (游戏调色板索引) */
#define COLOR_BLACK        0
#define COLOR_WHITE        63
#define COLOR_YELLOW       62
#define COLOR_GREEN        48
#define COLOR_RED          16
#define COLOR_BLUE         44
#define COLOR_CYAN         47
#define COLOR_GRAY         15
#define COLOR_ORANGE       200

/* ========================================================================
 * FDOTHER.DAT 16x16字体缓存
 * ======================================================================== */

#define FONT_CHAR_COUNT    128
static u8* font_cache[FONT_CHAR_COUNT];
static int font_initialized = 0;

/* ========================================================================
 * 从FDOTHER.DAT加载16x16字体
 * ======================================================================== */
static int load_font_from_fdother(fd2_game_t* game) {
    if (font_initialized) return 0;
    
    memset(font_cache, 0, sizeof(font_cache));
    
    if (!fd2_resources_is_loaded(&game->resources, FD2_DAT_FDOTHER)) return -1;
    
    /* 尝试加载字体资源 (根据IDA分析，FDOTHER.DAT包含16x16字体) */
    u32 res_size;
    const u8* res_data = fd2_resources_get(&game->resources, FD2_DAT_FDOTHER, 0, &res_size);
    if (!res_data || res_size < 4) return -1;
    
    int w, h;
    if (fd2_image_get_dimensions(res_data, res_size, &w, &h) != 0) return -1;
    
    /* 如果资源是字体表，需要按16x16分割 */
    if (w == 16 && h >= 16) {
        int char_count = h / 16;
        u8* pixels = NULL;
        
        if (fd2_rle_decompress_from_resource(res_data, res_size, &pixels, &w, &h) == 0) {
            for (int i = 0; i < char_count && i < FONT_CHAR_COUNT; i++) {
                u8* glyph = (u8*)malloc(FONT_W * FONT_H);
                if (glyph) {
                    for (int row = 0; row < FONT_H; row++) {
                        memcpy(glyph + row * FONT_W, 
                               pixels + (i * FONT_H + row) * w, 
                               FONT_W);
                    }
                    font_cache[i] = glyph;
                }
            }
            free(pixels);
        }
    }
    
    font_initialized = 1;
    return 0;
}

/* ========================================================================
 * 绘制16x16字符到缓冲区
 * ======================================================================== */
static void draw_char_to_buf(u8* buf, int buf_pitch, int x, int y, 
                              int char_idx, u8 color) {
    if (char_idx < 0 || char_idx >= FONT_CHAR_COUNT) return;
    if (!font_cache[char_idx]) return;
    if (x < 0 || y < 0 || x + FONT_W > PANEL_W || y + FONT_H > PANEL_H) return;
    
    u8* glyph = font_cache[char_idx];
    
    for (int row = 0; row < FONT_H; row++) {
        for (int col = 0; col < FONT_W; col++) {
            u8 px = glyph[row * FONT_W + col];
            if (px != 0) {
                buf[(y + row) * buf_pitch + (x + col)] = color;
            }
        }
    }
}

/* ========================================================================
 * 绘制字符串到缓冲区
 * ======================================================================== */
static void draw_string_to_buf(u8* buf, int buf_pitch, int x, int y,
                                const char* str, u8 color) {
    if (!str) return;
    
    int cx = x;
    int len = strlen(str);
    
    for (int i = 0; i < len; i++) {
        char c = str[i];
        if (c == ' ') {
            cx += FONT_W;
        } else if (c >= 32 && c < 32 + FONT_CHAR_COUNT) {
            draw_char_to_buf(buf, buf_pitch, cx, y, c - 32, color);
            cx += FONT_W;
        }
    }
}

/* ========================================================================
 * 绘制数字到缓冲区
 * ======================================================================== */
static void draw_number_to_buf(u8* buf, int buf_pitch, int x, int y,
                                int num, u8 color) {
    char buf_str[16];
    snprintf(buf_str, sizeof(buf_str), "%d", num);
    draw_string_to_buf(buf, buf_pitch, x, y, buf_str, color);
}

/* ========================================================================
 * 填充矩形背景
 * ======================================================================== */
static void fill_rect(u8* buf, int buf_pitch, int x, int y, int w, int h, u8 color) {
    for (int row = 0; row < h; row++) {
        for (int col = 0; col < w; col++) {
            int bx = x + col;
            int by = y + row;
            if (bx >= 0 && bx < PANEL_W && by >= 0 && by < PANEL_H) {
                buf[by * buf_pitch + bx] = color;
            }
        }
    }
}

/* ========================================================================
 * 绘制边框
 * ======================================================================== */
static void draw_border(u8* buf, int buf_pitch, int x, int y, int w, int h, u8 color) {
    /* 上边 */
    for (int col = 0; col < w; col++) {
        buf[y * buf_pitch + (x + col)] = color;
    }
    /* 下边 */
    for (int col = 0; col < w; col++) {
        buf[(y + h - 1) * buf_pitch + (x + col)] = color;
    }
    /* 左边 */
    for (int row = 0; row < h; row++) {
        buf[(y + row) * buf_pitch + x] = color;
    }
    /* 右边 */
    for (int row = 0; row < h; row++) {
        buf[(y + row) * buf_pitch + (x + w - 1)] = color;
    }
}

/* ========================================================================
 * sub_11EB0风格: 帧缓冲拷贝
 * 
 * 对应IDA sub_11EB0:
 * sub_11EB0(656644, 320, dword_53A49+32904, 456, 312, 192)
 * ======================================================================== */
static void fb_copy_11eb0(u8* dst_screen, int dst_pitch,
                           const u8* src_buffer, int src_pitch,
                           int w, int h, int dst_x, int dst_y) {
    if (!dst_screen || !src_buffer) return;
    
    for (int row = 0; row < h; row++) {
        int sy = dst_y + row;
        if (sy < 0 || sy >= FD2_SCREEN_H) continue;
        
        for (int col = 0; col < w; col++) {
            int sx = dst_x + col;
            if (sx < 0 || sx >= FD2_SCREEN_W) continue;
            
            u8 px = src_buffer[row * src_pitch + col];
            if (px != 0) {
                dst_screen[sy * FD2_SCREEN_W + sx] = px;
            }
        }
    }
}

/* ========================================================================
 * 绘制水平线
 * ======================================================================== */
static void draw_hline(u8* buf, int buf_pitch, int x, int y, int w, u8 color) {
    for (int col = 0; col < w; col++) {
        int bx = x + col;
        if (bx >= 0 && bx < PANEL_W) {
            buf[y * buf_pitch + bx] = color;
        }
    }
}

/* ========================================================================
 * 渲染角色信息面板内容
 * ======================================================================== */
static void render_char_info_panel(u8* buf, int buf_pitch,
                                    state_battle_data_t* data, 
                                    int char_idx,
                                    fd2_game_t* game) {
    if (!data || !buf || char_idx < 0 || char_idx >= data->total_char_count) return;
    
    battle_char_data_t* ch = &data->char_data[char_idx];
    
    /* 清除背景 (黑色) */
    fill_rect(buf, buf_pitch, 0, 0, PANEL_W, PANEL_H, COLOR_BLACK);
    
    /* 绘制边框 */
    draw_border(buf, buf_pitch, 8, 8, PANEL_W - 16, PANEL_H - 16, COLOR_WHITE);
    
    /* 加载字体 */
    load_font_from_fdother(game);
    
    /* 渲染文字信息 */
    int text_x = 20;
    int text_y = 16;
    
    /* 角色编号 "No.XX" */
    char idx_buf[16];
    snprintf(idx_buf, sizeof(idx_buf), "No.%02d", char_idx);
    draw_string_to_buf(buf, buf_pitch, text_x, text_y, idx_buf, COLOR_YELLOW);
    text_y += FONT_LINE_H;
    
    /* 类型 */
    const char* type_str = "???";
    if (ch->char_type == 0) type_str = "ALLY";
    else if (ch->char_type == 1) type_str = "ENEMY";
    else if (ch->char_type == 2) type_str = "NPC";
    draw_string_to_buf(buf, buf_pitch, text_x, text_y, type_str, COLOR_CYAN);
    text_y += FONT_LINE_H;
    
    /* 等级 "Lv:XX" */
    char lv_buf[16];
    snprintf(lv_buf, sizeof(lv_buf), "Lv:%d", ch->direction);
    draw_string_to_buf(buf, buf_pitch, text_x, text_y, lv_buf, COLOR_GREEN);
    text_y += FONT_LINE_H;
    
    /* 分割线 */
    draw_hline(buf, buf_pitch, 20, text_y, PANEL_W - 40, COLOR_GRAY);
    text_y += 4;
    
    /* HP "HP:XX/XX" */
    char hp_buf[32];
    int max_hp = (ch->icon_id_alt > 0) ? ch->icon_id_alt : 100;
    snprintf(hp_buf, sizeof(hp_buf), "HP:%d/%d", ch->icon_id, max_hp);
    draw_string_to_buf(buf, buf_pitch, text_x, text_y, hp_buf, COLOR_GREEN);
    text_y += FONT_LINE_H;
    
    /* MP "MP:XX/XX" */
    char mp_buf[32];
    int max_mp = (ch->portrait_id > 0) ? ch->portrait_id * 2 : 50;
    snprintf(mp_buf, sizeof(mp_buf), "MP:%d/%d", ch->portrait_id, max_mp);
    draw_string_to_buf(buf, buf_pitch, text_x, text_y, mp_buf, COLOR_BLUE);
    text_y += FONT_LINE_H;
    
    /* 位置 "POS:(X,Y)" */
    char pos_buf[32];
    snprintf(pos_buf, sizeof(pos_buf), "POS:(%d,%d)", ch->tile_x, ch->tile_y);
    draw_string_to_buf(buf, buf_pitch, text_x, text_y, pos_buf, COLOR_GRAY);
    text_y += FONT_LINE_H;
    
    /* 状态 */
    const char* status_str = "ALIVE";
    u8 status_color = COLOR_GREEN;
    if (ch->death_flag) {
        status_str = "DEAD";
        status_color = COLOR_RED;
    } else if (ch->active_byte & 1) {
        status_str = "MOVED";
        status_color = COLOR_ORANGE;
    }
    draw_string_to_buf(buf, buf_pitch, text_x, text_y, status_str, status_color);
}

/* ========================================================================
 * battle_render_char_info - 公开API
 * ======================================================================== */
void battle_render_char_info(state_battle_data_t* data, fd2_game_t* game, int char_idx) {
    if (!data || !game || char_idx < 0 || char_idx >= data->total_char_count) return;
    
    /* 创建渲染缓冲区 */
    u8* render_buf = (u8*)calloc(PANEL_BUF_PITCH * PANEL_H, sizeof(u8));
    if (!render_buf) return;
    
    /* 渲染角色信息面板 */
    render_char_info_panel(render_buf, PANEL_BUF_PITCH, data, char_idx, game);
    
    /* 拷贝到屏幕 */
    u8* screen = game->render.screen;
    if (screen) {
        fb_copy_11eb0(screen, FD2_SCREEN_W, render_buf, PANEL_BUF_PITCH,
                      PANEL_W, PANEL_H, PANEL_SCREEN_X, PANEL_SCREEN_Y);
    }
    
    free(render_buf);
}

/* ========================================================================
 * battle_render_info_panel - 战场主循环调用
 * ======================================================================== */
void battle_render_info_panel(state_battle_data_t* data, fd2_game_t* game) {
    if (!data || !game) return;
    
    if (data->selected_char_idx >= 0 && data->selected_char_idx < data->total_char_count) {
        battle_render_char_info(data, game, data->selected_char_idx);
    }
}
