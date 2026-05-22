/**
 * FD2 UI渲染测试程序
 *
 * 根据IDA MCP汇编代码分析，测试fdother中所有UI资源的读取和绘制
 *
 * FDOTHER.DAT中的UI资源索引（根据汇编代码和文档分析）:
 *   索引0:  字体数据 (1:1复制 sub_111BA)
 *   索引7:  动画图像 (RLE, sub_4E98D)
 *   索引8:  动画图像 (RLE)
 *   索引15: 背景图像 (RLE)
 *   索引35: 背景图像 (RLE)
 *   索引36: 背景图像 (RLE)
 *   索引40: 背景图像 (RLE)
 *   索引41: 背景图像 (RLE)
 *   索引42: 背景图像 (RLE)
 *   索引46: 背景图像 (RLE)
 *   索引47: 背景图像 (RLE)
 *   索引54: 场景数据/图像 (RLE)
 *   索引55: 背景图像 (RLE)
 *   索引56: 背景图像 (RLE)
 *   索引57: 场景数据/图像 (RLE)
 *   索引59: 场景数据/图像 (RLE)
 *   索引69: 菜单项 (RLE)
 *   索引70: 菜单项 (RLE)
 *   索引71: 菜单项 (RLE)
 *   索引72: 菜单项 (RLE)
 *   索引73: 菜单项 (RLE)
 *   索引74: 标题文字 (RLE)
 *   索引75: 调色板 (768字节 6-bit RGB)
 *   索引77: 标题背景 (RLE)
 *   索引79: 特殊效果 (RLE)
 *   索引96: 密码界面 (RLE)
 *   索引97: 密码界面 (RLE)
 *   索引98: 密码界面 (RLE)
 *   索引99: 过渡画面 (RLE)
 *   索引101: 过渡画面 (RLE)
 *   索引102: 过渡画面 (RLE)
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
#include "fd2_render.h"
#include "fd2_resources.h"
#include "fd2_globals.h"

#define UI_TEST_WINDOW_SCALE 3

typedef struct {
    int index;
    const char* name;
    const char* type;
} ui_resource_info_t;

static const ui_resource_info_t g_ui_resources[] = {
    {0,   "字体数据",      "font"},
    {7,   "动画图像1",     "rle_image"},
    {8,   "动画图像2",     "rle_image"},
    {15,  "背景图像1",     "rle_image"},
    {35,  "背景图像2",     "rle_image"},
    {36,  "背景图像3",     "rle_image"},
    {40,  "背景图像4",     "rle_image"},
    {41,  "背景图像5",     "rle_image"},
    {42,  "背景图像6",     "rle_image"},
    {46,  "背景图像7",     "rle_image"},
    {47,  "背景图像8",     "rle_image"},
    {54,  "场景数据图像1", "rle_image"},
    {55,  "背景图像9",     "rle_image"},
    {56,  "背景图像10",    "rle_image"},
    {57,  "场景数据图像2", "rle_image"},
    {59,  "场景数据图像3", "rle_image"},
    {69,  "菜单项1",       "rle_image"},
    {70,  "菜单项2",       "rle_image"},
    {71,  "菜单项3",       "rle_image"},
    {72,  "菜单项4",       "rle_image"},
    {73,  "菜单项5",       "rle_image"},
    {74,  "标题文字",      "rle_image"},
    {75,  "全局调色板",    "palette"},
    {77,  "标题背景",      "rle_image"},
    {79,  "特殊效果",      "rle_image"},
    {96,  "密码界面1",     "rle_image"},
    {97,  "密码界面2",     "rle_image"},
    {98,  "密码界面3",     "rle_image"},
    {99,  "过渡画面1",     "rle_image"},
    {101, "过渡画面2",     "rle_image"},
    {102, "过渡画面3",     "rle_image"},
};

#define UI_RESOURCE_COUNT (sizeof(g_ui_resources) / sizeof(g_ui_resources[0]))

typedef struct {
    SDL_Window*   window;
    SDL_Renderer* renderer;
    SDL_Texture*  texture;
    u8            screen[FD2_SCREEN_SIZE];
    u8            palette[FD2_PALETTE_BYTES];
    u32*          argb;
    u32*          argb_palette;
    int           scale;
} test_render_t;

static int test_render_init(test_render_t* r, int scale) {
    memset(r, 0, sizeof(*r));
    r->scale = scale;

    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        fprintf(stderr, "SDL_Init failed: %s\n", SDL_GetError());
        return -1;
    }

    r->window = SDL_CreateWindow("FD2 UI Render Test",
                                  SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                                  FD2_SCREEN_W * scale, FD2_SCREEN_H * scale,
                                  SDL_WINDOW_SHOWN);
    if (!r->window) {
        fprintf(stderr, "SDL_CreateWindow failed: %s\n", SDL_GetError());
        return -1;
    }

    r->renderer = SDL_CreateRenderer(r->window, -1, SDL_RENDERER_ACCELERATED);
    if (!r->renderer) {
        fprintf(stderr, "SDL_CreateRenderer failed: %s\n", SDL_GetError());
        return -1;
    }

    r->texture = SDL_CreateTexture(r->renderer, SDL_PIXELFORMAT_ARGB8888,
                                    SDL_TEXTUREACCESS_STREAMING,
                                    FD2_SCREEN_W, FD2_SCREEN_H);
    if (!r->texture) {
        fprintf(stderr, "SDL_CreateTexture failed: %s\n", SDL_GetError());
        return -1;
    }

    r->argb = (u32*)malloc(FD2_SCREEN_SIZE * sizeof(u32));
    r->argb_palette = (u32*)malloc(256 * sizeof(u32));
    if (!r->argb || !r->argb_palette) {
        fprintf(stderr, "Failed to allocate ARGB buffers\n");
        return -1;
    }

    return 0;
}

static void test_render_shutdown(test_render_t* r) {
    if (r->texture) SDL_DestroyTexture(r->texture);
    if (r->renderer) SDL_DestroyRenderer(r->renderer);
    if (r->window) SDL_DestroyWindow(r->window);
    free(r->argb);
    free(r->argb_palette);
    SDL_Quit();
}

static void test_render_set_palette_6bit(test_render_t* r, const u8* pal_6bit) {
    for (int i = 0; i < 256; i++) {
        r->palette[i * 3 + 0] = (pal_6bit[i * 3 + 0] << 2) | (pal_6bit[i * 3 + 0] >> 4);
        r->palette[i * 3 + 1] = (pal_6bit[i * 3 + 1] << 2) | (pal_6bit[i * 3 + 1] >> 4);
        r->palette[i * 3 + 2] = (pal_6bit[i * 3 + 2] << 2) | (pal_6bit[i * 3 + 2] >> 4);
    }
    for (int i = 0; i < 256; i++) {
        r->argb_palette[i] = 0xFF000000 |
            ((u32)r->palette[i * 3 + 0] << 16) |
            ((u32)r->palette[i * 3 + 1] << 8) |
            ((u32)r->palette[i * 3 + 2]);
    }
}

static void test_render_fill_screen(test_render_t* r, u8 color) {
    memset(r->screen, color, FD2_SCREEN_SIZE);
}

static void test_render_blit_trans(test_render_t* r, const u8* pixels, int w, int h, int dx, int dy, u8 transparent) {
    for (int y = 0; y < h; y++) {
        int sy = dy + y;
        if (sy < 0 || sy >= FD2_SCREEN_H) continue;
        for (int x = 0; x < w; x++) {
            int sx = dx + x;
            if (sx < 0 || sx >= FD2_SCREEN_W) continue;
            u8 p = pixels[y * w + x];
            if (p != transparent) {
                r->screen[sy * FD2_SCREEN_W + sx] = p;
            }
        }
    }
}

static void test_render_present(test_render_t* r) {
    for (int i = 0; i < FD2_SCREEN_SIZE; i++) {
        r->argb[i] = r->argb_palette[r->screen[i]];
    }

    void* pixels;
    int pitch;
    if (SDL_LockTexture(r->texture, NULL, &pixels, &pitch) == 0) {
        memcpy(pixels, r->argb, FD2_SCREEN_SIZE * sizeof(u32));
        SDL_UnlockTexture(r->texture);
    }

    SDL_RenderCopy(r->renderer, r->texture, NULL, NULL);
    SDL_RenderPresent(r->renderer);
}

static void wait_for_key(const char* message) {
    printf("[PRESS] %s - 按任意键继续...\n", message);
    SDL_Event e;
    int waiting = 1;
    while (waiting) {
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) {
                waiting = 0;
                return;
            }
            if (e.type == SDL_KEYDOWN) {
                if (e.key.keysym.sym == SDLK_ESCAPE) {
                    waiting = 0;
                    return;
                }
                if (e.key.keysym.sym == SDLK_q) {
                    waiting = 0;
                    return;
                }
                waiting = 0;
            }
        }
        SDL_Delay(10);
    }
}

static int test_rle_image(test_render_t* r, const u8* res_data, u32 res_size, int dx, int dy, const char* name) {
    if (res_size < 4) {
        printf("  [SKIP] %s: 资源大小不足 (%u < 4)\n", name, res_size);
        return -1;
    }

    int w = res_data[0] | (res_data[1] << 8);
    int h = res_data[2] | (res_data[3] << 8);

    if (w <= 0 || w > 640 || h <= 0 || h > 480) {
        printf("  [SKIP] %s: 无效尺寸 %dx%d\n", name, w, h);
        return -1;
    }

    printf("  [DRAW] %s: %dx%d @ (%d, %d)\n", name, w, h, dx, dy);

    u8* pixels = (u8*)malloc(w * h);
    if (!pixels) {
        printf("  [ERROR] %s: 内存分配失败\n", name);
        return -1;
    }

    int ret = fd2_rle_decompress(res_data + 4, res_size - 4,
                                  pixels, 0, 0, w, w, h, -1);
    if (ret != 0) {
        printf("  [ERROR] %s: RLE解压失败\n", name);
        free(pixels);
        return -1;
    }

    test_render_blit_trans(r, pixels, w, h, dx, dy, 0);
    free(pixels);
    return 0;
}

static int test_ui_screen_menu(test_render_t* r, fd2_resources_t* res) {
    printf("\n=== 测试: 主菜单界面 ===\n");

    u32 pal_size;
    const u8* pal_res = fd2_resources_get(res, FD2_DAT_FDOTHER, 75, &pal_size);
    if (pal_res && pal_size >= 768) {
        test_render_set_palette_6bit(r, pal_res);
        printf("  [PALETTE] 设置全局调色板 (索引75)\n");
    }

    test_render_fill_screen(r, 0);

    test_rle_image(r, fd2_resources_get(res, FD2_DAT_FDOTHER, 77, &pal_size),
                   pal_size, 0, 0, "标题背景(77)");

    test_rle_image(r, fd2_resources_get(res, FD2_DAT_FDOTHER, 74, &pal_size),
                   pal_size, 40, 10, "标题文字(74)");

    int menu_y = 60;
    for (int i = 69; i <= 73; i++) {
        test_rle_image(r, fd2_resources_get(res, FD2_DAT_FDOTHER, i, &pal_size),
                       pal_size, 60, menu_y, "菜单项");
        menu_y += 20;
    }

    test_render_present(r);
    wait_for_key("主菜单界面渲染完成");
    return 0;
}

static int test_ui_screen_password(test_render_t* r, fd2_resources_t* res) {
    printf("\n=== 测试: 密码界面 ===\n");

    u32 pal_size;
    const u8* pal_res = fd2_resources_get(res, FD2_DAT_FDOTHER, 75, &pal_size);
    if (pal_res && pal_size >= 768) {
        test_render_set_palette_6bit(r, pal_res);
    }

    test_render_fill_screen(r, 0);

    test_rle_image(r, fd2_resources_get(res, FD2_DAT_FDOTHER, 96, &pal_size),
                   pal_size, 0, 0, "密码界面1(96)");
    test_rle_image(r, fd2_resources_get(res, FD2_DAT_FDOTHER, 97, &pal_size),
                   pal_size, 0, 0, "密码界面2(97)");
    test_rle_image(r, fd2_resources_get(res, FD2_DAT_FDOTHER, 98, &pal_size),
                   pal_size, 0, 0, "密码界面3(98)");

    test_render_present(r);
    wait_for_key("密码界面渲染完成");
    return 0;
}

static int test_ui_screen_transition(test_render_t* r, fd2_resources_t* res) {
    printf("\n=== 测试: 过渡画面 ===\n");

    u32 pal_size;
    const u8* pal_res = fd2_resources_get(res, FD2_DAT_FDOTHER, 75, &pal_size);
    if (pal_res && pal_size >= 768) {
        test_render_set_palette_6bit(r, pal_res);
    }

    int transition_indices[] = {99, 101, 102};
    const char* transition_names[] = {"过渡画面1(99)", "过渡画面2(101)", "过渡画面3(102)"};

    for (int i = 0; i < 3; i++) {
        test_render_fill_screen(r, 0);
        u32 size;
        const u8* data = fd2_resources_get(res, FD2_DAT_FDOTHER, transition_indices[i], &size);
        test_rle_image(r, data, size, 0, 0, transition_names[i]);
        test_render_present(r);

        char msg[64];
        snprintf(msg, sizeof(msg), "%s 渲染完成", transition_names[i]);
        wait_for_key(msg);
    }

    return 0;
}

static int test_ui_screen_backgrounds(test_render_t* r, fd2_resources_t* res) {
    printf("\n=== 测试: 背景图像 ===\n");

    u32 pal_size;
    const u8* pal_res = fd2_resources_get(res, FD2_DAT_FDOTHER, 75, &pal_size);
    if (pal_res && pal_size >= 768) {
        test_render_set_palette_6bit(r, pal_res);
    }

    int bg_indices[] = {15, 35, 36, 40, 41, 42, 46, 47, 55, 56};
    const char* bg_names[] = {
        "背景1(15)", "背景2(35)", "背景3(36)", "背景4(40)", "背景5(41)",
        "背景6(42)", "背景7(46)", "背景8(47)", "背景9(55)", "背景10(56)"
    };

    for (int i = 0; i < 10; i++) {
        test_render_fill_screen(r, 0);
        u32 size;
        const u8* data = fd2_resources_get(res, FD2_DAT_FDOTHER, bg_indices[i], &size);
        test_rle_image(r, data, size, 0, 0, bg_names[i]);
        test_render_present(r);

        char msg[64];
        snprintf(msg, sizeof(msg), "%s 渲染完成", bg_names[i]);
        wait_for_key(msg);
    }

    return 0;
}

static int test_ui_screen_scene_images(test_render_t* r, fd2_resources_t* res) {
    printf("\n=== 测试: 场景数据图像 ===\n");

    u32 pal_size;
    const u8* pal_res = fd2_resources_get(res, FD2_DAT_FDOTHER, 75, &pal_size);
    if (pal_res && pal_size >= 768) {
        test_render_set_palette_6bit(r, pal_res);
    }

    int scene_indices[] = {54, 57, 59};
    const char* scene_names[] = {"场景图像1(54)", "场景图像2(57)", "场景图像3(59)"};

    for (int i = 0; i < 3; i++) {
        test_render_fill_screen(r, 0);
        u32 size;
        const u8* data = fd2_resources_get(res, FD2_DAT_FDOTHER, scene_indices[i], &size);
        test_rle_image(r, data, size, 0, 0, scene_names[i]);
        test_render_present(r);

        char msg[64];
        snprintf(msg, sizeof(msg), "%s 渲染完成", scene_names[i]);
        wait_for_key(msg);
    }

    return 0;
}

static int test_ui_screen_animation(test_render_t* r, fd2_resources_t* res) {
    printf("\n=== 测试: 动画图像 ===\n");

    u32 pal_size;
    const u8* pal_res = fd2_resources_get(res, FD2_DAT_FDOTHER, 75, &pal_size);
    if (pal_res && pal_size >= 768) {
        test_render_set_palette_6bit(r, pal_res);
    }

    int anim_indices[] = {7, 8};
    const char* anim_names[] = {"动画图像1(7)", "动画图像2(8)"};

    for (int i = 0; i < 2; i++) {
        test_render_fill_screen(r, 0);
        u32 size;
        const u8* data = fd2_resources_get(res, FD2_DAT_FDOTHER, anim_indices[i], &size);
        test_rle_image(r, data, size, 40, 20, anim_names[i]);
        test_render_present(r);

        char msg[64];
        snprintf(msg, sizeof(msg), "%s 渲染完成", anim_names[i]);
        wait_for_key(msg);
    }

    return 0;
}

static int test_ui_screen_special_effects(test_render_t* r, fd2_resources_t* res) {
    printf("\n=== 测试: 特殊效果 ===\n");

    u32 pal_size;
    const u8* pal_res = fd2_resources_get(res, FD2_DAT_FDOTHER, 75, &pal_size);
    if (pal_res && pal_size >= 768) {
        test_render_set_palette_6bit(r, pal_res);
    }

    test_render_fill_screen(r, 0);

    test_rle_image(r, fd2_resources_get(res, FD2_DAT_FDOTHER, 79, &pal_size),
                   pal_size, 0, 0, "特殊效果(79)");

    test_render_present(r);
    wait_for_key("特殊效果渲染完成");
    return 0;
}

static int test_ui_screen_all_resources(test_render_t* r, fd2_resources_t* res) {
    printf("\n=== 测试: 所有UI资源网格展示 ===\n");

    u32 pal_size;
    const u8* pal_res = fd2_resources_get(res, FD2_DAT_FDOTHER, 75, &pal_size);
    if (pal_res && pal_size >= 768) {
        test_render_set_palette_6bit(r, pal_res);
    }

    test_render_fill_screen(r, 0);

    int grid_x = 4;
    int grid_y = 5;
    int cell_w = FD2_SCREEN_W / grid_x;
    int cell_h = FD2_SCREEN_H / grid_y;

    int drawn = 0;
    for (int idx = 0; idx < (int)UI_RESOURCE_COUNT; idx++) {
        if (g_ui_resources[idx].type[0] == 'p') continue;
        if (g_ui_resources[idx].type[0] == 'f') continue;

        u32 size;
        const u8* data = fd2_resources_get(res, FD2_DAT_FDOTHER, g_ui_resources[idx].index, &size);
        if (!data || size < 4) continue;

        int w = data[0] | (data[1] << 8);
        int h = data[2] | (data[3] << 8);
        if (w <= 0 || w > 640 || h <= 0 || h > 480) continue;

        int gx = drawn % grid_x;
        int gy = drawn / grid_x;
        if (gy >= grid_y) break;

        int dx = gx * cell_w + (cell_w - w) / 2;
        int dy = gy * cell_h + (cell_h - h) / 2;

        u8* pixels = (u8*)malloc(w * h);
        if (pixels) {
            if (fd2_rle_decompress(data + 4, size - 4, pixels, 0, 0, w, w, h, -1) == 0) {
                test_render_blit_trans(r, pixels, w, h, dx, dy, 0);
            }
            free(pixels);
        }

        drawn++;
    }

    test_render_present(r);
    printf("  [GRID] 共绘制 %d 个资源\n", drawn);
    wait_for_key("所有UI资源网格展示完成");
    return 0;
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

    printf("FD2 UI渲染测试程序\n");
    printf("==================\n");
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

    test_render_t render;
    if (test_render_init(&render, UI_TEST_WINDOW_SCALE) != 0) {
        fprintf(stderr, "渲染系统初始化失败\n");
        fd2_resources_shutdown(&res);
        return 1;
    }

    printf("控制: 按任意键切换到下一个测试，ESC/Q退出\n\n");

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
            case 0: test_ui_screen_all_resources(&render, &res); break;
            case 1: test_ui_screen_menu(&render, &res); break;
            case 2: test_ui_screen_password(&render, &res); break;
            case 3: test_ui_screen_transition(&render, &res); break;
            case 4: test_ui_screen_backgrounds(&render, &res); break;
            case 5: test_ui_screen_scene_images(&render, &res); break;
            case 6: test_ui_screen_animation(&render, &res); break;
            case 7: test_ui_screen_special_effects(&render, &res); break;
            default:
                printf("\n所有测试完成!\n");
                goto done;
        }

        test_index++;
        printf("\n测试进度: %d/%d\n", test_index, 8);
    }

done:
    printf("\n清理资源...\n");
    test_render_shutdown(&render);
    fd2_resources_shutdown(&res);
    printf("UI渲染测试完成\n");
    return 0;
}
