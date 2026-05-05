#include "fd2_scene_interact.h"
#include "fd2_globals.h"
#include "fd2_data_loader.h"
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
    
    g_n8_1 = NULL;
    g_dword_53BDF = 0;
    
    /* 打开fdicon.b24 */
    fp = fopen("fdicon.b24", "rb");
    if (!fp) {
        printf("File not found fdicon.b24!!!\n");
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
void fd2_scene_interact_render_update(fd2_state_machine_t* sm) {
    u8 v10;
    int n3;
    char* dst;
    int v7;
    
    if (!sm) return;
    
    /* 1. 获取场景类型 */
    v10 = 0; /* TODO: *sub_4E809(n17) */
    
    /* 2. memmove(n655360, FDSHAP_DAT, 153216) */
    if (g_n655360_0 && g_FDSHAP_DAT) {
        memcpy((void*)g_n655360_0, (void*)g_FDSHAP_DAT, 153216);
    }
    
    /* 3. sub_4EBFF((u8*)(n655360+107020), (s16*)FDOTHER_DAT__12, 456) */
    (void)v10;
    (void)n3;
    (void)dst;
    (void)v7;
    
    /* 4. sub_15F84() - 文本渲染 */
    /* sub_15F84(a1, n5+495, ..., FDTXT_DAT__0, n5+495, n655360+109764, 456, 205, 76, 74, 19, 0) */
    
    /* 5. 计算光标位置 */
    (void)v10;
    (void)n3;
    (void)dst;
    (void)v7;
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
