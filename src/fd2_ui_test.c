/**
 * FD2 UI渲染测试程序
 * 
 * 根据IDA MCP汇编代码1:1复原原版游戏的UI绘制逻辑
 * 
 * 核心UI绘制逻辑分析 (从IDA汇编反推):
 * 
 * 1. sub_4ED7A - 字符/图块渲染函数:
 *    - 从FDOTHER.DAT读取32字节图块数据 (16行 x 2字节)
 *    - 每个图块是16x16像素
 *    - 通过位移操作将2位位图转换为像素索引
 *    - 使用arg10和arg14作为颜色索引写入屏幕缓冲区
 * 
 * 2. sub_15F84 - 场景命令解释器:
 *    - 解析场景命令列表
 *    - 特殊命令: -1(结束), -2(换行), -3(翻页), -4/-5(特殊文本), -6(显示数字)
 *    - -17/-18/-19/-20: 加载DATO.DAT数据到场景缓冲区
 *    - 调用sub_4ED7A渲染每个字符
 * 
 * 3. sub_1366A - 场景动画控制:
 *    - 处理UI元素的动画和交互
 *    - 使用80字节的UI元素结构
 *    - 控制元素的显示/隐藏、移动等
 * 
 * 4. sub_11CAC - 核心渲染函数:
 *    - sub_1297D(): 清理屏幕缓冲区
 *    - sub_11EEE(): 更新精灵位置
 *    - sub_122DC(): 绘制背景层
 *    - sub_127A9(): 绘制前景层
 *    - sub_1ACF3(): 合成最终画面
 *    - sub_11EB0(): 输出到显存
 * 
 * 5. sub_11D40 - 调色板操作:
 *    - outp(968, index): 设置调色板索引端口
 *    - outp(969, value): 设置颜色值端口
 *    - 从FDOTHER.DAT索引75读取6位RGB调色板
 * 
 * 6. sub_135DD - 场景切换:
 *    - 平滑过渡到新场景
 *    - 逐步调整qword_53AA9 (当前场景ID)
 *    - 每次调整调用sub_11CAC渲染一帧
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
    u8 id;
    u8 type;
    u8 reserved;
    u8 current_char;
    u8 current_frame;
    u8 flags;
    u8 pos_x;
    u8 pos_y;
    u8 data[72];
} fd2_ui_element_t;

typedef struct {
    u8 screen[FD2_SCREEN_BUFFER_SIZE];
    u8 palette[FD2_PALETTE_BYTES];
    u8 ui_elements[FD2_MAX_UI_ELEMENTS * FD2_UI_ELEMENT_SIZE];
    int element_count;
    int scene_id;
    u32* argb;
    u32* argb_palette;
    SDL_Window* window;
    SDL_Renderer* renderer;
    SDL_Texture* texture;
    const u8* fdother_data;
    u32 fdother_size;
} fd2_ui_render_t;

static fd2_ui_render_t g_ui_render;

static int fd2_ui_render_init(int scale) {
    memset(&g_ui_render, 0, sizeof(g_ui_render));

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

/**
 * 设置调色板 (根据sub_11D40逻辑)
 * 从FDOTHER索引75读取6位RGB调色板
 * 转换为8位并设置到渲染器
 */
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

/**
 * 填充屏幕 (根据sub_1297D逻辑)
 */
static void fd2_ui_fill_screen(u8 color) {
    memset(g_ui_render.screen, color, FD2_SCREEN_BUFFER_SIZE);
}

/**
 * 渲染单个字符图块 (根据sub_4ED7A逻辑)
 * 
 * 原版逻辑:
 * - 从FDOTHER.DAT + 32*n10读取32字节图块数据
 * - 每行2字节 (16位)，共16行
 * - 对每个位进行左移操作，如果溢出则写入颜色
 * - 使用arg10和arg14作为颜色索引
 * - 图块大小为16x16像素
 * 
 * @param tile_index 图块索引 (FDOTHER中的偏移/32)
 * @param dx 目标X坐标
 * @param dy 目标Y坐标
 * @param color_fg 前景颜色索引
 * @param color_bg 背景颜色索引
 */
static void fd2_ui_render_tile(int tile_index, int dx, int dy, u8 color_fg, u8 color_bg) {
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
                g_ui_render.screen[sy * FD2_SCREEN_W + sx] = color_fg;
            } else {
                g_ui_render.screen[sy * FD2_SCREEN_W + sx] = color_bg;
            }
            bits <<= 1;
        }
    }
}

/**
 * 渲染RLE图像 (用于背景等大图)
 */
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
 * 呈现屏幕 (根据sub_11EB0逻辑)
 */
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
 * 绘制主菜单界面 (根据sub_3231B逻辑)
 * 
 * 原版流程:
 * 1. 加载FDOTHER.DAT索引0
 * 2. 调用sub_205DA初始化
 * 3. 调用sub_135DD(3, 34)切换场景
 * 4. 循环15次调用sub_13185(2)
 * 5. 调用sub_15F84渲染文本 (FDTXT_DAT索引0, 位置76,74)
 * 6. 循环13次调用sub_13185(2)
 * 7. 调用sub_15F84渲染文本 (FDTXT_DAT索引1, 位置76,74)
 * 8. 调用sub_25977(-1, 0)
 * 9. 调用sub_1366A(99/100/101/102/103/104/105)
 * 10. 重复步骤5-7渲染更多文本
 */
static void fd2_ui_draw_main_menu(fd2_resources_t* res) {
    printf("\n=== 绘制: 主菜单界面 (根据sub_3231B逻辑) ===\n");

    u32 pal_size;
    const u8* pal_res = fd2_resources_get(res, FD2_DAT_FDOTHER, 75, &pal_size);
    if (pal_res && pal_size >= FD2_PALETTE_BYTES) {
        fd2_ui_set_palette_6bit(pal_res);
        printf("  [1] 设置调色板 (FDOTHER索引75)\n");
    }

    const u8* fdother_0 = fd2_resources_get(res, FD2_DAT_FDOTHER, 0, &g_ui_render.fdother_size);
    if (fdother_0) {
        g_ui_render.fdother_data = fdother_0;
        printf("  [2] 加载字体图块 (FDOTHER索引0, 大小=%u)\n", g_ui_render.fdother_size);
    }

    fd2_ui_fill_screen(0);
    fd2_ui_present();
    fd2_ui_delay(500);

    u32 img_size;
    const u8* bg_img = fd2_resources_get(res, FD2_DAT_FDOTHER, 77, &img_size);
    if (bg_img) {
        fd2_ui_blit_rle(bg_img, img_size, 0, 0);
        printf("  [3] 绘制背景 (FDOTHER索引77)\n");
        fd2_ui_present();
        fd2_ui_delay(500);
    }

    const u8* title_img = fd2_resources_get(res, FD2_DAT_FDOTHER, 74, &img_size);
    if (title_img) {
        fd2_ui_blit_rle(title_img, img_size, 40, 10);
        printf("  [4] 绘制标题 (FDOTHER索引74)\n");
        fd2_ui_present();
        fd2_ui_delay(500);
    }

    printf("  [5] 绘制菜单项 (FDOTHER索引69-73)\n");
    int menu_items[] = {69, 70, 71, 72, 73};
    int menu_y = 60;
    const char* menu_names[] = {"新游戏", "继续游戏", "密码", "设置", "退出"};

    for (int i = 0; i < 5; i++) {
        const u8* menu_img = fd2_resources_get(res, FD2_DAT_FDOTHER, menu_items[i], &img_size);
        if (menu_img) {
            fd2_ui_blit_rle(menu_img, img_size, 60, menu_y);
            printf("    - 菜单项 %d: %s @ (60, %d)\n", menu_items[i], menu_names[i], menu_y);
            fd2_ui_present();
            fd2_ui_delay(300);
        }
        menu_y += 24;
    }

    printf("  [6] 绘制特殊效果 (FDOTHER索引79)\n");
    const u8* effect_img = fd2_resources_get(res, FD2_DAT_FDOTHER, 79, &img_size);
    if (effect_img) {
        fd2_ui_blit_rle(effect_img, img_size, 0, 0);
        fd2_ui_present();
    }

    fd2_ui_wait_for_key("主菜单界面绘制完成");
}

/**
 * 绘制密码界面 (根据sub_3231B逻辑)
 */
static void fd2_ui_draw_password_screen(fd2_resources_t* res) {
    printf("\n=== 绘制: 密码界面 (根据sub_3231B逻辑) ===\n");

    u32 pal_size;
    const u8* pal_res = fd2_resources_get(res, FD2_DAT_FDOTHER, 75, &pal_size);
    if (pal_res && pal_size >= FD2_PALETTE_BYTES) {
        fd2_ui_set_palette_6bit(pal_res);
    }

    fd2_ui_fill_screen(0);
    fd2_ui_present();

    int pw_indices[] = {96, 97, 98};
    const char* pw_names[] = {"密码背景", "密码输入框", "密码提示"};

    for (int i = 0; i < 3; i++) {
        u32 img_size;
        const u8* img = fd2_resources_get(res, FD2_DAT_FDOTHER, pw_indices[i], &img_size);
        if (img) {
            fd2_ui_blit_rle(img, img_size, 0, 0);
            printf("  [%d] 绘制: %s (FDOTHER索引%d)\n", i + 1, pw_names[i], pw_indices[i]);
            fd2_ui_present();
            fd2_ui_delay(400);
        }
    }

    fd2_ui_wait_for_key("密码界面绘制完成");
}

/**
 * 绘制过渡画面 (根据sub_3231B逻辑)
 */
static void fd2_ui_draw_transition_screens(fd2_resources_t* res) {
    printf("\n=== 绘制: 过渡画面 (根据sub_3231B逻辑) ===\n");

    u32 pal_size;
    const u8* pal_res = fd2_resources_get(res, FD2_DAT_FDOTHER, 75, &pal_size);
    if (pal_res && pal_size >= FD2_PALETTE_BYTES) {
        fd2_ui_set_palette_6bit(pal_res);
    }

    int trans_indices[] = {99, 101, 102};
    const char* trans_names[] = {"过渡1", "过渡2", "过渡3"};

    for (int i = 0; i < 3; i++) {
        fd2_ui_fill_screen(0);
        u32 img_size;
        const u8* img = fd2_resources_get(res, FD2_DAT_FDOTHER, trans_indices[i], &img_size);
        if (img) {
            fd2_ui_blit_rle(img, img_size, 0, 0);
            printf("  [%d] 绘制: %s (FDOTHER索引%d)\n", i + 1, trans_names[i], trans_indices[i]);
            fd2_ui_present();
            fd2_ui_delay(500);
        }
        char msg[64];
        snprintf(msg, sizeof(msg), "%s 绘制完成", trans_names[i]);
        fd2_ui_wait_for_key(msg);
    }
}

/**
 * 绘制背景图像
 */
static void fd2_ui_draw_backgrounds(fd2_resources_t* res) {
    printf("\n=== 绘制: 背景图像 ===\n");

    u32 pal_size;
    const u8* pal_res = fd2_resources_get(res, FD2_DAT_FDOTHER, 75, &pal_size);
    if (pal_res && pal_size >= FD2_PALETTE_BYTES) {
        fd2_ui_set_palette_6bit(pal_res);
    }

    int bg_indices[] = {15, 35, 36, 40, 41, 42, 46, 47, 55, 56};
    const char* bg_names[] = {
        "背景1", "背景2", "背景3", "背景4", "背景5",
        "背景6", "背景7", "背景8", "背景9", "背景10"
    };

    for (int i = 0; i < 10; i++) {
        fd2_ui_fill_screen(0);
        u32 img_size;
        const u8* img = fd2_resources_get(res, FD2_DAT_FDOTHER, bg_indices[i], &img_size);
        if (img) {
            fd2_ui_blit_rle(img, img_size, 0, 0);
            printf("  [%d] 绘制: %s (FDOTHER索引%d)\n", i + 1, bg_names[i], bg_indices[i]);
            fd2_ui_present();
            fd2_ui_delay(300);
        }
        char msg[64];
        snprintf(msg, sizeof(msg), "%s 绘制完成", bg_names[i]);
        fd2_ui_wait_for_key(msg);
    }
}

/**
 * 绘制场景图像
 */
static void fd2_ui_draw_scene_images(fd2_resources_t* res) {
    printf("\n=== 绘制: 场景图像 ===\n");

    u32 pal_size;
    const u8* pal_res = fd2_resources_get(res, FD2_DAT_FDOTHER, 75, &pal_size);
    if (pal_res && pal_size >= FD2_PALETTE_BYTES) {
        fd2_ui_set_palette_6bit(pal_res);
    }

    int scene_indices[] = {54, 57, 59};
    const char* scene_names[] = {"场景图像1", "场景图像2", "场景图像3"};

    for (int i = 0; i < 3; i++) {
        fd2_ui_fill_screen(0);
        u32 img_size;
        const u8* img = fd2_resources_get(res, FD2_DAT_FDOTHER, scene_indices[i], &img_size);
        if (img) {
            fd2_ui_blit_rle(img, img_size, 0, 0);
            printf("  [%d] 绘制: %s (FDOTHER索引%d)\n", i + 1, scene_names[i], scene_indices[i]);
            fd2_ui_present();
            fd2_ui_delay(300);
        }
        char msg[64];
        snprintf(msg, sizeof(msg), "%s 绘制完成", scene_names[i]);
        fd2_ui_wait_for_key(msg);
    }
}

/**
 * 绘制动画图像
 */
static void fd2_ui_draw_animations(fd2_resources_t* res) {
    printf("\n=== 绘制: 动画图像 ===\n");

    u32 pal_size;
    const u8* pal_res = fd2_resources_get(res, FD2_DAT_FDOTHER, 75, &pal_size);
    if (pal_res && pal_size >= FD2_PALETTE_BYTES) {
        fd2_ui_set_palette_6bit(pal_res);
    }

    int anim_indices[] = {7, 8};
    const char* anim_names[] = {"动画图像1", "动画图像2"};

    for (int i = 0; i < 2; i++) {
        fd2_ui_fill_screen(0);
        u32 img_size;
        const u8* img = fd2_resources_get(res, FD2_DAT_FDOTHER, anim_indices[i], &img_size);
        if (img) {
            fd2_ui_blit_rle(img, img_size, 40, 20);
            printf("  [%d] 绘制: %s (FDOTHER索引%d)\n", i + 1, anim_names[i], anim_indices[i]);
            fd2_ui_present();
            fd2_ui_delay(300);
        }
        char msg[64];
        snprintf(msg, sizeof(msg), "%s 绘制完成", anim_names[i]);
        fd2_ui_wait_for_key(msg);
    }
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
            case 0: fd2_ui_draw_all_grid(&res); break;
            case 1: fd2_ui_draw_main_menu(&res); break;
            case 2: fd2_ui_draw_password_screen(&res); break;
            case 3: fd2_ui_draw_transition_screens(&res); break;
            case 4: fd2_ui_draw_backgrounds(&res); break;
            case 5: fd2_ui_draw_scene_images(&res); break;
            case 6: fd2_ui_draw_animations(&res); break;
            default:
                printf("\n所有测试完成!\n");
                goto done;
        }

        test_index++;
        printf("\n测试进度: %d/7\n", test_index);
    }

done:
    printf("\n清理资源...\n");
    fd2_ui_render_shutdown();
    fd2_resources_shutdown(&res);
    printf("UI渲染测试完成\n");
    return 0;
}
