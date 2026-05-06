/**
 * FD2 开场动画系统
 * 对应原游戏 sub_1F894 (地址: 0x1F894)
 * 
 * 原游戏启动时调用此函数播放开场动画序列
 * 
 * 完整动画流程 (基于IDA 1:1实现):
 * 1. 初始化阶段: 加载FDOTHER.DAT多个索引(77,76,74,99,101,69-73)
 * 2. 主动画循环 (n535: 535→0): 垂直滚动blit，关键帧触发事件
 * 3. 菜单阶段: 淡入淡出，存档检查，用户选择
 */

#include "fd2_opening_animation.h"
#include "fd2_afm.h"
#include "fd2_globals.h"
#include "fd2_render.h"
#include "fd2_render_pipeline.h"
#include "fd2_resources.h"
#include "fd2_data_loader.h"
#include "fd2_decoder.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* FDOTHER.DAT资源索引常量 */
#define FD2_OPENING_FDOTHER_INIT_0   77  /* 初始化资源0 */
#define FD2_OPENING_FDOTHER_INIT_1   76  /* 初始化资源1 */
#define FD2_OPENING_FDOTHER_INIT_2   74  /* 初始化资源2 */
#define FD2_OPENING_FDOTHER_MUSIC    99  /* 音乐资源 */
#define FD2_OPENING_FDOTHER_BG       101 /* 背景资源 */
#define FD2_OPENING_FDOTHER_ANIM_0   69  /* 动画资源0-4 */
#define FD2_OPENING_FDOTHER_ANIM_4   73  /* 动画资源4 */
#define FD2_OPENING_FDOTHER_MENU_BG  7   /* 菜单背景 */
#define FD2_OPENING_FDOTHER_MUSIC_2  8   /* 菜单音乐 */
#define FD2_OPENING_FDOTHER_TIME_0   102 /* 时间点资源 */
#define FD2_OPENING_FDOTHER_TIME_1   101 /* 最终时间点资源 */

/* 动画关键帧 */
#define FD2_ANIM_FRAME_START         535
#define FD2_ANIM_FRAME_MID_0         450  /* 触发sub_1F73F(100,99) */
#define FD2_ANIM_FRAME_MID_1         330  /* 触发sub_1F81E(4,90,99)+sub_1F81E(5,50,0) */
#define FD2_ANIM_FRAME_MID_2         210  /* 触发sub_1F81E(6,90,99)+sub_1F81E(7,50,0) */
#define FD2_ANIM_FRAME_MID_3         110  /* 触发sub_1F81E(8,90,99) */
#define FD2_ANIM_FRAME_MID_4         25   /* 触发sub_1F81E(0,15,0) */
#define FD2_ANIM_FRAME_END           10   /* 触发sub_1F73F(75,76) */

/* 时间点数组 (原游戏 dst_数组) */
static const int g_opening_time_points[] = {500, 400, 300, 200, 100, 50, 30, 20, 10, 5, 3, 1};
#define FD2_OPENING_TIME_COUNT 12

/* 模拟原游戏 delay() 函数 */
static void fd2_delay(int ms) {
    SDL_Delay(ms);
}

/*
 * sub_10620: 检查键盘缓冲区变化 (原游戏 0x10620)
 * 
 * 原游戏实现:
 *   return MEMORY[0x41C] != MEMORY[0x41A];
 * 
 * 0x41A = 键盘缓冲区头指针
 * 0x41C = 键盘缓冲区尾指针
 * 当用户按键时，尾指针变化，两者不等
 * 
 * SDL2实现: 非阻塞检查是否有新按键按下
 * 返回: 1=有按键, 0=无按键
 */
static int g_key_pressed = 0;

static int fd2_check_key_pressed(void) {
    if (g_key_pressed) return 1;
    
    SDL_Event event;
    while (SDL_PollEvent(&event)) {
        if (event.type == SDL_KEYDOWN && !event.key.repeat) {
            g_key_pressed = 1;
            return 1;
        }
        if (event.type == SDL_QUIT) {
            g_key_pressed = 1;
            return 1;
        }
    }
    return 0;
}

/* 重置按键状态 */
static void fd2_reset_key_state(void) {
    g_key_pressed = 0;
}

/*
 * fd2_play_opening_animation: 开场动画完整播放 (原游戏 sub_1F894)
 * 
 * 返回: 0=选择Start, 1=选择Load, 其他=退出
 */
int fd2_play_opening_animation(fd2_state_machine_t* sm) {
    if (!sm) return -1;

    printf("[OPENING] Starting opening animation sequence...\n");
    
    /* 重置按键状态 */
    fd2_reset_key_state();

    /* ====================================================================
     * 阶段1: 初始化资源加载 (对应原游戏 0x1F894-0x1FA85)
     * ==================================================================== */
    
    /* 1. memset(655360, 0, 64000) - 清屏 */
    fd2_render_fill_screen(&sm->render, 0);
    
    /* 2. 加载FDOTHER.DAT资源 (按顺序加载) */
    /* FDOTHER_DAT = sub_111BA(..., "FDOTHER.DAT", 77) */
    /* FDOTHER_DAT = sub_111BA(..., "FDOTHER.DAT", 76) */
    /* _FDOTHER.DAT__1 = sub_111BA(..., "FDOTHER.DAT", 74) */
    /* sub_4E98D渲染，sub_1F525淡入，sub_17AA9精灵渲染 */
    
    /* 3. sub_11D40(0, 255, 64) - 设置调色板(亮度63) */
    fd2_render_set_brightness(&sm->render, 63);
    
    /* 4. sub_1F882() - 音效控制 */
    /* sub_1F882(1) + sub_1F882(30) - 播放音效 */
    
    /* 5. 加载索引99，清屏，设置黑色调色板 */
    /* memset(655360, 0, 64000) */
    fd2_render_fill_screen(&sm->render, 0);
    /* sub_11D40(0, 255, 0) - 黑色调色板(亮度0) */
    fd2_render_set_brightness(&sm->render, 0);
    
    /* 6. sub_20421(3, 90, 1) - 播放AFM动画索引3, 延迟90ms */
    printf("[OPENING] Playing AFM animation index 3...\n");
    fd2_resources_t* res = fd2_get_resources();
    fd2_afm_play(3, 90, 1, &sm->render, res);
    
    /* 7. 加载索引101，设置调色板(偏移64) */
    /* sub_11D40(0, 255, 64) - 设置调色板(亮度63) */
    fd2_render_set_brightness(&sm->render, 63);
    
    /* 8. 加载FDOTHER索引69-73 (5个动画帧图像) 到缓冲区 */
    /* 原游戏: n15 = malloc(0x396C0) = 235200字节 */
    /* for (n5=0; n5<5; ++n5) { */
    /*   sub_111BA(..., "FDOTHER.DAT", n5+69); */
    /*   sub_4E98D(..., 0, 147*n5, n15, 320, -1); */
    /* } */
    
    printf("[OPENING] Loading animation frames (FDOTHER indices 69-73)...\n");
    
    /* 分配动画缓冲区 (235200字节 = 320*147*5) */
    /* 原游戏: n15 = malloc(0x396C0) = 235200字节 */
    printf("[OPENING] Allocating animation buffer (235200 bytes)...\n");
    fflush(stdout);
    void* n15 = malloc(235200);
    if (!n15) {
        printf("[OPENING] Failed to allocate animation buffer\n");
        fflush(stdout);
        return 0;
    }
    memset(n15, 0, 235200);
    
    printf("[OPENING] Animation buffer allocated at %p\n", n15);
    fflush(stdout);
    
    /* 加载5个动画帧 */
    for (int n5 = 0; n5 < 5; ++n5) {
        int index = n5 + 69;  /* 索引69-73 */
        int dst_y = 147 * n5;  /* 目标Y偏移 */
        
        printf("[OPENING] Loading FDOTHER index %d to y=%d...\n", index, dst_y);
        fflush(stdout);
        
        /* 从资源管理器获取数据 */
        u32 dat_size = 0;
        const u8* dat_data = fd2_resources_get(res, FD2_DAT_FDOTHER, index, &dat_size);
        
        if (dat_data) {
            /* sub_4E98D: RLE解压缩渲染到n15缓冲区 */
            /* 每帧图像最大尺寸320x147 */
            /* 参数: dst_y = 147*n5, stride = 320, palette_offset = -1 */
            int ret = fd2_rle_decompress_to_buffer(dat_data, dat_size, n15, dst_y, 320, -1);
            printf("[OPENING] Decompress result: %d (dat_size=%u)\n", ret, dat_size);
            fflush(stdout);
        } else {
            printf("[OPENING] Failed to load FDOTHER index %d\n", index);
            fflush(stdout);
        }
    }
    
    /* sub_4E381() - 刷新屏幕 */
    printf("[OPENING] Animation frames loaded, presenting screen...\n");
    fflush(stdout);
    
    /* 清屏为黑色 */
    fd2_render_fill_screen(&sm->render, 0);
    
    printf("[OPENING] Screen cleared, calling present...\n");
    fflush(stdout);
    fd2_render_present(&sm->render);
    printf("[OPENING] Screen presented, starting animation loop...\n");
    fflush(stdout);

    /* ====================================================================
     * 阶段2: 主动画循环 (n535: 535→0)
     * 对应原游戏 for (n535=535; ; --n535) 循环
     * ==================================================================== */
    printf("[OPENING] Starting main animation loop (535 frames)...\n");
    
    int n535 = FD2_ANIM_FRAME_START;
    int v33 = 0;  /* 时间点索引 */
    int n12 = 12; /* 时间点计数器 */

    while (1) {
        if (n535 < 0) {
            /* 动画播放完毕，进入菜单阶段 */
            printf("[OPENING] Animation loop completed, entering menu\n");
            goto opening_menu;
        }
        
        /* 每50帧打印一次进度 */
        if (n535 % 50 == 0) {
            printf("[OPENING] Animation frame: %d\n", n535);
        }
        
        /* sub_11EB0(655360, 320, n15+320*n535, 320, 320, 200) */
        /* 垂直滚动blit: 从n15缓冲区复制到屏幕 */
        {
            int src_offset = n535 * 320;
            int screen_size = 320 * 200;
            
            if (src_offset < screen_size) {
                /* sub_11EB0本质是memmove循环 */
                /* sub_11EB0(dst, stride, src, arg4, arg5, arg6, arg7, arg8, arg9, count) */
                /* 实际调用: sub_11EB0(655360, 320, n15+320*n535, 320, 320, 200) */
                /* 复制200行，每行320字节，dst步长320，src步长320 */
                
                u8* src = (u8*)n15 + src_offset;
                u8* dst = sm->render.screen;
                
                for (int row = 0; row < 200; ++row) {
                    if (src_offset + row * 320 < 235200) {
                        memcpy(dst, src, 320);
                        dst += 320;
                        src += 320;
                    }
                }
            }
        }
        
        if (n535 == FD2_ANIM_FRAME_START) {
            /* sub_1F525() - 首次淡入 */
            printf("[OPENING] First frame, fade in\n");
        }
        
        /* 关键帧事件触发 */
        switch (n535) {
            case FD2_ANIM_FRAME_MID_0:  /* 330 */
                /* sub_1F882() */
                /* sub_1F81E(4, 90, 99) */
                /* sub_1F81E(5, 50, 0) */
                printf("[OPENING] Key frame 330 - animation event 0\n");
                /* TODO: 加载并渲染对应资源 */
                goto render_frame;
                
            case FD2_ANIM_FRAME_MID_1:  /* 210 */
                /* sub_1F882() */
                /* sub_1F81E(6, 90, 99) */
                /* sub_1F81E(7, 50, 0) */
                printf("[OPENING] Key frame 210 - animation event 1\n");
                goto render_frame;
                
            case FD2_ANIM_FRAME_MID_2:  /* 110 */
                /* sub_1F882() */
                /* sub_1F81E(8, 90, 99) */
                printf("[OPENING] Key frame 110 - animation event 2\n");
                goto render_frame;
                
            case FD2_ANIM_FRAME_END:    /* 10 */
                /* sub_1F73F(75, 76, n15, 10) */
                printf("[OPENING] Key frame 10 - animation event 3\n");
                break;
        }
        
        /* 检查是否到达时间点 */
        if (v33 < FD2_OPENING_TIME_COUNT && n535 == g_opening_time_points[v33]) {
            n12 = 0;
            /* sub_25A96(..., 0, 1) - 播放音效 */
            /* FDOTHER_DAT = sub_111BA(..., 102) */
            /* sub_11D40(0, 255, 0) */
            printf("[OPENING] Time point reached: %d\n", n535);
            v33++;
        }
        
        if (n12 == 11) {
            /* FDOTHER_DAT = sub_111BA(..., 101) */
            /* sub_11D40(0, 255, 0) */
            printf("[OPENING] Time counter reached 11\n");
        }
        
        n12++;
        
        /* 处理SDL事件防止窗口无响应 */
        SDL_PumpEvents();
        
        fd2_delay(30);  /* delay(30) */
        
        if (n535 == 0) {
            fd2_delay(1000);  /* delay(1000) */
        }
        
        /* sub_10620() - 检查按键跳过 */
        if (fd2_check_key_pressed()) {
            printf("[OPENING] Animation skipped by user\n");
            goto opening_menu;
        }
        
render_frame:
        fd2_render_present(&sm->render);
        --n535;
    }

opening_menu:
    /* ====================================================================
     * 阶段3: 菜单显示和用户选择
     * 对应原游戏 0x1FC66-0x1FF6A
     * ==================================================================== */
    printf("[OPENING] Entering menu phase...\n");
    
    /* 1. 淡出效果 (n40: 40→0) */
    for (int n40 = 40; n40 >= 0; --n40) {
        /* sub_2DF01(0, 255, n40, 0x3F, 0, 0) */
        fd2_delay(8);
    }
    fd2_delay(100);
    fd2_render_present(&sm->render);
    
    /* 2. 释放旧资源 */
    if (n15) {
        free(n15);
        n15 = NULL;
    }
    
    /* 3. 加载菜单资源 */
    /* _FDOTHER.DAT__3 = sub_111BA(..., "FDOTHER.DAT", 7) */
    /* FDOTHER_DAT = sub_111BA(..., "FDOTHER.DAT", 8) */
    
    /* 4. 清屏，设置黑色调色板 */
    fd2_render_fill_screen(&sm->render, 0);
    fd2_render_set_brightness(&sm->render, 0);
    
    /* 5. sub_20421(1, 15, 1) - 播放AFM动画索引1 */
    /* sub_25B45(..., 3, 1) */
    /* sub_11DF2(0, 255, 64) - 设置调色板 */
    fd2_render_set_brightness(&sm->render, 63);
    
    /* 6. 渲染菜单背景 */
    /* sub_16886(655360, 320, _FDOTHER.DAT__3, 0) */
    
    /* 7. 淡入效果 (n40_1: 0→40) */
    for (int n40_1 = 0; n40_1 <= 40; ++n40_1) {
        /* sub_2DF01(0, 255, n40_1, 0x38, 0x3C, 0x3F) */
        fd2_delay(8);
    }
    fd2_render_present(&sm->render);
    
    /* 8. 检查存档是否存在 */
    int n2_1 = 1;  /* 菜单项数量 */
    {
        FILE* fp = fopen("FD2.SAV", "rb");
        if (fp) {
            void* save_buf = malloc(22987);
            if (save_buf) {
                fread(save_buf, 1, 22987, fp);
                /* sub_4DF28 - 解密存档 */
                /* 检查存档校验和 */
                fclose(fp);
                
                /* 如果存档有效，菜单项增加 */
                unsigned char* byte_ptr = (unsigned char*)save_buf + 12485;
                if (*byte_ptr != 255) {
                    n2_1 = 3;  /* Start, Load, Quit */
                } else {
                    n2_1 = 2;  /* Start, Quit */
                }
                free(save_buf);
            } else {
                fclose(fp);
            }
        }
    }
    
    /* 9. 显示菜单选项 */
    /* sub_1FF79(_FDOTHER.DAT__2, 0, n2_1) - 显示菜单 */
    printf("[OPENING] Displaying menu with %d options\n", n2_1);
    
    /* 10. 等待用户输入 */
    int n2_2 = 0;  /* 当前选中项 */
    int v27 = 0;   /* 选择标志 */
    
    while (!v27) {
        /* sub_1FF79(_FDOTHER.DAT__2, n2_2, n2_1) - 更新菜单高亮 */
        
        /* int386(22, &n3, &n3) - 读取键盘 */
        SDL_Event event;
        while (SDL_WaitEvent(&event)) {
            if (event.type == SDL_QUIT) {
                v27 = 1;
                n2_2 = 255;  /* 退出 */
                break;
            }
            
            if (event.type == SDL_KEYDOWN && !event.key.repeat) {
                u8 hi_byte = event.key.keysym.scancode >> 8;
                u8 lo_byte = event.key.keysym.scancode & 0xFF;
                
                if (hi_byte == 72 || lo_byte == 72) {
                    /* 上箭头 - 向上移动 */
                    /* sub_25A96(..., 2, 1) - 播放音效 */
                    int n2_3 = n2_1 - 1;
                    if (n2_2) {
                        --n2_2;
                    } else {
                        n2_2 = n2_3;
                    }
                    printf("[OPENING] Menu select: %d (up)\n", n2_2);
                    break;
                }
                else if (hi_byte == 80 || lo_byte == 80) {
                    /* 下箭头 - 向下移动 */
                    /* sub_25A96(..., 2, 1) - 播放音效 */
                    int n2_3 = n2_1 - 1;
                    if (n2_2 == n2_3) {
                        n2_2 = 0;
                    } else {
                        ++n2_2;
                    }
                    printf("[OPENING] Menu select: %d (down)\n", n2_2);
                    break;
                }
                else if (lo_byte == 13 || lo_byte == 32 || 
                         hi_byte == 224 || hi_byte == 82) {
                    /* Enter/Space/Insert/扩展键 - 确认 */
                    /* sub_25A96(..., 1, 1) - 播放音效 */
                    v27 = 1;
                    printf("[OPENING] Menu confirmed: %d\n", n2_2);
                    break;
                }
            }
        }
    }
    
    /* 11. 闪烁效果 (4次) */
    for (int n4 = 0; n4 < 4; ++n4) {
        /* sub_1FF79(..., -1, n2_1) - 隐藏高亮 */
        fd2_delay(80);
        /* sub_1FF79(..., n2_2, n2_1) - 显示高亮 */
        fd2_delay(80);
    }
    
    /* 12. 清理资源 */
    /* sub_1F882() */
    /* memset(655360, 0, 64000) */
    fd2_render_fill_screen(&sm->render, 0);
    /* free(_FDOTHER.DAT__2) */
    /* sub_25A96(..., -1, 1) */
    /* free(_FDOTHER.DAT_) */
    
    fd2_render_present(&sm->render);
    
    /* 13. 返回选择结果 */
    printf("[OPENING] Menu result: %d\n", n2_2);
    return n2_2;
}
