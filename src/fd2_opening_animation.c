#include "fd2_opening_animation.h"
#include "fd2_resources.h"
#include "fd2_globals.h"
#include "fd2_render.h"
#include "fd2_rle.h"
#include "fd2_audio.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <SDL2/SDL.h>

#define FD2_DAT_FDOTHER 0
#define FD2_DAT_FDTXT   1

extern fd2_resources_t* fd2_get_resources(void);
extern int fd2_afm_play(int a1, int a2, int a3, fd2_render_t* render, fd2_resources_t* res);
extern void fd2_delay(int ms);

/* Forward declarations for local helpers */
static void sub_1F882(fd2_render_t* render);
static void sub_1F525(fd2_render_t* render);
static void sub_11D40(fd2_render_t* render, int a2, int a3, int a4);
static void fd2_render_menu_from_fdother(u8* screen, int screen_offset, 
                                          int fdother_index, int selected_index, int item_index);

/* ========================================================================
 * Local Helper Functions (原游戏相关逻辑的本地实现)
 * ======================================================================== */

/* fd2_delay: 延迟函数 */
void fd2_delay(int ms) {
    SDL_Delay(ms);
}

/* sub_1F882: 等待按键 (原游戏 0x1F882) */
static void sub_1F882(fd2_render_t* render) {
    (void)render;
    SDL_Event event;
    int pressed = 0;
    
    SDL_PumpEvents();
    SDL_FlushEvent(SDL_KEYDOWN);
    
    while (!pressed && !g_sdl_quit_requested) {
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_QUIT) {
                g_sdl_quit_requested = 1;
                return;
            }
            if (event.type == SDL_KEYDOWN) {
                pressed = 1;
            }
        }
        SDL_Delay(10);
    }
    
    SDL_Delay(100);
    while (!g_sdl_quit_requested) {
        SDL_PumpEvents();
        int all_released = 1;
        const Uint8* state = SDL_GetKeyboardState(NULL);
        for (int i = 0; i < SDL_NUM_SCANCODES; i++) {
            if (state[i]) {
                all_released = 0;
                break;
            }
        }
        if (all_released) break;
        SDL_Delay(10);
    }
}

/* sub_1F525: 淡入效果 (原游戏 0x1F525) */
static void sub_1F525(fd2_render_t* render) {
    if (!render || !g_palette_loaded) return;
    fd2_render_present(render);
}

/* sub_11D40: 设置调色板 (原游戏 0x11D40) */
static void sub_11D40(fd2_render_t* render, int a2, int a3, int a4) {
    if (!render || !g_palette_loaded) return;
    (void)a2; (void)a3; (void)a4;
}

/*
 * fd2_render_menu_from_fdother: 渲染菜单项 (基于IDA sub_16886)
 * 从FDOTHER.DAT主文件加载资源并RLE解码到屏幕
 */
static void fd2_render_menu_from_fdother(u8* screen, int screen_offset, 
                                          int fdother_index, int selected_index, int item_index) {
    if (!screen || fdother_index < 0) return;
    
    fd2_resources_t* res = fd2_get_resources();
    u32 res_size = 0;
    const u8* res_data = fd2_resources_get(res, FD2_DAT_FDOTHER, fdother_index, &res_size);
    
    if (!res_data || res_size < 4) {
        printf("[MENU] ERROR: Failed to load FDOTHER index %d (size=%u)\n", fdother_index, res_size);
        return;
    }
    
    printf("[MENU] Rendering item %d, selected=%d, using FDOTHER index %d, size=%u\n",
           item_index, selected_index, fdother_index, res_size);
    
    /* RLE解码到屏幕 */
    fd2_rle_decompress_to_buffer(res_data, res_size, screen, screen_offset, 320, -1);
}

/*
 * sub_1FF79: 渲染开始菜单 (原游戏 0x1FF79)
 * 对应IDA反编译:
 *   sub_3702F(a1, a2, a3, a4, 20);     // 背景索引20
 *   n2_1 = (!n2_2) ? 2 : 1;            // 选中项0用索引1，否则用2
 *   sub_16886(707969, 320, _FDOTHER.DAT_, n2_1);
 *   if (n2 > 1) { n3 = (n2_2==1)?4:3; sub_16886(710849, 320, _FDOTHER.DAT_, n3); }
 *   if (n2 > 2) { n5 = (n2_2==2)?6:5; sub_16886(713729, 320, _FDOTHER.DAT_, n5); }
 * 
 * 屏幕偏移计算 (相对于屏幕缓冲区655360):
 *   707969 - 655360 = 52609 = 164*320 + 129 -> y=164, x=129
 *   710849 - 655360 = 55489 = 173*320 + 129 -> y=173, x=129  
 *   713729 - 655360 = 58369 = 182*320 + 129 -> y=182, x=129
 */
static void sub_1FF79(u8* screen, int selected_item, int menu_count) {
    int menu_x = 129;
    int menu_y[] = {164, 173, 182};
    
    /* 渲染背景 (索引20) */
    fd2_render_menu_from_fdother(screen, 0, 20, selected_item, -1);
    
    /* 渲染菜单项 */
    for (int i = 0; i < menu_count && i < 3; i++) {
        /* 根据选中状态选择索引 */
        int res_index;
        if (i == 0) {
            /* 第一项: 索引1(选中) / 索引2(未选中) */
            res_index = (selected_item == 0) ? 1 : 2;
        } else if (i == 1) {
            /* 第二项: 索引3(未选中) / 索引4(选中) */
            res_index = (selected_item == 1) ? 4 : 3;
        } else {
            /* 第三项: 索引5(未选中) / 索引6(选中) */
            res_index = (selected_item == 2) ? 6 : 5;
        }
        
        int screen_offset = menu_y[i] * 320 + menu_x;
        fd2_render_menu_from_fdother(screen, screen_offset, res_index, selected_item, i);
    }
}

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
    int n2_1 = 3;        /* var_1C: 菜单选项数 */
    int v27 = 0;         /* var_2C: 菜单选择标志 */
    int n2_2 = 0;        /* var_28: 当前选中项 */
    int n2_3 = 0;
    
    /* ====================================================================
     * 加载调色板从索引76 (对应原游戏 sub_11D40)
     * ==================================================================== */
    {
        u32 size = 0;
        const u8* data = fd2_resources_get(res, FD2_DAT_FDOTHER, 76, &size);
        printf("[OPENING] Loaded FDOTHER index 76 for palette, size=%u\n", size);
        
        if (data && size >= 768) {
            memcpy(g_palette_6bit, data, 768);
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
    
    /* ====================================================================
     * 检查存档是否存在，设置菜单选项数
     * ==================================================================== */
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
     * 渲染菜单 (对应原游戏 sub_1FF79)
     * ==================================================================== */
    sub_1FF79(sm->render.screen, n2_2, n2_1);
    printf("[OPENING] Menu rendered\n");
    
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
        
        /* 重新渲染菜单并刷新屏幕 */
        fd2_render_fill_screen(&sm->render, 0);
        sub_1FF79(sm->render.screen, n2_2, n2_1);
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
