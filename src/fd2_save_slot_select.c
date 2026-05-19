/**
 * 存档Slot选择界面
 * 对应原游戏 sub_29BCB 函数
 */

#include "fd2_save_load.h"
#include "fd2_render.h"
#include "fd2_input.h"
#include "fd2_decoder.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <SDL2/SDL.h>

/* 每个slot在屏幕上的位置和大小 */
#define SLOT_Y_START      30
#define SLOT_HEIGHT       35
#define SLOT_GAP          5
#define SLOT_LABEL_X      10
#define SLOT_INFO_X       100
#define SLOT_WIDTH        300

/* 按键扫描码 */
#define KEY_UP       72
#define KEY_DOWN     80
#define KEY_ENTER    28
#define KEY_SPACE    57
#define KEY_ESC      1

/*
 * 绘制矩形框（用字符模拟）
 */
static void draw_rect(fd2_render_t* render, int x, int y, int w, int h, u8 color) {
    int i;
    for (i = x; i < x + w && i < 320; i++) {
        fd2_render_plot(render, i, y, color);
        fd2_render_plot(render, i, y + h - 1, color);
    }
    for (i = y; i < y + h && i < 200; i++) {
        fd2_render_plot(render, x, i, color);
        fd2_render_plot(render, x + w - 1, i, color);
    }
}

/*
 * 填充矩形区域
 */
static void fill_rect(fd2_render_t* render, int x, int y, int w, int h, u8 color) {
    int ix, iy;
    for (iy = y; iy < y + h && iy < 200; iy++) {
        for (ix = x; ix < x + w && ix < 320; ix++) {
            fd2_render_plot(render, ix, iy, color);
        }
    }
}

/*
 * 显示存档slot选择界面
 * 对应原游戏 sub_29BCB
 * 
 * 参数:
 *   sav:        存档数据
 *   base_path:  exe所在目录路径
 * 
 * 返回值:
 *   0-3: 用户选择的slot索引
 *   -1:  用户取消（ESC）
 */
int fd2_save_slot_select(fd2_sav_data_t* sav, const char* base_path) {
    fd2_render_t* render = NULL;
    int selected_slot = 0;
    int result = -1;
    int slot_idx;
    
    /* 获取render实例 */
    extern fd2_render_t* g_render;
    render = g_render;
    if (!render) {
        fprintf(stderr, "fd2_save_slot_select: render not initialized\n");
        return -1;
    }
    
    printf("[SAVE_SELECT] Entering save slot selection interface\n");
    
    /* 清屏，使用黑色背景 */
    fd2_render_fill_screen(render, 0);
    
    /* 设置调色板（白色文字） */
    /* 颜色1 = 白色 */
    render->palette[3] = 255;    /* R */
    render->palette[4] = 255;    /* G */
    render->palette[5] = 255;    /* B */
    /* 颜色2 = 黄色（选中高亮） */
    render->palette[6] = 255;
    render->palette[7] = 255;
    render->palette[8] = 0;
    /* 颜色3 = 灰色（空slot） */
    render->palette[9] = 128;
    render->palette[10] = 128;
    render->palette[11] = 128;
    
    while (1) {
        SDL_Event event;
        int key_pressed = 0;
        
        /* 清屏 */
        fd2_render_fill_screen(render, 0);
        
        /* 绘制标题 */
        /* 在颜色1的位置绘制"LOAD GAME"文字（简化：绘制一个框） */
        fill_rect(render, 60, 5, 200, 20, 1);
        
        /* 绘制4个slot */
        for (slot_idx = 0; slot_idx < 4; slot_idx++) {
            int slot_y = SLOT_Y_START + slot_idx * (SLOT_HEIGHT + SLOT_GAP);
            u8 border_color;
            u8 text_color;
            
            /* 判断是否是当前选中的slot */
            if (slot_idx == selected_slot) {
                border_color = 2;  /* 黄色边框（选中） */
                text_color = 2;
            } else {
                border_color = 1;  /* 白色边框 */
                text_color = 1;
            }
            
            /* 绘制slot背景框 */
            fill_rect(render, 10, slot_y, SLOT_WIDTH, SLOT_HEIGHT, 0);
            draw_rect(render, 10, slot_y, SLOT_WIDTH, SLOT_HEIGHT, border_color);
            
            /* 绘制slot编号 */
            /* Slot 1 / Slot 2 / Slot 3 / Slot 4 */
            if (sav->battleSlots[slot_idx].n17 == 255) {
                /* 空slot - 显示"EMPTY" */
                fill_rect(render, SLOT_LABEL_X, slot_y + 10, 50, 12, 3);  /* 灰色 */
            } else {
                /* 有存档 - 显示场景编号 */
                u8 c;
                int scene = sav->battleSlots[slot_idx].n17;
                /* 绘制"Scene:XX"的简化表示 */
                fill_rect(render, SLOT_LABEL_X, slot_y + 10, 80, 12, text_color);
            }
            
            /* 绘制slot编号标签 "1" "2" "3" "4" */
            fill_rect(render, SLOT_LABEL_X, slot_y + 2, 10, 8, text_color);
        }
        
        /* 绘制底部提示 */
        fill_rect(render, 50, 180, 80, 12, 1);  /* UP/DOWN */
        fill_rect(render, 140, 180, 60, 12, 1);  /* ENTER */
        fill_rect(render, 210, 180, 40, 12, 1);  /* ESC */
        
        /* 刷新屏幕 */
        fd2_render_present(render);
        
        /* 等待用户输入 */
        while (!key_pressed) {
            SDL_Delay(50);
            
            while (SDL_PollEvent(&event)) {
                if (event.type == SDL_QUIT) {
                    return -1;
                }
                if (event.type == SDL_KEYDOWN) {
                    switch (event.key.keysym.scancode) {
                        case SDL_SCANCODE_UP:
                            if (selected_slot > 0) {
                                selected_slot--;
                            }
                            key_pressed = 1;
                            break;
                        case SDL_SCANCODE_DOWN:
                            if (selected_slot < 3) {
                                selected_slot++;
                            }
                            key_pressed = 1;
                            break;
                        case SDL_SCANCODE_RETURN:
                        case SDL_SCANCODE_SPACE:
                            result = selected_slot;
                            key_pressed = 1;
                            break;
                        case SDL_SCANCODE_ESCAPE:
                            result = -1;
                            key_pressed = 1;
                            break;
                        default:
                            break;
                    }
                }
            }
        }
        
        if (key_pressed && result != -2) {
            break;
        }
    }
    
    printf("[SAVE_SELECT] User selected slot %d (result=%d)\n", selected_slot, result);
    
    if (result == -1) {
        printf("[SAVE_SELECT] User cancelled\n");
    } else {
        printf("[SAVE_SELECT] Slot %d: scene=%d\n", result, sav->battleSlots[result].n17);
    }
    
    return result;
}
