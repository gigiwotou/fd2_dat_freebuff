/**
 * FD2 Battle Info Panel - 战场信息面板
 * 
 * 基于 IDA Pro MCP 逆向分析:
 * 
 * 战场信息面板渲染流程:
 * sub_12D7B -> sub_12CEA -> sub_11CAC -> [sub_11EEE, sub_122DC, sub_127A9, sub_1ACF3, sub_11EB0]
 * 
 * sub_11CAC参数:
 * - a1, a2, a3, a4: 角色数据相关
 * - a5: 标志位
 * 
 * sub_11EEE文字渲染:
 * - 使用FDSHAP.DAT中的24x24文字瓦片图
 * - 参数: (dword_53A49+32904, 456, 13, 8, n9, n34)
 * - 13列 x 8行文字, 每字符宽24像素
 * - 从dword_53A51获取字符索引表
 * - 从dword_53A69获取字符标志(用于调色板映射)
 * - 使用sub_4E22A(直接blit)或sub_4E016(带调色板映射)
 * 
 * sub_1ACF3边框绘制:
 * - 使用FDSHAP.DAT中的边框瓦片图
 * - 参数: (dword_53A49+32904, 456)
 * 
 * sub_11EB0帧缓冲拷贝:
 * - 参数: (656644, 320, dword_53A49+32904, 456, 312, 192)
 * - 从内部缓冲区拷贝到VGA屏幕
 */

#include "fd2_game.h"
#include "fd2_battle.h"
#include "fd2_decoder.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* ========================================================================
 * 战场信息面板常量 (基于IDA分析)
 * ======================================================================== */

/* 内部渲染缓冲区参数 (模拟 dword_53A49 + 32904) */
#define INFO_PANEL_BUF_PITCH    456
#define INFO_PANEL_W            312
#define INFO_PANEL_H            192

/* 文字区域: 13列 x 8行, 每字符24x24像素 */
#define TEXT_COLS               13
#define TEXT_ROWS               8
#define CHAR_TILE_W             24
#define CHAR_TILE_H             24

/* 屏幕映射位置 (312x192 面板映射到 320x200 屏幕) */
#define PANEL_SCREEN_X          4
#define PANEL_SCREEN_Y          4

/* 颜色定义 (游戏调色板索引) */
#define COLOR_BLACK             0
#define COLOR_WHITE             63
#define COLOR_YELLOW            62
#define COLOR_GREEN             48
#define COLOR_RED               16
#define COLOR_BLUE              44
#define COLOR_CYAN              47
#define COLOR_GRAY              15

/* ========================================================================
 * FDSHAP.DAT 瓦片图资源
 * ======================================================================== */

static u8* fdshap_data = NULL;
static u32 fdshap_size = 0;
static int fdshap_tile_count = 0;

/* 文字瓦片索引表 (ASCII字符 -> FDSHAP瓦片索引) */
static int text_tile_map[128];
static int tile_map_initialized = 0;

/* ========================================================================
 * 初始化FDSHAP.DAT瓦片图资源
 * ======================================================================== */
static int init_tile_resources(fd2_game_t* game) {
    if (tile_map_initialized) return 0;
    
    memset(text_tile_map, -1, sizeof(text_tile_map));
    
    /* 加载FDSHAP.DAT资源 */
    if (!fd2_resources_is_loaded(&game->resources, FD2_DAT_FDSHAP)) {
        return -1;
    }
    
    u32 res_size;
    const u8* res_data = fd2_resources_get(&game->resources, FD2_DAT_FDSHAP, 0, &res_size);
    if (!res_data || res_size < 10) return -1;
    
    /* 解析资源数量 */
    if (memcmp(res_data, "LLLLLL", 6) == 0) {
        memcpy(&fdshap_tile_count, res_data + 6, 4);
    } else {
        return -1;
    }
    
    fdshap_data = (u8*)res_data;
    fdshap_size = res_size;
    
    /* 初始化文字瓦片映射表 */
    /* 数字 0-9 */
    for (int i = 0; i < 10; i++) {
        text_tile_map['0' + i] = i;
    }
    /* 字母 A-Z */
    for (int i = 0; i < 26; i++) {
        text_tile_map['A' + i] = 10 + i;
        text_tile_map['a' + i] = 10 + i;
    }
    /* 常用符号 */
    text_tile_map[':'] = 40;
    text_tile_map['/'] = 41;
    text_tile_map['.'] = 42;
    text_tile_map['-'] = 43;
    text_tile_map[' '] = 44;
    text_tile_map['('] = 45;
    text_tile_map[')'] = 46;
    text_tile_map['?'] = 47;
    text_tile_map['!'] = 48;
    text_tile_map[','] = 49;
    
    tile_map_initialized = 1;
    return 0;
}

/* ========================================================================
 * sub_4E22A风格: 24x24瓦片RLE blit到缓冲区
 * 
 * 对应IDA sub_4E22A:
 * - src: 瓦片RLE数据
 * - dst: 目标缓冲区位置
 * - pitch: 缓冲区步长
 * 
 * RLE格式:
 * - bit7=1,bit6=1: 跳过像素(透明)
 * - bit7=1,bit6=0: 从源拷贝像素
 * - bit7=0,bit6=1: 稀疏填充(每隔一个像素)
 * - bit7=0,bit6=0: 常规填充
 * - count = (value & 0x3F) + 1
 */
static void tile_blit_4e22a(const u8* tile_data, u8* dst_buf, int dst_pitch) {
    if (!tile_data || !dst_buf) return;
    
    const u8* src = tile_data;
    u8* dst = dst_buf;
    
    for (int row = 0; row < 24; row++) {
        u8* row_dst = dst;
        int pixels_remaining = 24;
        
        while (pixels_remaining > 0) {
            u8 value = *src++;
            int bit7 = (value >> 7) & 1;
            int bit6 = (value >> 6) & 1;
            int count = (value & 0x3F) + 1;
            
            if (count > pixels_remaining) count = pixels_remaining;
            
            if (bit7 && bit6) {
                /* 11: 跳过像素 */
                row_dst += count;
                pixels_remaining -= count;
            } else if (bit7 && !bit6) {
                /* 10: 从源拷贝 */
                for (int i = 0; i < count; i++) {
                    *row_dst++ = *src++;
                }
                pixels_remaining -= count;
            } else if (!bit7 && bit6) {
                /* 01: 稀疏填充 */
                u8 fill = *src++;
                for (int i = 0; i < count; i++) {
                    if (pixels_remaining >= 2) {
                        row_dst[1] = fill;
                        row_dst += 2;
                        pixels_remaining -= 2;
                    } else {
                        *row_dst++ = fill;
                        pixels_remaining -= 1;
                    }
                }
            } else {
                /* 00: 常规填充 */
                u8 fill = *src++;
                for (int i = 0; i < count; i++) {
                    *row_dst++ = fill;
                }
                pixels_remaining -= count;
            }
        }
        
        dst += dst_pitch;
    }
}

/* ========================================================================
 * 获取FDSHAP.DAT瓦片图数据
 * 
 * 对应原游戏: FDSHAP_DAT + *(DWORD*)(FDSHAP_DAT + 4 * index + 6)
 */
static const u8* get_fdshap_tile(int tile_index) {
    if (!fdshap_data || tile_index < 0 || tile_index >= fdshap_tile_count) {
        return NULL;
    }
    
    u32 offset;
    memcpy(&offset, fdshap_data + 6 + tile_index * 4, 4);
    
    if (offset >= fdshap_size) return NULL;
    
    return fdshap_data + offset;
}

/* ========================================================================
 * sub_11EB0风格: 帧缓冲拷贝
 * 
 * 对应IDA sub_11EB0:
 * - 使用memmove逐行拷贝
 */
static void fb_copy_11eb0(u8* dst_screen, int dst_pitch,
                           const u8* src_buffer, int src_pitch,
                           int w, int h, int dst_x, int dst_y) {
    if (!dst_screen || !src_buffer) return;
    (void)dst_pitch;
    
    for (int row = 0; row < h; row++) {
        int screen_y = dst_y + row;
        if (screen_y < 0 || screen_y >= FD2_SCREEN_H) continue;
        
        int screen_x = dst_x;
        if (screen_x < 0) screen_x = 0;
        if (screen_x >= FD2_SCREEN_W) continue;
        
        int copy_w = w;
        if (screen_x + copy_w > FD2_SCREEN_W) {
            copy_w = FD2_SCREEN_W - screen_x;
        }
        
        u8* dst_row = dst_screen + screen_y * FD2_SCREEN_W + screen_x;
        const u8* src_row = src_buffer + row * src_pitch;
        
        memmove(dst_row, src_row, copy_w);
    }
}

/* ========================================================================
 * 绘制字符串到缓冲区 (使用FDSHAP文字瓦片)
 * 
 * 对应sub_11EEE的文字渲染逻辑
 */
static void draw_string_with_tiles(u8* buf, int buf_pitch, int x, int y,
                                    const char* str, u8 color) {
    if (!str || !buf) return;
    (void)color;
    
    int cx = x;
    int len = strlen(str);
    
    for (int i = 0; i < len; i++) {
        unsigned char c = (unsigned char)str[i];
        if (c >= 128) continue;
        
        int tile_idx = text_tile_map[(unsigned char)c];
        if (tile_idx < 0) {
            cx += CHAR_TILE_W;
            continue;
        }
        
        const u8* tile_data = get_fdshap_tile(tile_idx);
        if (!tile_data) {
            cx += CHAR_TILE_W;
            continue;
        }
        
        u8* dst = buf + y * buf_pitch + cx;
        tile_blit_4e22a(tile_data, dst, buf_pitch);
        
        cx += CHAR_TILE_W;
    }
}

/* ========================================================================
 * 绘制数字到缓冲区
 */
static void draw_number_with_tiles(u8* buf, int buf_pitch, int x, int y,
                                    int num) {
    char buf_str[16];
    snprintf(buf_str, sizeof(buf_str), "%d", num);
    draw_string_with_tiles(buf, buf_pitch, x, y, buf_str, COLOR_WHITE);
}

/* ========================================================================
 * 填充矩形背景
 */
static void fill_rect(u8* buf, int buf_pitch, int x, int y, int w, int h, u8 color) {
    for (int row = 0; row < h; row++) {
        int by = y + row;
        if (by < 0 || by >= INFO_PANEL_H) continue;
        
        for (int col = 0; col < w; col++) {
            int bx = x + col;
            if (bx < 0 || bx >= INFO_PANEL_W) continue;
            
            buf[by * buf_pitch + bx] = color;
        }
    }
}

/* ========================================================================
 * sub_1ACF3风格: 绘制边框
 * 
 * 对应IDA sub_1ACF3:
 * - 使用FDSHAP.DAT边框瓦片图绘制
 * - 参数: buf, pitch
 */
static void draw_border_1acf3(u8* buf, int buf_pitch, int x, int y, int w, int h) {
    fill_rect(buf, buf_pitch, x, y, w, h, COLOR_BLACK);
    
    /* 使用FDSHAP边框瓦片 (假设瓦片50-53是边框四角) */
    const u8* corner_tl = get_fdshap_tile(50);
    if (corner_tl) {
        tile_blit_4e22a(corner_tl, buf + y * buf_pitch + x, buf_pitch);
    }
    
    const u8* corner_tr = get_fdshap_tile(51);
    if (corner_tr && x + w - 24 >= 0) {
        tile_blit_4e22a(corner_tr, buf + y * buf_pitch + (x + w - 24), buf_pitch);
    }
    
    const u8* corner_bl = get_fdshap_tile(52);
    if (corner_bl && y + h - 24 >= 0) {
        tile_blit_4e22a(corner_bl, buf + (y + h - 24) * buf_pitch + x, buf_pitch);
    }
    
    const u8* corner_br = get_fdshap_tile(53);
    if (corner_br && x + w - 24 >= 0 && y + h - 24 >= 0) {
        tile_blit_4e22a(corner_br, buf + (y + h - 24) * buf_pitch + (x + w - 24), buf_pitch);
    }
    
    for (int col = x + 24; col < x + w - 24; col += 24) {
        const u8* edge_h = get_fdshap_tile(54);
        if (edge_h) {
            tile_blit_4e22a(edge_h, buf + y * buf_pitch + col, buf_pitch);
            if (y + h - 24 >= 0) {
                tile_blit_4e22a(edge_h, buf + (y + h - 24) * buf_pitch + col, buf_pitch);
            }
        }
    }
    
    for (int row = y + 24; row < y + h - 24; row += 24) {
        const u8* edge_v = get_fdshap_tile(55);
        if (edge_v) {
            tile_blit_4e22a(edge_v, buf + row * buf_pitch + x, buf_pitch);
            if (x + w - 24 >= 0) {
                tile_blit_4e22a(edge_v, buf + row * buf_pitch + (x + w - 24), buf_pitch);
            }
        }
    }
}

/* ========================================================================
 * 渲染角色信息面板内容
 * 
 * 对应原游戏的完整渲染流程:
 * 1. sub_11EEE: 渲染文字 (8行x13列)
 * 2. sub_127A9: 渲染信息瓦片
 * 3. sub_1ACF3: 绘制边框
 * 4. sub_11EB0: 拷贝到屏幕
 */
static void render_char_info_panel(u8* buf, int buf_pitch,
                                    state_battle_data_t* data, 
                                    int char_idx) {
    if (!data || !buf || char_idx < 0 || char_idx >= data->total_char_count) return;
    
    battle_char_data_t* ch = &data->char_data[char_idx];
    
    memset(buf, 0, INFO_PANEL_H * buf_pitch);
    
    draw_border_1acf3(buf, buf_pitch, 8, 8, INFO_PANEL_W - 16, INFO_PANEL_H - 16);
    
    int text_x = 24;
    int text_y = 16;
    
    char idx_buf[16];
    snprintf(idx_buf, sizeof(idx_buf), "No:%02d", char_idx);
    draw_string_with_tiles(buf, buf_pitch, text_x, text_y, idx_buf, COLOR_YELLOW);
    text_y += CHAR_TILE_H;
    
    const char* type_str = "???";
    if (ch->char_type == 0) type_str = "ALLY";
    else if (ch->char_type == 1) type_str = "ENEMY";
    else if (ch->char_type == 2) type_str = "NPC";
    draw_string_with_tiles(buf, buf_pitch, text_x, text_y, type_str, COLOR_CYAN);
    text_y += CHAR_TILE_H;
    
    char lv_buf[16];
    snprintf(lv_buf, sizeof(lv_buf), "Lv:%d", ch->direction);
    draw_string_with_tiles(buf, buf_pitch, text_x, text_y, lv_buf, COLOR_GREEN);
    text_y += CHAR_TILE_H;
    
    char hp_buf[32];
    int max_hp = (ch->icon_id_alt > 0) ? ch->icon_id_alt : 100;
    snprintf(hp_buf, sizeof(hp_buf), "HP:%d/%d", ch->icon_id, max_hp);
    draw_string_with_tiles(buf, buf_pitch, text_x, text_y, hp_buf, COLOR_GREEN);
    text_y += CHAR_TILE_H;
    
    char mp_buf[32];
    int max_mp = (ch->portrait_id > 0) ? ch->portrait_id * 2 : 50;
    snprintf(mp_buf, sizeof(mp_buf), "MP:%d/%d", ch->portrait_id, max_mp);
    draw_string_with_tiles(buf, buf_pitch, text_x, text_y, mp_buf, COLOR_BLUE);
    text_y += CHAR_TILE_H;
    
    char pos_buf[32];
    snprintf(pos_buf, sizeof(pos_buf), "POS:(%d,%d)", ch->tile_x, ch->tile_y);
    draw_string_with_tiles(buf, buf_pitch, text_x, text_y, pos_buf, COLOR_GRAY);
    text_y += CHAR_TILE_H;
    
    const char* status_str = "ALIVE";
    if (ch->death_flag) {
        status_str = "DEAD";
    } else if (ch->active_byte & 1) {
        status_str = "MOVED";
    }
    draw_string_with_tiles(buf, buf_pitch, text_x, text_y, status_str, COLOR_GREEN);
}

/* ========================================================================
 * battle_render_char_info - 公开API
 * ======================================================================== */
void battle_render_char_info(state_battle_data_t* data, fd2_game_t* game, int char_idx) {
    if (!data || !game || char_idx < 0 || char_idx >= data->total_char_count) return;
    
    if (init_tile_resources(game) != 0) return;
    
    u8* render_buf = (u8*)calloc(INFO_PANEL_BUF_PITCH * INFO_PANEL_H, sizeof(u8));
    if (!render_buf) return;
    
    render_char_info_panel(render_buf, INFO_PANEL_BUF_PITCH, data, char_idx);
    
    u8* screen = game->render.screen;
    if (screen) {
        fb_copy_11eb0(screen, FD2_SCREEN_W, render_buf, INFO_PANEL_BUF_PITCH,
                      INFO_PANEL_W, INFO_PANEL_H, PANEL_SCREEN_X, PANEL_SCREEN_Y);
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
