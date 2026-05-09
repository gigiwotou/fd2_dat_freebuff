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

/* ========================================================================
 * fd2_render_menu_item: 渲染单个菜单项 (基于IDA sub_16886)
 * 前向声明
 * ======================================================================== */
static void fd2_render_menu_item(u8* screen, int screen_offset, 
                                  const u8* menu_data, u32 menu_size,
                                  int menu_index, int selected_item, int current_item);

/*
 * fd2_play_opening_animation: 开场动画完整播放 (原游戏 sub_1F894)
 * 
 * 返回: 0=选择Start, 1=选择Load, 其他=退出
 */
int fd2_play_opening_animation(fd2_state_machine_t* sm) {
    if (!sm) return -1;

    printf("[OPENING] Opening animation skipped, showing menu directly...\n");

    fd2_resources_t* res = fd2_get_resources();

    /* ====================================================================
     * 变量初始化 (对应原游戏 0x1F899-0x1F8C3)
     * ==================================================================== */
    int n2_1 = 3;        /* var_1C: 菜单选项数 - 显示所有3个选项 */
    int v27 = 0;         /* var_2C: 菜单选择标志 */
    int n2_2 = 0;        /* var_28: 当前选中项 */
    
    /* ====================================================================
     * 加载菜单资源 (对应原游戏 sub_1FF79)
     * 正确的菜单资源：FDOTHER.DAT索引7
     * ==================================================================== */
    
    /* 加载调色板从索引76 */
    {
        u32 size = 0;
        const u8* data = fd2_resources_get(res, FD2_DAT_FDOTHER, 76, &size);
        printf("[OPENING] Loaded FDOTHER index 76 for palette, size=%u\n", size);
        
        if (data && size >= 768) {
            memcpy(g_palette_6bit, data, 768);
            g_palette_loaded = 1;
            g_current_palette_data = g_palette_6bit;
        }
    }
    
    /* 加载开场画面背景资源 - FDOTHER.DAT索引75 */
    u32 bg_size = 0;
    const u8* bg_data = fd2_resources_get(res, FD2_DAT_FDOTHER, 75, &bg_size);
    printf("[OPENING] Loading background from FDOTHER index 75, size=%u\n", bg_size);
    
    if (bg_data && bg_size > 0) {
        /* 使用RLE解码背景 */
        fd2_rle_decompress_to_buffer(bg_data, bg_size, sm->render.screen, 0, 320, -1);
        printf("[OPENING] Background RLE decoded successfully\n");
    } else {
        /* 降级渲染 - 使用灰色背景 */
        printf("[OPENING] Background resource not found, using fallback gray\n");
        for (int i = 0; i < 64000; i++) {
            sm->render.screen[i] = 50;  /* 灰色背景 */
        }
    }
    
    /* 加载第二层画面 - FDOTHER.DAT索引76 */
    u32 layer2_size = 0;
    const u8* layer2_data = fd2_resources_get(res, FD2_DAT_FDOTHER, 76, &layer2_size);
    printf("[OPENING] Loading layer 2 from FDOTHER index 76, size=%u\n", layer2_size);
    
    if (layer2_data && layer2_size > 0) {
        /* 使用RLE解码第二层 */
        fd2_rle_decompress_to_buffer(layer2_data, layer2_size, sm->render.screen, 0, 320, -1);
        printf("[OPENING] Layer 2 RLE decoded successfully\n");
    }
    
    /* 设置调色板 - 使用FDOTHER.DAT索引76的调色板数据 */
    {
        u32 pal_size = 0;
        const u8* pal_data = fd2_resources_get(res, FD2_DAT_FDOTHER, 76, &pal_size);
        printf("[OPENING] Loading palette from FDOTHER index 76, size=%u\n", pal_size);
        
        if (pal_data && pal_size >= 768) {
            memcpy(g_palette_6bit, pal_data, 768);
            g_palette_loaded = 1;
            g_current_palette_data = g_palette_6bit;
            
            /* 将6-bit调色板转换为8-bit并设置到渲染器 */
            for (int i = 0; i < 256; i++) {
                int idx = i * 3;
                int r = g_palette_6bit[idx + 0];
                int g = g_palette_6bit[idx + 1];
                int b = g_palette_6bit[idx + 2];
                sm->render.palette[idx + 0] = (u8)((r << 2) | (r >> 4));
                sm->render.palette[idx + 1] = (u8)((g << 2) | (g >> 4));
                sm->render.palette[idx + 2] = (u8)((b << 2) | (b >> 4));
            }
            
            /* 更新ARGB调色板 */
            for (int i = 0; i < 256; i++) {
                sm->render.argb_palette[i] =
                    (0xFFu << 24) |
                    ((u32)sm->render.palette[i * 3 + 0] << 16) |
                    ((u32)sm->render.palette[i * 3 + 1] << 8)  |
                    ((u32)sm->render.palette[i * 3 + 2]);
            }
            printf("[OPENING] Palette loaded and converted successfully\n");
        }
    }
    
    /* 刷新屏幕显示开场画面 */
    fd2_render_present(&sm->render);
    printf("[OPENING] Opening screen displayed\n");
    SDL_Delay(500);
    
    /* ====================================================================
     * 加载正确的菜单资源：FDOTHER.DAT索引7
     * 根据IDA分析，菜单文本来自索引7
     * ==================================================================== */
    u32 menu_size = 0;
    const u8* menu_data = fd2_resources_get(res, FD2_DAT_FDOTHER, 7, &menu_size);
    printf("[OPENING] Loaded FDOTHER index 7 for menu, size=%u\n", menu_size);
    
    if (!menu_data || menu_size < 100) {
        printf("[OPENING] ERROR: Failed to load menu data from index 7\n");
    } else {
        printf("[OPENING] Menu data loaded successfully\n");
        /* 打印菜单数据前32字节用于调试 */
        printf("[OPENING] Menu data header: ");
        for (int i = 0; i < 32 && i < menu_size; i++) {
            printf("%02X ", menu_data[i]);
        }
        printf("\n");
    }
    
    /* ====================================================================
     * 检查存档是否存在，设置菜单选项数
     * ==================================================================== */
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
    
    printf("[OPENING] Displaying menu with %d options\n", n2_1);
    
    /* ====================================================================
     * 渲染菜单 (简化版本 - 直接绘制像素)
     * ==================================================================== */
    if (menu_data && menu_size > 6) {
        /* 菜单文本位置 */
        int base_x = 100;
        int base_y = 140;
        int row_height = 24;
        
        /* 菜单选项 */
        const char* menu_items[] = {"START GAME", "LOAD GAME", "EXIT"};
        
        /* 渲染菜单项 */
        for (int i = 0; i < n2_1 && i < 3; i++) {
            const char* text = menu_items[i];
            int x = base_x;
            int y = base_y + i * row_height;
            
            /* 选中项高亮 - 使用白色背景 */
            if (i == n2_2) {
                /* 绘制选中背景 */
                for (int py = 0; py < 16; py++) {
                    for (int px = 0; px < (int)strlen(text) * 16; px++) {
                        int offset = (y + py) * 320 + x + px;
                        if (offset >= 0 && offset < 64000) {
                            sm->render.screen[offset] = 200;  /* 亮灰色背景 */
                        }
                    }
                }
            }
            
            /* 渲染文本 - 简单方块字符 */
            for (int j = 0; text[j]; j++) {
                int char_x = x + j * 16;
                int char_y = y;
                /* 使用明显的颜色：选中=白色，未选中=浅灰色 */
                u8 color = (i == n2_2) ? 255 : 150;  /* 白色/浅灰色 */
                
                /* 绘制简单的方块字符 */
                for (int py = 2; py < 14; py++) {
                    for (int px = 2; px < 14; px++) {
                        int offset = (char_y + py) * 320 + char_x + px;
                        if (offset >= 0 && offset < 64000) {
                            sm->render.screen[offset] = color;
                        }
                    }
                }
            }
        }
        
        printf("[OPENING] Menu rendered\n");
    }
    
    /* 刷新屏幕 */
    fd2_render_present(&sm->render);
    fflush(stdout);
    
    /* 等待用户输入 */
    while (!v27) {
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
        
        /* 刷新屏幕 */
        fd2_render_present(&sm->render);
        fd2_delay(16);
    }
    
    /* 淡入效果 */
    sub_1F882(&sm->render);
    fd2_render_fill_screen(&sm->render, 0);
    fd2_render_present(&sm->render);
    
    printf("[OPENING] Menu result: %d\n", n2_2);
    return n2_2;
}

/* ========================================================================
 * fd2_render_menu_item: 渲染单个菜单项 (基于IDA sub_16886)
 * ======================================================================== */
static void fd2_render_menu_item(u8* screen, int screen_offset, 
                                  const u8* menu_data, u32 menu_size,
                                  int menu_index, int selected_item, int current_item) {
    if (!screen || !menu_data || menu_size < 10) return;
    
    int resource_offset_offset = 6 + 4 * menu_index;
    if (resource_offset_offset + 4 > (int)menu_size) {
        printf("[MENU] ERROR: Offset %d out of bounds (size=%u)\n", resource_offset_offset, menu_size);
        return;
    }
    
    /* 读取当前菜单项的偏移 */
    u32 resource_offset = *(u32*)(menu_data + resource_offset_offset);
    printf("[MENU] Menu index %d: offset=%u\n", menu_index, resource_offset);
    
    if (resource_offset >= menu_size) {
        printf("[MENU] ERROR: Resource offset %u >= size %u\n", resource_offset, menu_size);
        return;
    }
    
    /* 读取下一个菜单项的偏移来计算当前项的大小 */
    u32 next_offset = menu_size;
    int next_offset_offset = 6 + 4 * (menu_index + 1);
    if (next_offset_offset + 4 <= (int)menu_size) {
        next_offset = *(u32*)(menu_data + next_offset_offset);
    }
    
    u32 resource_size = next_offset - resource_offset;
    printf("[MENU] Next offset=%u, resource size=%u\n", next_offset, resource_size);
    
    if (resource_size == 0 || resource_offset + resource_size > menu_size) {
        printf("[MENU] ERROR: Invalid resource size %u\n", resource_size);
        return;
    }
    
    const u8* resource_ptr = menu_data + resource_offset;
    
    /* 打印资源数据前16字节用于调试 */
    printf("[MENU] Resource data: ");
    for (int i = 0; i < 16 && i < (int)resource_size; i++) {
        printf("%02X ", resource_ptr[i]);
    }
    printf("\n");
    
    /* 尝试RLE解码 */
    printf("[MENU] Rendering menu item %d at screen offset %d, resource size=%u\n", 
           menu_index, screen_offset, resource_size);
    
    fd2_rle_decompress_to_buffer(resource_ptr, 
                                 resource_size,
                                 screen, 
                                 screen_offset, 
                                 320, 
                                 -1);
}
