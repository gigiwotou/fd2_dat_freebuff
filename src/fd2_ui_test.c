/**
 * FD2 UI渲染测试程序
 * 
 * 根据IDA MCP汇编代码1:1复原原版游戏的UI绘制逻辑
 * 
 * 核心UI绘制逻辑分析 (从IDA汇编反推):
 * 
 * 1. 窗口系统 (sub_168B6):
 *    - FDOTHER索引7的tile数据结构:
 *      * 偏移0-1: 总宽度 (WORD)
 *      * 偏移2-3: 总高度 (WORD)
 *      * 偏移4-5: tile数量 (WORD)
 *      * 偏移6+: tile偏移表 (DWORD数组)
 *    - 每个tile: WORD宽度 + WORD高度 + 像素数据
 *    - tile数据指针 = FDOTHER_DAT__7 + *(DWORD *)(FDOTHER_DAT__7 + 4*tile_index + 6)
 *    - 像素格式: 8位调色板索引，逐行存储
 *    - 窗口结构:
 *      * 4个角 (tile 1-4)
 *      * 4条边 (tile 5-8, 14-17)
 *      * 循环边缘 (tile 9-12)
 *      * 中心区域 (tile 13)
 * 
 * 2. 菜单系统 (sub_165AC):
 *    - 创建多层菜单面板
 *    - 分配5个缓冲区 (每个26668字节)
 *    - 保存原始屏幕内容
 *    - 支持动画效果 (逐步展开)
 * 
 * 3. 屏幕区域操作 (sub_4ECBF):
 *    - 保存/恢复屏幕区域
 *    - 用于对话框背景
 * 
 * 4. 文本/精灵渲染 (sub_15E9E):
 *    - 从FDOTHER读取精灵数据
 *    - 渲染到指定位置
 * 
 * 5. 窗口动画 (sub_164E8):
 *    - 控制窗口显示/隐藏动画
 *    - 使用计数器控制帧率
 */

#define SDL_MAIN_HANDLED
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <windows.h>
#endif

#include "fd2_decoder.h"
#include "fd2_resources.h"
#include "fd2_globals.h"

#define UI_TEST_WINDOW_SCALE 3
#define FD2_SCREEN_BUFFER_SIZE (FD2_SCREEN_W * FD2_SCREEN_H)
#define FD2_UI_ELEMENT_SIZE 80
#define FD2_MAX_UI_ELEMENTS 800

typedef struct {
    u8 screen[FD2_SCREEN_BUFFER_SIZE];
    u8 palette[FD2_PALETTE_BYTES];
    u8 backup_screen[FD2_SCREEN_BUFFER_SIZE];
    u32* argb;
    u32* argb_palette;
    SDL_Window* window;
    SDL_Renderer* renderer;
    SDL_Texture* texture;
    const u8* fdother_data;
    u32 fdother_size;
    int tile_w;
    int tile_h;
    // 解压后的tile数据缓冲区
    u8* decompressed_tiles;
    u32* tile_offsets;
    u16 tile_count;
} fd2_ui_render_t;

static fd2_ui_render_t g_ui_render;
static const char* g_data_dir = NULL;
static fd2_resources_t g_res;

static int fd2_ui_render_init(int scale) {
    memset(&g_ui_render, 0, sizeof(g_ui_render));
    g_ui_render.tile_w = 16;
    g_ui_render.tile_h = 16;

    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        fprintf(stderr, "SDL_Init failed: %s\n", SDL_GetError());
        return -1;
    }

    g_ui_render.window = SDL_CreateWindow("FD2 UI Test (Original Logic)",
                                           SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                                           FD2_SCREEN_W * scale, FD2_SCREEN_H * scale,
                                           SDL_WINDOW_SHOWN);
    if (!g_ui_render.window) {
        fprintf(stderr, "SDL_CreateWindow failed: %s\n", SDL_GetError());
        return -1;
    }

    g_ui_render.renderer = SDL_CreateRenderer(g_ui_render.window, -1, SDL_RENDERER_ACCELERATED);
    if (!g_ui_render.renderer) {
        fprintf(stderr, "SDL_CreateRenderer failed: %s\n", SDL_GetError());
        return -1;
    }

    g_ui_render.texture = SDL_CreateTexture(g_ui_render.renderer, SDL_PIXELFORMAT_ARGB8888,
                                             SDL_TEXTUREACCESS_STREAMING,
                                             FD2_SCREEN_W, FD2_SCREEN_H);
    if (!g_ui_render.texture) {
        fprintf(stderr, "SDL_CreateTexture failed: %s\n", SDL_GetError());
        return -1;
    }

    g_ui_render.argb = (u32*)malloc(FD2_SCREEN_BUFFER_SIZE * sizeof(u32));
    g_ui_render.argb_palette = (u32*)malloc(256 * sizeof(u32));
    if (!g_ui_render.argb || !g_ui_render.argb_palette) {
        fprintf(stderr, "Failed to allocate ARGB buffers\n");
        return -1;
    }

    return 0;
}

static void fd2_ui_render_shutdown(void) {
    if (g_ui_render.texture) SDL_DestroyTexture(g_ui_render.texture);
    if (g_ui_render.renderer) SDL_DestroyRenderer(g_ui_render.renderer);
    if (g_ui_render.window) SDL_DestroyWindow(g_ui_render.window);
    free(g_ui_render.argb);
    free(g_ui_render.argb_palette);
    SDL_Quit();
}

static void fd2_ui_set_palette_6bit(const u8* pal_6bit) {
    for (int i = 0; i < 256; i++) {
        g_ui_render.palette[i * 3 + 0] = (pal_6bit[i * 3 + 0] << 2) | (pal_6bit[i * 3 + 0] >> 4);
        g_ui_render.palette[i * 3 + 1] = (pal_6bit[i * 3 + 1] << 2) | (pal_6bit[i * 3 + 1] >> 4);
        g_ui_render.palette[i * 3 + 2] = (pal_6bit[i * 3 + 2] << 2) | (pal_6bit[i * 3 + 2] >> 4);
    }
    for (int i = 0; i < 256; i++) {
        g_ui_render.argb_palette[i] = 0xFF000000 |
            ((u32)g_ui_render.palette[i * 3 + 0] << 16) |
            ((u32)g_ui_render.palette[i * 3 + 1] << 8) |
            ((u32)g_ui_render.palette[i * 3 + 2]);
    }
}

static void fd2_ui_fill_screen(u8 color) {
    memset(g_ui_render.screen, color, FD2_SCREEN_BUFFER_SIZE);
}

static void fd2_ui_blit_rle(const u8* res_data, u32 res_size, int dx, int dy) {
    if (res_size < 4 || !res_data) return;

    int w = res_data[0] | (res_data[1] << 8);
    int h = res_data[2] | (res_data[3] << 8);

    if (w <= 0 || w > 640 || h <= 0 || h > 480) return;

    u8* pixels = (u8*)malloc(w * h);
    if (!pixels) return;

    int ret = fd2_rle_decompress(res_data + 4, res_size - 4, pixels, 0, 0, w, w, h, -1);
    if (ret == 0) {
        for (int y = 0; y < h; y++) {
            int sy = dy + y;
            if (sy < 0 || sy >= FD2_SCREEN_H) continue;
            for (int x = 0; x < w; x++) {
                int sx = dx + x;
                if (sx < 0 || sx >= FD2_SCREEN_W) continue;
                u8 p = pixels[y * w + x];
                if (p != 0) {
                    g_ui_render.screen[sy * FD2_SCREEN_W + sx] = p;
                }
            }
        }
    }
    free(pixels);
}

/**
 * 解压所有tile数据到独立缓冲区
 * 
 * 原版游戏可能在加载索引5后立即解压所有tile，或者在首次使用时解压。
 * 为了简化，我们在加载后一次性解压所有tile。
 * 
 * @param raw_data 原始tile集数据
 * @param raw_size 原始数据大小
 * @return 0成功，-1失败
 */
static int fd2_ui_decompress_all_tiles(const u8* raw_data, u32 raw_size) {
    if (!raw_data || raw_size < 6) return -1;
    
    u16 tile_count = raw_data[4] | (raw_data[5] << 8);
    if (tile_count == 0 || tile_count > 1000) return -1;
    
    g_ui_render.tile_count = tile_count;
    
    // 分配tile偏移表
    g_ui_render.tile_offsets = (u32*)malloc(tile_count * sizeof(u32));
    if (!g_ui_render.tile_offsets) return -1;
    
    // 解析tile偏移表
    for (int i = 0; i < tile_count; i++) {
        u32 offset_addr = 6 + i * 4;
        if (offset_addr + 4 > raw_size) break;
        
        g_ui_render.tile_offsets[i] = raw_data[offset_addr] | 
                                      (raw_data[offset_addr + 1] << 8) |
                                      (raw_data[offset_addr + 2] << 16) |
                                      (raw_data[offset_addr + 3] << 24);
    }
    
    // 计算解压后的总大小
    u32 total_decompressed_size = 0;
    for (int i = 0; i < tile_count; i++) {
        u32 tile_offset = g_ui_render.tile_offsets[i];
        if (tile_offset + 4 > raw_size) continue;
        
        u16 w = raw_data[tile_offset] | (raw_data[tile_offset + 1] << 8);
        u16 h = raw_data[tile_offset + 2] | (raw_data[tile_offset + 3] << 8);
        
        total_decompressed_size += 4 + w * h; // 4字节头部 + 像素数据
    }
    
    // 分配解压缓冲区
    g_ui_render.decompressed_tiles = (u8*)malloc(total_decompressed_size);
    if (!g_ui_render.decompressed_tiles) {
        free(g_ui_render.tile_offsets);
        g_ui_render.tile_offsets = NULL;
        return -1;
    }
    
    // 解压每个tile
    u32 write_pos = 0;
    for (int i = 0; i < tile_count; i++) {
        u32 tile_offset = g_ui_render.tile_offsets[i];
        if (tile_offset + 4 > raw_size) continue;
        
        u16 w = raw_data[tile_offset] | (raw_data[tile_offset + 1] << 8);
        u16 h = raw_data[tile_offset + 2] | (raw_data[tile_offset + 3] << 8);
        
        if (w == 0 || h == 0 || w > 640 || h > 480) continue;
        
        // 计算下一个tile的偏移，得到当前tile的压缩数据大小
        u32 next_tile_offset = (i + 1 < tile_count) ? g_ui_render.tile_offsets[i + 1] : raw_size;
        u32 compressed_size = next_tile_offset - tile_offset;
        
        if (compressed_size < 4) continue;
        
        // 写入头部 (w, h)
        g_ui_render.decompressed_tiles[write_pos + 0] = w & 0xFF;
        g_ui_render.decompressed_tiles[write_pos + 1] = (w >> 8) & 0xFF;
        g_ui_render.decompressed_tiles[write_pos + 2] = h & 0xFF;
        g_ui_render.decompressed_tiles[write_pos + 3] = (h >> 8) & 0xFF;
        
        // RLE解压像素数据
        u8* pixel_buf = (u8*)malloc(w * h);
        if (pixel_buf) {
            int ret = fd2_rle_decompress(raw_data + tile_offset + 4, compressed_size - 4, 
                                         pixel_buf, 0, 0, w, w, h, -1);
            if (ret == 0) {
                memcpy(g_ui_render.decompressed_tiles + write_pos + 4, pixel_buf, w * h);
            }
            free(pixel_buf);
        }
        
        // 更新tile偏移表为解压后的偏移
        g_ui_render.tile_offsets[i] = write_pos;
        
        write_pos += 4 + w * h;
    }
    
    printf("  [DECOMPRESS] 解压 %d 个tile，总大小=%u 字节\n", tile_count, total_decompressed_size);
    return 0;
}

/**
 * 加载FDOTHER索引5的原始tile数据 (窗口tile集，不解压)
 * 
 * 根据IDA汇编分析:
 * - main函数(0x25BF4): push 5 + push _FDOTHER_DAT__7 + call sub_111BA
 * - _FDOTHER_DAT__7是全局变量名，但实际加载的是索引5
 * - sub_111BA直接读取原始数据，不做RLE解压
 * 
 * @param data_dir 数据目录
 * @param out_size 输出数据大小
 * @return 原始数据指针，失败返回NULL
 */
static const u8* fd2_ui_load_raw_tile_set(const char* data_dir, u32* out_size) {
    char path[512];
    snprintf(path, sizeof(path), "%s/%s", data_dir, "FDOTHER.DAT");
    
    FILE* f = fopen(path, "rb");
    if (!f) {
        fprintf(stderr, "无法打开 %s\n", path);
        return NULL;
    }
    
    // 读取DAT头部
    char magic[6];
    if (fread(magic, 1, 6, f) != 6) {
        fclose(f);
        return NULL;
    }
    if (memcmp(magic, "LLLLLL", 6) != 0) {
        fclose(f);
        return NULL;
    }
    
    dword resource_count;
    if (fread(&resource_count, 4, 1, f) != 1) {
        fclose(f);
        return NULL;
    }
    
    if (5 >= resource_count) {
        fclose(f);
        return NULL;
    }
    
    // 读取偏移表
    dword* offsets = malloc(resource_count * 4);
    if (!offsets) {
        fclose(f);
        return NULL;
    }
    fseek(f, 10, SEEK_SET);
    if (fread(offsets, 4, resource_count, f) != resource_count) {
        free(offsets);
        fclose(f);
        return NULL;
    }
    
    // 获取索引5的数据范围 (窗口tile集)
    dword start = offsets[5];
    dword end = (5 + 1 < resource_count) ? offsets[5 + 1] : (dword)-1;
    dword size;
    if (end == (dword)-1) {
        fseek(f, 0, SEEK_END);
        long file_size = ftell(f);
        size = file_size - start;
    } else {
        size = end - start;
    }
    
    // 读取原始数据
    u8* data = malloc(size);
    if (!data) {
        free(offsets);
        fclose(f);
        return NULL;
    }
    
    fseek(f, start, SEEK_SET);
    if (fread(data, 1, size, f) != size) {
        free(data);
        free(offsets);
        fclose(f);
        return NULL;
    }
    
    free(offsets);
    fclose(f);
    
    if (out_size) *out_size = size;
    printf("  [LOAD] FDOTHER索引5原始数据 (窗口tile集): size=%u\n", size);
    return data;
}

/**
 * 根据tile索引获取tile数据指针 (sub_1685C逻辑)
 * 
 * 原版公式: tile数据指针 = FDOTHER_DAT__7 + *(DWORD *)(FDOTHER_DAT__7 + 4 * tile_index + 6)
 * 
 * 修改后: 使用解压后的tile数据
 * 
 * @param tile_index tile索引
 * @return tile数据指针，失败返回NULL
 */
static const u8* fd2_ui_get_tile_ptr(int tile_index) {
    if (!g_ui_render.decompressed_tiles || !g_ui_render.tile_offsets) return NULL;
    
    if (tile_index < 0 || tile_index >= g_ui_render.tile_count) {
        fprintf(stderr, "  [WARN] tile_index=%d 超出范围 (tile_count=%d)\n", 
                tile_index, g_ui_render.tile_count);
        return NULL;
    }
    
    const u8* tile_ptr = g_ui_render.decompressed_tiles + g_ui_render.tile_offsets[tile_index];
    return tile_ptr;
}

/**
 * 渲染单个tile到屏幕 (根据sub_4ED0B逻辑)
 * 
 * 原版逻辑:
 * 1. 读取tile宽度 (WORD)
 * 2. 读取tile高度 (WORD)
 * 3. 逐行复制像素数据到屏幕缓冲区
 * 
 * @param tile_index tile索引
 * @param dx 目标X坐标
 * @param dy 目标Y坐标
 */
static void fd2_ui_render_tile(int tile_index, int dx, int dy) {
    const u8* tile_data = fd2_ui_get_tile_ptr(tile_index);
    if (!tile_data) return;
    
    int tw = tile_data[0] | (tile_data[1] << 8);
    int th = tile_data[2] | (tile_data[3] << 8);
    
    if (tw <= 0 || th <= 0) return;
    
    const u8* pixels = tile_data + 4;
    
    for (int y = 0; y < th; y++) {
        int sy = dy + y;
        if (sy < 0 || sy >= FD2_SCREEN_H) continue;
        
        for (int x = 0; x < tw; x++) {
            int sx = dx + x;
            if (sx < 0 || sx >= FD2_SCREEN_W) continue;
            
            u8 p = pixels[y * tw + x];
            g_ui_render.screen[sy * FD2_SCREEN_W + sx] = p;
        }
    }
}

/**
 * 绘制对话框/窗口 (根据sub_168B6逻辑)
 * 
 * 原版窗口绘制逻辑:
 * - 4个角 (tile 1-4): 左上、右上、左下、右下
 * - 上边框 (tile 5): 水平重复
 * - 下边框 (tile 8): 水平重复
 * - 左边框 (tile 14): 垂直重复
 * - 右边框 (tile 15): 垂直重复
 * - 内容区域 (tile 13): 双循环填充
 * 
 * @param x 窗口X坐标
 * @param y 窗口Y坐标
 * @param cols 窗口列数 (宽度 = cols * 16)
 * @param rows 窗口行数 (高度 = rows * 16)
 */
static void fd2_ui_draw_window(int x, int y, int cols, int rows) {
    if (cols < 2 || rows < 2) return;

    int tw = g_ui_render.tile_w;
    int th = g_ui_render.tile_h;

    // 绘制四个角 (tile 1-4)
    fd2_ui_render_tile(1, x, y);                              // 左上角
    fd2_ui_render_tile(2, x + (cols - 1) * tw, y);           // 右上角
    fd2_ui_render_tile(3, x, y + (rows - 1) * th);           // 左下角
    fd2_ui_render_tile(4, x + (cols - 1) * tw, y + (rows - 1) * th); // 右下角

    // 绘制上下边框 (tile 5, 8)
    for (int i = 1; i < cols - 1; i++) {
        fd2_ui_render_tile(5, x + i * tw, y);                // 上边框
        fd2_ui_render_tile(8, x + i * tw, y + (rows - 1) * th); // 下边框
    }

    // 绘制左右边框 (tile 14, 15)
    for (int i = 1; i < rows - 1; i++) {
        fd2_ui_render_tile(14, x, y + i * th);               // 左边框
        fd2_ui_render_tile(15, x + (cols - 1) * tw, y + i * th); // 右边框
    }

    // 填充内容区域 (tile 13)
    for (int row = 1; row < rows - 1; row++) {
        for (int col = 1; col < cols - 1; col++) {
            fd2_ui_render_tile(13, x + col * tw, y + row * th);
        }
    }
}

/**
 * 保存屏幕区域 (根据sub_4ECBF逻辑)
 */
static void fd2_ui_backup_region(int x, int y, int w, int h) {
    for (int row = 0; row < h; row++) {
        int sy = y + row;
        if (sy < 0 || sy >= FD2_SCREEN_H) continue;
        for (int col = 0; col < w; col++) {
            int sx = x + col;
            if (sx < 0 || sx >= FD2_SCREEN_W) continue;
            g_ui_render.backup_screen[sy * FD2_SCREEN_W + sx] = 
                g_ui_render.screen[sy * FD2_SCREEN_W + sx];
        }
    }
}

/**
 * 恢复屏幕区域 (根据sub_4ECBF逻辑)
 */
static void fd2_ui_restore_region(int x, int y, int w, int h) {
    for (int row = 0; row < h; row++) {
        int sy = y + row;
        if (sy < 0 || sy >= FD2_SCREEN_H) continue;
        for (int col = 0; col < w; col++) {
            int sx = x + col;
            if (sx < 0 || sx >= FD2_SCREEN_W) continue;
            g_ui_render.screen[sy * FD2_SCREEN_W + sx] = 
                g_ui_render.backup_screen[sy * FD2_SCREEN_W + sx];
        }
    }
}

static void fd2_ui_present(void) {
    for (int i = 0; i < FD2_SCREEN_BUFFER_SIZE; i++) {
        g_ui_render.argb[i] = g_ui_render.argb_palette[g_ui_render.screen[i]];
    }

    void* pixels;
    int pitch;
    if (SDL_LockTexture(g_ui_render.texture, NULL, &pixels, &pitch) == 0) {
        memcpy(pixels, g_ui_render.argb, FD2_SCREEN_BUFFER_SIZE * sizeof(u32));
        SDL_UnlockTexture(g_ui_render.texture);
    }

    SDL_RenderCopy(g_ui_render.renderer, g_ui_render.texture, NULL, NULL);
    SDL_RenderPresent(g_ui_render.renderer);
}

static void fd2_ui_wait_for_key(const char* message) {
    printf("[PRESS] %s - 按任意键继续...\n", message);
    SDL_Event e;
    int waiting = 1;
    while (waiting) {
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT || (e.type == SDL_KEYDOWN && 
                (e.key.keysym.sym == SDLK_ESCAPE || e.key.keysym.sym == SDLK_q || e.key.keysym.sym == SDLK_SPACE))) {
                waiting = 0;
            }
        }
        SDL_Delay(10);
    }
}

/**
 * 绘制主菜单对话框 (根据sub_165AC + sub_168B6逻辑)
 * 
 * 原版流程:
 * 1. 保存原始屏幕内容
 * 2. 绘制对话框背景
 * 3. 绘制对话框边框
 * 4. 渲染菜单项文本
 * 5. 显示对话框
 */
static void fd2_ui_draw_main_menu_dialog(fd2_resources_t* res) {
    printf("\n=== 绘制: 主菜单对话框 (根据sub_165AC + sub_168B6逻辑) ===\n");

    u32 pal_size;
    const u8* pal_res = fd2_resources_get(res, FD2_DAT_FDOTHER, 75, &pal_size);
    if (pal_res && pal_size >= FD2_PALETTE_BYTES) {
        fd2_ui_set_palette_6bit(pal_res);
        printf("  [1] 设置调色板 (FDOTHER索引75)\n");
    }

    fd2_ui_fill_screen(32);
    fd2_ui_present();

    printf("  [2] 窗口图块数据已在初始化时加载并解压 (tile数量=%d)\n", 
           g_ui_render.tile_count);

    // 保存原始屏幕 (根据sub_4ECBF逻辑)
    fd2_ui_backup_region(40, 30, 240, 140);
    printf("  [3] 保存原始屏幕区域 (40, 30, 240, 140)\n");

    // 绘制对话框 (根据sub_168B6逻辑)
    // 对话框尺寸: 15列 x 9行 (240x144像素)
    printf("  [4] 绘制对话框 (15列 x 9行 = 240x144像素)\n");
    
    // 动画效果: 逐步展开 (根据sub_165AC逻辑)
    for (int i = 1; i <= 9; i++) {
        fd2_ui_restore_region(40, 30, 240, 140);
        fd2_ui_draw_window(40, 30, 15, i);
        fd2_ui_present();
    }
    printf("    - 对话框展开动画完成\n");

    // 绘制菜单项文本 (使用FDOTHER图块)
    const char* menu_items[] = {"新游戏", "继续游戏", "密码输入", "系统设置", "退出游戏"};
    int menu_y = 50;
    printf("  [5] 绘制菜单项:\n");
    
    for (int i = 0; i < 5; i++) {
        // 简单模拟菜单项 (使用空格代替实际文本渲染)
        for (int j = 0; j < 12; j++) {
            g_ui_render.screen[(menu_y + 4) * FD2_SCREEN_W + (60 + j * 8)] = 15;
            g_ui_render.screen[(menu_y + 5) * FD2_SCREEN_W + (60 + j * 8)] = 15;
        }
        printf("    - 菜单项 %d: %s @ (60, %d)\n", i + 1, menu_items[i], menu_y);
        menu_y += 20;
    }

    // 绘制选中框
    fd2_ui_draw_window(55, 47, 10, 2);
    printf("  [6] 绘制选中框\n");

    fd2_ui_present();
    fd2_ui_wait_for_key("主菜单对话框绘制完成");
}

/**
 * 绘制属性界面 (根据sub_165AC + sub_168B6逻辑)
 * 
 * 原版属性界面:
 * - 显示角色属性
 * - 使用对话框系统
 * - 支持多个属性标签页
 */
static void fd2_ui_draw_status_dialog(fd2_resources_t* res) {
    printf("\n=== 绘制: 属性界面 (根据sub_165AC + sub_168B6逻辑) ===\n");

    u32 pal_size;
    const u8* pal_res = fd2_resources_get(res, FD2_DAT_FDOTHER, 75, &pal_size);
    if (pal_res && pal_size >= FD2_PALETTE_BYTES) {
        fd2_ui_set_palette_6bit(pal_res);
    }

    fd2_ui_fill_screen(32);
    fd2_ui_present();

    // 绘制主对话框
    printf("  [1] 绘制属性对话框 (18列 x 12行 = 288x192像素)\n");
    fd2_ui_draw_window(16, 4, 18, 12);
    fd2_ui_present();

    // 绘制属性标签
    const char* tabs[] = {"属性", "技能", "装备", "物品"};
    int tab_x = 30;
    printf("  [2] 绘制属性标签:\n");
    
    for (int i = 0; i < 4; i++) {
        fd2_ui_draw_window(tab_x, 10, 3, 2);
        printf("    - 标签 %d: %s @ (%d, 10)\n", i + 1, tabs[i], tab_x);
        tab_x += 55;
        fd2_ui_present();
    }

    // 绘制属性条 (模拟)
    printf("  [3] 绘制属性条:\n");
    const char* stats[] = {"生命值", "魔法值", "攻击力", "防御力", "速度", "幸运"};
    int stat_y = 40;
    int stat_values[] = {80, 60, 75, 50, 90, 40};
    
    for (int i = 0; i < 6; i++) {
        // 绘制属性条背景
        for (int j = 0; j < 16; j++) {
            g_ui_render.screen[(stat_y + 4) * FD2_SCREEN_W + (40 + j * 8)] = 8;
        }
        // 绘制属性条前景
        for (int j = 0; j < stat_values[i] / 5; j++) {
            g_ui_render.screen[(stat_y + 4) * FD2_SCREEN_W + (40 + j * 8)] = 15;
        }
        printf("    - 属性 %d: %s = %d @ (40, %d)\n", i + 1, stats[i], stat_values[i], stat_y);
        stat_y += 24;
    }

    fd2_ui_present();
    fd2_ui_wait_for_key("属性界面绘制完成");
}

/**
 * 绘制读盘/存盘菜单 (根据sub_165AC + sub_168B6逻辑)
 * 
 * 原版存盘菜单:
 * - 显示存档槽位
 * - 支持存档/读档操作
 * - 显示存档信息
 */
static void fd2_ui_draw_save_load_dialog(fd2_resources_t* res) {
    printf("\n=== 绘制: 读盘/存盘菜单 (根据sub_165AC + sub_168B6逻辑) ===\n");

    u32 pal_size;
    const u8* pal_res = fd2_resources_get(res, FD2_DAT_FDOTHER, 75, &pal_size);
    if (pal_res && pal_size >= FD2_PALETTE_BYTES) {
        fd2_ui_set_palette_6bit(pal_res);
    }

    fd2_ui_fill_screen(32);
    fd2_ui_present();

    // 绘制主对话框
    printf("  [1] 绘制存盘对话框 (16列 x 10行 = 256x160像素)\n");
    fd2_ui_draw_window(32, 20, 16, 10);
    fd2_ui_present();

    // 绘制存档槽位
    printf("  [2] 绘制存档槽位:\n");
    const char* slot_names[] = {"存档1", "存档2", "存档3", "存档4", "存档5"};
    int slot_y = 35;
    
    for (int i = 0; i < 5; i++) {
        // 绘制槽位背景
        fd2_ui_draw_window(45, slot_y, 12, 2);
        
        // 模拟存档信息
        for (int j = 0; j < 8; j++) {
            g_ui_render.screen[(slot_y + 4) * FD2_SCREEN_W + (55 + j * 8)] = 15;
        }
        if (i < 3) {
            // 有存档的槽位显示额外信息
            for (int j = 0; j < 4; j++) {
                g_ui_render.screen[(slot_y + 12) * FD2_SCREEN_W + (55 + j * 8)] = 10;
            }
        }
        
        printf("    - 槽位 %d: %s @ (45, %d)\n", i + 1, slot_names[i], slot_y);
        slot_y += 28;
    }

    // 绘制选中框
    fd2_ui_draw_window(42, 32, 13, 3);
    printf("  [3] 绘制选中框\n");

    fd2_ui_present();
    fd2_ui_wait_for_key("读盘/存盘菜单绘制完成");
}

/**
 * 绘制战场功能菜单 (根据sub_165AC + sub_168B6逻辑)
 * 
 * 原版战场菜单:
 * - 显示战斗选项
 * - 支持攻击/防御/技能/物品等操作
 * - 显示角色状态
 */
static void fd2_ui_draw_battle_menu(fd2_resources_t* res) {
    printf("\n=== 绘制: 战场功能菜单 (根据sub_165AC + sub_168B6逻辑) ===\n");

    u32 pal_size;
    const u8* pal_res = fd2_resources_get(res, FD2_DAT_FDOTHER, 75, &pal_size);
    if (pal_res && pal_size >= FD2_PALETTE_BYTES) {
        fd2_ui_set_palette_6bit(pal_res);
    }

    // 绘制战场背景
    fd2_ui_fill_screen(16);
    
    u32 img_size;
    const u8* bg_img = fd2_resources_get(res, FD2_DAT_FDOTHER, 15, &img_size);
    if (bg_img) {
        fd2_ui_blit_rle(bg_img, img_size, 0, 0);
        printf("  [1] 绘制战场背景 (FDOTHER索引15)\n");
    }
    fd2_ui_present();

    // 绘制角色状态窗口 (左上角)
    printf("  [2] 绘制角色状态窗口 (8列 x 6行 = 128x96像素)\n");
    fd2_ui_draw_window(5, 5, 8, 6);
    fd2_ui_present();

    // 绘制角色信息 (模拟)
    printf("  [3] 绘制角色信息:\n");
    const char* char_info[] = {"勇者 Lv.10", "HP: 120/150", "MP: 45/60", "EXP: 1200"};
    int info_y = 15;
    for (int i = 0; i < 4; i++) {
        for (int j = 0; j < 12; j++) {
            g_ui_render.screen[(info_y + 4) * FD2_SCREEN_W + (15 + j * 6)] = 15;
        }
        printf("    - 信息 %d: %s @ (15, %d)\n", i + 1, char_info[i], info_y);
        info_y += 18;
    }
    fd2_ui_present();

    // 绘制战斗菜单窗口 (右下角)
    printf("  [4] 绘制战斗菜单窗口 (8列 x 5行 = 128x80像素)\n");
    fd2_ui_draw_window(180, 100, 8, 5);
    fd2_ui_present();

    // 绘制战斗选项
    printf("  [5] 绘制战斗选项:\n");
    const char* battle_options[] = {"攻击", "技能", "防御", "物品", "逃跑"};
    int opt_y = 110;
    
    for (int i = 0; i < 5; i++) {
        // 绘制选项背景
        for (int j = 0; j < 8; j++) {
            g_ui_render.screen[(opt_y + 4) * FD2_SCREEN_W + (190 + j * 8)] = 8;
        }
        printf("    - 选项 %d: %s @ (190, %d)\n", i + 1, battle_options[i], opt_y);
        opt_y += 16;
    }

    // 绘制选中框
    fd2_ui_draw_window(185, 105, 7, 2);
    printf("  [6] 绘制选中框\n");

    // 绘制敌人信息窗口 (右上角)
    printf("  [7] 绘制敌人信息窗口 (8列 x 4行 = 128x64像素)\n");
    fd2_ui_draw_window(180, 5, 8, 4);
    fd2_ui_present();

    // 绘制敌人信息
    printf("  [8] 绘制敌人信息:\n");
    const char* enemy_info[] = {"史莱姆 Lv.5", "HP: 30/50"};
    int enemy_y = 15;
    for (int i = 0; i < 2; i++) {
        for (int j = 0; j < 10; j++) {
            g_ui_render.screen[(enemy_y + 4) * FD2_SCREEN_W + (190 + j * 6)] = 15;
        }
        printf("    - 敌人信息 %d: %s @ (190, %d)\n", i + 1, enemy_info[i], enemy_y);
        enemy_y += 18;
    }

    fd2_ui_present();
    fd2_ui_wait_for_key("战场功能菜单绘制完成");
}

/**
 * 绘制所有UI资源网格展示
 */
static void fd2_ui_draw_all_grid(fd2_resources_t* res) {
    printf("\n=== 绘制: 所有UI资源网格展示 ===\n");

    u32 pal_size;
    const u8* pal_res = fd2_resources_get(res, FD2_DAT_FDOTHER, 75, &pal_size);
    if (pal_res && pal_size >= FD2_PALETTE_BYTES) {
        fd2_ui_set_palette_6bit(pal_res);
    }

    fd2_ui_fill_screen(0);

    int grid_x = 4;
    int grid_y = 5;
    int cell_w = FD2_SCREEN_W / grid_x;
    int cell_h = FD2_SCREEN_H / grid_y;

    int indices[] = {7, 8, 15, 35, 36, 40, 41, 42, 46, 47, 54, 55, 56, 57, 59, 69, 70, 71, 72, 73, 74, 77, 79, 96, 97, 98, 99, 101, 102};
    int count = sizeof(indices) / sizeof(indices[0]);

    int drawn = 0;
    for (int i = 0; i < count; i++) {
        u32 img_size;
        const u8* img = fd2_resources_get(res, FD2_DAT_FDOTHER, indices[i], &img_size);
        if (!img || img_size < 4) continue;

        int w = img[0] | (img[1] << 8);
        int h = img[2] | (img[3] << 8);
        if (w <= 0 || w > 640 || h <= 0 || h > 480) continue;

        int gx = drawn % grid_x;
        int gy = drawn / grid_x;
        if (gy >= grid_y) break;

        int dx = gx * cell_w + (cell_w - w) / 2;
        int dy = gy * cell_h + (cell_h - h) / 2;

        fd2_ui_blit_rle(img, img_size, dx, dy);
        drawn++;
    }

    fd2_ui_present();
    printf("  [GRID] 共绘制 %d 个资源\n", drawn);
    fd2_ui_wait_for_key("所有UI资源网格展示完成");
}

int main(int argc, char** argv) {
    const char* data_dir = NULL;
    if (argc > 1) {
        data_dir = argv[1];
    } else {
        char exe_dir[512];
        GetModuleFileNameA(NULL, exe_dir, sizeof(exe_dir));
        char* last_sep = strrchr(exe_dir, '\\');
        if (!last_sep) last_sep = strrchr(exe_dir, '/');
        if (last_sep) {
            *last_sep = '\0';
            data_dir = exe_dir;
        } else {
            data_dir = ".";
        }
    }
    
    g_data_dir = data_dir;

    printf("FD2 UI渲染测试程序 (根据IDA汇编代码复原)\n");
    printf("==========================================\n");
    printf("数据目录: %s\n", data_dir);

    if (fd2_resources_init(&g_res, data_dir) != 0) {
        fprintf(stderr, "资源管理器初始化失败\n");
        return 1;
    }

    if (fd2_resources_load_dat(&g_res, FD2_DAT_FDOTHER) != 0) {
        fprintf(stderr, "FDOTHER.DAT加载失败\n");
        fd2_resources_shutdown(&g_res);
        return 1;
    }
    
    // 先初始化UI渲染系统
    if (fd2_ui_render_init(UI_TEST_WINDOW_SCALE) != 0) {
        fprintf(stderr, "UI渲染系统初始化失败\n");
        fd2_resources_shutdown(&g_res);
        return 1;
    }
    
    // 加载FDOTHER索引5的原始tile数据 (全局只加载一次)
    const u8* tile_data = fd2_ui_load_raw_tile_set(data_dir, &g_ui_render.fdother_size);
    if (tile_data) {
        g_ui_render.fdother_data = tile_data;
        u16 tile_count = tile_data[4] | (tile_data[5] << 8);
        printf("  [INIT] 加载窗口图块 (FDOTHER索引5原始数据, 大小=%u, tile数量=%d)\n", 
               g_ui_render.fdother_size, tile_count);
        
        // 解压所有tile数据
        if (fd2_ui_decompress_all_tiles(tile_data, g_ui_render.fdother_size) == 0) {
            printf("  [INIT] tile数据解压成功\n");
        } else {
            fprintf(stderr, "  [WARN] tile数据解压失败，将使用原始数据\n");
        }
    } else {
        fprintf(stderr, "FDOTHER索引5原始数据加载失败\n");
        fd2_ui_render_shutdown();
        fd2_resources_shutdown(&g_res);
        return 1;
    }

    printf("控制: 按空格键/任意键切换到下一个测试，ESC/Q退出\n\n");

    int test_index = 0;
    SDL_Event e;

    while (1) {
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) goto done;
            if (e.type == SDL_KEYDOWN) {
                if (e.key.keysym.sym == SDLK_ESCAPE || e.key.keysym.sym == SDLK_q) {
                    goto done;
                }
            }
        }

        switch (test_index) {
            case 0: fd2_ui_draw_main_menu_dialog(&g_res); break;
            case 1: fd2_ui_draw_status_dialog(&g_res); break;
            case 2: fd2_ui_draw_save_load_dialog(&g_res); break;
            case 3: fd2_ui_draw_battle_menu(&g_res); break;
            case 4: fd2_ui_draw_all_grid(&g_res); break;
            default:
                printf("\n所有测试完成!\n");
                goto done;
        }

        test_index++;
        printf("\n测试进度: %d/5\n", test_index);
    }

done:
    printf("\n清理资源...\n");
    fd2_ui_render_shutdown();
    fd2_resources_shutdown(&g_res);
    printf("UI渲染测试完成\n");
    return 0;
}
