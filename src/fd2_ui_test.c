/**
 * FD2 UI渲染测试程序 - 1:1 MCP汇编复原版
 * 
 * 根据IDA Pro MCP汇编分析1:1实现原版游戏UI绘制逻辑
 */

#define SDL_MAIN_HANDLED
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <windows.h>
#endif

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef int s32;

#define FD2_SCREEN_W 320
#define FD2_SCREEN_H 200
#define FD2_SCREEN_BUFFER_SIZE (FD2_SCREEN_W * FD2_SCREEN_H)
#define FD2_PALETTE_SIZE 768
#define FD2_UI_WINDOW_SCALE 3

/**
 * UI渲染状态
 */
typedef struct {
    u8 screen[FD2_SCREEN_BUFFER_SIZE];
    u8 palette[FD2_PALETTE_SIZE];
    u32* argb;
    u32* argb_palette;
    SDL_Window* window;
    SDL_Renderer* renderer;
    SDL_Texture* texture;
    
    /* Tile数据 */
    const u8* tile_data;
    u32 tile_data_size;
    u8* decompressed_tiles;
    u32* tile_offsets;
    u16 tile_count;
    
    /* 存储每个tile的宽高信息 */
    u16* tile_widths;
    u16* tile_heights;
} fd2_ui_render_t;

static fd2_ui_render_t g_ui_render;

/**
 * 初始化UI渲染系统
 */
static int fd2_ui_render_init(void) {
    memset(&g_ui_render, 0, sizeof(g_ui_render));

    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        fprintf(stderr, "SDL_Init failed: %s\n", SDL_GetError());
        return -1;
    }

    g_ui_render.window = SDL_CreateWindow("FD2 UI Test (1:1 MCP Assembly)",
                                           SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                                           FD2_SCREEN_W * FD2_UI_WINDOW_SCALE, 
                                           FD2_SCREEN_H * FD2_UI_WINDOW_SCALE,
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
    free(g_ui_render.decompressed_tiles);
    free(g_ui_render.tile_offsets);
    free(g_ui_render.tile_widths);
    free(g_ui_render.tile_heights);
    free((void*)g_ui_render.tile_data);
    SDL_Quit();
}

/**
 * 设置调色板 (6位RGB → 8位)
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
 * 清屏
 */
static void fd2_ui_clear_screen(u8 color) {
    memset(g_ui_render.screen, color, FD2_SCREEN_BUFFER_SIZE);
}

/**
 * 加载FDOTHER索引5的tile数据 (窗口tile集)
 * 注意：sub_111BA(..., 5)加载的是索引5
 */
static const u8* fd2_ui_load_tile_set(const char* data_dir, u32* out_size) {
    char path[512];
    snprintf(path, sizeof(path), "%s/FDOTHER.DAT", data_dir);
    
    FILE* f = fopen(path, "rb");
    if (!f) {
        fprintf(stderr, "无法打开 %s\n", path);
        return NULL;
    }
    
    char magic[6];
    if (fread(magic, 1, 6, f) != 6 || memcmp(magic, "LLLLLL", 6) != 0) {
        fclose(f);
        return NULL;
    }
    
    u32 resource_count;
    if (fread(&resource_count, 4, 1, f) != 1) {
        fclose(f);
        return NULL;
    }
    
    if (5 >= resource_count) {
        fclose(f);
        return NULL;
    }
    
    u32* offsets = malloc(resource_count * 4);
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
    
    u32 start = offsets[5];
    u32 end = (5 + 1 < resource_count) ? offsets[5 + 1] : (u32)-1;
    u32 size;
    if (end == (u32)-1) {
        fseek(f, 0, SEEK_END);
        long file_size = ftell(f);
        size = file_size - start;
    } else {
        size = end - start;
    }
    
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
    printf("  [LOAD] FDOTHER索引4 tile数据: size=%u\n", size);
    return data;
}

/**
 * 解析tile集数据 (索引4已经是解压后的原始数据)
 * 
 * Tile集格式:
 * - 偏移0-3: 魔术字节 "LMI1"
 * - 偏移4-5: tile数量 (WORD)
 * - 偏移6+: tile偏移表 (DWORD数组) - 值为相对偏移
 * - 每个tile: 宽度(WORD) + 高度(WORD) + 原始像素数据 (无压缩)
 */
static int fd2_ui_parse_tile_set(const u8* raw_data, u32 raw_size) {
    if (!raw_data || raw_size < 6) return -1;
    
    if (memcmp(raw_data, "LMI1", 4) != 0) {
        fprintf(stderr, "  [WARN] 魔术字节不是'LMI1'\n");
        return -1;
    }
    
    u16 tile_count = raw_data[4] | (raw_data[5] << 8);
    if (tile_count == 0 || tile_count > 1000) return -1;
    
    g_ui_render.tile_count = tile_count;
    printf("  [PARSE] Tile数量: %d\n", tile_count);
    
    g_ui_render.tile_offsets = (u32*)malloc(tile_count * sizeof(u32));
    g_ui_render.tile_widths = (u16*)malloc(tile_count * sizeof(u16));
    g_ui_render.tile_heights = (u16*)malloc(tile_count * sizeof(u16));
    if (!g_ui_render.tile_offsets || !g_ui_render.tile_widths || !g_ui_render.tile_heights) return -1;
    
    /* 解析tile偏移表并存储宽高 */
    int valid_tiles = 0;
    for (int i = 0; i < tile_count; i++) {
        u32 offset_addr = 6 + i * 4;
        if (offset_addr + 4 > raw_size) break;
        
        u32 tile_offset = raw_data[offset_addr] | 
                          (raw_data[offset_addr + 1] << 8) |
                          (raw_data[offset_addr + 2] << 16) |
                          (raw_data[offset_addr + 3] << 24);
        
        g_ui_render.tile_offsets[i] = tile_offset;
        
        u32 tile_addr = tile_offset;
        if (tile_addr + 4 <= raw_size) {
            u16 w = raw_data[tile_addr] | (raw_data[tile_addr + 1] << 8);
            u16 h = raw_data[tile_addr + 2] | (raw_data[tile_addr + 3] << 8);
            g_ui_render.tile_widths[i] = w;
            g_ui_render.tile_heights[i] = h;
            
            if (w > 0 && h > 0 && w <= 64 && h <= 64) {
                valid_tiles++;
            }
        }
        
        if (i < 5) {
            printf("    Tile %d: offset=0x%X, %dx%d\n", i, tile_offset, 
                   g_ui_render.tile_widths[i], g_ui_render.tile_heights[i]);
        }
    }
    
    /* 直接使用原始数据，不需要解压 */
    g_ui_render.decompressed_tiles = (u8*)raw_data;
    
    printf("  [PARSE] Tile数据解析完成 (原始数据，无压缩), 有效tile=%d\n", valid_tiles);
    return 0;
}

/**
 * 根据tile索引获取tile数据指针 (sub_1685C逻辑)
 * 
 * sub_1685C: tile_ptr = base + *(DWORD *)(base + tile_index*4 + 6)
 */
static const u8* fd2_ui_get_tile_ptr(int tile_index) {
    if (!g_ui_render.decompressed_tiles || !g_ui_render.tile_offsets) return NULL;
    
    if (tile_index < 0 || tile_index >= g_ui_render.tile_count) {
        return NULL;
    }
    
    /* tile_offsets已经是相对偏移，直接加到基地址 */
    return g_ui_render.decompressed_tiles + g_ui_render.tile_offsets[tile_index];
}

/**
 * 渲染单个tile到屏幕 (sub_4ED0B逻辑: 逐行复制所有像素)
 */
static void fd2_ui_render_tile(int tile_index, int dx, int dy) {
    const u8* tile_data = fd2_ui_get_tile_ptr(tile_index);
    if (!tile_data) return;
    
    /* tile数据格式: 宽度(WORD) + 高度(WORD) + 像素数据 */
    int tw = tile_data[0] | (tile_data[1] << 8);
    int th = tile_data[2] | (tile_data[3] << 8);
    
    if (tw <= 0 || th <= 0 || tw > 64 || th > 64) return;
    
    const u8* pixels = tile_data + 4;
    
    for (int y = 0; y < th; y++) {
        int sy = dy + y;
        if (sy < 0 || sy >= FD2_SCREEN_H) continue;
        
        for (int x = 0; x < tw; x++) {
            int sx = dx + x;
            if (sx < 0 || sx >= FD2_SCREEN_W) continue;
            
            u8 pixel = pixels[y * tw + x];
            /* 跳过0值像素（透明色） */
            if (pixel != 0) {
                g_ui_render.screen[sy * FD2_SCREEN_W + sx] = pixel;
            }
        }
    }
}

/**
 * 1:1实现sub_168B6窗口绘制函数
 * 
 * 根据MCP反编译代码，参数映射:
 * a5 = x坐标 (像素)
 * a6 = tile_size (16)
 * a7 = y坐标偏移 (48 = 3 * 16)
 * a8 = y坐标 (像素)
 * a9 = rows (行数)
 * a10 = cols (列数)
 * 
 * Tile索引使用:
 * 1=左上角, 2=右上角, 3=左下角, 4=右下角
 * 5=上边框, 6=上边框特殊, 7=下边框特殊, 8=下边框
 * 9=左边框上, 10=左边框中, 11=左边框下
 * 12=右边框上, 14=右边框中, 15=右边框下, 16=右边框特殊上, 17=右边框特殊下
 * 13=内容区域
 */
static void fd2_ui_draw_window(int x, int y, int rows, int cols) {
    if (cols < 2 || rows < 2) return;
    
    int tile_size = 16;
    int dx = x;
    int dy = y;
    
    /* 四个角 */
    fd2_ui_render_tile(1, dx, dy);
    fd2_ui_render_tile(2, dx + (cols - 1) * tile_size, dy);
    fd2_ui_render_tile(3, dx, dy + (rows - 1) * tile_size);
    fd2_ui_render_tile(4, dx + (cols - 1) * tile_size, dy + (rows - 1) * tile_size);
    
    /* 上边框 */
    for (int i = 1; i < cols - 1; i++) {
        fd2_ui_render_tile(5, dx + i * tile_size, dy);
    }
    
    /* 下边框 */
    for (int i = 1; i < cols - 1; i++) {
        fd2_ui_render_tile(8, dx + i * tile_size, dy + (rows - 1) * tile_size);
    }
    
    /* 左边框 */
    for (int i = 1; i < rows - 1; i++) {
        fd2_ui_render_tile(14, dx, dy + i * tile_size);
    }
    
    /* 右边框 */
    for (int i = 1; i < rows - 1; i++) {
        fd2_ui_render_tile(15, dx + (cols - 1) * tile_size, dy + i * tile_size);
    }
    
    /* 内容区域 */
    for (int row = 1; row < rows - 1; row++) {
        for (int col = 1; col < cols - 1; col++) {
            fd2_ui_render_tile(13, dx + col * tile_size, dy + row * tile_size);
        }
    }
}

/**
 * 显示屏幕
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

/**
 * 加载调色板 (FDOTHER索引75)
 */
static int fd2_ui_load_palette(const char* data_dir) {
    char path[512];
    snprintf(path, sizeof(path), "%s/FDOTHER.DAT", data_dir);
    
    FILE* f = fopen(path, "rb");
    if (!f) return -1;
    
    char magic[6];
    if (fread(magic, 1, 6, f) != 6 || memcmp(magic, "LLLLLL", 6) != 0) {
        fclose(f);
        return -1;
    }
    
    u32 resource_count;
    if (fread(&resource_count, 4, 1, f) != 1) {
        fclose(f);
        return -1;
    }
    
    if (75 >= resource_count) {
        fclose(f);
        return -1;
    }
    
    u32* offsets = malloc(resource_count * 4);
    if (!offsets) {
        fclose(f);
        return -1;
    }
    fseek(f, 10, SEEK_SET);
    if (fread(offsets, 4, resource_count, f) != resource_count) {
        free(offsets);
        fclose(f);
        return -1;
    }
    
    u32 start = offsets[75];
    u32 end = (75 + 1 < resource_count) ? offsets[75 + 1] : (u32)-1;
    u32 size;
    if (end == (u32)-1) {
        fseek(f, 0, SEEK_END);
        long file_size = ftell(f);
        size = file_size - start;
    } else {
        size = end - start;
    }
    
    if (size < FD2_PALETTE_SIZE) {
        free(offsets);
        fclose(f);
        return -1;
    }
    
    u8* pal_data = malloc(size);
    if (!pal_data) {
        free(offsets);
        fclose(f);
        return -1;
    }
    
    fseek(f, start, SEEK_SET);
    if (fread(pal_data, 1, size, f) != size) {
        free(pal_data);
        free(offsets);
        fclose(f);
        return -1;
    }
    
    free(offsets);
    fclose(f);
    
    fd2_ui_set_palette_6bit(pal_data);
    free(pal_data);
    
    printf("  [PALETTE] 加载调色板成功 (FDOTHER索引75)\n");
    return 0;
}

/**
 * 测试1: 主菜单对话框
 */
static void fd2_ui_test_main_menu(void) {
    printf("\n=== 测试1: 主菜单对话框 ===\n");
    
    fd2_ui_clear_screen(0);
    fd2_ui_present();
    SDL_Delay(500);
    
    printf("  [1] 绘制主菜单窗口 (19列 x 5行)\n");
    fd2_ui_draw_window(2 * 16, 3 * 16, 5, 19);
    fd2_ui_present();
    
    printf("  [2] 对话框绘制完成\n");
    fd2_ui_wait_for_key("主菜单对话框");
}

/**
 * 测试2: 属性界面
 */
static void fd2_ui_test_status_dialog(void) {
    printf("\n=== 测试2: 属性界面 ===\n");
    
    fd2_ui_clear_screen(0);
    fd2_ui_present();
    SDL_Delay(500);
    
    printf("  [1] 绘制属性窗口 (18列 x 12行)\n");
    fd2_ui_draw_window(1 * 16, 1 * 16, 12, 18);
    fd2_ui_present();
    
    printf("  [2] 属性界面绘制完成\n");
    fd2_ui_wait_for_key("属性界面");
}

/**
 * 测试3: 读盘/存盘菜单
 */
static void fd2_ui_test_save_load_dialog(void) {
    printf("\n=== 测试3: 读盘/存盘菜单 ===\n");
    
    fd2_ui_clear_screen(0);
    fd2_ui_present();
    SDL_Delay(500);
    
    printf("  [1] 绘制读盘窗口 (16列 x 8行)\n");
    fd2_ui_draw_window(3 * 16, 2 * 16, 8, 16);
    fd2_ui_present();
    
    printf("  [2] 读盘菜单绘制完成\n");
    fd2_ui_wait_for_key("读盘/存盘菜单");
}

/**
 * 测试4: 战场菜单
 */
static void fd2_ui_test_battle_menu(void) {
    printf("\n=== 测试4: 战场菜单 ===\n");
    
    fd2_ui_clear_screen(0);
    fd2_ui_present();
    SDL_Delay(500);
    
    printf("  [1] 绘制战场窗口 (10列 x 5行)\n");
    fd2_ui_draw_window(5 * 16, 4 * 16, 5, 10);
    fd2_ui_present();
    
    printf("  [2] 战场菜单绘制完成\n");
    fd2_ui_wait_for_key("战场菜单");
}

/**
 * 测试5: 多个窗口组合
 */
static void fd2_ui_test_multiple_windows(void) {
    printf("\n=== 测试5: 多窗口组合测试 ===\n");
    
    fd2_ui_clear_screen(0);
    fd2_ui_present();
    SDL_Delay(500);
    
    printf("  [1] 绘制主窗口 (20列 x 8行)\n");
    fd2_ui_draw_window(1 * 16, 1 * 16, 8, 20);
    fd2_ui_present();
    SDL_Delay(500);
    
    printf("  [2] 绘制子窗口 (10列 x 4行)\n");
    fd2_ui_draw_window(4 * 16, 3 * 16, 4, 10);
    fd2_ui_present();
    
    printf("  [3] 多窗口组合测试完成\n");
    fd2_ui_wait_for_key("多窗口组合");
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

    printf("FD2 UI渲染测试程序 (1:1 MCP汇编复原)\n");
    printf("==========================================\n");
    printf("数据目录: %s\n", data_dir);
    printf("屏幕尺寸: %dx%d (DOS VGA模式)\n\n", FD2_SCREEN_W, FD2_SCREEN_H);

    if (fd2_ui_render_init() != 0) {
        fprintf(stderr, "UI渲染系统初始化失败\n");
        return 1;
    }

    if (fd2_ui_load_palette(data_dir) != 0) {
        fprintf(stderr, "  [WARN] 调色板加载失败，使用默认调色板\n");
    }
    
    const u8* tile_data = fd2_ui_load_tile_set(data_dir, &g_ui_render.tile_data_size);
    if (tile_data) {
        g_ui_render.tile_data = tile_data;
        
        if (fd2_ui_parse_tile_set(tile_data, g_ui_render.tile_data_size) == 0) {
            printf("  [INIT] tile数据解析并解压成功\n");
        } else {
            fprintf(stderr, "  [WARN] tile数据解析失败\n");
        }
    } else {
        fprintf(stderr, "  [WARN] FDOTHER索引5 tile数据加载失败\n");
    }

    printf("\n控制: 按空格键切换到下一个测试，ESC/Q退出\n\n");

    int test_index = 0;

    while (1) {
        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) goto done;
            if (e.type == SDL_KEYDOWN) {
                if (e.key.keysym.sym == SDLK_ESCAPE || e.key.keysym.sym == SDLK_q) {
                    goto done;
                }
            }
        }

        switch (test_index) {
            case 0: fd2_ui_test_main_menu(); break;
            case 1: fd2_ui_test_status_dialog(); break;
            case 2: fd2_ui_test_save_load_dialog(); break;
            case 3: fd2_ui_test_battle_menu(); break;
            case 4: fd2_ui_test_multiple_windows(); break;
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
    printf("UI渲染测试完成\n");
    return 0;
}
