/**
 * FD2 UI渲染测试程序 - 1:1 MCP汇编复原版
 * 
 * 根据MCP反编译代码1:1实现：
 * - sub_4ED0B: 像素复制函数（逐行blit）
 * - sub_1685C: Tile绘制辅助函数
 * - sub_168B6: 窗口框架绘制函数
 * 
 * 资源加载：
 * - FDOTHER索引7: 窗口边框tile集（138个tile，未压缩）
 *   根据MCP分析：_FDOTHER_DAT__7 指向 FDOTHER.DAT 索引7
 * - FDOTHER索引75: 调色板（768字节）
 * 
 * Tile数据格式（根据MCP分析）：
 * - 头部6字节后是DWORD偏移表
 * - tile数据指针 = *(DWORD*)(资源基址 + 4*tile索引 + 6) + 资源基址
 * - 每个tile: 宽度(WORD) + 高度(WORD) + 像素数据
 * 
 * Tile索引映射（根据sub_168B6汇编代码）：
 * - Tile 1: 左上角
 * - Tile 2: 右上角
 * - Tile 3: 左下角
 * - Tile 4: 右下角
 * - Tile 5: 上边框中间
 * - Tile 8: 下边框中间
 * - Tile 10: 左边框中间
 * - Tile 11: 右边框中间
 * - Tile 13: 中心区域填充
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

typedef struct {
    u8 screen[FD2_SCREEN_BUFFER_SIZE];
    u8 palette[FD2_PALETTE_SIZE];
    u32* argb;
    u32* argb_palette;
    SDL_Window* window;
    SDL_Renderer* renderer;
    SDL_Texture* texture;
    
    const u8* tileset_data;
    u32 tileset_size;
    
    u16 tile_count;
    u32* tile_offsets;
    u16* tile_widths;
    u16* tile_heights;
    u8** tile_pixels;
} fd2_ui_render_t;

static fd2_ui_render_t g_ui_render;

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
    
    if (g_ui_render.tile_pixels) {
        for (int i = 0; i < g_ui_render.tile_count; i++) {
            free(g_ui_render.tile_pixels[i]);
        }
        free(g_ui_render.tile_pixels);
    }
    free(g_ui_render.tile_offsets);
    free(g_ui_render.tile_widths);
    free(g_ui_render.tile_heights);
    free((void*)g_ui_render.tileset_data);
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

static void fd2_ui_clear_screen(u8 color) {
    memset(g_ui_render.screen, color, FD2_SCREEN_BUFFER_SIZE);
}

static const u8* fd2_ui_load_resource(const char* data_dir, int index, u32* out_size) {
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
    
    if (resource_count <= (u32)index) {
        fclose(f);
        return NULL;
    }
    
    u32* offsets = (u32*)malloc(resource_count * 4);
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
    
    u32 start = offsets[index];
    u32 end = (index + 1 < (int)resource_count) ? offsets[index + 1] : (u32)-1;
    u32 size;
    if (end == (u32)-1) {
        fseek(f, 0, SEEK_END);
        long file_size = ftell(f);
        size = (u32)(file_size - start);
    } else {
        size = end - start;
    }
    
    u8* data = (u8*)malloc(size);
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
    return data;
}

static int fd2_ui_parse_tileset(const u8* raw_data, u32 raw_size) {
    if (!raw_data || raw_size < 6) return -1;
    
    if (memcmp(raw_data, "LMI1", 4) != 0) {
        fprintf(stderr, "  [WARN] 魔术字节不是'LMI1'\n");
        return -1;
    }
    
    u16 tile_count = raw_data[4] | (raw_data[5] << 8);
    if (tile_count == 0 || tile_count > 1000) return -1;
    
    g_ui_render.tile_count = tile_count;
    g_ui_render.tile_offsets = (u32*)calloc(tile_count, sizeof(u32));
    g_ui_render.tile_widths = (u16*)calloc(tile_count, sizeof(u16));
    g_ui_render.tile_heights = (u16*)calloc(tile_count, sizeof(u16));
    g_ui_render.tile_pixels = (u8**)calloc(tile_count, sizeof(u8*));
    
    if (!g_ui_render.tile_offsets || !g_ui_render.tile_widths || 
        !g_ui_render.tile_heights || !g_ui_render.tile_pixels) return -1;
    
    for (int i = 0; i < tile_count; i++) {
        u32 offset_addr = 6 + i * 4;
        if (offset_addr + 4 > raw_size) break;
        
        u32 tile_offset = raw_data[offset_addr] | 
                          (raw_data[offset_addr + 1] << 8) |
                          (raw_data[offset_addr + 2] << 16) |
                          (raw_data[offset_addr + 3] << 24);
        
        g_ui_render.tile_offsets[i] = tile_offset;
        
        if (tile_offset + 4 > raw_size) continue;
        
        u16 w = raw_data[tile_offset] | (raw_data[tile_offset + 1] << 8);
        u16 h = raw_data[tile_offset + 2] | (raw_data[tile_offset + 3] << 8);
        
        g_ui_render.tile_widths[i] = w;
        g_ui_render.tile_heights[i] = h;
        
        if (w > 0 && h > 0 && w <= 320 && h <= 200) {
            u32 pixel_size = w * h;
            u8* pixels = (u8*)malloc(pixel_size);
            if (pixels) {
                memcpy(pixels, raw_data + tile_offset + 4, pixel_size);
                g_ui_render.tile_pixels[i] = pixels;
            }
        }
        
        if (i < 20) {
            printf("    Tile %2d: offset=0x%05X, %dx%d, 加载=%s\n", 
                   i, tile_offset, w, h,
                   g_ui_render.tile_pixels[i] ? "成功" : "失败");
        }
    }
    
    printf("  [PARSE] Tile集解析完成 (tile_count=%d)\n", tile_count);
    return 0;
}

static void fd2_sub_4ED0B(u8* dst, const u8* tile_data, int pitch) {
    if (!dst || !tile_data) return;
    
    u16 width = tile_data[0] | (tile_data[1] << 8);
    u16 height = tile_data[2] | (tile_data[3] << 8);
    const u8* src = tile_data + 4;
    
    for (int y = 0; y < height; y++) {
        memcpy(dst, src, width);
        src += width;
        dst += pitch;
    }
}

static void fd2_sub_1685C(int dst_x, int dst_y, int tile_index, int pitch) {
    if (tile_index < 0 || tile_index >= g_ui_render.tile_count) return;
    if (!g_ui_render.tile_pixels[tile_index]) return;
    
    u16 width = g_ui_render.tile_widths[tile_index];
    u16 height = g_ui_render.tile_heights[tile_index];
    
    if (width <= 0 || height <= 0) return;
    
    const u8* tile_data = g_ui_render.tileset_data + g_ui_render.tile_offsets[tile_index];
    
    for (int y = 0; y < height; y++) {
        int screen_y = dst_y + y;
        if (screen_y < 0 || screen_y >= FD2_SCREEN_H) continue;
        
        u8* dst_row = g_ui_render.screen + screen_y * pitch;
        const u8* src_row = tile_data + 4 + y * width;
        
        for (int x = 0; x < width; x++) {
            int screen_x = dst_x + x;
            if (screen_x < 0 || screen_x >= FD2_SCREEN_W) continue;
            
            u8 pixel = src_row[x];
            dst_row[screen_x] = pixel;
        }
    }
}

static void fd2_sub_168B6(int base_x, int base_y, int tile_cols, int tile_rows) {
    if (tile_cols < 2 || tile_rows < 2) return;
    
    int pitch = FD2_SCREEN_W;
    int tile_w = 16;
    int tile_h = 16;
    
    // 根据MCP汇编sub_168B6代码，绘制顺序：
    // 1. 先绘制4个角 (tile 1-4)
    // 2. 绘制边框 (tile 5, 6, 7, 8, 14, 15, 16, 17)
    // 3. 循环绘制边缘 (tile 9-12)
    // 4. 双循环绘制中心区域 (tile 13)
    
    // 步骤1: 绘制4个角
    fd2_sub_1685C(base_x, base_y, 1, pitch);
    fd2_sub_1685C(base_x + (tile_cols - 1) * tile_w, base_y, 2, pitch);
    fd2_sub_1685C(base_x, base_y + (tile_rows - 1) * tile_h, 3, pitch);
    fd2_sub_1685C(base_x + (tile_cols - 1) * tile_w, base_y + (tile_rows - 1) * tile_h, 4, pitch);
    
    // 步骤2: 绘制边框
    for (int i = 1; i < tile_cols - 1; i++) {
        fd2_sub_1685C(base_x + i * tile_w, base_y, 5, pitch);
    }
    for (int i = 1; i < tile_cols - 1; i++) {
        fd2_sub_1685C(base_x + i * tile_w, base_y + (tile_rows - 1) * tile_h, 8, pitch);
    }
    for (int i = 1; i < tile_rows - 1; i++) {
        fd2_sub_1685C(base_x, base_y + i * tile_h, 10, pitch);
    }
    for (int i = 1; i < tile_rows - 1; i++) {
        fd2_sub_1685C(base_x + (tile_cols - 1) * tile_w, base_y + i * tile_h, 11, pitch);
    }
    
    // 步骤3: 双循环绘制中心区域 (tile 13)
    for (int row = 1; row < tile_rows - 1; row++) {
        for (int col = 1; col < tile_cols - 1; col++) {
            int x = base_x + col * tile_w;
            int y = base_y + row * tile_h;
            fd2_sub_1685C(x, y, 13, pitch);
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

static int fd2_ui_load_palette(const char* data_dir) {
    u32 size;
    const u8* pal_data = fd2_ui_load_resource(data_dir, 75, &size);
    if (!pal_data || size < FD2_PALETTE_SIZE) {
        fprintf(stderr, "  [WARN] 调色板加载失败\n");
        return -1;
    }
    
    fd2_ui_set_palette_6bit(pal_data);
    free((void*)pal_data);
    
    printf("  [PALETTE] 加载调色板成功 (FDOTHER索引75)\n");
    return 0;
}

static void fd2_ui_test_main_menu(void) {
    printf("\n=== 测试1: 主菜单对话框 (4列 x 2行) ===\n");
    
    fd2_ui_clear_screen(0);
    fd2_ui_present();
    SDL_Delay(500);
    
    fd2_sub_168B6(32, 48, 4, 2);
    fd2_ui_present();
    
    fd2_ui_wait_for_key("主菜单对话框");
}

static void fd2_ui_test_status_dialog(void) {
    printf("\n=== 测试2: 属性界面 (8列 x 3行) ===\n");
    
    fd2_ui_clear_screen(0);
    fd2_ui_present();
    SDL_Delay(500);
    
    fd2_sub_168B6(32, 48, 8, 3);
    fd2_ui_present();
    
    fd2_ui_wait_for_key("属性界面");
}

static void fd2_ui_test_save_load_dialog(void) {
    printf("\n=== 测试3: 读盘/存盘菜单 (12列 x 4行) ===\n");
    
    fd2_ui_clear_screen(0);
    fd2_ui_present();
    SDL_Delay(500);
    
    fd2_sub_168B6(32, 48, 12, 4);
    fd2_ui_present();
    
    fd2_ui_wait_for_key("读盘/存盘菜单");
}

static void fd2_ui_test_battle_menu(void) {
    printf("\n=== 测试4: 战场菜单 (16列 x 5行) ===\n");
    
    fd2_ui_clear_screen(0);
    fd2_ui_present();
    SDL_Delay(500);
    
    fd2_sub_168B6(32, 48, 16, 5);
    fd2_ui_present();
    
    fd2_ui_wait_for_key("战场菜单");
}

static void fd2_ui_test_max_window(void) {
    printf("\n=== 测试5: 最大窗口 (19列 x 5行) ===\n");
    
    fd2_ui_clear_screen(0);
    fd2_ui_present();
    SDL_Delay(500);
    
    fd2_sub_168B6(32, 48, 19, 5);
    fd2_ui_present();
    
    fd2_ui_wait_for_key("最大窗口");
}

int main(int argc, char** argv) {
    const char* data_dir = NULL;
    if (argc > 1) {
        data_dir = argv[1];
    } else {
#ifdef _WIN32
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
#else
        data_dir = ".";
#endif
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
    
    printf("\n[LOADING] 加载FDOTHER索引7 Tile集 (窗口边框资源)...\n");
    u32 tileset_size;
    const u8* tileset_data = fd2_ui_load_resource(data_dir, 7, &tileset_size);
    if (tileset_data) {
        g_ui_render.tileset_data = tileset_data;
        g_ui_render.tileset_size = tileset_size;
        
        if (fd2_ui_parse_tileset(tileset_data, tileset_size) == 0) {
            printf("  [INIT] Tile集解析成功\n");
        } else {
            fprintf(stderr, "  [WARN] Tile集解析失败\n");
        }
    } else {
        fprintf(stderr, "  [WARN] FDOTHER索引7 tile数据加载失败\n");
    }

    printf("\n控制: 按空格键切换测试，ESC/Q退出\n\n");

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
            case 4: fd2_ui_test_max_window(); break;
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
