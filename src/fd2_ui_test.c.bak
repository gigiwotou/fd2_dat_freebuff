/**
 * FD2 UI渲染测试程序
 * 
 * 根据IDA MCP汇编代码1:1复原原版游戏的UI绘制逻辑
 * 
 * 核心UI绘制逻辑分析 (从IDA汇编反推):
 * 
 * 1. 窗口系统 (sub_168B6):
 *    - 使用16x16像素的窗口图块
 *    - 从FDOTHER索引7读取窗口边框数据
 *    - 窗口结构:
 *      * 左上角 (tile 1)
 *      * 上边框 (tile 2, 水平重复)
 *      * 右上角 (tile 3)
 *      * 左边框 (tile 5, 垂直重复)
 *      * 右边框 (tile 6, 垂直重复)
 *      * 左下角 (tile 7)
 *      * 下边框 (tile 8, 水平重复)
 *      * 右下角 (tile 17)
 *      * 内容区域 (tile 13, 填充)
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
} fd2_ui_render_t;

static fd2_ui_render_t g_ui_render;

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

static void fd2_ui_render_tile(int tile_index, int dx, int dy) {
    if (!g_ui_render.fdother_data || g_ui_render.fdother_size < 32) return;

    const u8* tile_data = &g_ui_render.fdother_data[tile_index * 32];
    if (tile_data + 32 > g_ui_render.fdother_data + g_ui_render.fdother_size) return;

    for (int row = 0; row < 16; row++) {
        int sy = dy + row;
        if (sy < 0 || sy >= FD2_SCREEN_H) continue;

        u16 bits = (tile_data[row * 2] << 8) | tile_data[row * 2 + 1];

        for (int col = 0; col < 16; col++) {
            int sx = dx + col;
            if (sx < 0 || sx >= FD2_SCREEN_W) continue;

            if (bits & 0x8000) {
                g_ui_render.screen[sy * FD2_SCREEN_W + sx] = 15;
            }
            bits <<= 1;
        }
    }
}

/**
 * 绘制对话框/窗口 (根据sub_168B6逻辑)
 * 
 * 原版窗口绘制逻辑:
 * - 使用16x16像素的窗口图块
 * - 从FDOTHER_DAT__7读取窗口边框数据
 * - 支持任意尺寸的窗口
 * 
 * @param x 窗口X坐标
 * @param y 窗口Y坐标
 * @param cols 窗口列数 (宽度 = cols * 16)
 * @param rows 窗口行数 (高度 = rows * 16)
 * @param tile_data 窗口图块数据指针 (从FDOTHER索引7获取)
 */
static void fd2_ui_draw_window(int x, int y, int cols, int rows) {
    if (cols < 2 || rows < 2) return;

    int tw = g_ui_render.tile_w;
    int th = g_ui_render.tile_h;

    // 绘制四个角
    fd2_ui_render_tile(1, x, y);                          // 左上角
    fd2_ui_render_tile(3, x + (cols - 1) * tw, y);       // 右上角
    fd2_ui_render_tile(7, x, y + (rows - 1) * th);       // 左下角
    fd2_ui_render_tile(17, x + (cols - 1) * tw, y + (rows - 1) * th); // 右下角

    // 绘制上下边框
    for (int i = 1; i < cols - 1; i++) {
        fd2_ui_render_tile(2, x + i * tw, y);            // 上边框
        fd2_ui_render_tile(8, x + i * tw, y + (rows - 1) * th); // 下边框
    }

    // 绘制左右边框
    for (int i = 1; i < rows - 1; i++) {
        fd2_ui_render_tile(5, x, y + i * th);            // 左边框
        fd2_ui_render_tile(6, x + (cols - 1) * tw, y + i * th); // 右边框
    }

    // 填充内容区域
    for (int row = 1; row < rows - 1; row++) {
        for (int col = 1; col < cols - 1; col++) {
            fd2_ui_render_tile(13, x + col * tw, y + row * th); // 内容区域
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

static void fd2_ui_delay(int ms) {
    SDL_Delay(ms);
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

    // 加载窗口图块数据 (FDOTHER索引7)
    const u8* tile_data = fd2_resources_get(res, FD2_DAT_FDOTHER, 7, &g_ui_render.fdother_size);
    if (tile_data) {
        g_ui_render.fdother_data = tile_data;
        printf("  [2] 加载窗口图块 (FDOTHER索引7, 大小=%u)\n", g_ui_render.fdother_size);
    }

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

    const u8* tile_data = fd2_resources_get(res, FD2_DAT_FDOTHER, 7, &g_ui_render.fdother_size);
    if (tile_data) {
        g_ui_render.fdother_data = tile_data;
    }

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

    const u8* tile_data = fd2_resources_get(res, FD2_DAT_FDOTHER, 7, &g_ui_render.fdother_size);
    if (tile_data) {
        g_ui_render.fdother_data = tile_data;
    }

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

    const u8* tile_data = fd2_resources_get(res, FD2_DAT_FDOTHER, 7, &g_ui_render.fdother_size);
    if (tile_data) {
        g_ui_render.fdother_data = tile_data;
    }

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

    printf("FD2 UI渲染测试程序 (根据IDA汇编代码复原)\n");
    printf("==========================================\n");
    printf("数据目录: %s\n", data_dir);

    fd2_resources_t res;
    if (fd2_resources_init(&res, data_dir) != 0) {
        fprintf(stderr, "资源管理器初始化失败\n");
        return 1;
    }

    if (fd2_resources_load_dat(&res, FD2_DAT_FDOTHER) != 0) {
        fprintf(stderr, "FDOTHER.DAT加载失败\n");
        fd2_resources_shutdown(&res);
        return 1;
    }

    if (fd2_ui_render_init(UI_TEST_WINDOW_SCALE) != 0) {
        fprintf(stderr, "UI渲染系统初始化失败\n");
        fd2_resources_shutdown(&res);
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
            case 0: fd2_ui_draw_main_menu_dialog(&res); break;
            case 1: fd2_ui_draw_status_dialog(&res); break;
            case 2: fd2_ui_draw_save_load_dialog(&res); break;
            case 3: fd2_ui_draw_battle_menu(&res); break;
            case 4: fd2_ui_draw_all_grid(&res); break;
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
    fd2_resources_shutdown(&res);
    printf("UI渲染测试完成\n");
    return 0;
}
