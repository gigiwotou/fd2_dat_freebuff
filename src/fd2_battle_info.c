/**
 * FD2 Battle Info Panel - 原游戏UI实现
 * 
 * 基于 IDA Pro MCP 逆向分析:
 * 
 * 函数调用链:
 * sub_12D7B -> sub_12CEA -> sub_11CAC -> [sub_1297D, sub_4E31C, sub_11EEE, sub_122DC, sub_127A9, sub_1ACF3, sub_11EB0]
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
 *   - 使用 FDSHAP.DAT 24x24精灵渲染文字
 *   - 8行 x 13列，每字符宽24像素
 *   - 从 dword_53A51 获取字符索引表
 *   - 从 dword_53A69 获取字符标志
 *   - 使用 sub_4E22A(直接blit) 或 sub_4E016(带调色板映射)
 * 
 * sub_4E22A - 精灵blit (24x24):
 *   - RLE解码直接拷贝到目标缓冲区
 *   - 格式: 24行，每行24像素
 *   - RLE命令: 同sub_4E98D (bit7,bit6确定模式)
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

/* 文字区域: 8行 x 13列，每字符24像素宽 */
#define TEXT_COLS          13
#define TEXT_ROWS          8
#define CHAR_W             24
#define CHAR_H             24

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
 * FDSHAP.DAT 精灵数据
 * ======================================================================== */

/* FDSHAP.DAT资源基地址 (类似原游戏的 FDSHAP_DAT) */
static u8* fdshap_data = NULL;
static u32 fdshap_size = 0;
static int fdshap_resource_count = 0;

/* 字符精灵索引表 (ASCII -> FDSHAP精灵索引) */
/* 原游戏从 dword_53A51 获取字符布局数据 */
static int char_to_sprite[128];
static int sprite_table_initialized = 0;

/* ========================================================================
 * 初始化FDSHAP.DAT和字符精灵索引表
 * ======================================================================== */
static int init_sprite_table(fd2_game_t* game) {
    if (sprite_table_initialized) return 0;
    
    memset(char_to_sprite, -1, sizeof(char_to_sprite));
    
    /* 加载FDSHAP.DAT */
    if (!fd2_resources_is_loaded(&game->resources, FD2_DAT_FDSHAP)) {
        return -1;
    }
    
    u32 res_size;
    const u8* res_data = fd2_resources_get(&game->resources, FD2_DAT_FDSHAP, 0, &res_size);
    if (!res_data || res_size < 10) return -1;
    
    /* 解析资源数量 */
    if (memcmp(res_data, "LLLLLL", 6) == 0) {
        memcpy(&fdshap_resource_count, res_data + 6, 4);
    } else {
        return -1;
    }
    
    fdshap_data = (u8*)res_data;
    fdshap_size = res_size;
    
    /* 初始化字符到精灵的映射 (根据原游戏dword_53A51布局) */
    /* 这里需要匹配原游戏的字符表，暂时使用简单映射 */
    /* 数字 0-9 */
    for (int i = 0; i < 10; i++) {
        char_to_sprite['0' + i] = i;
    }
    /* 字母 A-Z */
    for (int i = 0; i < 26; i++) {
        char_to_sprite['A' + i] = 10 + i;
        char_to_sprite['a' + i] = 10 + i;
    }
    /* 常用符号 */
    char_to_sprite[':'] = 40;
    char_to_sprite['/'] = 41;
    char_to_sprite['.'] = 42;
    char_to_sprite['-'] = 43;
    char_to_sprite[' '] = 44;  /* 空格 */
    char_to_sprite['('] = 45;
    char_to_sprite[')'] = 46;
    char_to_sprite['?'] = 47;
    char_to_sprite['!'] = 48;
    char_to_sprite[','] = 49;
    
    sprite_table_initialized = 1;
    return 0;
}

/* ========================================================================
 * sub_4E22A风格: 24x24精灵RLE blit到缓冲区
 * 
 * 对应IDA sub_4E22A:
 * char __cdecl sub_4E22A(char *src, char *dst, int a3)
 * - src: 精灵RLE数据
 * - dst: 目标缓冲区位置
 * - a3: 缓冲区步长 (pitch)
 * 
 * RLE格式 (同sub_4E98D):
 *   每个字节通过bit7,bit6确定命令类型:
 *   - 11xxxxxx: 跳过像素 (透明)
 *   - 10xxxxxx: 从源拷贝像素
 *   - 01xxxxxx: 稀疏填充 (每隔一个像素)
 *   - 00xxxxxx: 常规填充
 *   count = (value & 0x3F) + 1
 * 
 * 精灵尺寸: 24x24像素
 */
static void sprite_blit_4e22a(const u8* sprite_data, u8* dst_buf, int dst_pitch) {
    if (!sprite_data || !dst_buf) return;
    
    const u8* src = sprite_data;
    u8* dst = dst_buf;
    
    /* 24行，每行24像素 */
    for (int row = 0; row < 24; row++) {
        u8* row_dst = dst;
        int pixels_remaining = 24;
        
        while (pixels_remaining > 0) {
            u8 value = *src++;
            int bit7 = (value >> 7) & 1;
            int bit6 = (value >> 6) & 1;
            int count = (value & 0x3F) + 1;
            
            if (count > pixels_remaining) {
                count = pixels_remaining;
            }
            
            if (bit7 && bit6) {
                /* 11: 跳过像素 (透明) */
                row_dst += count;
                pixels_remaining -= count;
            } else if (bit7 && !bit6) {
                /* 10: 从源拷贝像素 */
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
        
        /* 移动到下一行 */
        dst += dst_pitch;
    }
}

/* ========================================================================
 * sub_4E016风格: 24x24精灵RLE blit带调色板映射
 * 
 * 对应IDA sub_4E016:
 * char __cdecl sub_4E016(char *a1, _BYTE *buf, int a3, int a4)
 * - a1: 精灵RLE数据
 * - buf: 目标缓冲区位置
 * - a3: 缓冲区步长
 * - a4: 调色板映射表指针
 * 
 * 与sub_4E22A类似，但像素值需要通过调色板映射转换:
 *   pixel = palette_map[pixel_value]
 * 
 * 预留待用: 当需要调色板映射时启用
 */
#if 0
static void sprite_blit_4e016(const u8* sprite_data, u8* dst_buf, 
                               int dst_pitch, const u8* palette_map) {
    if (!sprite_data || !dst_buf || !palette_map) return;
    
    const u8* src = sprite_data;
    u8* dst = dst_buf;
    
    /* 24行，每行24像素 */
    for (int row = 0; row < 24; row++) {
        u8* row_dst = dst;
        int pixels_remaining = 24;
        
        while (pixels_remaining > 0) {
            u8 value = *src++;
            int bit7 = (value >> 7) & 1;
            int bit6 = (value >> 6) & 1;
            int count = (value & 0x3F) + 1;
            
            if (count > pixels_remaining) {
                count = pixels_remaining;
            }
            
            if (bit7 && bit6) {
                /* 11: 跳过像素 (透明) */
                row_dst += count;
                pixels_remaining -= count;
            } else if (bit7 && !bit6) {
                /* 10: 从源拷贝像素 + 调色板映射 */
                for (int i = 0; i < count; i++) {
                    u8 pixel_val = *src++;
                    *row_dst++ = palette_map[pixel_val];
                }
                pixels_remaining -= count;
            } else if (!bit7 && bit6) {
                /* 01: 稀疏填充 + 调色板映射 */
                u8 fill_src = *src++;
                u8 fill = palette_map[fill_src];
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
                /* 00: 常规填充 + 调色板映射 */
                u8 fill_src = *src++;
                u8 fill = palette_map[fill_src];
                for (int i = 0; i < count; i++) {
                    *row_dst++ = fill;
                }
                pixels_remaining -= count;
            }
        }
        
        /* 移动到下一行 */
        dst += dst_pitch;
    }
}
#endif

/* ========================================================================
 * 获取FDSHAP.DAT精灵数据指针
 * 
 * 对应原游戏: FDSHAP_DAT + *(DWORD*)(FDSHAP_DAT + 4 * index + 6)
 * 
 * FDSHAP.DAT格式:
 *   - 字节0-5: "LLLLLL" 魔数
 *   - 字节6+: 资源偏移表 (每4字节一个偏移)
 */
static const u8* get_fdshap_sprite(int sprite_index) {
    if (!fdshap_data || sprite_index < 0 || sprite_index >= fdshap_resource_count) {
        return NULL;
    }
    
    /* 读取偏移表 */
    u32 offset;
    memcpy(&offset, fdshap_data + 6 + sprite_index * 4, 4);
    
    if (offset >= fdshap_size) return NULL;
    
    /* 返回精灵数据 (跳过精灵内部头) */
    return fdshap_data + offset;
}

/* ========================================================================
 * sub_11EB0风格: 帧缓冲拷贝
 * 
 * 对应IDA sub_11EB0:
 * sub_11EB0(656644, 320, dword_53A49+32904, 456, 312, 192)
 * 
 * 使用memmove逐行拷贝，处理不同步长
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
 * 绘制字符串到缓冲区 (使用FDSHAP精灵)
 * 
 * 对应sub_11EEE的文字渲染逻辑:
 * - 每个字符24像素宽
 * - 使用sprite_blit_4e22a或sprite_blit_4e016
 */
static void draw_string_with_sprites(u8* buf, int buf_pitch, int x, int y,
                                      const char* str, u8 color) {
    if (!str || !buf) return;
    (void)color;
    
    int cx = x;
    int len = strlen(str);
    
    for (int i = 0; i < len; i++) {
        unsigned char c = (unsigned char)str[i];
        if (c >= 128) continue;
        
        int sprite_idx = char_to_sprite[(unsigned char)c];
        if (sprite_idx < 0) {
            cx += CHAR_W;
            continue;
        }
        
        const u8* sprite_data = get_fdshap_sprite(sprite_idx);
        if (!sprite_data) {
            cx += CHAR_W;
            continue;
        }
        
        /* 计算目标位置 */
        u8* dst = buf + y * buf_pitch + cx;
        
        /* 使用精灵blit */
        sprite_blit_4e22a(sprite_data, dst, buf_pitch);
        
        cx += CHAR_W;
    }
}

/* ========================================================================
 * 绘制数字到缓冲区
 */
static void draw_number_with_sprites(u8* buf, int buf_pitch, int x, int y,
                                      int num) {
    char buf_str[16];
    snprintf(buf_str, sizeof(buf_str), "%d", num);
    draw_string_with_sprites(buf, buf_pitch, x, y, buf_str, COLOR_WHITE);
}

/* ========================================================================
 * 填充矩形背景
 */
static void fill_rect(u8* buf, int buf_pitch, int x, int y, int w, int h, u8 color) {
    for (int row = 0; row < h; row++) {
        int by = y + row;
        if (by < 0 || by >= PANEL_H) continue;
        
        for (int col = 0; col < w; col++) {
            int bx = x + col;
            if (bx < 0 || bx >= PANEL_W) continue;
            
            buf[by * buf_pitch + bx] = color;
        }
    }
}

/* ========================================================================
 * sub_1ACF3风格: 绘制边框
 * 
 * 对应IDA sub_1ACF3:
 * - 使用FDSHAP.DAT边框精灵绘制
 * - 参数: buf, pitch
 * 
 * 简化实现: 使用精灵绘制边框四角和边缘
 */
static void draw_border_1acf3(u8* buf, int buf_pitch, int x, int y, int w, int h) {
    /* 清除背景 */
    fill_rect(buf, buf_pitch, x, y, w, h, COLOR_BLACK);
    
    /* 使用FDSHAP边框精灵 (假设精灵50-53是边框四角) */
    /* 左上角 */
    const u8* corner_tl = get_fdshap_sprite(50);
    if (corner_tl) {
        sprite_blit_4e22a(corner_tl, buf + y * buf_pitch + x, buf_pitch);
    }
    
    /* 右上角 */
    const u8* corner_tr = get_fdshap_sprite(51);
    if (corner_tr && x + w - 24 >= 0) {
        sprite_blit_4e22a(corner_tr, buf + y * buf_pitch + (x + w - 24), buf_pitch);
    }
    
    /* 左下角 */
    const u8* corner_bl = get_fdshap_sprite(52);
    if (corner_bl && y + h - 24 >= 0) {
        sprite_blit_4e22a(corner_bl, buf + (y + h - 24) * buf_pitch + x, buf_pitch);
    }
    
    /* 右下角 */
    const u8* corner_br = get_fdshap_sprite(53);
    if (corner_br && x + w - 24 >= 0 && y + h - 24 >= 0) {
        sprite_blit_4e22a(corner_br, buf + (y + h - 24) * buf_pitch + (x + w - 24), buf_pitch);
    }
    
    /* 上边和下边 */
    for (int col = x + 24; col < x + w - 24; col += 24) {
        const u8* edge_h = get_fdshap_sprite(54);
        if (edge_h) {
            sprite_blit_4e22a(edge_h, buf + y * buf_pitch + col, buf_pitch);
            if (y + h - 24 >= 0) {
                sprite_blit_4e22a(edge_h, buf + (y + h - 24) * buf_pitch + col, buf_pitch);
            }
        }
    }
    
    /* 左边和右边 */
    for (int row = y + 24; row < y + h - 24; row += 24) {
        const u8* edge_v = get_fdshap_sprite(55);
        if (edge_v) {
            sprite_blit_4e22a(edge_v, buf + row * buf_pitch + x, buf_pitch);
            if (x + w - 24 >= 0) {
                sprite_blit_4e22a(edge_v, buf + row * buf_pitch + (x + w - 24), buf_pitch);
            }
        }
    }
}

/* ========================================================================
 * 渲染角色信息面板内容
 * 
 * 对应原游戏的完整渲染流程:
 * 1. sub_11EEE: 渲染文字 (8行x13列)
 * 2. sub_127A9: 渲染信息精灵
 * 3. sub_1ACF3: 绘制边框
 * 4. sub_11EB0: 拷贝到屏幕
 */
static void render_char_info_panel(u8* buf, int buf_pitch,
                                    state_battle_data_t* data, 
                                    int char_idx) {
    if (!data || !buf || char_idx < 0 || char_idx >= data->total_char_count) return;
    
    battle_char_data_t* ch = &data->char_data[char_idx];
    
    /* 1. 清除背景 */
    memset(buf, 0, PANEL_H * buf_pitch);
    
    /* 2. 绘制边框 (sub_1ACF3风格) */
    draw_border_1acf3(buf, buf_pitch, 8, 8, PANEL_W - 16, PANEL_H - 16);
    
    /* 3. 渲染文字信息 (sub_11EEE风格) */
    int text_x = 24;
    int text_y = 16;
    
    /* 角色编号 "No:XX" */
    char idx_buf[16];
    snprintf(idx_buf, sizeof(idx_buf), "No:%02d", char_idx);
    draw_string_with_sprites(buf, buf_pitch, text_x, text_y, idx_buf, COLOR_YELLOW);
    text_y += CHAR_H;
    
    /* 类型 */
    const char* type_str = "???";
    if (ch->char_type == 0) type_str = "ALLY";
    else if (ch->char_type == 1) type_str = "ENEMY";
    else if (ch->char_type == 2) type_str = "NPC";
    draw_string_with_sprites(buf, buf_pitch, text_x, text_y, type_str, COLOR_CYAN);
    text_y += CHAR_H;
    
    /* 等级 "Lv:XX" */
    char lv_buf[16];
    snprintf(lv_buf, sizeof(lv_buf), "Lv:%d", ch->direction);
    draw_string_with_sprites(buf, buf_pitch, text_x, text_y, lv_buf, COLOR_GREEN);
    text_y += CHAR_H;
    
    /* HP "HP:XX/XX" */
    char hp_buf[32];
    int max_hp = (ch->icon_id_alt > 0) ? ch->icon_id_alt : 100;
    snprintf(hp_buf, sizeof(hp_buf), "HP:%d/%d", ch->icon_id, max_hp);
    draw_string_with_sprites(buf, buf_pitch, text_x, text_y, hp_buf, COLOR_GREEN);
    text_y += CHAR_H;
    
    /* MP "MP:XX/XX" */
    char mp_buf[32];
    int max_mp = (ch->portrait_id > 0) ? ch->portrait_id * 2 : 50;
    snprintf(mp_buf, sizeof(mp_buf), "MP:%d/%d", ch->portrait_id, max_mp);
    draw_string_with_sprites(buf, buf_pitch, text_x, text_y, mp_buf, COLOR_BLUE);
    text_y += CHAR_H;
    
    /* 位置 "POS:(X,Y)" */
    char pos_buf[32];
    snprintf(pos_buf, sizeof(pos_buf), "POS:(%d,%d)", ch->tile_x, ch->tile_y);
    draw_string_with_sprites(buf, buf_pitch, text_x, text_y, pos_buf, COLOR_GRAY);
    text_y += CHAR_H;
    
    /* 状态 */
    const char* status_str = "ALIVE";
    if (ch->death_flag) {
        status_str = "DEAD";
    } else if (ch->active_byte & 1) {
        status_str = "MOVED";
    }
    draw_string_with_sprites(buf, buf_pitch, text_x, text_y, status_str, COLOR_GREEN);
}

/* ========================================================================
 * battle_render_char_info - 公开API
 * ======================================================================== */
void battle_render_char_info(state_battle_data_t* data, fd2_game_t* game, int char_idx) {
    if (!data || !game || char_idx < 0 || char_idx >= data->total_char_count) return;
    
    /* 初始化精灵表 */
    if (init_sprite_table(game) != 0) return;
    
    /* 创建渲染缓冲区 */
    u8* render_buf = (u8*)calloc(PANEL_BUF_PITCH * PANEL_H, sizeof(u8));
    if (!render_buf) return;
    
    /* 渲染角色信息面板 */
    render_char_info_panel(render_buf, PANEL_BUF_PITCH, data, char_idx);
    
    /* 拷贝到屏幕 (sub_11EB0风格) */
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