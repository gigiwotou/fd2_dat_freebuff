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
 * sub_16886: 从FDOTHER.DAT加载资源并解码到屏幕 (原游戏 0x16886)
 * 对应IDA反编译:
 *   sub_3702F(a1, a2, a3, a4, 32);
 *   sub_4E98D(*(_DWORD *)(a7 + 4 * a8 + 6) + a7, 0, 0, a5, a6, -1);
 * 
 * 参数:
 *   dst_x = 目标X坐标
 *   dst_y = 目标Y坐标
 *   dat_ptr = 资源基址指针 (嵌套DAT文件指针,不是FDOTHER.DAT主文件!)
 *   resource_index = 资源索引
 */
static void sub_16886(u8* screen, int dst_x, int dst_y, const u8* dat_ptr, int resource_index) {
    if (!screen || !dat_ptr) {
        printf("[MENU] ERROR: Invalid params for sub_16886 (index=%d)\n", resource_index);
        return;
    }
    
    /* 根据IDA公式: 资源指针 = dat_ptr + *(uint32_t*)(dat_ptr + 4*resource_index + 6) */
    u32 resource_offset = *(const uint32_t*)(dat_ptr + 4 * resource_index + 6);
    const u8* res_data = dat_ptr + resource_offset;
    
    /* 读取图像尺寸 (小端序) */
    int16_t w = *(int16_t*)(res_data + 0);
    int16_t h = *(int16_t*)(res_data + 2);
    
    printf("[MENU] sub_16886: index=%d, offset=%u, dst=(%d,%d)\n", 
           resource_index, resource_offset, dst_x, dst_y);
    printf("[MENU] Resource %d: dims=%dx%d\n", resource_index, w, h);
    
    /* 验证尺寸 */
    if (w <= 0 || w > 640 || h <= 0 || h > 480) {
        printf("[MENU] ERROR: Invalid dimensions %dx%d\n", w, h);
        return;
    }
    
    /* 验证目标区域不越界 */
    if (dst_x + w > 320 || dst_y + h > 200) {
        printf("[MENU] ERROR: Destination out of bounds (%d+%d, %d+%d)\n", dst_x, w, dst_y, h);
        return;
    }
    
    /* 估算资源大小 (从偏移表下一个条目减去当前偏移,或使用固定大小) */
    u32 resource_size = 100000; /* 临时估算 */
    
    /* RLE解码到屏幕 */
    int result = fd2_rle_decompress(res_data + 4, resource_size - 4, screen, dst_x, dst_y, 320, w, h, -1);
    if (result != 0) {
        printf("[MENU] WARNING: RLE decompression returned %d for index %d\n", result, resource_index);
    }
}

/*
 * sub_1FF79: 渲染开始菜单 (原游戏 0x1FF79)
 * 对应IDA反编译:
 *   sub_3702F(a1, a2, a3, a4, 20);     // 栈检查,20是栈大小参数
 *   n2_1 = (!n2_2) ? 2 : 1;            // 选中项0用索引1，否则用2
 *   sub_16886(707969, 320, _FDOTHER.DAT_, n2_1);
 *   if (n2 > 1) { n3 = (n2_2==1)?4:3; sub_16886(710849, 320, _FDOTHER.DAT_, n3); }
 *   if (n2 > 2) { n5 = (n2_2==2)?6:5; sub_16886(713729, 320, _FDOTHER.DAT_, n5); }
 * 
 * 注意: nested_dat_ptr是索引7的资源指针(嵌套DAT文件指针),不是FDOTHER.DAT主文件!
 * 背景在调用此函数之前已经用嵌套DAT索引0渲染!
 * 
 * 屏幕偏移计算 (相对于屏幕缓冲区655360):
 *   707969 - 655360 = 52609 = 164*320 + 129 -> y=164, x=129
 *   710849 - 655360 = 55489 = 173*320 + 129 -> y=173, x=129  
 *   713729 - 655360 = 58369 = 182*320 + 129 -> y=182, x=129
 */
static void sub_1FF79(u8* screen, int selected_item, int menu_count, const u8* nested_dat_ptr) {
    int menu_x = 129;
    int menu_y[] = {164, 173, 182};
    
    /* 渲染菜单项1 (索引1=未选中, 索引2=选中) */
    {
        int res_index = (selected_item == 0) ? 1 : 2;
        sub_16886(screen, menu_x, menu_y[0], nested_dat_ptr, res_index);
    }
    
    /* 渲染菜单项2 (索引3=未选中, 索引4=选中) */
    if (menu_count > 1) {
        int res_index = (selected_item == 1) ? 4 : 3;
        sub_16886(screen, menu_x, menu_y[1], nested_dat_ptr, res_index);
    }
    
    /* 渲染菜单项3 (索引5=未选中, 索引6=选中) */
    if (menu_count > 2) {
        int res_index = (selected_item == 2) ? 6 : 5;
        sub_16886(screen, menu_x, menu_y[2], nested_dat_ptr, res_index);
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
     * 获取FDOTHER.DAT完整数据指针 (用于访问偏移表)
     * 对应原游戏的全局指针 dword_53F56
     * ==================================================================== */
    const fd2_dat_t* fdother_dat = fd2_resources_get_dat(res, FD2_DAT_FDOTHER);
    if (!fdother_dat) {
        printf("[OPENING] ERROR: FDOTHER.DAT not loaded\n");
        return -1;
    }
    
    printf("[OPENING] FDOTHER.DAT data=%p, file_size=%u, resource_count=%u\n", 
           fdother_dat->data, fdother_dat->file_size, fdother_dat->resource_count);
    
    /* 打印偏移表前25项用于调试 */
    printf("[OPENING] FDOTHER offset table (first 25 entries):\n");
    for (int i = 0; i < 25 && i < (int)fdother_dat->resource_count; i++) {
        const fd2_resource_t* ri = &fdother_dat->resources[i];
        printf("  [%2d] offset=%u, size=%u", i, ri->start, ri->size);
        if (ri->start < fdother_dat->file_size - 4) {
            int16_t w = *(int16_t*)(fdother_dat->data + ri->start + 0);
            int16_t h = *(int16_t*)(fdother_dat->data + ri->start + 2);
            if (w > 0 && w < 640 && h > 0 && h < 480) {
                printf(" -> %dx%d\n", w, h);
            } else {
                printf(" -> INVALID %dx%d\n", w, h);
            }
        } else {
            printf("\n");
        }
    }
    
    /* ====================================================================
     * 加载菜单调色板从索引8 (对应原游戏 sub_1F894 第120-127行)
     * 原游戏: FDOTHER_DAT = sub_111BA(..., 8);
     * 索引8是菜单调色板，大小768字节(256色×3)
     * ==================================================================== */
    {
        const fd2_resource_t* pal_res = &fdother_dat->resources[8];
        const u8* pal_data = fdother_dat->data + pal_res->start;
        u32 pal_size = pal_res->size;
        
        printf("[OPENING] Loading menu palette from index 8, offset=%u, size=%u\n", pal_res->start, pal_size);
        
        if (pal_size >= 768) {
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
            printf("[OPENING] Menu palette loaded and converted successfully\n");
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
     * 加载索引7的嵌套DAT文件 (对应原游戏 0x1FCB6-0x1FCCB)
     * 原游戏: push 7; call sub_111BA; mov var_24, eax
     * 索引7是一个嵌套的DAT文件，包含菜单资源的偏移表
     * ==================================================================== */
    if (7 >= fdother_dat->resource_count) {
        printf("[OPENING] ERROR: Index 7 (nested DAT) not found in FDOTHER.DAT\n");
        return -1;
    }
    
    const fd2_resource_t* nested_res = &fdother_dat->resources[7];
    const u8* nested_dat_data = fdother_dat->data + nested_res->start;
    u32 nested_dat_size = nested_res->size;
    
    printf("[OPENING] Nested DAT (index 7): offset=%u, size=%u\n", nested_res->start, nested_dat_size);
    
    /* 验证嵌套DAT文件头 */
    if (nested_dat_size < 10) {
        printf("[OPENING] ERROR: Nested DAT too small (%u bytes)\n", nested_dat_size);
        return -1;
    }
    
    /* 解析嵌套DAT的资源数量 (偏移6开始的4字节) */
    u32 nested_resource_count = 0;
    for (u32 i = 0; ; i++) {
        u32 offset;
        memcpy(&offset, nested_dat_data + 6 + i * 4, 4);
        if (offset >= nested_dat_size) {
            nested_resource_count = i;
            break;
        }
        if (i >= 100) {
            nested_resource_count = i;
            break;
        }
    }
    
    printf("[OPENING] Nested DAT resource count: %u\n", nested_resource_count);
    
    /* 打印嵌套DAT的偏移表用于调试 */
    printf("[OPENING] Nested DAT offset table:\n");
    for (u32 i = 0; i < nested_resource_count && i <= 25; i++) {
        u32 offset;
        memcpy(&offset, nested_dat_data + 6 + i * 4, 4);
        printf("  [%2u] offset=%u", i, offset);
        if (offset < nested_dat_size - 4) {
            int16_t w = *(int16_t*)(nested_dat_data + offset + 0);
            int16_t h = *(int16_t*)(nested_dat_data + offset + 2);
            if (w > 0 && w < 640 && h > 0 && h < 480) {
                printf(" -> %dx%d\n", w, h);
            } else {
                printf(" -> %dx%d\n", w, h);
            }
        } else {
            printf("\n");
        }
    }
    
    /* 嵌套DAT的数据指针 (从偏移0开始，包含文件头和偏移表) */
    const u8* nested_dat_ptr = nested_dat_data;
    
    /* ====================================================================
     * 渲染菜单背景 (对应原游戏 sub_1F894 第133行)
     * 原游戏: sub_16886(..., 655360, 320, nested_dat_ptr, 0);
     * 使用嵌套DAT的索引0作为背景
     * ==================================================================== */
    fd2_render_fill_screen(&sm->render, 0);
    sub_16886(sm->render.screen, 0, 0, nested_dat_ptr, 0);
    printf("[OPENING] Menu background rendered from nested DAT index 0\n");
    
    /* ====================================================================
     * 渲染菜单项 (对应原游戏 sub_1FF79)
     * 注意: 使用嵌套DAT指针，不是FDOTHER.DAT主文件!
     * ==================================================================== */
    sub_1FF79(sm->render.screen, n2_2, n2_1, nested_dat_ptr);
    printf("[OPENING] Menu items rendered\n");
    
    /* 刷新屏幕 */
    SDL_PumpEvents();  /* 确保事件队列更新 */
    fd2_render_present(&sm->render);
    fflush(stdout);
    
    /* 等待用户输入 */
    while (!v27) {
        SDL_Event event;
        int need_render = 0;
        
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
                    need_render = 1;
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
                    need_render = 1;
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
        
        /* 只在需要时重新渲染 */
        if (need_render) {
            fd2_render_fill_screen(&sm->render, 0);
            sub_16886(sm->render.screen, 0, 0, nested_dat_ptr, 0);  /* 重新渲染背景 */
            sub_1FF79(sm->render.screen, n2_2, n2_1, nested_dat_ptr);
            fd2_render_present(&sm->render);
        }
        fd2_delay(16);
    }
    
    /* 淡入效果 */
    sub_1F882(&sm->render);
    fd2_render_fill_screen(&sm->render, 0);
    fd2_render_present(&sm->render);
    
    printf("[OPENING] Menu result: %d\n", n2_2);
    return n2_2;
}
