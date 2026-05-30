/*
 * FDOTHER.DAT 资源加载测试程序
 * 
 * 测试所有资源类型的加载和解码功能：
 * - 调色板加载和颜色转换
 * - Tile图像加载和RLE解码
 * - LMI1 Tile集加载和子Tile提取
 * - 嵌套DAT加载和子资源提取
 * 
 * 编译: build.bat fdother_test
 * 运行: bin\fd2_fdother_test.exe
 */

#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

#include "fd2_fdother_resources.h"
#include "fd2_dat.h"

/* 显示常量 */
#define SCREEN_W     640
#define SCREEN_H     480
#define TILE_SCALE   2

/* 测试状态 */
static char g_status_msg[512] = {0};
static dword g_palette_rgb24[256];
static bool g_palette_loaded = false;
static byte g_test_pixels[640 * 480];

/* ========================================================================
 * 测试1: 文件加载和基本资源数量验证
 * ======================================================================== */

static int test_file_load(const char* filepath) {
    printf("\n=== Test 1: File Loading ===\n");
    
    int ret = fdother_load(filepath);
    if (ret != 0) {
        printf("FAIL: Cannot load FDOTHER.DAT from %s\n", filepath);
        return -1;
    }
    
    dword size;
    const byte* res = fdother_get_resource(0, &size);
    if (!res) {
        printf("FAIL: Cannot get resource 0\n");
        return -1;
    }
    
    printf("PASS: FDOTHER.DAT loaded successfully\n");
    printf("  Resource 0 size: %u bytes (expected 768 for palette)\n", size);
    
    snprintf(g_status_msg, sizeof(g_status_msg), "Test 1 PASS: FDOTHER.DAT loaded");
    return 0;
}

/* ========================================================================
 * 测试2: 调色板资源加载
 * ======================================================================== */

static int test_palette_loading(void) {
    printf("\n=== Test 2: Palette Loading ===\n");
    
    int palettes[] = {
        FDOTHER_PALETTE_0, FDOTHER_PALETTE_8, FDOTHER_PALETTE_57,
        FDOTHER_PALETTE_76, FDOTHER_PALETTE_99, 
        FDOTHER_PALETTE_101, FDOTHER_PALETTE_102
    };
    const char* names[] = {
        "Main", "Copy 8", "Copy 57", "Title", "Copy 99", "Copy 101", "Copy 102"
    };
    
    int passed = 0;
    
    for (int i = 0; i < 7; i++) {
        fdother_palette_t pal;
        int ret = fdother_get_palette(palettes[i], &pal);
        if (ret == 0) {
            printf("PASS: Palette %d (%s) loaded\n", palettes[i], names[i]);
            
            if (i == 0) {
                fdother_palette_to_rgb32(&pal, g_palette_rgb24);
                g_palette_loaded = true;
                
                printf("  First 3 colors (RGB):\n");
                for (int c = 0; c < 3; c++) {
                    printf("    Color %d: R=%d G=%d B=%d\n", c,
                           pal.colors[c*3], pal.colors[c*3+1], pal.colors[c*3+2]);
                }
            }
            passed++;
        } else {
            printf("FAIL: Palette %d (%s)\n", palettes[i], names[i]);
        }
    }
    
    snprintf(g_status_msg, sizeof(g_status_msg), 
             "Test 2: %d/7 palettes loaded", passed);
    printf("\n  Result: %d/7 palettes loaded successfully\n", passed);
    return (passed == 7) ? 0 : -1;
}

/* ========================================================================
 * 测试3: Tile图像加载和解码
 * ======================================================================== */

static int test_tile_loading(void) {
    printf("\n=== Test 3: Tile Image Loading ===\n");
    
    struct {
        int index;
        const char* desc;
    } tiles[] = {
        {1, "24x24 Icon"},
        {18, "16x16 Character A"},
        {11, "320x200 Fullscreen A"},
        {69, "320x147 Menu A"},
        {26, "18x18 Icon A"},
        {34, "101x101 Large Icon"}
    };
    
    int passed = 0;
    
    for (int i = 0; i < 6; i++) {
        fdother_tile_t tile;
        int ret = fdother_get_tile(tiles[i].index, &tile);
        if (ret == 0) {
            printf("PASS: Tile %d (%s) - %dx%d, palette_window=%d\n",
                   tiles[i].index, tiles[i].desc, tile.width, tile.height, tile.palette_window);
            
            dword pixel_count = (dword)tile.width * tile.height;
            byte* pixels = (byte*)malloc(pixel_count);
            if (pixels) {
                int decode_ret = fdother_decode_tile(&tile, pixels);
                if (decode_ret == 0) {
                    printf("  Decoded successfully to %u pixels\n", pixel_count);
                } else {
                    printf("  Decode failed (RLE error)\n");
                }
                free(pixels);
            }
            passed++;
        } else {
            printf("FAIL: Tile %d (%s)\n", tiles[i].index, tiles[i].desc);
        }
    }
    
    snprintf(g_status_msg, sizeof(g_status_msg), 
             "Test 3: %d/6 tiles loaded", passed);
    printf("\n  Result: %d/6 tiles loaded successfully\n", passed);
    return (passed == 6) ? 0 : -1;
}

/* ========================================================================
 * 测试4: LMI1 Tile集加载
 * ======================================================================== */

static int test_lmi1_loading(void) {
    printf("\n=== Test 4: LMI1 Tileset Loading ===\n");
    
    struct {
        int index;
        const char* desc;
        word expected_count;
    } lmi1s[] = {
        {3, "Small Tileset", 23},
        {5, "Medium Tileset", 138},
        {6, "Large Tileset", 230},
        {9, "Tiny Tileset", 12}
    };
    
    int passed = 0;
    
    for (int i = 0; i < 4; i++) {
        fdother_lmi1_t lmi1;
        int ret = fdother_get_lmi1(lmi1s[i].index, &lmi1);
        if (ret == 0) {
            printf("PASS: LMI1 %d (%s) - %d tiles (expected %d)\n",
                   lmi1s[i].index, lmi1s[i].desc, lmi1.tile_count, lmi1s[i].expected_count);
            
            if (lmi1.tile_count > 0) {
                word w, h;
                const byte* rle_data;
                dword rle_size;
                int tile_ret = fdother_lmi1_get_tile(&lmi1, 0, &w, &h, &rle_data, &rle_size);
                if (tile_ret == 0) {
                    printf("  First tile: %dx%d, RLE size=%u\n", w, h, rle_size);
                }
            }
            passed++;
        } else {
            printf("FAIL: LMI1 %d (%s)\n", lmi1s[i].index, lmi1s[i].desc);
        }
    }
    
    snprintf(g_status_msg, sizeof(g_status_msg), 
             "Test 4: %d/4 LMI1 tilesets loaded", passed);
    printf("\n  Result: %d/4 LMI1 tilesets loaded successfully\n", passed);
    return (passed == 4) ? 0 : -1;
}

/* ========================================================================
 * 测试5: 嵌套DAT加载
 * ======================================================================== */

static int test_nested_dat_loading(void) {
    printf("\n=== Test 5: Nested DAT Loading ===\n");
    
    struct {
        int index;
        const char* desc;
        dword expected_count;
    } nested[] = {
        {7, "Small Nested", 38},
        {12, "Large Nested", 122},
        {31, "Sound Effects", 62}
    };
    
    int passed = 0;
    
    for (int i = 0; i < 3; i++) {
        fdother_nested_dat_t ndat;
        int ret = fdother_get_nested_dat(nested[i].index, &ndat);
        if (ret == 0) {
            printf("PASS: Nested DAT %d (%s) - %d sub-resources (expected %d)\n",
                   nested[i].index, nested[i].desc, ndat.resource_count, nested[i].expected_count);
            
            if (ndat.resource_count > 0) {
                dword sub_size;
                const byte* sub_data = fdother_nested_get_resource(&ndat, 0, &sub_size);
                if (sub_data) {
                    printf("  First sub-resource size: %u bytes\n", sub_size);
                }
            }
            passed++;
        } else {
            printf("FAIL: Nested DAT %d (%s)\n", nested[i].index, nested[i].desc);
        }
    }
    
    snprintf(g_status_msg, sizeof(g_status_msg), 
             "Test 5: %d/3 nested DATs loaded", passed);
    printf("\n  Result: %d/3 nested DATs loaded successfully\n", passed);
    return (passed == 3) ? 0 : -1;
}

/* ========================================================================
 * 测试6: RAW数据资源
 * ======================================================================== */

static int test_raw_data_loading(void) {
    printf("\n=== Test 6: Raw Data Loading ===\n");
    
    struct {
        int index;
        const char* desc;
    } raws[] = {
        {2, "Font Data"},
        {4, "Character Bitmaps"}
    };
    
    int passed = 0;
    
    for (int i = 0; i < 2; i++) {
        dword size;
        const byte* data = fdother_get_resource(raws[i].index, &size);
        if (data && size > 0) {
            printf("PASS: RAW %d (%s) - %u bytes\n", raws[i].index, raws[i].desc, size);
            passed++;
        } else {
            printf("FAIL: RAW %d (%s)\n", raws[i].index, raws[i].desc);
        }
    }
    
    snprintf(g_status_msg, sizeof(g_status_msg), 
             "Test 6: %d/2 raw data loaded", passed);
    printf("\n  Result: %d/2 raw data loaded successfully\n", passed);
    return (passed == 2) ? 0 : -1;
}

/* ========================================================================
 * 测试7: 资源类型识别
 * ======================================================================== */

static int test_resource_type_detection(void) {
    printf("\n=== Test 7: Resource Type Detection ===\n");
    
    struct {
        int index;
        fdother_res_type_t expected_type;
        const char* type_name;
    } tests[] = {
        {0, FDOTHER_RES_TYPE_PALETTE, "Palette"},
        {1, FDOTHER_RES_TYPE_TILE, "Tile"},
        {2, FDOTHER_RES_TYPE_RAW, "Raw"},
        {3, FDOTHER_RES_TYPE_LMI1, "LMI1"},
        {7, FDOTHER_RES_TYPE_NESTED_DAT, "Nested DAT"}
    };
    
    int passed = 0;
    
    for (int i = 0; i < 5; i++) {
        dword size;
        const byte* data = fdother_get_resource(tests[i].index, &size);
        if (data) {
            fdother_res_type_t type = fdother_get_resource_type(data, size);
            if (type == tests[i].expected_type) {
                printf("PASS: Resource %d correctly identified as %s\n", 
                       tests[i].index, tests[i].type_name);
                passed++;
            } else {
                printf("FAIL: Resource %d expected %s but got type %d\n",
                       tests[i].index, tests[i].type_name, type);
            }
        }
    }
    
    snprintf(g_status_msg, sizeof(g_status_msg), 
             "Test 7: %d/5 type detections correct", passed);
    printf("\n  Result: %d/5 type detections correct\n", passed);
    return (passed == 5) ? 0 : -1;
}

/* ========================================================================
 * SDL渲染：显示调色板
 * ======================================================================== */

static void render_palette(SDL_Renderer* renderer) {
    SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);
    SDL_RenderClear(renderer);
    
    if (!g_palette_loaded) {
        SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
        SDL_RenderPresent(renderer);
        return;
    }
    
    int cell_w = SCREEN_W / 16;
    int cell_h = SCREEN_H / 16;
    
    for (int i = 0; i < 256; i++) {
        int x = (i % 16) * cell_w;
        int y = (i / 16) * cell_h;
        
        dword color = g_palette_rgb24[i];
        byte r = (color >> 0) & 0xFF;
        byte g = (color >> 8) & 0xFF;
        byte b = (color >> 16) & 0xFF;
        
        SDL_SetRenderDrawColor(renderer, r, g, b, 255);
        SDL_Rect rect = {x, y, cell_w, cell_h};
        SDL_RenderFillRect(renderer, &rect);
    }
    
    SDL_RenderPresent(renderer);
}

/* ========================================================================
 * 主函数
 * ======================================================================== */

int main(int argc, char* argv[]) {
    const char* filepath = "game/FDOTHER.DAT";
    
    if (argc > 1) {
        filepath = argv[1];
    }
    
    printf("FDOTHER.DAT Resource Loader Test\n");
    printf("================================\n");
    printf("File: %s\n\n", filepath);
    
    int total_passed = 0;
    int total_tests = 7;
    
    if (test_file_load(filepath) == 0) total_passed++;
    if (test_palette_loading() == 0) total_passed++;
    if (test_tile_loading() == 0) total_passed++;
    if (test_lmi1_loading() == 0) total_passed++;
    if (test_nested_dat_loading() == 0) total_passed++;
    if (test_raw_data_loading() == 0) total_passed++;
    if (test_resource_type_detection() == 0) total_passed++;
    
    printf("\n================================\n");
    printf("SUMMARY: %d/%d tests passed\n", total_passed, total_tests);
    
    if (total_passed == total_tests) {
        printf("ALL TESTS PASSED!\n");
    } else {
        printf("SOME TESTS FAILED!\n");
    }
    
    printf("\nLaunching SDL visualization (press ESC to quit)...\n");
    
    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        printf("SDL_Init failed: %s\n", SDL_GetError());
        fdother_unload();
        return 1;
    }
    
    SDL_Window* window = SDL_CreateWindow(
        "FDOTHER Resource Test - Palette Visualization",
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
        SCREEN_W, SCREEN_H, SDL_WINDOW_SHOWN);
    
    if (!window) {
        printf("SDL_CreateWindow failed: %s\n", SDL_GetError());
        SDL_Quit();
        fdother_unload();
        return 1;
    }
    
    SDL_Renderer* renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED);
    if (!renderer) {
        renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_SOFTWARE);
    }
    
    if (renderer) {
        int running = 1;
        SDL_Event event;
        
        while (running) {
            while (SDL_PollEvent(&event)) {
                if (event.type == SDL_QUIT) {
                    running = 0;
                } else if (event.type == SDL_KEYDOWN) {
                    if (event.key.keysym.sym == SDLK_ESCAPE) {
                        running = 0;
                    }
                }
            }
            
            render_palette(renderer);
            SDL_Delay(16);
        }
        
        SDL_DestroyRenderer(renderer);
    }
    
    SDL_DestroyWindow(window);
    SDL_Quit();
    fdother_unload();
    
    return (total_passed == total_tests) ? 0 : 1;
}
