/* 验证LMI1 tile解码 (基于sub_4ED0B) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <SDL2/SDL.h>

#include "fd2_types.h"
#include "fd2_fdother_resources.h"

int main(int argc, char* argv[]) {
    if (argc < 2) {
        printf("用法: %s <index>\n", argv[0]);
        return 1;
    }
    
    int lmi1_index = atoi(argv[1]);
    
    /* 加载FDOTHER.DAT */
    if (fdother_load("bin/FDOTHER.DAT") != 0) {
        printf("无法加载FDOTHER.DAT\n");
        return 1;
    }
    
    fdother_lmi1_t lmi1;
    if (fdother_get_lmi1(lmi1_index, &lmi1) != 0) {
        printf("无法加载LMI1 %d\n", lmi1_index);
        return 1;
    }
    
    printf("LMI1 %d: %d tiles, size=%u\n", lmi1_index, lmi1.tile_count, lmi1.size);
    
    /* 验证每个tile的尺寸 */
    for (int i = 0; i < lmi1.tile_count && i < 10; i++) {
        word w, h;
        if (fdother_lmi1_get_tile_size(&lmi1, i, &w, &h) == 0) {
            printf("  tile[%d]: %dx%d\n", i, w, h);
        } else {
            printf("  tile[%d]: 错误\n", i);
        }
    }
    
    /* 渲染前5个tile到BMP */
    if (SDL_Init(SDL_INIT_VIDEO) != 0) {
        printf("SDL_Init失败: %s\n", SDL_GetError());
        return 1;
    }
    
    for (int i = 0; i < 5 && i < lmi1.tile_count; i++) {
        word w, h;
        if (fdother_lmi1_get_tile_size(&lmi1, i, &w, &h) != 0 || w == 0 || h == 0) continue;
        if (w > 512 || h > 512) continue;
        
        byte* pixels = calloc(1, w * h * 3);
        if (!pixels) continue;
        
        int ret = fdother_lmi1_decode_tile(&lmi1, i, pixels, w);
        if (ret <= 0) {
            printf("tile[%d]解码失败\n", i);
            free(pixels);
            continue;
        }
        
        /* 应用调色板索引(简单灰度) */
        byte* rgb = malloc(w * h * 3);
        for (int j = 0; j < w * h; j++) {
            byte v = pixels[j] * 4;
            rgb[j*3]   = v;
            rgb[j*3+1] = v;
            rgb[j*3+2] = v;
        }
        
        char filename[64];
        sprintf(filename, "output/lmi1_test_%d_tile%d.bmp", lmi1_index, i);
        
        /* 写BMP */
        SDL_Surface* surf = SDL_CreateRGBSurface(0, w, h, 24, 0, 0, 0, 0);
        if (surf) {
            memcpy(surf->pixels, rgb, w * h * 3);
            SDL_SaveBMP(surf, filename);
            SDL_FreeSurface(surf);
            printf("  保存: %s (%dx%d)\n", filename, w, h);
        }
        
        free(pixels);
        free(rgb);
    }
    
    SDL_Quit();
    return 0;
}
