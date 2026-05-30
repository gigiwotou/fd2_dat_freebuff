/**
 * FDOTHER.DAT 资源查看器
 * 
 * 功能：
 * 1. 绘制调色板 (索引 0,8,57,76,99,101,102)
 * 2. 绘制图片 (Tile图像)
 * 3. 播放音效 (索引31中的62个音效)
 * 
 * 操作：
 * - 上/下箭头：切换 0-102 子资源集
 * - 左/右箭头：切换子项（调色板颜色、嵌套DAT子资源、LMI1子tile、音效等）
 */

#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "fd2_types.h"
#include "fd2_fdother_resources.h"
#include "fd2_dat.h"
#include "fd2_sfx.h"
#include "fd2_rle.h"

/* ========================================================================
 * 窗口和渲染配置
 * ======================================================================== */
#define GAME_WIDTH     320
#define GAME_HEIGHT    200
#define SCALE_FACTOR   3
#define VIEWER_WIDTH   (GAME_WIDTH * SCALE_FACTOR)   /* 960 */
#define VIEWER_HEIGHT  (GAME_HEIGHT * SCALE_FACTOR)  /* 600 */
#define VIEWER_TITLE   "FDOTHER.DAT Resource Viewer (320x200 x3)"

/* ========================================================================
 * 全局状态
 * ======================================================================== */
static SDL_Window*     g_window = NULL;
static SDL_Renderer*   g_renderer = NULL;
static SDL_Texture*    g_texture = NULL;
static Uint32          g_pixels[VIEWER_WIDTH * VIEWER_HEIGHT];
static fdother_res_type_t g_current_type = FDOTHER_RES_TYPE_RAW;
static int             g_current_index = 0;        /* 主资源索引 0-102 */
static int             g_sub_index = 0;            /* 子项索引 */
static int             g_max_sub_items = 0;        /* 最大子项数 */

/* 解码缓冲 */
static byte            g_decode_buffer[64000];     /* 最大 320x200 */
static dword           g_decode_width = 0;
static dword           g_decode_height = 0;

/* 音效管理器实例 */
static fd2_sfx_manager_t g_viewer_sfx_mgr;

/* 字体配置 */
#define FONT_CHARS_PER_LINE  16
#define FONT_LINES_PER_PAGE  12
#define FONT_CHARS_PER_PAGE  (FONT_CHARS_PER_LINE * FONT_LINES_PER_PAGE) /* 192 */
#define FONT_CHAR_WIDTH      16
#define FONT_CHAR_HEIGHT     16
#define FONT_TOTAL_CHARS     1824
#define FONT_PAGE_COUNT      ((FONT_TOTAL_CHARS + FONT_CHARS_PER_PAGE - 1) / FONT_CHARS_PER_PAGE) /* 10页 */
static int g_font_page = 0;  /* 当前字体页 (0-9) */

/* 偏移表实例 (索引2) */
static fdother_offset_table_t g_offset_table = {0};
static bool g_offset_table_loaded = false;

/* ========================================================================
 * 资源类型名称
 * ======================================================================== */
static const char* get_type_name(fdother_res_type_t type) {
    switch (type) {
        case FDOTHER_RES_TYPE_PALETTE:    return "PALETTE";
        case FDOTHER_RES_TYPE_TILE:       return "TILE";
        case FDOTHER_RES_TYPE_LMI1:       return "LMI1";
        case FDOTHER_RES_TYPE_NESTED_DAT: return "NESTED_DAT";
        case FDOTHER_RES_TYPE_RAW:        return "RAW";
        default: return "UNKNOWN";
    }
}

/* 获取资源描述 */
static const char* get_resource_desc(int index) {
    switch (index) {
        case 0: return "主调色板";
        case 1: return "图标 24x24";
        case 2: return "偏移表 (9419子资源)";
        case 3: return "LMI1 Tile集 (23 tiles)";
        case 4: return "RAW数据 (字符位图?)";
        case 5: return "LMI1 Tile集 (138 tiles)";
        case 6: return "LMI1 Tile集 (230 tiles)";
        case 7: return "嵌套DAT (38子资源)";
        case 8: return "调色板副本";
        case 9: return "LMI1 Tile集 (12 tiles)";
        case 10: return "图标 62x26";
        case 11: return "全屏图像 320x200 A";
        case 12: return "嵌套DAT (122子资源)";
        case 13: return "LMI1 Tile集 (28 tiles)";
        case 14: return "LMI1 Tile集 (32 tiles)";
        case 15: return "全屏图像 320x200 B";
        case 18: return "字符位图 16x16 A";
        case 19: return "字符位图 30x30 A";
        case 20: return "字符位图 16x16 B";
        case 21: return "字符位图 30x30 B";
        case 26: return "图标 18x18 (大数据)";
        case 29: return "LMI1 Tile集 (24 tiles)";
        case 31: return "音效DAT (62音效)";
        case 34: return "大图标 101x101";
        case 42: return "大图像 312x192";
        case 55: return "全屏图像 320x200 C";
        case 56: return "全屏图像 320x200 D";
        case 57: return "调色板副本";
        case 61: return "全屏图像 320x200 G";
        case 62: return "全屏图像 320x200 H";
        case 63: return "嵌套DAT (130子资源)";
        case 64: return "嵌套DAT (34子资源)";
        case 69: case 70: case 71: case 72: case 73: return "菜单图像 320x147";
        case 74: return "标题文字 320x200";
        case 75: return "全屏图像 320x200 I";
        case 76: return "标题画面调色板";
        case 77: return "嵌套DAT (26子资源)";
        case 78: return "嵌套DAT (14子资源)";
        case 80: return "嵌套DAT (74子资源)";
        case 96: return "图标 24x24 B";
        case 97: return "全屏图像 320x200 J";
        case 98: return "条形图像 155x30";
        case 99: return "调色板副本";
        case 100: return "全屏图像 320x200 K";
        case 101: return "调色板副本";
        case 102: return "调色板副本";
        default: return "未知资源";
    }
}

/* ========================================================================
 * 渲染函数
 * ======================================================================== */

/* 清空像素缓冲 */
static void clear_pixels(void) {
    memset(g_pixels, 0, sizeof(g_pixels));
}

/* 绘制像素到屏幕 (固定3倍缩放，基于320x200游戏画布) */
static void draw_pixels(const byte* pixels, int width, int height, 
                        const byte* palette_rgb24, int palette_window) {
    clear_pixels();
    
    int scale = SCALE_FACTOR;
    int start_x = 0, start_y = 0;
    
    /* 计算居中位置 (基于320x200游戏画布) */
    if (width > 0 && height > 0) {
        start_x = ((GAME_WIDTH - width) * scale) / 2;
        start_y = ((GAME_HEIGHT - height) * scale) / 2;
    }
    
    /* 渲染像素（应用调色板窗口作为颜色偏移） */
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            byte pal_idx = pixels[y * width + x];
            
            /* 应用调色板窗口偏移 */
            int adjusted_idx = (palette_window + pal_idx) & 0xFF;
            
            int r = palette_rgb24[adjusted_idx * 3 + 0];
            int g = palette_rgb24[adjusted_idx * 3 + 1];
            int b = palette_rgb24[adjusted_idx * 3 + 2];
            
            Uint32 color = (0xFF << 24) | (r << 16) | (g << 8) | b;
            
            /* 缩放绘制 */
            for (int sy = 0; sy < scale; sy++) {
                for (int sx = 0; sx < scale; sx++) {
                    int dx = start_x + x * scale + sx;
                    int dy = start_y + y * scale + sy;
                    if (dx >= 0 && dx < VIEWER_WIDTH && dy >= 0 && dy < VIEWER_HEIGHT) {
                        g_pixels[dy * VIEWER_WIDTH + dx] = color;
                    }
                }
            }
        }
    }
}

/* 绘制调色板 (基于320x200游戏画布) */
static void draw_palette_view(const byte* palette_rgb24) {
    clear_pixels();
    
    /* 256色，每行16个，共16行 */
    int cell_w = 20;  /* 320/16 = 20 */
    int cell_h = 12;  /* 200/16 ≈ 12 */
    int cols = 16;
    int start_x = 0;
    int start_y = 0;
    
    for (int i = 0; i < 256; i++) {
        int col = i % cols;
        int row = i / cols;
        
        int x = start_x + col * cell_w;
        int y = start_y + row * cell_h;
        
        int r = palette_rgb24[i * 3 + 0];
        int g = palette_rgb24[i * 3 + 1];
        int b = palette_rgb24[i * 3 + 2];
        
        Uint32 color = (0xFF << 24) | (r << 16) | (g << 8) | b;
        
        /* 填充色块 */
        for (int cy = 0; cy < cell_h; cy++) {
            for (int cx = 0; cx < cell_w; cx++) {
                int px = x + cx;
                int py = y + cy;
                if (px >= 0 && px < VIEWER_WIDTH && py >= 0 && py < VIEWER_HEIGHT) {
                    g_pixels[py * VIEWER_WIDTH + px] = color;
                }
            }
        }
    }
    
    /* 高亮当前选中的颜色 */
    if (g_sub_index >= 0 && g_sub_index < 256) {
        int col = g_sub_index % cols;
        int row = g_sub_index / cols;
        
        int x = start_x + col * cell_w;
        int y = start_y + row * cell_h;
        
        Uint32 white = (0xFF << 24) | (0xFF << 16) | (0xFF << 8) | 0xFF;
        
        /* 绘制白色边框 */
        for (int i = 0; i < cell_w; i++) {
            if (x + i >= 0 && x + i < VIEWER_WIDTH && y >= 0 && y < VIEWER_HEIGHT)
                g_pixels[y * VIEWER_WIDTH + x + i] = white;
            if (x + i >= 0 && x + i < VIEWER_WIDTH && y + cell_h - 1 < VIEWER_HEIGHT)
                g_pixels[(y + cell_h - 1) * VIEWER_WIDTH + x + i] = white;
        }
        for (int i = 0; i < cell_h; i++) {
            if (x >= 0 && x < VIEWER_WIDTH && y + i >= 0 && y + i < VIEWER_HEIGHT)
                g_pixels[(y + i) * VIEWER_WIDTH + x] = white;
            if (x + cell_w - 1 < VIEWER_WIDTH && y + i >= 0 && y + i < VIEWER_HEIGHT)
                g_pixels[(y + i) * VIEWER_WIDTH + x + cell_w - 1] = white;
        }
    }
}

/* 绘制字体 (索引4: 1824字符, 16x16位图) */
static void draw_font_view(const byte* font_data) {
    clear_pixels();
    
    int chars_per_page = FONT_CHARS_PER_PAGE;
    int start_char = g_font_page * chars_per_page;
    int end_char = start_char + chars_per_page;
    if (end_char > FONT_TOTAL_CHARS) end_char = FONT_TOTAL_CHARS;
    
    /* 计算居中偏移 */
    int total_w = FONT_CHARS_PER_LINE * FONT_CHAR_WIDTH;
    int start_x = (VIEWER_WIDTH - total_w) / 2;
    int start_y = 20;
    
    /* 白色前景，黑色背景 */
    Uint32 fg_color = (0xFF << 24) | (0xFF << 16) | (0xFF << 8) | 0xFF;
    Uint32 bg_color = (0xFF << 24) | (0 << 16) | (0 << 8) | 0;
    
    for (int i = start_char; i < end_char; i++) {
        int local_idx = i - start_char;
        int col = local_idx % FONT_CHARS_PER_LINE;
        int row = local_idx / FONT_CHARS_PER_LINE;
        
        int char_x = start_x + col * FONT_CHAR_WIDTH;
        int char_y = start_y + row * FONT_CHAR_HEIGHT;
        
        /* 每个字符32字节 (16行 x 2字节) */
        const byte* cdata = font_data + i * 32;
        
        for (int cy = 0; cy < FONT_CHAR_HEIGHT; cy++) {
            /* 大端字节序 */
            word bits = (cdata[cy * 2] << 8) | cdata[cy * 2 + 1];
            
            for (int cx = 0; cx < FONT_CHAR_WIDTH; cx++) {
                int px = char_x + cx;
                int py = char_y + cy;
                
                if (px >= 0 && px < VIEWER_WIDTH && py >= 0 && py < VIEWER_HEIGHT) {
                    if (bits & (1 << (15 - cx))) {
                        g_pixels[py * VIEWER_WIDTH + px] = fg_color;
                    } else {
                        g_pixels[py * VIEWER_WIDTH + px] = bg_color;
                    }
                }
            }
        }
    }
    
    /* 高亮选中字符 */
    if (g_sub_index >= 0 && g_sub_index < FONT_CHARS_PER_PAGE) {
        int global_idx = start_char + g_sub_index;
        if (global_idx < FONT_TOTAL_CHARS) {
            int local_idx = g_sub_index;
            int col = local_idx % FONT_CHARS_PER_LINE;
            int row = local_idx / FONT_CHARS_PER_LINE;
            
            int x = start_x + col * FONT_CHAR_WIDTH;
            int y = start_y + row * FONT_CHAR_HEIGHT;
            
            Uint32 yellow = (0xFF << 24) | (0xFF << 16) | (0xFF << 8) | 0x00;
            
            /* 黄色边框 */
            for (int i = 0; i < FONT_CHAR_WIDTH; i++) {
                if (x + i >= 0 && x + i < VIEWER_WIDTH && y >= 0 && y < VIEWER_HEIGHT)
                    g_pixels[y * VIEWER_WIDTH + x + i] = yellow;
                if (x + i >= 0 && x + i < VIEWER_WIDTH && y + FONT_CHAR_HEIGHT - 1 < VIEWER_HEIGHT)
                    g_pixels[(y + FONT_CHAR_HEIGHT - 1) * VIEWER_WIDTH + x + i] = yellow;
            }
            for (int i = 0; i < FONT_CHAR_HEIGHT; i++) {
                if (x >= 0 && x < VIEWER_WIDTH && y + i >= 0 && y + i < VIEWER_HEIGHT)
                    g_pixels[(y + i) * VIEWER_WIDTH + x] = yellow;
                if (x + FONT_CHAR_WIDTH - 1 < VIEWER_WIDTH && y + i >= 0 && y + i < VIEWER_HEIGHT)
                    g_pixels[(y + i) * VIEWER_WIDTH + x + FONT_CHAR_WIDTH - 1] = yellow;
            }
        }
    }
}

/* 更新纹理 */
static void update_texture(void) {
    SDL_UpdateTexture(g_texture, NULL, g_pixels, VIEWER_WIDTH * sizeof(Uint32));
    SDL_RenderClear(g_renderer);
    SDL_RenderCopy(g_renderer, g_texture, NULL, NULL);
    SDL_RenderPresent(g_renderer);
}

/* ========================================================================
 * 资源加载和显示
 * ======================================================================== */

/* 加载主调色板为RGB24 */
static int load_main_palette_rgb24(byte* out_rgb24) {
    fdother_palette_t pal;
    /* 修正：始终使用索引0的主调色板 */
    int ret = fdother_get_palette(0, &pal);
    if (ret != 0) return -1;
    
    fdother_palette_to_rgb24(&pal, out_rgb24);
    return 0;
}

/* 加载并解码Tile图像 */
static int load_and_decode_tile_image(int index, byte* out_pixels, 
                                       word* out_w, word* out_h) {
    fdother_tile_t tile;
    int ret = fdother_get_tile(index, &tile);
    if (ret != 0) return -1;
    
    if (out_w) *out_w = tile.width;
    if (out_h) *out_h = tile.height;
    
    ret = fdother_decode_tile(&tile, out_pixels);
    return ret;
}

/* 当前资源加载和显示 */
static void refresh_display(void) {
    dword res_size;
    const byte* res_data = fdother_get_resource(g_current_index, &res_size);
    
    if (!res_data || res_size == 0) {
        printf("资源 %d: 无数据\n", g_current_index);
        return;
    }
    
    g_current_type = fdother_get_resource_type(res_data, res_size);
    g_sub_index = 0;
    g_max_sub_items = 0;
    g_decode_width = 0;
    g_decode_height = 0;
    
    byte palette_rgb24[768];
    
    /* 统一使用索引0的主调色板 */
    int pal_ret = fdother_get_palette(0, (fdother_palette_t*)palette_rgb24);
    if (pal_ret == 0) {
        fdother_palette_t pal;
        if (fdother_get_palette(0, &pal) == 0) {
            fdother_palette_to_rgb24(&pal, palette_rgb24);
        }
    }
    
    switch (g_current_type) {
        case FDOTHER_RES_TYPE_PALETTE: {
            if (pal_ret == 0) {
                draw_palette_view(palette_rgb24);
                g_max_sub_items = 256;
            }
            break;
        }
        
        case FDOTHER_RES_TYPE_TILE: {
            fdother_tile_t tile;
            if (fdother_parse_tile(res_data, res_size, &tile) == 0) {
                /* 清零解码缓冲区，确保SKIP操作对应的位置为0 */
                memset(g_decode_buffer, 0, tile.width * tile.height);
                /* RLE解码时不应用调色板窗口 */
                fd_decompress_rle(tile.rle_data, tile.rle_size, g_decode_buffer, tile.width, tile.height, -1);
                g_decode_width = tile.width;
                g_decode_height = tile.height;
                draw_pixels(g_decode_buffer, tile.width, tile.height, palette_rgb24, tile.palette_window);
            }
            break;
        }
        
        case FDOTHER_RES_TYPE_LMI1: {
            fdother_lmi1_t lmi1;
            if (fdother_get_lmi1(g_current_index, &lmi1) == 0) {
                g_max_sub_items = lmi1.tile_count;
                
                /* 显示第一个tile */
                if (g_sub_index < lmi1.tile_count) {
                    word w, h;
                    const byte* rle_data;
                    dword rle_size;
                    
                    if (fdother_lmi1_get_tile(&lmi1, g_sub_index, &w, &h, &rle_data, &rle_size) == 0) {
                        memset(g_decode_buffer, 0, w * h);
                        /* LMI1 tile没有palette_window头，直接使用RLE数据 */
                        fd_decompress_rle(rle_data, rle_size, g_decode_buffer, w, h, -1);
                        g_decode_width = w;
                        g_decode_height = h;
                        draw_pixels(g_decode_buffer, w, h, palette_rgb24, 0);
                    }
                }
            }
            break;
        }
        
        case FDOTHER_RES_TYPE_NESTED_DAT: {
            fdother_nested_dat_t nested;
            if (fdother_get_nested_dat(g_current_index, &nested) == 0) {
                g_max_sub_items = nested.resource_count;
                
                /* 显示第一个子资源 */
                if (g_sub_index < (int)nested.resource_count) {
                    dword sub_size;
                    const byte* sub_data = fdother_nested_get_resource(&nested, g_sub_index, &sub_size);
                    
                    if (sub_data && sub_size > 0 && sub_size < res_size) {
                        fdother_res_type_t sub_type = fdother_get_resource_type(sub_data, sub_size);
                        
                        if (sub_type == FDOTHER_RES_TYPE_TILE) {
                            fdother_tile_t tile;
                            if (fdother_parse_tile(sub_data, sub_size, &tile) == 0) {
                                if (tile.rle_data && tile.rle_size > 0 && tile.rle_size < sub_size) {
                                    /* 清零解码缓冲区 */
                                    memset(g_decode_buffer, 0, tile.width * tile.height);
                                    /* RLE解码时不应用调色板窗口 */
                                    fd_decompress_rle(tile.rle_data, tile.rle_size, g_decode_buffer, tile.width, tile.height, -1);
                                    g_decode_width = tile.width;
                                    g_decode_height = tile.height;
                                    draw_pixels(g_decode_buffer, tile.width, tile.height, palette_rgb24, tile.palette_window);
                                }
                            }
                        }
                    }
                }
            }
            break;
        }
        
        case FDOTHER_RES_TYPE_RAW: {
            /* RAW数据 - 检查是否为字体资源 (索引4) */
            if (g_current_index == 4) {
                /* 索引4是字体资源 (1824字符, 16x16位图) */
                g_max_sub_items = FONT_CHARS_PER_PAGE;
                draw_font_view(res_data);
            } else if (g_current_index == 2) {
                /* 索引2是偏移表 (9419子资源) */
                if (!g_offset_table_loaded) {
                    if (fdother_parse_offset_table(2, &g_offset_table) == 0) {
                        g_offset_table_loaded = true;
                        g_max_sub_items = g_offset_table.offset_count - 1;
                        printf("偏移表加载成功: %u个偏移, %u个子资源\n", 
                               g_offset_table.offset_count, g_max_sub_items);
                    }
                }
                
                if (g_offset_table_loaded && g_sub_index < g_max_sub_items) {
                    dword sub_size;
                    const byte* sub_data = fdother_offset_table_get_resource(&g_offset_table, g_sub_index, &sub_size);
                    
                    if (sub_data && sub_size > 0) {
                        /* 尝试解析为TILE */
                        fdother_tile_t tile;
                        if (fdother_parse_tile(sub_data, sub_size, &tile) == 0) {
                            if (tile.rle_data && tile.rle_size > 0 && tile.rle_size < sub_size) {
                                /* 清零解码缓冲区 */
                                memset(g_decode_buffer, 0, tile.width * tile.height);
                                /* RLE解码时不应用调色板窗口 */
                                fd_decompress_rle(tile.rle_data, tile.rle_size, g_decode_buffer, tile.width, tile.height, -1);
                                g_decode_width = tile.width;
                                g_decode_height = tile.height;
                                draw_pixels(g_decode_buffer, tile.width, tile.height, palette_rgb24, tile.palette_window);
                            }
                        }
                    }
                }
            } else {
                /* 其他RAW数据显示为信息 */
                clear_pixels();
                g_max_sub_items = 0;
            }
            break;
        }
    }
    
    update_texture();
}

/* 打印资源信息 */
static void print_resource_info(void) {
    dword res_size;
    const byte* res_data = fdother_get_resource(g_current_index, &res_size);
    
    if (!res_data || res_size == 0) {
        printf("\n=== 资源 %d: 无数据 ===\n\n", g_current_index);
        return;
    }
    
    g_current_type = fdother_get_resource_type(res_data, res_size);
    
    printf("\n=== 资源 %d [%s] ===\n", g_current_index, get_type_name(g_current_type));
    printf("描述: %s\n", get_resource_desc(g_current_index));
    printf("大小: %u 字节\n", res_size);
    printf("子项: %d / %d\n", g_sub_index, g_max_sub_items);
    
    switch (g_current_type) {
        case FDOTHER_RES_TYPE_PALETTE:
            printf("类型: 调色板 (256颜色)\n");
            break;
            
        case FDOTHER_RES_TYPE_TILE: {
            fdother_tile_t tile;
            if (fdother_get_tile(g_current_index, &tile) == 0) {
                printf("类型: Tile图像\n");
                printf("尺寸: %dx%d\n", tile.width, tile.height);
                printf("调色板窗口: %d\n", tile.palette_window);
                printf("RLE数据: %u 字节\n", tile.rle_size);
            }
            break;
        }
            
        case FDOTHER_RES_TYPE_LMI1: {
            fdother_lmi1_t lmi1;
            if (fdother_get_lmi1(g_current_index, &lmi1) == 0) {
                printf("类型: LMI1 Tile集\n");
                printf("Tile数量: %d\n", lmi1.tile_count);
                printf("总大小: %u 字节\n", lmi1.size);
            }
            break;
        }
            
        case FDOTHER_RES_TYPE_NESTED_DAT: {
            fdother_nested_dat_t nested;
            if (fdother_get_nested_dat(g_current_index, &nested) == 0) {
                printf("类型: 嵌套DAT\n");
                printf("子资源数量: %d\n", nested.resource_count);
                printf("总大小: %u 字节\n", nested.size);
            }
            break;
        }
            
        case FDOTHER_RES_TYPE_RAW:
            printf("类型: RAW数据\n");
            if (g_current_index == 4) {
                printf("字体: %d 字符 (16x16位图)\n", FONT_TOTAL_CHARS);
                printf("页: %d / %d (每页%d字符)\n", g_font_page, FONT_PAGE_COUNT - 1, FONT_CHARS_PER_PAGE);
            } else if (g_current_index == 2) {
                if (g_offset_table_loaded) {
                    printf("偏移表: %u个偏移\n", g_offset_table.offset_count);
                    printf("子资源: %d / %d\n", g_sub_index, g_max_sub_items);
                    
                    dword sub_size;
                    const byte* sub_data = fdother_offset_table_get_resource(&g_offset_table, g_sub_index, &sub_size);
                    if (sub_data && sub_size > 0) {
                        printf("当前子资源大小: %u字节\n", sub_size);
                        fdother_tile_t tile;
                        if (fdother_parse_tile(sub_data, sub_size, &tile) == 0) {
                            printf("子资源类型: Tile图像 %dx%d\n", tile.width, tile.height);
                            printf("调色板窗口: %d, 头大小: %d\n", tile.palette_window, tile.header_size);
                        }
                    }
                } else {
                    printf("偏移表加载失败\n");
                }
            }
            break;
    }
    
    printf("\n");
}

/* ========================================================================
 * 主循环
 * ======================================================================== */
static int main_loop(void) {
    int running = 1;
    SDL_Event event;
    
    /* 打印初始信息 */
    print_resource_info();
    
    while (running) {
        while (SDL_PollEvent(&event)) {
            switch (event.type) {
                case SDL_QUIT:
                    running = 0;
                    break;
                    
                case SDL_KEYDOWN:
                    switch (event.key.keysym.sym) {
                        case SDLK_ESCAPE:
                        case SDLK_q:
                            running = 0;
                            break;
                            
                        case SDLK_UP:
                        /* 切换到上一个主资源 */
                        if (g_current_index > 0) {
                            g_current_index--;
                            g_font_page = 0;  /* 重置字体页 */
                            print_resource_info();
                            refresh_display();
                        }
                        break;
                        
                    case SDLK_DOWN:
                        /* 切换到下一个主资源 */
                        if (g_current_index < 102) {
                            g_current_index++;
                            g_font_page = 0;  /* 重置字体页 */
                            print_resource_info();
                            refresh_display();
                        }
                        break;
                        
                    case SDLK_LEFT:
                        /* 切换到上一个子项 */
                        if (g_current_index == 4) {
                            /* 字体资源：切换到上一页 */
                            if (g_font_page > 0) {
                                g_font_page--;
                                g_sub_index = 0;
                                print_resource_info();
                                refresh_display();
                            }
                        } else {
                            if (g_sub_index > 0) {
                                g_sub_index--;
                                print_resource_info();
                                refresh_display();
                            }
                        }
                        break;
                        
                    case SDLK_RIGHT:
                        /* 切换到下一个子项 */
                        if (g_current_index == 4) {
                            /* 字体资源：切换到下一页 */
                            if (g_font_page < FONT_PAGE_COUNT - 1) {
                                g_font_page++;
                                g_sub_index = 0;
                                print_resource_info();
                                refresh_display();
                            }
                        } else {
                            if (g_sub_index < g_max_sub_items - 1) {
                                g_sub_index++;
                                print_resource_info();
                                refresh_display();
                            }
                        }
                        break;
                            
                        case SDLK_SPACE:
                            /* 播放音效 (仅索引31) */
                            if (g_current_index == 31 && g_viewer_sfx_mgr.initialized) {
                                printf("播放音效 %d\n", g_sub_index);
                                fd2_sfx_play(&g_viewer_sfx_mgr, g_sub_index);
                            }
                            break;
                            
                        case SDLK_p:
                            /* 播放/暂停 */
                            if (g_viewer_sfx_mgr.initialized) {
                                fd2_sfx_toggle_mute(&g_viewer_sfx_mgr);
                                printf("音效 %s\n", g_viewer_sfx_mgr.muted ? "静音" : "恢复");
                            }
                            break;
                    }
                    break;
            }
        }
        
        SDL_Delay(16); /* ~60fps */
    }
    
    return 0;
}

/* ========================================================================
 * 入口点
 * ======================================================================== */
int main(int argc, char* argv[]) {
    const char* filepath = "game/FDOTHER.DAT";
    
    if (argc > 1) {
        filepath = argv[1];
    }
    
    printf("=== FDOTHER.DAT Resource Viewer ===\n\n");
    printf("加载文件: %s\n", filepath);
    
    /* 加载FDOTHER.DAT */
    int ret = fdother_load(filepath);
    if (ret != 0) {
        printf("错误: 无法加载 FDOTHER.DAT\n");
        return 1;
    }
    printf("FDOTHER.DAT 加载成功\n");
    
    /* 初始化音效系统 */
    ret = fd2_sfx_init(&g_viewer_sfx_mgr, filepath);
    if (ret == 0) {
        printf("音效系统初始化成功\n");
        /* 加载所有音效 */
        fd2_sfx_load_all(&g_viewer_sfx_mgr);
    } else {
        printf("音效系统初始化失败 (音频不可用)\n");
    }
    
    /* 初始化SDL */
    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        printf("SDL初始化失败: %s\n", SDL_GetError());
        fd2_sfx_shutdown(&g_viewer_sfx_mgr);
        fdother_unload();
        return 1;
    }
    
    /* 创建窗口 */
    g_window = SDL_CreateWindow(
        VIEWER_TITLE,
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
        VIEWER_WIDTH, VIEWER_HEIGHT,
        SDL_WINDOW_SHOWN
    );
    
    if (!g_window) {
        printf("窗口创建失败: %s\n", SDL_GetError());
        SDL_Quit();
        fd2_sfx_shutdown(&g_viewer_sfx_mgr);
        fdother_unload();
        return 1;
    }
    
    /* 创建渲染器 */
    g_renderer = SDL_CreateRenderer(g_window, -1, SDL_RENDERER_ACCELERATED);
    if (!g_renderer) {
        g_renderer = SDL_CreateRenderer(g_window, -1, SDL_RENDERER_SOFTWARE);
    }
    
    if (!g_renderer) {
        printf("渲染器创建失败: %s\n", SDL_GetError());
        SDL_DestroyWindow(g_window);
        SDL_Quit();
        fd2_sfx_shutdown(&g_viewer_sfx_mgr);
        fdother_unload();
        return 1;
    }
    
    /* 创建纹理 */
    g_texture = SDL_CreateTexture(
        g_renderer,
        SDL_PIXELFORMAT_ARGB8888,
        SDL_TEXTUREACCESS_STREAMING,
        VIEWER_WIDTH, VIEWER_HEIGHT
    );
    
    if (!g_texture) {
        printf("纹理创建失败: %s\n", SDL_GetError());
        SDL_DestroyRenderer(g_renderer);
        SDL_DestroyWindow(g_window);
        SDL_Quit();
        fd2_sfx_shutdown(&g_viewer_sfx_mgr);
        fdother_unload();
        return 1;
    }
    
    /* 显示操作说明 */
    printf("\n=== 操作说明 ===\n");
    printf("↑/↓ : 切换资源索引 (0-102)\n");
    printf("←/→ : 切换子项 (或字体页)\n");
    printf("空格 : 播放音效 (索引31)\n");
    printf("P   : 静音/恢复\n");
    printf("Q/ESC: 退出\n\n");
    
    /* 初始显示 */
    refresh_display();
    
    /* 主循环 */
    main_loop();
    
    /* 清理 */
    SDL_DestroyTexture(g_texture);
    SDL_DestroyRenderer(g_renderer);
    SDL_DestroyWindow(g_window);
    SDL_Quit();
    
    fd2_sfx_shutdown(&g_viewer_sfx_mgr);
    fdother_unload();
    
    /* 清理偏移表 */
    if (g_offset_table_loaded) {
        fdother_offset_table_free(&g_offset_table);
        g_offset_table_loaded = false;
    }
    
    printf("\n程序退出\n");
    return 0;
}
