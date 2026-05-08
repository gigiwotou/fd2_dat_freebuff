#include <SDL2/SDL.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>

typedef uint32_t u32;

int main(int argc, char* argv[]) {
    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        printf("SDL_Init failed: %s\n", SDL_GetError());
        return 1;
    }
    printf("SDL initialized\n");

    SDL_Window* win = SDL_CreateWindow("SDL Test", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, 
                                       640, 400, SDL_WINDOW_SHOWN);
    if (!win) {
        printf("Window create failed: %s\n", SDL_GetError());
        SDL_Quit();
        return 1;
    }
    printf("Window created\n");

    SDL_Renderer* ren = SDL_CreateRenderer(win, -1, SDL_RENDERER_ACCELERATED);
    if (!ren) {
        printf("Renderer create failed: %s\n", SDL_GetError());
        SDL_DestroyWindow(win);
        SDL_Quit();
        return 1;
    }
    printf("Renderer created\n");

    SDL_Texture* tex = SDL_CreateTexture(ren, SDL_PIXELFORMAT_ARGB8888, 
                                          SDL_TEXTUREACCESS_STREAMING, 320, 200);
    if (!tex) {
        printf("Texture create failed: %s\n", SDL_GetError());
        SDL_DestroyRenderer(ren);
        SDL_DestroyWindow(win);
        SDL_Quit();
        return 1;
    }
    printf("Texture created\n");

    /* 填充像素 - 白色方块测试 */
    u32 pixels[320 * 200];
    memset(pixels, 0, sizeof(pixels));  /* 黑色背景 */
    
    /* 白色方块在中央 */
    for (int y = 80; y < 120; y++) {
        for (int x = 120; x < 200; x++) {
            pixels[y * 320 + x] = 0xFFFFFFFF;  /* 白色 */
        }
    }
    
    /* 红色边框 */
    for (int x = 10; x < 310; x++) {
        pixels[10 * 320 + x] = 0xFFFF0000;   /* 红色 */
        pixels[190 * 320 + x] = 0xFFFF0000;
    }
    for (int y = 10; y < 190; y++) {
        pixels[y * 320 + 10] = 0xFFFF0000;
        pixels[y * 320 + 310] = 0xFFFF0000;
    }
    
    SDL_UpdateTexture(tex, NULL, pixels, 320 * sizeof(u32));
    SDL_RenderClear(ren);
    SDL_RenderCopy(ren, tex, NULL, NULL);
    SDL_RenderPresent(ren);
    
    printf("Test pattern rendered (white block with red border)\n");
    printf("If you see a white block with red border, SDL rendering is working!\n");
    printf("Window will close in 10 seconds...\n");
    fflush(stdout);
    
    SDL_Delay(10000);
    
    SDL_DestroyTexture(tex);
    SDL_DestroyRenderer(ren);
    SDL_DestroyWindow(win);
    SDL_Quit();
    
    printf("Test completed\n");
    return 0;
}
