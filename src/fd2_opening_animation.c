/**
 * FD2 开场动画系统
 * 对应原游戏 sub_1F894 (地址: 0x1F894, 大小: 0x6E5)
 * 
 * 原游戏启动时由sub_25EBB调用此函数播放开场动画序列
 * 
 * 完整动画流程 (基于IDA 1:1实现):
 * 1. 初始化阶段: 加载FDOTHER.DAT多个索引(77,76,74,99,101,69-73)
 * 2. 主动画循环 (n535/esi: 535→0): 垂直滚动blit，关键帧触发事件
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

/* 时间点数组 (原游戏 dst_数组 [esp+0h] var_6C, 15个DWORD) */
static const int g_opening_time_points[] = {500, 400, 300, 200, 100, 50, 30, 20, 10, 5, 3, 1, 0, 0, 0};
#define FD2_OPENING_TIME_COUNT 12

/* 模拟原游戏 delay() 函数 */
static void fd2_delay(int ms) {
    SDL_Delay(ms);
}

    /* 全局调色板数据 (对应原游戏 FDOTHER_DAT) */
static u8 g_palette_6bit[768];
static int g_palette_loaded = 0;
static const u8* g_current_palette_data = NULL;  /* 当前FDOTHER_DAT指针 */

/*
 * sub_11D40: 设置VGA调色板 (原游戏 0x11D40)
 * 
 * 原游戏逻辑:
 *   while (a5 <= a6) {
 *     outp(968, a5);  // 写入调色板寄存器地址
 *     outp(969, FDOTHER_DAT[3*a5] - a7);     // R
 *     outp(969, FDOTHER_DAT[3*a5+1] - a7);   // G
 *     outp(969, FDOTHER_DAT[3*a5+2] - a7);   // B
 *     ++a5;
 *   }
 * 
 * 参数:
 *   start_color: 起始颜色索引 (a5)
 *   end_color:   结束颜色索引 (a6)
 *   color_offset: 颜色偏移/亮度调整 (a7)
 */
static void sub_11D40(fd2_render_t* render, int start_color, int end_color, int color_offset) {
    const u8* palette_data = g_current_palette_data ? g_current_palette_data : g_palette_6bit;
    if (!g_palette_loaded) return;
    
    u8 palette_8bit[768];
    memcpy(palette_8bit, render->palette, 768);
    
    for (int i = start_color; i <= end_color; i++) {
        int idx = i * 3;
        
        /* 原游戏反汇编：
         * v8 = FDOTHER_DAT[3*a5] - a7;
         * if (v8 < 0) LOBYTE(v8) = 0;
         * outp(969, v8);
         */
        int r = (int)palette_data[idx + 0] - color_offset;
        int g = (int)palette_data[idx + 1] - color_offset;
        int b = (int)palette_data[idx + 2] - color_offset;
        
        if (r < 0) r = 0;
        if (g < 0) g = 0;
        if (b < 0) b = 0;
        
        /* 6-bit转8-bit: v8 = (v6 << 2) | (v6 >> 4) */
        palette_8bit[idx + 0] = (u8)((r << 2) | (r >> 4));
        palette_8bit[idx + 1] = (u8)((g << 2) | (g >> 4));
        palette_8bit[idx + 2] = (u8)((b << 2) | (b >> 4));
    }
    
    fd2_render_set_palette_8bit(render, palette_8bit);
}

/*
 * sub_1F525: 淡入效果 (原游戏 0x1F525)
 * 
 * 原游戏逻辑:
 *   for (n64=64; n64>=0; --n64) {
 *     sub_11D40(0, 255, n64);  // colorOffset从64递减到0
 *     delay(2);
 *   }
 * 
 * 功能: 从暗到亮的淡入效果 (65步×2ms ≈ 130ms)
 */
static void sub_1F525(fd2_render_t* render) {
    for (int n64 = 64; n64 >= 0; --n64) {
        sub_11D40(render, 0, 255, n64);
        fd2_render_present(render);
        fd2_delay(2);
    }
    sub_11D40(render, 0, 255, 0);
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
/*
 * sub_10620: 检测按键 (原游戏 0x10620)
 * 
 * 原游戏通过读取BIOS键盘缓冲区(0x41A, 0x41C)来检测按键
 * SDL2实现: 非阻塞检查是否有新按键按下
 * 返回: 1=有按键, 0=无按键
 * 
 * 注意: 这是即时检测，不是全局状态！
 */
static int fd2_check_key_pressed(void) {
    /* 使用SDL_GetKeyboardState获取当前按键状态，不消费事件 */
    const Uint8* state = SDL_GetKeyboardState(NULL);
    /* 检测回车键和空格键（原游戏检测scan code 28和57） */
    if (state[SDL_SCANCODE_RETURN] || state[SDL_SCANCODE_SPACE] || 
        state[SDL_SCANCODE_ESCAPE] || state[SDL_SCANCODE_UP] || state[SDL_SCANCODE_DOWN]) {
        return 1;
    }
    return 0;
}

/*
 * sub_1F882: 淡入效果 (原游戏 0x1F882)
 * 
 * 反汇编代码:
 *   for (n64=0; n64<64; ++n64) {
 *     sub_11D40(0, 255, n64);  // 亮度从64递减到0
 *     delay(2);
 *   }
 * 
 * 功能: 从暗到亮的淡入效果 (64步×2ms ≈ 128ms)
 * 注意: 这不是等待按键函数！
 */
static void sub_1F882(fd2_render_t* render) {
    for (int n64 = 0; n64 < 64; ++n64) {
        sub_11D40(render, 0, 255, n64);
        fd2_render_present(render);
        fd2_delay(2);
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
 * 反编译代码:
 *   if (n99 != -1) {
 *     memset(655360, 0, 64000);
 *     FDOTHER_DAT = sub_111BA(..., n99);
 *   }
 *   sub_11D40(0, 255, 0);        // 黑色调色板
 *   sub_20421(n4, n15, 0);       // 播放AFM动画
 *   return sub_1F882();          // 等待按键
 * 
 * 调用方式 (从汇编):
 *   n535==330: push 99; push 90; push 4; call sub_1F81E  → sub_1F81E(4, 90, 99)
 *   n535==330: push 0;  push 50; push 5; call sub_1F81E  → sub_1F81E(5, 50, 0)
 */
static void sub_1F81E(fd2_state_machine_t* sm, int n4, int n15, int n99) {
    fd2_resources_t* res = fd2_get_resources();
    
    if (n99 != -1) {
        fd2_render_fill_screen(&sm->render, 0);
    }
    
    sub_11D40(&sm->render, 0, 255, 0);
    
    printf("[OPENING] sub_1F81E: Playing AFM n4=%d, n15=%d, n99=%d\n", n4, n15, n99);
    fd2_afm_play(n4, n15, 0, &sm->render, res);
    
    sub_1F882(&sm->render);
}

/*
 * sub_1F73F: 复杂特效 (原游戏 0x1F73F)
 * 
 * 反编译代码:
 *   sub_1F882();                          // 等待按键
 *   memset(655360, 0, 64000);             // 清屏
 *   FDOTHER_DAT = sub_111BA(..., n5);     // 加载索引n5
 *   _FDOTHER.DAT_ = sub_111BA(..., n100); // 加载索引n100
 *   sub_4E98D(_FDOTHER.DAT_, 0, 0, 655360, 320, -1); // 解码到屏幕
 *   sub_1F525();                          // 淡入
 *   sub_17AA9(1);                         // 音效
 *   sub_17AA9(6);                         // 音效
 *   sub_1F882();                          // 等待按键
 *   FDOTHER_DAT = sub_111BA(..., 101);    // 加载索引101
 *   sub_11EB0(n15+320*n99, n99, ..., 655360, 320, n15+320*n99, 320, 320, 200);
 *   return sub_1F525();                   // 再次淡入
 * 
 * 调用方式 (从汇编):
 *   n535==450: push 450; push n15; push 99; push 100; call sub_1F73F
 *   n535==10:  push 10;  push n15; push 76; push 75;  call sub_1F73F
 */
static void sub_1F73F(fd2_state_machine_t* sm, int n100, int n5, void* n15, int n99) {
    fd2_resources_t* res = fd2_get_resources();
    
    sub_1F882(&sm->render);
    
    fd2_render_fill_screen(&sm->render, 0);
    
    u32 dat_size = 0;
    const u8* dat_data = fd2_resources_get(res, FD2_DAT_FDOTHER, n5, &dat_size);
    if (dat_data) {
        fd2_rle_decompress_to_buffer(dat_data, dat_size, sm->render.screen, 0, 320, -1);
    }
    
    dat_data = fd2_resources_get(res, FD2_DAT_FDOTHER, n100, &dat_size);
    if (dat_data) {
        fd2_rle_decompress_to_buffer(dat_data, dat_size, sm->render.screen, 0, 320, -1);
        fd2_render_present(&sm->render);
    }
    
    sub_1F525(&sm->render);
    
    sub_1F882(&sm->render);
    
    int dst_offset = n99 * 320;
    if (dst_offset >= 0 && dst_offset + 64000 <= 270080) {
        sub_11EB0(sm->render.screen, 320,
                  (u8*)n15 + dst_offset, 320,
                  320, 200);
    }
    
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

    printf("[OPENING] Starting opening animation sequence (sub_1F894)...\n");

    fd2_resources_t* res = fd2_get_resources();

    /* ====================================================================
     * 变量初始化 (对应原游戏 0x1F899-0x1F8C3)
     * ==================================================================== */
    int n2_1 = 1;        /* var_1C: 菜单选项数 */
    int v27 = 0;         /* var_2C: 菜单选择标志 */
    int n2_2 = 0;        /* var_28: 当前选中项 */
    int n12 = 12;        /* var_20: 计数器 */
    unsigned char v33 = 0; /* var_14: 时间点索引 */
    
    /* dst_数组 = {450, 330, 210, 110, 25, 10} */
    int dst_[6] = {450, 330, 210, 110, 25, 10};

    /* ====================================================================
     * 阶段1: 初始化资源加载 (对应原游戏 0x1F8E6-0x1FA80)
     * ==================================================================== */
    
    /* sub_111BA(..., "FDOTHER.DAT", 77) */
    {
        u32 size = 0;
        const u8* data = fd2_resources_get(res, FD2_DAT_FDOTHER, 77, &size);
        printf("[OPENING] Loaded FDOTHER index 77, size=%u\n", size);
    }
    
    /* memset(655360, 0, 64000) - 清屏 */
    fd2_render_fill_screen(&sm->render, 0);
    
    /* FDOTHER_DAT = sub_111BA(..., "FDOTHER.DAT", 76)
     * 索引76包含768字节的6-bit RGB调色板数据 (256颜色×3字节)
     */
    {
        u32 size = 0;
        const u8* data = fd2_resources_get(res, FD2_DAT_FDOTHER, 76, &size);
        printf("[OPENING] Loaded FDOTHER index 76, size=%u\n", size);
        
        /* 提取调色板数据到全局缓冲区 */
        if (data && size >= 768) {
            memcpy(g_palette_6bit, data, 768);
            g_palette_loaded = 1;
            g_current_palette_data = g_palette_6bit;  /* 设置当前调色板指针 */
            printf("[OPENING] Palette loaded from index 76\n");
            
            /* 打印前几个调色板值用于验证 */
            printf("[OPENING] Palette[0] = R:%d G:%d B:%d\n", g_palette_6bit[0], g_palette_6bit[1], g_palette_6bit[2]);
            printf("[OPENING] Palette[1] = R:%d G:%d B:%d\n", g_palette_6bit[3], g_palette_6bit[4], g_palette_6bit[5]);
            printf("[OPENING] Palette[2] = R:%d G:%d B:%d\n", g_palette_6bit[6], g_palette_6bit[7], g_palette_6bit[8]);
        } else {
            printf("[OPENING] ERROR: Index 76 size %u < 768\n", size);
        }
    }
    
    /* sub_11D40(0, 255, 64) - 设置调色板(亮度64=最暗) */
    sub_11D40(&sm->render, 0, 255, 64);
    
    /* _FDOTHER.DAT__1 = sub_111BA(..., "FDOTHER.DAT", 74) */
    u32 size_74 = 0;
    const u8* data_74 = fd2_resources_get(res, FD2_DAT_FDOTHER, 74, &size_74);
    printf("[OPENING] Loaded FDOTHER index 74, size=%u\n", size_74);
    
    /* sub_4E98D(_FDOTHER.DAT__1, 0, 0, 655360, 320, -1) - 解码到屏幕 */
    if (data_74) {
        printf("[OPENING] Decoding FDOTHER index 74 to screen...\n");
        int result = fd2_rle_decompress_to_buffer(data_74, size_74, sm->render.screen, 0, 320, -1);
        printf("[OPENING] Decode result: %d\n", result);
        
        /* 调试：检查屏幕缓冲区 */
        int non_zero = 0;
        for (int i = 0; i < 64000; i++) {
            if (sm->render.screen[i] != 0) non_zero++;
        }
        printf("[OPENING] Screen buffer: %d non-zero pixels out of 64000\n", non_zero);
        
        fd2_render_present(&sm->render);
        printf("[OPENING] First frame rendered\n");
        fflush(stdout);
    }
    
    /* sub_1F525() - 淡入效果 */
    sub_1F525(&sm->render);
    
    /* sub_17AA9(1); sub_17AA9(30) - 音效 */
    printf("[OPENING] Playing sound effects 1 and 30\n");
    
    /* 淡入效果（原游戏sub_1F882） */
    sub_1F882(&sm->render);
    
    /* FDOTHER_DAT = sub_111BA(..., "FDOTHER.DAT", 99) */
    {
        u32 size = 0;
        const u8* data = fd2_resources_get(res, FD2_DAT_FDOTHER, 99, &size);
        printf("[OPENING] Loaded FDOTHER index 99, size=%u\n", size);
    }
    
    /* memset(655360, 0, 64000) - 清屏 */
    fd2_render_fill_screen(&sm->render, 0);
    
    /* sub_11D40(0, 255, 0) - 黑色调色板 */
    sub_11D40(&sm->render, 0, 255, 0);
    
    /* sub_20421(3, 90, 1) - 播放AFM动画 */
    printf("[OPENING] Playing AFM animation index 3...\n");
    fd2_afm_play(3, 90, 1, &sm->render, res);
    
    /* 淡入效果（原游戏sub_1F882） */
    sub_1F882(&sm->render);
    
    /* FDOTHER_DAT = sub_111BA(..., "FDOTHER.DAT", 101)
     * 索引101包含索引69-73图像的调色板数据
     */
    {
        u32 size = 0;
        const u8* data = fd2_resources_get(res, FD2_DAT_FDOTHER, 101, &size);
        printf("[OPENING] Loaded FDOTHER index 101, size=%u\n", size);
        
        /* 保存为当前调色板数据源 */
        if (data && size >= 768) {
            g_current_palette_data = data;
            printf("[OPENING] Palette source switched to index 101\n");
        }
    }
    
    /* sub_11D40(0, 255, 64) - 设置调色板(亮度64=最暗) */
    sub_11D40(&sm->render, 0, 255, 64);
    
    /* n15 = malloc(0x396C0) = 235200字节 */
    void* n15 = malloc(0x396C0);
    if (!n15) {
        printf("[OPENING] Failed to allocate animation buffer\n");
        return 0;
    }
    memset(n15, 0, 0x396C0);
    
    /* for (n5=0; n5<5; ++n5) 加载索引69-73 */
    printf("[OPENING] Loading FDOTHER indices 69-73...\n");
    for (int n5 = 0; n5 < 5; ++n5) {
        int index = n5 + 69;
        int dst_y = 147 * n5;
        
        u32 dat_size = 0;
        const u8* dat_data = fd2_resources_get(res, FD2_DAT_FDOTHER, index, &dat_size);
        
        printf("[OPENING]   Index %d: dat_size=%u, dst_y=%d (offset=%d)\n", index, dat_size, dst_y, dst_y * 320);
        
        if (dat_data) {
            int result = fd2_rle_decompress_to_buffer(dat_data, dat_size, n15, dst_y, 320, -1);
            printf("[OPENING]     Decode result: %d\n", result);
            
            /* 检查解码后的内容 */
            u8* dst_ptr = (u8*)n15 + dst_y * 320;
            int non_zero = 0;
            for (int i = 0; i < 147 * 320 && i < dat_size * 4; i++) {
                if (dst_ptr[i] != 0) non_zero++;
            }
            printf("[OPENING]     Decoded pixels: %d non-zero out of %d checked\n", non_zero, 147 * 320 < dat_size * 4 ? 147 * 320 : dat_size * 4);
        }
    }
    
    /* 检查n15缓冲区总内容 */
    {
        int total_non_zero = 0;
        for (int i = 0; i < 0x396C0; i++) {
            if (((u8*)n15)[i] != 0) total_non_zero++;
        }
        printf("[OPENING] n15 buffer total: %d non-zero pixels out of %d\n", total_non_zero, 0x396C0);
    }
    
    /* sub_4E381() - 刷新屏幕 */
    fd2_render_present(&sm->render);
    
    /* malloc(160) */
    void* n8_1 = malloc(160);

    /* ====================================================================
     * 阶段2: 主动画循环 (n535/esi: 535→0)
     * 对应原游戏 0x1FA85-0x1FC60
     * ==================================================================== */
    printf("[OPENING] Starting main animation loop (535 frames)...\n");
    fflush(stdout);
    
    for (int n535 = 535; ; --n535) {
        /* if (n535 < 0) goto LABEL_31 (菜单阶段) */
        if (n535 < 0) {
            goto opening_menu;
        }
        
        /* sub_11EB0(655360, 320, n15+320*n535, 320, 320, 200) */
        {
            int src_offset = n535 * 320;
            if (src_offset >= 0 && src_offset + 64000 <= 0x396C0) {
                sub_11EB0(sm->render.screen, 320,
                          (u8*)n15 + src_offset, 320,
                          320, 200);
            }
        }
        
        /* 刷新屏幕显示当前帧 */
        fd2_render_present(&sm->render);
        
        /* if (n535 == 535) sub_1F525() */
        if (n535 == 535) {
            sub_1F525(&sm->render);
        }
        
        /* if (n535 == 25) break (跳出循环到LABEL_13) */
        if (n535 == 25) {
            printf("[OPENING] Frame 25: breaking\n");
            fflush(stdout);
            
            /* sub_1F81E(0, 15, 0) */
            sub_1F81E(sm, 0, 15, 0);
            
            /* goto LABEL_13 */
            goto label_13;
        }
        
        /* switch (n535) */
        switch (n535) {
            case 330:
                /* sub_1F882() - 淡入效果 */
                sub_1F882(&sm->render);
                /* sub_1F81E(4, 90, 99) */
                sub_1F81E(sm, 4, 90, 99);
                /* sub_1F81E(5, 50, 0) */
                sub_1F81E(sm, 5, 50, 0);
                /* goto LABEL_13 */
                goto label_13;
                
            case 210:
                /* sub_1F882() - 淡入效果 */
                sub_1F882(&sm->render);
                /* sub_1F81E(6, 90, 99) */
                sub_1F81E(sm, 6, 90, 99);
                /* sub_1F81E(7, 50, 0) */
                sub_1F81E(sm, 7, 50, 0);
                /* goto LABEL_13 */
                goto label_13;
                
            case 110:
                /* sub_1F882() - 淡入效果 */
                sub_1F882(&sm->render);
                /* sub_1F81E(8, 90, 99) */
                sub_1F81E(sm, 8, 90, 99);
                /* goto LABEL_13 */
                goto label_13;
                
            case 450:
                /* sub_1F73F(100, 99, n15, 450) */
                sub_1F73F(sm, 100, 99, n15, 450);
                break;
                
            case 10:
                /* sub_1F73F(75, 76, n15, 10) */
                sub_1F73F(sm, 75, 76, n15, 10);
                break;
        }
        
        /* LABEL_24: 循环末尾逻辑 */
label_24:
        /* if (n535 == dst_[v33]) - 在特定帧切换调色板到索引102 */
        if (v33 < 6 && n535 == dst_[v33]) {
            n12 = 0;
            
            /* FDOTHER_DAT = sub_111BA(..., 102) - 切换到索引102调色板 */
            {
                u32 size = 0;
                const u8* data = fd2_resources_get(res, FD2_DAT_FDOTHER, 102, &size);
                if (data && size >= 768) {
                    g_current_palette_data = data;
                    printf("[OPENING] Palette -> index 102 at frame %d\n", n535);
                }
            }
            
            /* sub_11D40(0, 255, 0) - 正常亮度 */
            sub_11D40(&sm->render, 0, 255, 0);
            fd2_render_present(&sm->render);
            
            ++v33;
        }
        
        /* if (n12 == 11) - 切换回索引101调色板 */
        if (n12 == 11) {
            /* FDOTHER_DAT = sub_111BA(..., 101) */
            {
                u32 size = 0;
                const u8* data = fd2_resources_get(res, FD2_DAT_FDOTHER, 101, &size);
                if (data && size >= 768) {
                    g_current_palette_data = data;
                    printf("[OPENING] Palette -> index 101 (n12==11)\n");
                }
            }
            
            /* sub_11D40(0, 255, 0) - 正常亮度 */
            sub_11D40(&sm->render, 0, 255, 0);
            fd2_render_present(&sm->render);
        }
        
        ++n12;
        
        /* delay(30) */
        fd2_delay(30);
        
        /* if (!n535) delay(1000) */
        if (!n535) {
            fd2_delay(1000);
        }
        
        /* if (sub_10620()) goto LABEL_31 */
        if (fd2_check_key_pressed()) {
            goto opening_menu;
        }
        continue;
        
        /* LABEL_13: 从n535==25/330/210/110跳转过来 */
label_13:
        /* sub_11EB0(655360, 320, n15+320*n535, 320, 320, 200) */
        {
            int src_offset = n535 * 320;
            if (src_offset >= 0 && src_offset + 64000 <= 0x396C0) {
                sub_11EB0(sm->render.screen, 320,
                          (u8*)n15 + src_offset, 320,
                          320, 200);
            }
        }
        
        /* 刷新屏幕显示当前帧 */
        fd2_render_present(&sm->render);
        
        /* sub_111BA(..., "FDOTHER.DAT", 101) */
        /* sub_1F525() */
        sub_1F525(&sm->render);
        
        /* goto LABEL_24 */
        goto label_24;
    }

opening_menu:
    /* ====================================================================
     * 阶段3: 菜单显示和用户选择 (LABEL_31)
     * 对应原游戏 0x1FC66-0x1FF6A
     * ==================================================================== */
    printf("[OPENING] Entering menu phase (LABEL_31)...\n");
    
    /* for (n40=40; n40>=0; --n40) sub_2DF01(0, 255, n40, 0x3F, 0, 0); delay(8); */
    for (int n40 = 40; n40 >= 0; --n40) {
        sub_11D40(&sm->render, 0, 255, n40);
        fd2_render_present(&sm->render);
        fd2_delay(8);
    }
    fd2_delay(100);
    fd2_render_present(&sm->render);
    
    /* free(n15); free(_FDOTHER.DAT__1); */
    if (n15) {
        free(n15);
        n15 = NULL;
    }
    if (n8_1) {
        free(n8_1);
        n8_1 = NULL;
    }
    
    /* _FDOTHER.DAT__3 = sub_111BA(..., "FDOTHER.DAT", 7) */
    /* FDOTHER_DAT = sub_111BA(..., "FDOTHER.DAT", 8) */
    
    /* memset(655360, 0, 64000) */
    fd2_render_fill_screen(&sm->render, 0);
    
    /* sub_11D40(0, 255, 0) */
    sub_11D40(&sm->render, 0, 255, 0);
    
    /* sub_20421(1, 15, 1) */
    printf("[OPENING] Playing AFM animation index 1...\n");
    fd2_afm_play(1, 15, 1, &sm->render, res);
    
    /* sub_25B45(..., 3, 1) */
    /* sub_11DF2(0, 255, 64) */
    sub_11D40(&sm->render, 0, 255, 64);
    
    /* sub_16886(655360, 320, _FDOTHER.DAT__3, 0) */
    /* 渲染菜单背景 */
    
    /* for (n40_1=0; n40_1<=40; ++n40_1) sub_2DF01(0, 255, n40_1, 0x38, 0x3C, 0x3F); delay(8); */
    for (int n40_1 = 0; n40_1 <= 40; ++n40_1) {
        fd2_render_set_brightness(&sm->render, n40_1);
        fd2_render_present(&sm->render);
        fd2_delay(8);
    }
    fd2_render_present(&sm->render);
    
    /* 检查存档是否存在 */
    int n2_3;
    {
        FILE* fp = fopen("FD2.SAV", "rb");
        if (fp) {
            void* save_buf = malloc(22987);
            if (save_buf) {
                fread(save_buf, 1, 22987, fp);
                fclose(fp);
                
                n2_1 = 2;
                unsigned char* byte_ptr = (unsigned char*)save_buf + 12485;
                if (*byte_ptr != 255) {
                    n2_1 = 3;
                }
                free(save_buf);
            } else {
                fclose(fp);
            }
        }
    }
    
    /* sub_1FF79(..., 0, n2_1) - 显示菜单 */
    printf("[OPENING] Displaying menu with %d options\n", n2_1);
    
    /* 等待用户输入 */
    n2_2 = 0;
    v27 = 0;
    
    printf("[OPENING] Waiting for menu input...\n");
    fflush(stdout);
    
    while (!v27) {
        /* sub_1FF79(..., n2_2, n2_1) - 渲染菜单 */
        
        /* int386(22, &n3, &n3) - 读取键盘 */
        SDL_Event event;
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_QUIT) {
                v27 = 1;
                n2_2 = 255;
                break;
            }
            
            if (event.type == SDL_KEYDOWN && !event.key.repeat) {
                int scancode = event.key.keysym.scancode;
                int hi_byte = (scancode >> 8) & 0xFF;
                int lo_byte = scancode & 0xFF;
                
                n2_3 = n2_1 - 1;
                
                if (hi_byte == 72 || lo_byte == 72) {
                    /* 上箭头 */
                    if (n2_2) {
                        --n2_2;
                    } else {
                        n2_2 = n2_3;
                    }
                    printf("[OPENING] Menu select: %d (up)\n", n2_2);
                    fflush(stdout);
                }
                else if (hi_byte == 80 || lo_byte == 80) {
                    /* 下箭头 */
                    if (n2_2 == n2_3) {
                        n2_2 = 0;
                    } else {
                        ++n2_2;
                    }
                    printf("[OPENING] Menu select: %d (down)\n", n2_2);
                    fflush(stdout);
                }
                else if (lo_byte == 13 || lo_byte == 32 || 
                         hi_byte == 224 || hi_byte == 82) {
                    /* Enter/Space/特殊键 */
                    v27 = 1;
                    printf("[OPENING] Menu confirmed: %d\n", n2_2);
                    fflush(stdout);
                }
            }
        }
        
        fd2_render_present(&sm->render);
        fd2_delay(16);
    }
    
    /* 闪烁效果 (4次) */
    for (int n4 = 0; n4 < 4; ++n4) {
        fd2_delay(80);
        fd2_delay(80);
    }
    
    /* 淡入效果 */
    sub_1F882(&sm->render);
    fd2_render_fill_screen(&sm->render, 0);
    fd2_render_present(&sm->render);
    
    printf("[OPENING] Menu result: %d\n", n2_2);
    return n2_2;
}
