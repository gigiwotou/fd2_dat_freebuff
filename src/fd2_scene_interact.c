#include "fd2_state_machine.h"
#include "fd2_scene_interact.h"
#include "fd2_globals.h"
#include "fd2_data_loader.h"
#include "fd2_render.h"
#include "fd2_render_pipeline.h"
#include "fd2_scenes.h"
#include "fd2_rle.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* 辅助函数前向声明 */
static int fd2_get_bios_timer(void);
static int fd2_check_key_pressed(void);
static u8 GET_HIBYTE(u32 val);
static void SET_HIBYTE(u32* val, u8 hibyte);

/* 内部函数前向声明 */
static int fd2_scene_interact_main_loop_impl(fd2_state_machine_t* sm);
static void fd2_scene_load_fdicon_data(fd2_state_machine_t* sm);
static int fd2_scene_process_special_scene(fd2_state_machine_t* sm);
static int fd2_scene_process_normal_scene(fd2_state_machine_t* sm);
static void fd2_scene_handle_key_impl(fd2_state_machine_t* sm, int key_code);

/* ========================================================================
 * fd2_state_machine_interact_loop: 场景交互循环 (原游戏 sub_26152, 0x49A字节)
 *
 * 原游戏流程 (1:1 复制):
 * 1. 释放旧场景资源 (n8_1, FDFIELD_DAT__1, FDSHAP_DAT, FDFIELD_DAT__0)
 * 2. 打开fdicon.b24，调用sub_11019处理每个子场景
 * 3. 检查特殊场景 byte_523E7[n17]
 * 4. 特殊场景: memset, sub_11D40, sub_1956B, sub_15F84, sub_19953等
 * 5. 普通场景: malloc FDSHAP, sub_4E809, sub_1F882, sub_111BA等
 * 6. 主交互循环 (do-while)
 * ======================================================================== */
int fd2_state_machine_interact_loop(fd2_state_machine_t* sm) {
    if (!sm) return 0;
    
    /* 阶段1: 释放旧场景资源 (对应原游戏 0x26186-0x261f9) */
    if (g_n8_1) { free(g_n8_1); g_n8_1 = NULL; }
    if (g_FDFIELD_DAT__1) { free(g_FDFIELD_DAT__1); g_FDFIELD_DAT__1 = NULL; }
    if (g_FDSHAP_DAT) { free(g_FDSHAP_DAT); g_FDSHAP_DAT = NULL; }
    if (g_FDFIELD_DAT__0) { free(g_FDFIELD_DAT__0); g_FDFIELD_DAT__0 = NULL; }
    if (g_dword_53A61) { free(g_dword_53A61); g_dword_53A61 = NULL; }
    
    /* 阶段2: 加载fdicon.b24数据 (对应原游戏 0x2620a-0x26265) */
    fd2_scene_load_fdicon_data(sm);
    
    /* 阶段3: 检查特殊场景 (对应原游戏 0x26272) */
    if (g_byte_523E7[g_n17]) {
        return fd2_scene_process_special_scene(sm);
    }
    
    /* 阶段4: 处理普通场景 */
    return fd2_scene_process_normal_scene(sm);
}

/*
 * fd2_scene_load_fdicon_data: 加载fdicon.b24 (对应原游戏 0x2620a-0x26265)
 */
static void fd2_scene_load_fdicon_data(fd2_state_machine_t* sm) {
    FILE* fp;
    int n16;
    const char* path;
    
    g_n8_1 = NULL;
    g_dword_53BDF = 0;
    
    /* 打开FDICON.B24 - 使用资源加载路径 */
    path = fd2_get_data_path("", "FDICON.B24");
    fp = fopen(path, "rb");
    if (!fp) {
        printf("File not found fdicon.b24 at: %s!!!\n", path);
        return;
    }
    
    /* 循环处理每个子场景 (对应原游戏 for循环 0x26238-0x26260) */
    for (n16 = 0; n16 < g_n16_1; ++n16) {
        /* TODO: sub_11019() - 需要IDA分析 */
        /* sub_11019(*(u8*)(n8_3 + 80*n16 + 7), ..., n16, n8_3, ..., fp); */
    }
    
    fclose(fp);
    (void)sm;
}

/*
 * fd2_scene_process_special_scene: 处理特殊场景 (对应原游戏 0x26272-0x2637a)
 */
static int fd2_scene_process_special_scene(fd2_state_machine_t* sm) {
    (void)sm;
    int v9 = 0;
    int result;
    
    /* memset(n16, 655360, 0, 64000) */
    if (g_n655360_0) {
        memset((void*)g_n655360_0, 0, 64000);
    }
    
    /* sub_11D40(..., 0, 255, 0) */
    /* sub_1956B(75) */
    /* sub_15F84(..., FDTXT_DAT__0, 410, ..., 76, 74, 19, 1) */
    /* sub_16559(0) */
    
    g_FDFIELD_DAT__0 = (void*)1;
    
    /* sub_19953() - 主渲染循环 */
    /* v9 = 返回值 */
    
    g_FDFIELD_DAT__0 = NULL;
    /* sub_197E5() */
    /* result = sub_26996() */
    
    result = 0;
    
    if (v9 != -1 && !g_n4_1) {
        /* 加载FDOTHER.DAT索引13 */
        const char* path = fd2_get_data_path(NULL, "FDOTHER.DAT");
        g_FDOTHER_DAT__11 = fd2_dat_load_resource(path, (void*)g_FDOTHER_DAT__11, 13);
        /* sub_2968D(0) */
        if (g_FDOTHER_DAT__11) {
            free((void*)g_FDOTHER_DAT__11);
            g_FDOTHER_DAT__11 = NULL;
        }
    }
    
    /* do-while循环: sub_2AF28() */
    do {
        g_n8_1 = g_n8_3;
        /* result = sub_2AF28() */
        g_n8_1 = NULL;
    } while (!result);
    
    /* sub_11D40(..., 0, 255, 255) */
    
    return 0;
}

/*
 * fd2_scene_process_normal_scene: 处理普通场景 (对应原游戏 0x26384-0x265da)
 */
static int fd2_scene_process_normal_scene(fd2_state_machine_t* sm) {
    void* fdother_data;
    
    (void)sm;
    
    /* malloc(153216) for FDSHAP_DAT */
    g_FDSHAP_DAT = malloc(153216);
    if (!g_FDSHAP_DAT) return 0;
    
    /* dword_53F56 = (int)sub_4E809(n17) */
    /* LOBYTE(n16) = *(u8*)dword_53F56 */
    /* sub_1F882(dword_53F56, ...) */
    
    /* 加载FDOTHER.DAT索引10 (对应原游戏 0x263b7) */
    const char* path = fd2_get_data_path(NULL, "FDOTHER.DAT");
    
    /* n5 = 0 (对应原游戏 0x263b7) */
    g_n5 = 0;
    sm->globals.menu_index = 0;
    
    /* 加载FDOTHER.DAT (对应原游戏 0x263d8) */
    fdother_data = fd2_dat_load_resource(path, NULL, 10);
    
    /* sub_4E98D(fdother_data, 0, 0, FDSHAP_DAT+32904, 456, -1) */
    
    if (fdother_data) {
        free(fdother_data);
    }
    
    /* 加载FDOTHER.DAT索引10 (对应原游戏 0x26405-0x26420) */
    g_FDOTHER_DAT__12 = NULL;
    g_FDOTHER_DAT__12 = fd2_dat_load_resource(path, NULL, 10);
    
    /* 初始渲染更新 sub_265EC(&v20) */
    fd2_scene_interact_render_update(sm);
    
    /* sub_1F525() */
    /* sub_4E381() - 更新屏幕 */
    
    /* 主交互循环 (对应原游戏 0x26434-0x265bf) */
    (void)fd2_scene_interact_main_loop_impl(sm);
    
    /* free FDOTHER_DAT__12 (对应原游戏 0x265cb) */
    if (g_FDOTHER_DAT__12) {
        free((void*)g_FDOTHER_DAT__12);
        g_FDOTHER_DAT__12 = 0;
    }
    
    /* 返回 n5 != 2 (对应原游戏 0x265da) */
    return (g_n5 != 2) ? 0 : 1;
}

/*
 * fd2_scene_interact_main_loop_impl: 主交互循环实现
 * 对应原游戏 do { ... } while (!v21); (0x26434-0x265bf)
 */
static int fd2_scene_interact_main_loop_impl(fd2_state_machine_t* sm) {
    int v13 = 0;
    int result = 0;
    
    do {
        /* sub_265EC(&v20) - 渲染更新 */
        fd2_scene_interact_render_update(sm);
        
        /* BIOS定时器等待 (对应原游戏 0x2643e-0x26488) */
        v13 = fd2_get_bios_timer();
        while (!fd2_check_key_pressed()) {
            /* 检查退出请求 */
            if (g_sdl_quit_requested) {
                return 0;
            }
            
            /* 处理SDL事件 */
            SDL_Event e;
            while (SDL_PollEvent(&e)) {
                if (e.type == SDL_QUIT) {
                    fd2_request_quit();
                    return 0;
                }
            }
            
            if ((unsigned int)(fd2_get_bios_timer() - v13) >= 4) {
                /* 动画帧计数器 */
                g_n3_4++;
                if (g_n3_4 == 4) g_n3_4 = 0;
                fd2_scene_interact_render_update(sm);
                v13 = fd2_get_bios_timer();
            }
            SDL_Delay(1);
        }
        
        /* 获取按键扫描码 (对应原游戏 0x2648d-0x264a8) */
        SET_HIBYTE((u32*)&g_n3, 16);
        /* int386(22, &n3, &n3) */
        int key_code = fd2_get_key_code();
        g_n3 = key_code;
        SET_HIBYTE((u32*)&g_n3, key_code);
        
        /* 按键处理 switch (对应原游戏 0x264ba-0x2657c) */
        switch (GET_HIBYTE((u32)g_n3)) {
            case 0xE0: /* 扩展键 */
            case 0x52: /* Insert */
                SET_HIBYTE((u32*)&g_n3, 28); /* 转换为Enter */
                break;
                
            case 0x22: /* Tab键 */
                g_n16_1++;
                if (g_n16_1 == 10) g_n16_1 = 0;
                fd2_music_switch(g_n16_1, 0);
                break;
                
            case 0x4D: /* 右方向键 */
                /* sub_25A96(..., 77, ...) */
                g_n5--;
                if (g_n5 < 0) g_n5 = 5;
                break;
                
            case 0x4B: /* 左方向键 */
                /* sub_25A96(..., 75, ...) */
                g_n5++;
                if (g_n5 > 5) g_n5 = 0;
                break;
                
            default:
                /* 其他按键 */
                break;
        }
        
        /* 检查Enter或Space (对应原游戏 0x2657c-0x26592) */
        if (GET_HIBYTE((u32)g_n3) != 28) {
            if ((u8)g_n3 != 32) {
                continue; /* 不是确认键，继续循环 */
            }
        }
        
        /* 确认键处理 (对应原游戏 0x2659b-0x265af) */
        if (g_n5 != 2) {
            /* sub_25A96(..., 1, 3) */
        }
        
        /* sub_2670E() - 场景特效系统 */
        result = fd2_scene_execute_selection(sm, g_n5);
        
    } while (!result);
    
    return result;
}

/*
 * fd2_scene_interact_render_update: 场景渲染更新 (原游戏 sub_265EC, 0x123字节)
 *
 * 原游戏流程 (1:1 复制):
 * 1. v10 = *sub_4E809(n17) - 获取场景类型
 * 2. memmove(n655360, FDSHAP_DAT, 153216) - 复制图形数据
 * 3. sub_4EBFF() - 叠加FDOTHER数据
 * 4. sub_15F84() - 文本渲染
 * 5. 计算光标位置
 * 6. sub_4E22A() - 复制光标图像
 * 7. sub_11EB0() - 更新屏幕
 */
/*
 * fd2_scene_interact_render_update: 场景渲染更新 (原游戏 sub_265EC, 0x56字节)
 *
 * 原游戏流程 (1:1 复制):
 * 1. v10 = *sub_4E809(n17);         // 获取场景类型
 * 2. memmove(n655360, FDSHAP_DAT, 153216);  // 复制图形数据到屏幕缓冲区
 * 3. sub_4EBFF((n655360+107020), (s16*)FDOTHER_DAT__12, 456);  // 复制状态数据
 * 4. sub_15F84(..., FDTXT_DAT__0, n5+495, ...)  // 渲染文本
 * 5. 计算光标位置 byte_52375[6*v10+n5], byte_52363[6*v10+n5]
 * 6. sub_4E22A(...)  // 复制光标图像
 * 7. sub_11EB0(n655360+32904, dst, ...)  // 更新屏幕区域
 *
 * 现代SDL2改进：
 * - 使用 render->screen 作为主渲染缓冲区
 * - 添加SDL事件处理防止窗口无响应
 * - 添加调试输出
 */
void fd2_scene_interact_render_update(fd2_state_machine_t* sm) {
    u8 v10;
    int n3;
    static int render_call_count = 0;

    if (!sm) return;

    render_call_count++;

    /* 0. 处理SDL事件，防止窗口无响应 */
    SDL_Event event;
    while (SDL_PollEvent(&event)) {
        if (event.type == SDL_QUIT) {
            sm->running = 0;
            printf("[RENDER] SDL_QUIT received, stopping\n");
            return;
        }
        if (event.type == SDL_KEYDOWN && event.key.keysym.sym == SDLK_ESCAPE) {
            sm->running = 0;
            printf("[RENDER] ESC pressed, stopping\n");
            return;
        }
    }

    /* 1. 获取场景类型 (对应原游戏 0x2660a) */
    void* scene_meta = fd2_scene_get_metadata(g_n17);
    if (scene_meta) {
        v10 = *(u8*)scene_meta;  /* 第一个字节是场景类型 */
    } else {
        v10 = 0;
    }

    if (render_call_count <= 3) {
        printf("[RENDER] Call #%d: scene=%d, scene_type=%d, g_n5=%d, g_n3_4=%d\n", 
               render_call_count, g_n17, v10, g_n5, g_n3_4);
        printf("[RENDER]   g_n655360_0=%p, g_FDSHAP_DAT=%p, g_FDOTHER_DAT__12=%p\n",
               g_n655360_0, g_FDSHAP_DAT, g_FDOTHER_DAT__12);
        printf("[RENDER]   g_FDOTHER_DAT__6=%p, g_dword_53A61=%p\n",
               g_FDOTHER_DAT__6, g_dword_53A61);
    }

    /* 2. 解压FDSHAP.DAT资源到屏幕缓冲区 */
    if (g_n655360_0 && g_FDSHAP_DAT) {
        u8* fdshap = (u8*)g_FDSHAP_DAT;
        
        /* 调试：打印前6字节 */
        if (render_call_count <= 3) {
            printf("[RENDER] FDSHAP header: %c%c%c%c%c%c (0x%02x 0x%02x 0x%02x 0x%02x 0x%02x 0x%02x)\n",
                   fdshap[0], fdshap[1], fdshap[2], fdshap[3], fdshap[4], fdshap[5],
                   fdshap[0], fdshap[1], fdshap[2], fdshap[3], fdshap[4], fdshap[5]);
        }
        
        /* 检查魔数 "LLLLLL" */
        if (fdshap[0] == 'L' && fdshap[1] == 'L' && fdshap[2] == 'L' &&
            fdshap[3] == 'L' && fdshap[4] == 'L' && fdshap[5] == 'L') {
            
            /* 读取资源数量 */
            u32 resource_count = *(u32*)(fdshap + 6);
            
            if (render_call_count <= 3) {
                printf("[RENDER] FDSHAP.DAT: %u resources\n", resource_count);
            }
            
            /* 解析资源偏移表（从偏移10开始，每个4字节） */
            if (resource_count > 1) {
                /* 资源0：调色板（768字节）*/
                u32 palette_offset = *(u32*)(fdshap + 10);
                u32 resource1_offset = *(u32*)(fdshap + 14);
                u32 palette_size = resource1_offset - palette_offset;
                
                /* 更新SDL调色板 */
                if (palette_size >= 768) {
                    fd2_render_t* render = &sm->render;
                    /* FDSHAP调色板格式：RGBRGBRGB... (每字节0-255) */
                    /* 转换为SDL需要的格式 */
                    u8 sdl_palette[768];
                    for (int i = 0; i < 256; i++) {
                        sdl_palette[i * 3 + 0] = fdshap[palette_offset + i * 3 + 0];
                        sdl_palette[i * 3 + 1] = fdshap[palette_offset + i * 3 + 1];
                        sdl_palette[i * 3 + 2] = fdshap[palette_offset + i * 3 + 2];
                    }
                    fd2_render_set_palette_8bit(render, sdl_palette);
                    
                    if (render_call_count <= 3) {
                        printf("[RENDER] Palette updated from FDSHAP resource 0\n");
                    }
                }
                
                /* 资源1：主菜单背景图像（RLE压缩）*/
                u32 resource1_size = (resource_count > 2) ? 
                    (*(u32*)(fdshap + 18) - resource1_offset) : 
                    (153216 - resource1_offset);
                
                u8* resource1_data = fdshap + resource1_offset;
                
                /* 资源1头部：2字节宽度 + 2字节高度 */
                u16 img_width = *(u16*)(resource1_data);
                u16 img_height = *(u16*)(resource1_data + 2);
                
                if (render_call_count <= 3) {
                    printf("[RENDER] Resource 1: %dx%d, size=%u bytes\n", 
                           img_width, img_height, resource1_size);
                }
                
                /* 使用RLE解压缩 */
                if (img_width > 0 && img_height > 0 && img_width <= 320 && img_height <= 200) {
                    fd2_decode_fdother_resource(
                        resource1_data, 
                        resource1_size,
                        (u8*)g_n655360_0,
                        img_width,
                        img_height
                    );
                    
                    if (render_call_count <= 3) {
                        printf("[RENDER] Decompressed FDSHAP resource 1 to n655360_0\n");
                        printf("[RENDER]   First 16 pixels after decompress: ");
                        for (int i = 0; i < 16; i++) {
                            printf("%d ", ((u8*)g_n655360_0)[i]);
                        }
                        printf("\n");
                    }
                }
            }
        } else {
            /* 不是FDSHAP格式，直接拷贝（兼容旧逻辑）*/
            memcpy(g_n655360_0, g_FDSHAP_DAT, 153216);
        }
    }

    /* 3. sub_4EBFF((n655360+107020), (s16*)FDOTHER_DAT__12, 456) */
    /* 复制状态数据到缓冲区偏移107020 */
    if (g_n655360_0 && g_FDOTHER_DAT__12) {
        fd2_copy_screen_region((u8*)g_n655360_0 + 107020, (s16*)g_FDOTHER_DAT__12, 456);
    }

    /* 4. sub_15F84(..., FDTXT_DAT__0, n5+495, ...) - 渲染文本 */
    /* 根据原游戏调用: sub_15F84(a1, FDTXT_DAT__0, n5+495, n658255, argC, 205, 76, 74, 19, 1) */
    if (g_FDTXT_DAT__0 && g_n655360_0) {
        /* 文本渲染起始偏移 - 使用相对于屏幕缓冲区的偏移 */
        int text_row = 5;  /* 从第5行开始渲染 */
        int text_col = 20; /* 从第20列开始 */
        int row_width = 320;       /* argC - 行宽 */

        /* 简化实现：渲染菜单文本 */
        if (g_FDOTHER_DAT__6) {
            /* 使用FDOTHER_DAT__6作为字体数据 */
            /* 渲染6个菜单项 */
            for (int i = 0; i < 6; i++) {
                int char_idx = i;  /* 假设菜单项索引 */
                if (char_idx >= 0 && char_idx <= 9) {
                    /* 每个菜单项占一行 */
                    int screen_pos = (text_row + i) * 320 + text_col;

                    /* 安全检查：确保偏移在缓冲区范围内 */
                    if (screen_pos >= 0 && screen_pos < FD2_SCREEN_SIZE - 256) {
                        fd2_render_char(
                            g_FDOTHER_DAT__6,     /* 字体数据 */
                            char_idx,              /* 字符索引 */
                            g_n655360_0,           /* 屏幕缓冲区 */
                            screen_pos,            /* 偏移 */
                            row_width,             /* 行宽 */
                            76,                    /* color1 - 前景色 */
                            74,                    /* color2 - 背景色 */
                            1                      /* do_clear */
                        );
                    }
                }
            }
        }
    }

    /* 5. 计算光标位置 */
    n3 = g_n3_4;
    if (g_n3_4 == 3) n3 = 1;

    /* 光标X/Y坐标从表中读取 */
    u8 cursor_y = 0, cursor_x = 0;
    if (v10 < 30 && g_n5 < 6) {
        cursor_y = g_byte_52375[6 * v10 + g_n5];
        cursor_x = g_byte_52363[6 * v10 + g_n5];
    }

    if (render_call_count <= 3) {
        printf("[RENDER]   cursor_y=%d, cursor_x=%d, n3=%d\n", cursor_y, cursor_x, n3);
    }

    /* dst = n655360 + 32904 + cursor_y * 456 + cursor_x */
    char* dst = (char*)((u8*)g_n655360_0 + 32904 + (int)cursor_y * 456 + (int)cursor_x);

    /* 6. sub_4E22A(...) - 复制光标图像 */
    /* 从FDSHAP_DAT中的光标数据复制到屏幕缓冲区 */
    if (g_dword_53A61 && g_n655360_0) {
        /* 获取光标图像数据 (原游戏: dword_53A61 + *(DWORD*)(dword_53A61 + 4*n3)) */
        u8* cursor_src = *(u8**)((u8*)g_dword_53A61 + 4 * n3);
        fd2_copy_cursor_image((u8*)dst, cursor_src, 456);
    }

    /* 7. sub_11EB0(n655360+32904, dst, ..., 456, 320, ..., 456, 312, 192) */
    /* 更新屏幕区域到可见范围 */
    if (g_n655360_0) {
        fd2_screen_region_update(
            (u8*)g_n655360_0 + 32904,  /* dst */
            320,                         /* dst_stride */
            dst,                         /* src */
            456,                         /* src_stride */
            312,                         /* copy_size */
            192                          /* num_lines */
        );
    }

    /* 8. 渲染到SDL窗口 - 现代SDL2方式 */
    fd2_render_t* render = &sm->render;
    if (render && render->initialized && g_n655360_0) {
        /* 将游戏缓冲区数据拷贝到SDL渲染缓冲区 */
        /* 只拷贝可见区域 320x200 */
        for (int y = 0; y < 200; y++) {
            memcpy(render->screen + y * 320, (u8*)g_n655360_0 + y * 320, 320);
        }

        /* 使用简单测试色填充部分区域，验证渲染是否工作 */
        /* 临时调试：填充一个白色矩形区域 */
        for (int y = 10; y < 30; y++) {
            for (int x = 10; x < 50; x++) {
                render->screen[y * 320 + x] = 255;  /* 测试用白色像素 */
            }
        }

        if (render_call_count <= 3) {
            /* 打印渲染缓冲区前16个像素值 */
            printf("[RENDER]   First 16 pixels of render->screen: ");
            for (int i = 0; i < 16; i++) {
                printf("%d ", render->screen[i]);
            }
            printf("\n");
            printf("[RENDER]   Palette[0]=R%dG%dB%d, Palette[255]=R%dG%dB%d\n",
                   render->palette[0], render->palette[1], render->palette[2],
                   render->palette[255*3], render->palette[255*3+1], render->palette[255*3+2]);
        }

        fd2_render_present(render);
    }
}

/*
 * fd2_scene_execute_selection: 场景选择执行 (原游戏 sub_2670E, 0x288字节)
 *
 * 原游戏流程 (1:1 复制):
 * 1. 停止当前音乐 sub_25977(..., -1, 0)
 * 2. 如果n5==2: 执行特殊处理 (sub_1956B, sub_15F84, sub_19953等)
 * 3. 分配64000字节特效缓冲区
 * 4. memmove特效缓冲区
 * 5. 10步特效动画循环
 * 6. 根据n5执行不同特效 (sub_29300, sub_279BC, sub_29DAA等)
 * 7. 恢复音乐 sub_25977(..., 10, 0)
 * 8. 释放特效缓冲区
 */
int fd2_scene_execute_selection(fd2_state_machine_t* sm, int menuIndex) {
    void* n3;
    int n10;
    
    (void)sm;
    
    /* 1. 停止当前音乐 (对应原游戏 0x26737) */
    fd2_music_switch(-1, 0);
    
    /* 2. 如果n5==2: 执行特殊处理 (对应原游戏 0x26746-0x26810) */
    if (menuIndex == 2) {
        /* sub_1956B(75) */
        /* sub_15F84(..., FDTXT_DAT__0, 513, ..., 76, 74, 19, 1) */
        g_FDFIELD_DAT__0 = (void*)1;
        /* sub_16559(0) */
        /* sub_19953() */
        /* sub_197E5() */
        g_FDFIELD_DAT__0 = NULL;
        /* sub_26996() */
        
        /* 检查退出条件 */
        if (0 == -1 || g_n4_1) {
            return 0;
        }
        
        /* 检查场景范围 */
        if ((g_n17 < 27 && g_n16_1 > 16) || (g_n17 > 26 && g_n16_1 > 20)) {
            g_n8_1 = g_n8_3;
            /* sub_2AF28() - 返回0表示需要继续循环 */
            g_n8_1 = NULL;
            /* 假设sub_2AF28()返回0，继续循环 */
            return 0;
        }
    }
    
    /* 3. 分配特效缓冲区 (对应原游戏 0x26810-0x26822) */
    g_n8_1 = g_n8_3;
    n3 = malloc(64000);
    if (!n3) return 0;
    
    /* 4. memmove特效缓冲区 (对应原游戏 0x2682f) */
    memcpy(n3, (void*)g_n655360_0, 64000);
    
    /* 5. 10步特效动画循环 (对应原游戏 0x26837-0x268eb) */
    for (n10 = 1; n10 <= 10; ++n10) {
        /* sub_2921A(...) */
        
        /* memmove(655360, n655360, 64000) */
        /* sub_11D40(4*n10, ..., 0, 255, 4*n10) */
    }
    
    /* sub_11D40(..., 0, 255, 64) */
    /* memset(n10, 655360, 0, 64000) */
    
    /* 6. 根据n5执行不同特效 (对应原游戏 0x2690e-0x26974) */
    if (menuIndex == 0) {
        fd2_music_switch(13, 0);
        /* sub_29300(n3) */
    }
    else if (menuIndex == 4) {
        fd2_music_switch(11, 0);
        /* sub_29DAA(n3) */
    }
    else if (menuIndex == 2) {
        free(n3);
        g_n8_1 = NULL;
        return 0;
    }
    else if (menuIndex == 3) {
        fd2_music_switch(15, 0);
        /* sub_279BC((int)n3) */
    }
    else {
        fd2_music_switch(14, 0);
        /* sub_279BC((int)n3) */
    }
    
    /* 7. 恢复音乐 (对应原游戏 0x26974) */
    fd2_music_switch(10, 0);
    
    /* 8. 释放特效缓冲区 */
    free(n3);
    g_n8_1 = NULL;
    
    return 0;
}

/*
 * fd2_scene_handle_key: 按键处理 (原游戏 sub_117E7, 0x2C1字节)
 */
int fd2_scene_handle_key(fd2_state_machine_t* sm) {
    int key_code = sm->globals.key_code;
    fd2_scene_handle_key_impl(sm, key_code);
    return 0;
}

static void fd2_scene_handle_key_impl(fd2_state_machine_t* sm, int key_code) {
    int n44;
    
    (void)sm;
    
    /* 获取按键扫描码 sub_11AA8() */
    n44 = key_code;
    
    /* 处理特定按键 (对应原游戏 0x11805-0x11883) */
    if (n44 == 1 || n44 == 44 || n44 == 76) {
        /* 遍历场景对象列表 */
        /* if ((*(u8*)(v10+5) & 0x85) == 0 && *(u8*)(v10+6) == 2 && !v7) */
        /* sub_12D7B(v8) */
        /* dword_53AE9 = v8+1 */
        return;
    }
    
    /* 处理Enter/Space (对应原游戏 0x1188c-0x119b0) */
    if (n44 != 57 && n44 != 28) {
        if (n44 != 34) {
            switch (n44) {
                case ';': /* 分号键 */
                case 'I':
                    /* sub_2000A() */
                    return;
                    
                case '<': /* 小于号 */
                case 'G':
                    /* n3 = sub_12C0D() */
                    /* if (n3 != -1) sub_17AED(n3, a3) */
                    return;
                    
                case 'H': /* 上方向键 */
                    /* sub_25A96(..., 72, ...) */
                    /* sub_11B48() */
                    return;
                    
                case 'P': /* 下方向键 */
                    /* sub_25A96(..., 80, ...) */
                    /* sub_11B9B() */
                    return;
                    
                case 'K': /* 左方向键 */
                    /* sub_25A96(..., 75, ...) */
                    /* sub_11C59() */
                    return;
                    
                case 'M': /* 右方向键 */
                    /* sub_25A96(..., 77, ...) */
                    /* sub_11BFA() */
                    return;
            }
        }
        return;
    }
    
    /* Enter/Space处理 */
    if (g_byte_51A42) --g_byte_51A42;
    
    /* n6 = sub_12C0D() */
    /* if (n6 != -1) { ... } */
    
    /* sub_11CAC(0) */
    /* sub_1E292(a6, n6) */
    /* funcs_1197B[n17]() */
    /* sub_13565() */
    /* if (n255 != 255) funcs_1199C[n255](a6) */
    /* n255 = 255 */
}

/*
 * fd2_scene_handle_confirm: 确认键处理
 */
int fd2_scene_handle_confirm(fd2_state_machine_t* sm) {
    int menu_index = sm->globals.menu_index;
    return fd2_scene_execute_selection(sm, menu_index);
}

/*
 * fd2_scene_check_completion: 场景完成条件检查
 */
int fd2_scene_check_completion(fd2_state_machine_t* sm) {
    int scene_id = g_n17;
    
    if (scene_id < 0 || scene_id >= 30) return 0;
    
    if (funcs_1197B[scene_id]) {
        return funcs_1197B[scene_id](sm);
    }
    
    return 0;
}

/*
 * fd2_scene_process_effect: 特效处理
 */
int fd2_scene_process_effect(fd2_state_machine_t* sm, int effectType) {
    (void)sm;
    (void)effectType;
    return 0;
}

/*
 * fd2_scene_release_old_resources: 释放旧场景资源
 */
void fd2_scene_release_old_resources(fd2_state_machine_t* sm) {
    if (g_n8_1) { free(g_n8_1); g_n8_1 = NULL; }
    if (g_FDFIELD_DAT__1) { free(g_FDFIELD_DAT__1); g_FDFIELD_DAT__1 = NULL; }
    if (g_FDSHAP_DAT) { free(g_FDSHAP_DAT); g_FDSHAP_DAT = NULL; }
    if (g_FDFIELD_DAT__0) { free(g_FDFIELD_DAT__0); g_FDFIELD_DAT__0 = NULL; }
    (void)sm;
}

/*
 * fd2_scene_load_icons: 加载场景图标
 */
void fd2_scene_load_icons(fd2_state_machine_t* sm) {
    (void)sm;
}

/*
 * fd2_scene_load_graphics: 加载场景图形
 */
void fd2_scene_load_graphics(fd2_state_machine_t* sm) {
    (void)sm;
}

/* 辅助函数 */
static int fd2_get_bios_timer(void) {
    return SDL_GetTicks() / 1000;
}

static int fd2_check_key_pressed(void) {
    /* 处理事件队列，检查SDL_QUIT */
    SDL_Event e;
    while (SDL_PollEvent(&e)) {
        if (e.type == SDL_QUIT) {
            printf("[INPUT] SDL_QUIT detected in fd2_check_key_pressed\n");
            fd2_request_quit();
            return 1; /* 返回1让外层循环检查退出标志 */
        }
    }
    
    SDL_PumpEvents();
    const Uint8* state = SDL_GetKeyboardState(NULL);
    return state[SDL_SCANCODE_RETURN] || state[SDL_SCANCODE_SPACE] ||
           state[SDL_SCANCODE_UP] || state[SDL_SCANCODE_DOWN] ||
           state[SDL_SCANCODE_LEFT] || state[SDL_SCANCODE_RIGHT] ||
           state[SDL_SCANCODE_ESCAPE];
}

static u8 GET_HIBYTE(u32 val) {
    return (u8)((val >> 24) & 0xFF);
}

static void SET_HIBYTE(u32* val, u8 hibyte) {
    *val = (*val & 0x00FFFFFF) | ((u32)hibyte << 24);
}

/* 交互处理核心循环 (sub_17AED主逻辑) */
static int interact_core_loop(fd2_state_machine_t* sm, int a3) {
    g_n2_0 = 2;
    int v11 = 0;
    (void)a3;
    (void)v11;

    /* 1. 设置调色板 (对应原游戏 sub_11D40) */
    if (g_FDOTHER_DAT__5) {
        fd2_set_palette_vga(
            (const u8*)g_FDOTHER_DAT__5,
            0, 255, 0, &sm->render
        );
    }

    /* 2. 填充屏幕黑色 */
    fd2_render_fill_screen(&sm->render, 0);

    /* 3. 文本/UI渲染 (对应原游戏 sub_15F84) */
    if (g_FDOTHER_DAT__6) {
        fd2_render_text_ui(
            (const u8*)g_n8_3,
            (const u8*)g_FDOTHER_DAT__6,
            g_n17,
            658255,  /* 屏幕偏移 */
            320,     /* 行跨度 */
            205,     /* 前景色 */
            76,      /* 背景色 */
            74,      /* 标志 */
            19,      /* 刷新标志 */
            660,     /* arg1C */
            &sm->render
        );
    }

    /* 4. 渲染管线 (对应原游戏 sub_19953) */
    if (g_FDOTHER_DAT__13) {
        fd2_scene_render_pipeline(sm);
    }

    /* 5. 刷新屏幕 */
    fd2_screen_refresh(sm);

    return v11;
}
