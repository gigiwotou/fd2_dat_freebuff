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
 * sub_1F525: 淡入效果 (原游戏 0x1F525)
 * 
 * 原游戏逻辑:
 *   for (n64=64; n64>=0; --n64) {
 *     sub_11D40(0, 255, n64);
 *     delay(2);
 *   }
 * 
 * 原游戏sub_11D40: 颜色值 = FDOTHER[原始RGB] - n64
 * - n64=64: 颜色值 = 原始值-64，更暗
 * - n64=0: 颜色值 = 原始值，正常亮度
 * 
 * 功能: 从暗到亮的淡入效果 (65步×2ms ≈ 130ms)
 */
static void sub_1F525(fd2_render_t* render) {
    /* 使用简化的亮度渐变实现淡入效果 */
    /* 从暗(低亮度)渐变到正常(亮度63) */
    for (int brightness = 0; brightness <= 63; ++brightness) {
        fd2_render_set_brightness(render, brightness);
        fd2_render_present(render);
        fd2_delay(2);
    }
    /* 确保最终亮度为63 */
    fd2_render_set_brightness(render, 63);
    fd2_render_present(render);
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
 * sub_1F882: 等待按键/音效控制 (原游戏 0x1F882)
 * 
 * 功能: 等待用户按键，同时播放音效
 * 简化实现: 仅等待按键
 */
static void sub_1F882(void) {
    SDL_Event event;
    while (1) {
        while (SDL_WaitEvent(&event)) {
            if (event.type == SDL_KEYDOWN && !event.key.repeat) {
                return;
            }
            if (event.type == SDL_QUIT) {
                return;
            }
        }
    }
}

/*
 * sub_11EB0: 区域拷贝 (原游戏 0x11EB0)
 * 
 * 原游戏逻辑:
 *   for (i=0; i<a10; ++i) {
 *     memmove(a5, a7, a9);
 *     a5 += a6;  // dst_stride
 *     a7 += a8;  // src_stride
 *   }
 * 
 * 在动画中的调用: sub_11EB0(655360, 320, n15+320*n535, 320, 320, 200)
 * = 从n15+320*n535拷贝200行到屏幕(655360)，每行320字节
 */
static void sub_11EB0(u8* dst, int dst_stride,
                      const u8* src, int src_stride,
                      int copy_size, int num_lines) {
    for (int i = 0; i < num_lines; ++i) {
        memmove(dst, src, copy_size);
        dst += dst_stride;
        src += src_stride;
    }
}

/*
 * sub_1F81E: AFM动画播放 (原游戏 0x1F81E)
 * 
 * 原游戏逻辑:
 *   if (n99 != -1) {
 *     清屏;
 *     加载FDOTHER.DAT索引n99;
 *   }
 *   设置黑色调色板;
 *   sub_20421(n4, n15, 0);  // 播放AFM动画
 *   sub_1F882();            // 等待按键
 */
static void sub_1F81E(fd2_state_machine_t* sm, int n99, int n4, int n15) {
    fd2_resources_t* res = fd2_get_resources();
    
    if (n99 != -1) {
        fd2_render_fill_screen(&sm->render, 0);
        /* 加载FDOTHER.DAT索引n99 (如果需要) */
    }
    
    /* 设置黑色调色板 */
    fd2_render_set_brightness(&sm->render, 0);
    
    /* 播放AFM动画 */
    printf("[OPENING] sub_1F81E: Playing AFM animation n4=%d, n15=%d\n", n4, n15);
    fd2_afm_play(n4, n15, 0, &sm->render, res);
    
    /* 等待按键 */
    sub_1F882();
}

/*
 * sub_1F73F: 复杂特效 (原游戏 0x1F73F)
 * 
 * 原游戏逻辑:
 *   sub_1F882();           // 等待按键
 *   清屏;
 *   加载FDOTHER索引n5;
 *   加载FDOTHER索引n100;
 *   sub_4E98D解码到屏幕;
 *   sub_1F525();           // 淡入
 *   播放音效;
 *   sub_1F882();           // 等待按键
 *   加载FDOTHER索引101;
 *   sub_11EB0拷贝到n15+n99*320;
 *   sub_1F525();           // 淡入
 */
static void sub_1F73F(fd2_state_machine_t* sm, int n100, int n5, void* n15, int n99) {
    fd2_resources_t* res = fd2_get_resources();
    
    /* 等待按键 */
    sub_1F882();
    
    /* 清屏 */
    fd2_render_fill_screen(&sm->render, 0);
    
    /* 加载FDOTHER索引n5并解码到屏幕 */
    u32 dat_size = 0;
    const u8* dat_data = fd2_resources_get(res, FD2_DAT_FDOTHER, n5, &dat_size);
    if (dat_data) {
        fd2_rle_decompress_to_buffer(dat_data, dat_size, sm->render.screen, 0, 320, -1);
    }
    
    /* 淡入效果 */
    sub_1F525(&sm->render);
    
    /* 等待按键 */
    sub_1F882();
    
    /* 加载FDOTHER索引101 */
    /* (资源加载在初始化阶段已完成) */
    
    /* 拷贝到n15+n99*320位置 */
    int dst_offset = n99 * 320;
    if (dst_offset + 64000 <= 270080) {
        sub_11EB0((u8*)n15 + dst_offset, 320,
                  sm->render.screen, 320,
                  320, 200);
    }
    
    /* 再次淡入 */
    sub_1F525(&sm->render);
    
    printf("[OPENING] sub_1F73F: n100=%d, n5=%d, n99=%d\n", n100, n5, n99);
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
    
    fd2_resources_t* res = fd2_get_resources();
    
    /* 1. sub_111BA(..., "FDOTHER.DAT", 77) - 加载初始化资源 */
    u32 size_77 = 0;
    const u8* data_77 = fd2_resources_get(res, FD2_DAT_FDOTHER, 77, &size_77);
    printf("[OPENING] Loaded FDOTHER index 77, size=%u\n", size_77);
    
    /* 2. memset(655360, 0, 64000) - 清屏 */
    fd2_render_fill_screen(&sm->render, 0);
    
    /* 3. sub_111BA(..., "FDOTHER.DAT", 76) - 加载调色板数据 */
    /* 注意：索引76可能是复合资源，不是纯调色板 */
    u32 size_76 = 0;
    const u8* data_76 = fd2_resources_get(res, FD2_DAT_FDOTHER, 76, &size_76);
    printf("[OPENING] Loaded FDOTHER index 76, size=%u\n", size_76);
    
    /* 4. sub_11D40(0, 255, 64) - 设置调色板(亮度63) */
    fd2_render_set_brightness(&sm->render, 63);
    
    /* 5. sub_111BA(..., "FDOTHER.DAT", 74) - 加载初始图像 */
    u32 size_74 = 0;
    const u8* data_74 = fd2_resources_get(res, FD2_DAT_FDOTHER, 74, &size_74);
    printf("[OPENING] Loaded FDOTHER index 74, size=%u\n", size_74);
    
    /* 6. sub_4E98D解码到屏幕 */
    if (data_74) {
        fd2_rle_decompress_to_buffer(data_74, size_74, sm->render.screen, 0, 320, -1);
        fd2_render_present(&sm->render);
    }
    
    /* 7. sub_1F525() - 淡入效果 */
    sub_1F525(&sm->render);
    
    /* 8. sub_17AA9(1), sub_17AA9(30) - 播放音效 */
    /* TODO: 实现音效播放 */
    printf("[OPENING] Playing sound effects 1 and 30\n");
    
    /* 9. sub_1F882() - 等待按键 */
    printf("[OPENING] Waiting for key press after initial image...\n");
    fflush(stdout);
    sub_1F882();
    
    /* 10. sub_111BA(..., "FDOTHER.DAT", 99) - 加载音乐资源 */
    u32 size_99 = 0;
    const u8* data_99 = fd2_resources_get(res, FD2_DAT_FDOTHER, 99, &size_99);
    printf("[OPENING] Loaded FDOTHER index 99 (music), size=%u\n", size_99);
    
    /* 11. memset(655360, 0, 64000) - 清屏 */
    fd2_render_fill_screen(&sm->render, 0);
    
    /* 12. sub_11D40(0, 255, 0) - 黑色调色板(亮度0) */
    fd2_render_set_brightness(&sm->render, 0);
    
    /* 13. sub_20421(3, 90, 1) - 播放AFM动画索引3 */
    printf("[OPENING] Playing AFM animation index 3...\n");
    fd2_afm_play(3, 90, 1, &sm->render, res);
    
    /* 清除AFM动画期间积累的所有SDL事件 */
    SDL_Event dummy_event;
    while (SDL_PollEvent(&dummy_event)) { }
    
    /* 14. sub_1F882() - 等待按键 */
    printf("[OPENING] Waiting for key press after AFM animation...\n");
    fflush(stdout);
    sub_1F882();
    
    /* 15. sub_111BA(..., "FDOTHER.DAT", 101) - 加载背景资源 */
    u32 size_101 = 0;
    const u8* data_101 = fd2_resources_get(res, FD2_DAT_FDOTHER, 101, &size_101);
    printf("[OPENING] Loaded FDOTHER index 101 (bg), size=%u\n", size_101);
    
    /* 16. sub_11D40(0, 255, 64) - 设置调色板(亮度63) */
    fd2_render_set_brightness(&sm->render, 63);
    
    /* 8. 加载FDOTHER索引69-73 (5个动画帧图像) 到缓冲区 */
    /* 原游戏: n15 = malloc(0x396C0) = 235200字节 */
    /* for (n5=0; n5<5; ++n5) { */
    /*   sub_111BA(..., "FDOTHER.DAT", n5+69); */
    /*   sub_4E98D(..., 0, 147*n5, n15, 320, -1); */
    /* } */
    
    /* 分配动画缓冲区 (320*147*4 + 320*200 = 206080 + 64000 = 270080字节) */
    /* 索引69-72是320x147，索引73是320x200 */
    void* n15 = malloc(270080);
    if (!n15) {
        printf("[OPENING] Failed to allocate animation buffer\n");
        return 0;
    }
    memset(n15, 0, 270080);
    
    /* 加载5个动画帧 */
    printf("[OPENING] Loading FDOTHER indices 69-73...\n");
    for (int n5 = 0; n5 < 5; ++n5) {
        int index = n5 + 69;
        int dst_y = (n5 < 4) ? (147 * n5) : (147 * 4);
        
        u32 dat_size = 0;
        const u8* dat_data = fd2_resources_get(res, FD2_DAT_FDOTHER, index, &dat_size);
        
        printf("[OPENING]   Index %d: dat_size=%u, dst_y=%d\n", index, dat_size, dst_y);
        
        if (dat_data) {
            int ret = fd2_rle_decompress_to_buffer(dat_data, dat_size, n15, dst_y, 320, -1);
            printf("[OPENING]   Decompress result: %d\n", ret);
        }
    }
    
    /* 检查n15缓冲区内容 (打印前16字节) */
    {
        u8* check = (u8*)n15;
        printf("[OPENING] n15 buffer check (first 32 bytes at offset 0): ");
        for (int i = 0; i < 32; i++) {
            printf("%02x ", check[i]);
        }
        printf("\n");
        
        /* 检查offset 535*320处 */
        check = (u8*)n15 + 535 * 320;
        printf("[OPENING] n15 buffer check (at offset 535*320): ");
        for (int i = 0; i < 32; i++) {
            printf("%02x ", check[i]);
        }
        printf("\n");
    }
    
    /* 清屏为黑色 */
    fd2_render_fill_screen(&sm->render, 0);
    
    /* 设置亮度为63（正常亮度）- 对应原游戏 sub_11D40(0, 255, 64) */
    fd2_render_set_brightness(&sm->render, 63);
    
    fd2_render_present(&sm->render);

    printf("[OPENING] Starting main animation loop (535 frames)...\n");
    fflush(stdout);

    /* ====================================================================
     * 阶段2: 主动画循环 (n535: 535→0)
     * 对应原游戏 for (n535=535; ; --n535) 循环
     * ==================================================================== */
    /* 阶段2: 主动画循环 (n535: 535→0) */
    int n535 = FD2_ANIM_FRAME_START;
    int v33 = 0;
    int n12 = 0;

    Uint32 loop_start = SDL_GetTicks();
    printf("[OPENING] Animation loop starting at tick=%u\n", loop_start);
    fflush(stdout);

    while (1) {
        if (n535 < 0) {
            Uint32 loop_end = SDL_GetTicks();
            printf("[OPENING] Animation loop finished at tick=%u (duration=%ums), entering menu\n", 
                   loop_end, loop_end - loop_start);
            fflush(stdout);
            goto opening_menu;
        }
        
        /* 对应原游戏: sub_11EB0(655360, 320, n15+320*n535, 320, 320, 200) */
        /* 从n15+n535*320拷贝200行到屏幕 */
        {
            int src_offset = n535 * 320;
            if (src_offset >= 0 && src_offset + 64000 <= 270080) {
                sub_11EB0(sm->render.screen, 320,
                          (u8*)n15 + src_offset, 320,
                          320, 200);
            }
        }
        
        /* n535==535: sub_1F525() 淡入效果 */
        if (n535 == 535) {
            sub_1F525(&sm->render);
        }
        
        /* n535==25: 跳出循环到标签LABEL_31 */
        if (n535 == 25) {
            printf("[OPENING] Frame 25: breaking to menu\n");
            fflush(stdout);
            
            /* sub_1F81E(0, 15, 0) */
            sub_1F81E(sm, -1, 0, 15);
            
            /* sub_11EB0拷贝 */
            {
                int src_offset = n535 * 320;
                if (src_offset >= 0 && src_offset + 64000 <= 270080) {
                    sub_11EB0(sm->render.screen, 320,
                              (u8*)n15 + src_offset, 320,
                              320, 200);
                }
            }
            
            /* sub_1F525()淡入 */
            sub_1F525(&sm->render);
            
            goto opening_menu;
        }
        
        /* 关键帧事件触发 - switch语句 */
        switch (n535) {
            case 450:
                /* sub_1F73F(100, 99, n15, 450) */
                sub_1F73F(sm, 100, 99, n15, 450);
                break;
                
            case 330:
                /* sub_1F882() */
                sub_1F882();
                /* sub_1F81E(4, 90, 99) */
                sub_1F81E(sm, 99, 4, 90);
                /* sub_1F81E(5, 50, 0) */
                sub_1F81E(sm, 0, 5, 50);
                break;
                
            case 210:
                /* sub_1F882() */
                sub_1F882();
                /* sub_1F81E(6, 90, 99) */
                sub_1F81E(sm, 99, 6, 90);
                /* sub_1F81E(7, 50, 0) */
                sub_1F81E(sm, 0, 7, 50);
                break;
                
            case 110:
                /* sub_1F882() */
                sub_1F882();
                /* sub_1F81E(8, 90, 99) */
                sub_1F81E(sm, 99, 8, 90);
                break;
                
            case 10:
                /* sub_1F73F(75, 76, n15, 10) */
                sub_1F73F(sm, 75, 76, n15, 10);
                break;
        }
        
        /* 检查时间点 - 对应原游戏 dst_[v33] 数组检查 */
        if (v33 < FD2_OPENING_TIME_COUNT && n535 == g_opening_time_points[v33]) {
            n12 = 0;
            /* sub_25A96(..., 0, 1) - 资源加载 */
            /* 简化处理：仅重置计数器 */
            v33++;
        }
        
        if (n12 == 11) {
            /* sub_111BA(..., 101) + sub_11D40(0, 255, 0) */
            /* 简化处理 */
        }
        
        n12++;
        
        /* 渲染并延迟 */
        fd2_render_present(&sm->render);
        fd2_delay(30);
        
        if (n535 == 0) {
            fd2_delay(1000);
        }
        
        /* 检查按键跳过 (对应原游戏 sub_10620()) */
        if (fd2_check_key_pressed()) {
            goto opening_menu;
        }
        
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
    
    printf("[OPENING] Waiting for menu input...\n");
    fflush(stdout);
    
    while (!v27) {
        /* 处理SDL事件 */
        SDL_Event event;
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_QUIT) {
                v27 = 1;
                n2_2 = 255;
                break;
            }
            
            if (event.type == SDL_KEYDOWN && !event.key.repeat) {
                u8 hi_byte = event.key.keysym.scancode >> 8;
                u8 lo_byte = event.key.keysym.scancode & 0xFF;
                
                if (hi_byte == 72 || lo_byte == 72) {
                    /* 上箭头 - 向上移动 */
                    int n2_3 = n2_1 - 1;
                    if (n2_2) {
                        --n2_2;
                    } else {
                        n2_2 = n2_3;
                    }
                    printf("[OPENING] Menu select: %d (up)\n", n2_2);
                    fflush(stdout);
                }
                else if (hi_byte == 80 || lo_byte == 80) {
                    /* 下箭头 - 向下移动 */
                    int n2_3 = n2_1 - 1;
                    if (n2_2 == n2_3) {
                        n2_2 = 0;
                    } else {
                        ++n2_2;
                    }
                    printf("[OPENING] Menu select: %d (down)\n", n2_2);
                    fflush(stdout);
                }
                else if (lo_byte == 13 || lo_byte == 32 || 
                         lo_byte == 27 || hi_byte == 82) {
                    /* Enter/Space/ESC/Insert - 确认或退出 */
                    if (lo_byte == 27) {
                        /* ESC - 退出 */
                        n2_2 = 255;
                    }
                    v27 = 1;
                    printf("[OPENING] Menu confirmed: %d\n", n2_2);
                    fflush(stdout);
                }
            }
        }
        
        /* 渲染菜单 */
        fd2_render_present(&sm->render);
        fd2_delay(16);
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
