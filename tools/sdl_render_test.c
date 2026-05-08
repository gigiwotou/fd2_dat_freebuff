#include <SDL2/SDL.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>

#define SDL_MAIN_HANDLED

typedef uint32_t u32;

int main(int argc, char* argv[]) {
    printf("SDL Test Program Starting...\n");
    fflush(stdout);
    
    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        printf("SDL_Init failed: %s\n", SDL_GetError());
        return 1;
    }
    printf("SDL initialized OK\n");
    fflush(stdout);

    SDL_Window* win = SDL_CreateWindow("SDL Render Test", 
                                       SDL_WINDOWPOS_CENTERED, 
                                       SDL_WINDOWPOS_CENTERED, 
                                       640, 400, 
                                       SDL_WINDOW_SHOWN);
    if (!win) {
        printf("SDL_CreateWindow failed: %s\n", SDL_GetError());
        SDL_Quit();
        return 1;
    }
    printf("Window created OK\n");
    fflush(stdout);

    SDL_Renderer* ren = SDL_CreateRenderer(win, -1, SDL_RENDERER_ACCELERATED);
    if (!ren) {
        printf("SDL_CreateRenderer failed: %s\n", SDL_GetError());
        SDL_DestroyWindow(win);
        SDL_Quit();
        return 1;
    }
    printf("Renderer created OK\n");
    fflush(stdout);

    /* 创建320x200纹理 */
    SDL_Texture* tex = SDL_CreateTexture(ren, 
                                          SDL_PIXELFORMAT_ARGB8888,
                                          SDL_TEXTUREACCESS_STREAMING, 
                                          320, 200);
    if (!tex) {
        printf("SDL_CreateTexture failed: %s\n", SDL_GetError());
        SDL_DestroyRenderer(ren);
        SDL_DestroyWindow(win);
        SDL_Quit();
        return 1;
    }
    printf("Texture created OK\n");
    fflush(stdout);

    /* 填充测试图案 */
    u32 pixels[320 * 200];
    memset(pixels, 0, sizeof(pixels));  /* 黑色背景 */
    
    /* 白色方块 */
    for (int y = 50; y < 150; y++) {
        for (int x = 100; x < 220; x++) {
            pixels[y * 320 + x] = 0xFFFFFFFF;
        }
    }
    
    /* 红色文字区域 */
    for (int y = 70; y < 90; y++) {
        for (int x = 120; x < 200; x++) {
            pixels[y * 320 + x] = 0xFFFF0000;
        }
    }

    /* 渲染第一帧 - 白色方块 */
    SDL_UpdateTexture(tex, NULL, pixels, 320 * sizeof(u32));
    SDL_RenderClear(ren);
    SDL_RenderCopy(ren, tex, NULL, NULL);
    SDL_RenderPresent(ren);
    printf("Frame 1 rendered: White block with red area\n");
    printf("You should see a white block (100-220, 50-150) with red area\n");
    printf("Waiting 3 seconds...\n");
    fflush(stdout);
    SDL_Delay(3000);

    /* 渲染第二帧 - 绿色背景 */
    for (int i = 0; i < 320 * 200; i++) {
        pixels[i] = 0xFF00FF00;  /* 绿色 */
    }
    /* 蓝色方块 */
    for (int y = 50; y < 150; y++) {
        for (int x = 100; x < 220; x++) {
            pixels[y * 320 + x] = 0xFF0000FF;
        }
    }
    
    SDL_UpdateTexture(tex, NULL, pixels, 320 * sizeof(u32));
    SDL_RenderClear(ren);
    SDL_RenderCopy(ren, tex, NULL, NULL);
    SDL_RenderPresent(ren);
    printf("Frame 2 rendered: Green background with blue block\n");
    printf("Waiting 3 seconds...\n");
    fflush(stdout);
    SDL_Delay(3000);

    /* 清理 */
    SDL_DestroyTexture(tex);
    SDL_DestroyRenderer(ren);
    SDL_DestroyWindow(win);
    SDL_Quit();
    
    printf("Test completed successfully!\n");
    fflush(stdout);
    return 0;
}
