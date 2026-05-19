/*
 * FD2 三层状态机核心实现
 * 基于原游戏 (FD2.EXE) 的IDA反汇编代码1:1实现
 * 
 * 原游戏核心函数:
 * - main() 0x25BF4 - 游戏主循环
 * - sub_25EBB() 0x25EBB - 状态管理
 * - sub_117E7() 0x117E7 - 输入处理
 * - sub_26152() 0x26152 - 场景交互循环
 */

#include "fd2_state_machine.h"
#include "fd2_globals.h"
#include "fd2_data_loader.h"
#include "fd2_scene_interact.h"
#include "fd2_input_scan.h"
#include "fd2_opening_animation.h"
#include "fd2_save_load.h"
#include "fd2_decoder.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <string.h>

/* ========================================================================
 * 存档选择UI辅助函数 (从sub_29AB2/sub_29BCB提取)
 * ======================================================================== */

/* sub_4EBFF: 将像素数据块传输到屏幕缓冲区 */
static void fd2_blit_pixels(u8* src, int src_pitch, u8* dst, int dst_pitch, int w, int h) {
    for (int y = 0; y < h; y++) {
        memcpy(dst + y * dst_pitch, src + y * src_pitch, w);
    }
}

/* sub_4ED7A: 字符渲染 */
static void fd2_render_char(u8* font, int char_idx, u8* screen, int pitch, u8 color) {
    if (!font || char_idx < 0 || char_idx > 9) return;
    
    u8* char_data = font + 32 * char_idx;
    for (int row = 0; row < 16; row++) {
        u8 byte1 = char_data[row * 2];
        u8 byte2 = char_data[row * 2 + 1];
        
        for (int bit = 0; bit < 8; bit++) {
            if (byte1 & (0x80 >> bit)) {
                screen[row * pitch + bit] = color;
            }
            if (byte2 & (0x80 >> bit)) {
                screen[row * pitch + 8 + bit] = color;
            }
        }
    }
}

/* 渲染字符串到屏幕缓冲区 */
static void fd2_render_string(u8* font, const char* str, u8* screen, int pitch, int x, int y, u8 color) {
    u8* ptr = screen + y * pitch + x;
    while (*str) {
        if (*str >= '0' && *str <= '9') {
            fd2_render_char(font, *str - '0', ptr, pitch, color);
        }
        ptr += 16;
        str++;
    }
}

/* 存档槽位UI资源结构 */
typedef struct {
    u16 width;
    u16 height;
    u8 pixels[480];  /* 24x20 */
} fd2_ui_resource_t;

/* 渲染存档槽位UI: 对应原游戏 sub_29AB2 */
static void fd2_render_slot_ui(u8* screen, int pitch, int slot_idx, int is_selected, 
                               u8* slot_data, fd2_ui_resource_t** ui_res, u8* font_data) {
    int y_pos = 40 + slot_idx * 38;
    int res_idx = is_selected ? 0 : 1;
    
    if (ui_res[res_idx]) {
        fd2_ui_resource_t* res = ui_res[res_idx];
        int w = res->width;
        int h = res->height;
        int draw_x = 30;
        int draw_y = y_pos;
        u8* dest = screen + draw_y * pitch + draw_x;
        
        for (int row = 0; row < h && (draw_y + row) < 200; row++) {
            memcpy(dest + row * pitch, res->pixels, w);
        }
    }
    
    if (slot_data && slot_data[2560] != 255 && ui_res[2 + slot_idx]) {
        fd2_ui_resource_t* thumb = ui_res[2 + slot_idx];
        int thumb_x = 40;
        int thumb_y = y_pos + 5;
        u8* dest = screen + thumb_y * pitch + thumb_x;
        
        for (int row = 0; row < thumb->height && (thumb_y + row) < 200; row++) {
            memcpy(dest + row * pitch, thumb->pixels, thumb->width);
        }
    }
    
    char slot_num[2];
    slot_num[0] = '1' + slot_idx;
    slot_num[1] = '\0';
    fd2_render_string(font_data, slot_num, screen + y_pos * pitch + 270, pitch, 0, 20, 15);
    
    if (slot_data && slot_data[2560] != 255) {
        int scene_id = slot_data[0];
        char scene_str[8];
        snprintf(scene_str, sizeof(scene_str), "%d", scene_id);
        fd2_render_string(font_data, scene_str, screen + (y_pos + 20) * pitch + 40, pitch, 0, 20, 15);
    }
}
#include <SDL2/SDL.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdio.h>

/* DOS BIOS定时器模拟 (原游戏 MEMORY[0x46C]) */
static clock_t g_clock_start = 0;

/* 默认函数声明 */
static void scene_default_init(struct fd2_state_machine* sm);
static void scene_default_exit(struct fd2_state_machine* sm);
static int scene_default_check(struct fd2_state_machine* sm);
static void event_default(struct fd2_state_machine* sm);

/* 前置声明 - 主循环使用的辅助函数 */
static int fd2_get_game_state(fd2_state_machine_t* sm);
static void fd2_scene_setup(fd2_state_machine_t* sm);
static void fd2_update_screen(fd2_state_machine_t* sm);

/*
 * 模拟原游戏 sub_10620() - 垂直同步等待
 * 原游戏使用 int386(16) 检查显示适配器状态
 */
int fd2_wait_vsync(void) {
    SDL_Delay(16);
    return 1;
}

/*
 * 模拟原游戏 MEMORY[0x46C] - BIOS定时器滴答
 * 原游戏使用DOS BIOS定时器 (18.2 ticks/sec)
 */
static u16 get_bios_tick(void) {
    if (g_clock_start == 0) {
        g_clock_start = clock();
    }
    clock_t elapsed = clock() - g_clock_start;
    return (u16)((elapsed * 182 / 10) / CLOCKS_PER_SEC);
}

/*
 * 动画帧更新 (对应原游戏 n3_4计数器逻辑)
 * 
 * 原游戏代码:
 * if ((MEMORY[0x46C] - v13) >= 4) {
 *     if (++n3_4 == 4) n3_4 = 0;
 * }
 */
int fd2_check_anim_frame(struct fd2_state_machine* sm) {
    u16 current_tick = get_bios_tick();
    u16 diff = current_tick - sm->globals.bios_tick_base;
    
    if (diff >= FD2_ANIM_FRAME_DELAY) {
        sm->globals.bios_tick_base = current_tick;
        sm->globals.anim_frame++;
        if (sm->globals.anim_frame >= FD2_ANIM_FRAME_COUNT) {
            sm->globals.anim_frame = 0;
        }
        return 1;
    }
    return 0;
}

/*
 * fd2_get_game_state: 获取游戏状态 (对应原游戏 sub_25977(18, 0))
 * 返回0表示正常游戏循环，-1表示退出
 */
static int fd2_get_game_state(fd2_state_machine_t* sm) {
    (void)sm;
    return 0;
}

/*
 * fd2_scene_setup: 场景初始化设置 (对应原游戏 sub_22E5C)
 */
static void fd2_scene_setup(fd2_state_machine_t* sm) {
    (void)sm;
}

/*
 * fd2_update_screen: 更新屏幕 (对应原游戏 sub_4E381)
 */
static void fd2_update_screen(fd2_state_machine_t* sm) {
    (void)sm;
}

void fd2_update_anim_frame(struct fd2_state_machine* sm) {
    sm->globals.anim_frame++;
    if (sm->globals.anim_frame >= FD2_ANIM_FRAME_COUNT) {
        sm->globals.anim_frame = 0;
    }
}

/*
 * 默认场景处理函数 (对应原游戏 sub_21206)
 * 仅初始化栈帧，不执行任何操作
 */
static void scene_default_init(struct fd2_state_machine* sm) {
    (void)sm;
}

static void scene_default_exit(struct fd2_state_machine* sm) {
    (void)sm;
}

static int scene_default_check(struct fd2_state_machine* sm) {
    (void)sm;
    return 0;
}

static void event_default(struct fd2_state_machine* sm) {
    (void)sm;
}

/*
 * 初始化状态机
 * 对应原游戏 main() 中的初始化部分
 */
int fd2_state_machine_init(fd2_state_machine_t* sm) {
    if (!sm) return -1;
    
    memset(sm, 0, sizeof(*sm));
    
    /* 初始化全局变量 (对应原游戏数据段) */
    sm->globals.scene_id = 0;
    sm->globals.subscene_id = 0;
    sm->globals.scene_state = FD2_SCENE_STATE_IDLE;
    sm->globals.menu_index = 0;
    sm->globals.anim_frame = 0;
    sm->globals.progress = 0;
    sm->globals.scene_active_flag = FD2_SCENE_INACTIVE;
    sm->globals.exit_flag = 0;
    sm->globals.interact_result = 0;
    sm->globals.bios_tick_base = get_bios_tick();
    
    /* 初始化函数表为默认值 */
    for (int i = 0; i < FD2_SCENE_COUNT; i++) {
        sm->scenes[i].init_fn = scene_default_init;
        sm->scenes[i].exit_fn = scene_default_exit;
        sm->scenes[i].check_fn = scene_default_check;
        sm->scenes[i].music_id = 0;
        sm->scenes[i].is_special = 0;
        sm->scenes[i].name = "unknown";
        sm->scene_checks[i] = scene_default_check;
    }
    
    for (int i = 0; i < 30; i++) {
        sm->special_events[i] = event_default;
    }
    
    sm->running = 1;
    sm->initialized = 1;
    sm->globals_ptr = &sm->globals;
    
    /* 初始化随机数 (对应原游戏 rand() + sub_4EBE3()) */
    srand((unsigned int)time(NULL));
    int seed_count = rand() % 256;
    for (int i = 0; i < seed_count; i++) {
        rand();
    }
    
    /* 初始化渲染系统 (对应原游戏 VGA模式13h初始化) */
    if (fd2_render_init(&sm->render, FD2_RENDER_SCALE) != 0) {
        fprintf(stderr, "Failed to initialize render system\n");
        return -1;
    }
    
    return 0;
}

void fd2_state_machine_shutdown(fd2_state_machine_t* sm) {
    if (!sm) return;
    sm->running = 0;
    sm->initialized = 0;
    
    /* 清理渲染系统 */
    fd2_render_shutdown(&sm->render);
}

/*
 * 注册场景
 */
int fd2_register_scene(fd2_state_machine_t* sm,
                       int scene_id,
                       fd2_scene_init_fn init_fn,
                       fd2_scene_exit_fn exit_fn,
                       fd2_scene_check_fn check_fn,
                       u8 music_id,
                       u8 is_special,
                       const char* name) {
    if (!sm || scene_id < 0 || scene_id >= FD2_SCENE_COUNT) return -1;
    
    sm->scenes[scene_id].init_fn = init_fn ? init_fn : scene_default_init;
    sm->scenes[scene_id].exit_fn = exit_fn ? exit_fn : scene_default_exit;
    sm->scenes[scene_id].check_fn = check_fn ? check_fn : scene_default_check;
    sm->scenes[scene_id].music_id = music_id;
    sm->scenes[scene_id].is_special = is_special;
    sm->scenes[scene_id].name = name ? name : "unknown";
    
    return 0;
}

int fd2_register_special_event(fd2_state_machine_t* sm,
                                int event_id,
                                fd2_special_event_fn event_fn) {
    if (!sm || event_id < 0 || event_id >= 30) return -1;
    sm->special_events[event_id] = event_fn ? event_fn : event_default;
    return 0;
}

/*
 * 场景状态控制
 */
void fd2_set_scene_state(fd2_state_machine_t* sm, int state) {
    if (!sm) return;
    g_n2_0 = state;
    sm->globals.scene_state = state;
}

void fd2_switch_scene(fd2_state_machine_t* sm, int scene_id) {
    if (!sm || scene_id < 0 || scene_id >= FD2_SCENE_COUNT) return;
    g_n17 = scene_id;
    sm->globals.scene_id = scene_id;
    sm->globals.subscene_id = 0;
    g_n16_1 = 0;
}

void fd2_switch_subscene(fd2_state_machine_t* sm, int subscene_id) {
    if (!sm) return;
    if (subscene_id < 0 || subscene_id >= FD2_SUBSCENE_COUNT) {
        subscene_id = 0;
    }
    g_n16_1 = subscene_id;
    sm->globals.subscene_id = subscene_id;
}

/*
 * 菜单系统
 * 对应原游戏 n5变量管理和 sub_25A96() 音效播放
 */
void fd2_menu_navigate(fd2_state_machine_t* sm, int direction) {
    if (!sm) return;
    
    if (direction > 0) {
        sm->globals.menu_index--;
        if (sm->globals.menu_index < FD2_MENU_ITEM_MIN) {
            sm->globals.menu_index = FD2_MENU_ITEM_MAX;
        }
    } else {
        sm->globals.menu_index++;
        if (sm->globals.menu_index > FD2_MENU_ITEM_MAX) {
            sm->globals.menu_index = FD2_MENU_ITEM_MIN;
        }
    }
    g_n5 = sm->globals.menu_index;
}

void fd2_menu_confirm(fd2_state_machine_t* sm) {
    if (!sm) return;
    
    if (sm->globals.menu_index != FD2_MENU_ITEM_BACK) {
        /* TODO: 播放确认音效 */
    }
    
    if (sm->interaction.process_selection) {
        sm->interaction.process_selection(sm);
    }
}

int fd2_menu_get_index(fd2_state_machine_t* sm) {
    if (!sm) return 0;
    return sm->globals.menu_index;
}

/*
 * 第一层状态机: 输入处理 (对应原游戏 sub_117E7)
 * 
 * 原游戏核心逻辑:
 * 1. 获取按键扫描码 (sub_11AA8)
 * 2. 处理特殊按键 (ESC等)
 * 3. 处理方向键
 * 4. 处理确认键 (回车/空格)
 * 5. 调用funcs_1197B[n17]()检查场景完成
 * 6. 检查n2_0标志
 */
int fd2_get_key_code(void) {
    SDL_Event event;
    
    while (SDL_PollEvent(&event)) {
        if (event.type == SDL_QUIT) {
            /* 设置全局退出标志，让主循环能检测到 */
            extern void fd2_request_quit(void);
            fd2_request_quit();
            return FD2_KEY_ESC;
        }
        if (event.type == SDL_KEYDOWN && !event.key.repeat) {
            return fd2_sdl_to_scan_code(event.key.keysym.scancode);
        }
    }
    return 0;
}

int fd2_input_process(fd2_state_machine_t* sm) {
    if (!sm || !sm->initialized) return 0;
    
    int key_code = fd2_get_key_code();
    if (key_code == 0) return 0;
    
    g_n3 = key_code;
    sm->globals.key_code = key_code;
    
    /* 特殊按键处理 (原游戏: if (n44 == 1 || n44 == 44 || n44 == 76)) */
    if (key_code == FD2_KEY_ESC) {
        if (sm->input.process_special_key) {
            sm->input.process_special_key(sm, key_code);
        }
        return 0;
    }
    
    /* 方向键处理 (原游戏 switch (n44)) */
    switch (key_code) {
        case FD2_KEY_TAB:
            if (sm->input.process_special_key) {
                sm->input.process_special_key(sm, key_code);
            }
            break;
            
        case FD2_KEY_LEFT:
        case FD2_KEY_RIGHT:
        case FD2_KEY_UP:
        case FD2_KEY_DOWN:
            if (sm->input.process_direction_key) {
                sm->input.process_direction_key(sm, key_code);
            }
            break;
            
        case FD2_KEY_ENTER:
        case FD2_KEY_SPACE:
            if (sm->input.process_confirm_key) {
                sm->input.process_confirm_key(sm);
            }
            break;
    }
    
    return 1;
}

/*
 * 第二层状态机: 场景生命周期管理
 * 对应原游戏 funcs_25E23[n17]() 和 funcs_25E3A[n17]()
 */
void fd2_scene_init(fd2_state_machine_t* sm, int scene_id) {
    if (!sm || scene_id < 0 || scene_id >= FD2_SCENE_COUNT) return;
    
    g_byte_51AAC = FD2_SCENE_INACTIVE;
    sm->globals.scene_active_flag = FD2_SCENE_INACTIVE;
    
    if (sm->scenes[scene_id].init_fn) {
        sm->scenes[scene_id].init_fn(sm);
    }
    
    g_byte_51AAC = FD2_SCENE_ACTIVE;
    sm->globals.scene_active_flag = FD2_SCENE_ACTIVE;
    
    g_n2_0 = FD2_SCENE_STATE_IDLE;
    sm->globals.scene_state = FD2_SCENE_STATE_IDLE;
}

void fd2_scene_exit(fd2_state_machine_t* sm, int scene_id) {
    if (!sm || scene_id < 0 || scene_id >= FD2_SCENE_COUNT) return;
    
    if (sm->scenes[scene_id].exit_fn) {
        sm->scenes[scene_id].exit_fn(sm);
    }
    
    g_n2_0 = FD2_SCENE_STATE_IDLE;
    sm->globals.scene_state = FD2_SCENE_STATE_IDLE;
}

int fd2_scene_check_complete(fd2_state_machine_t* sm, int scene_id) {
    if (!sm || scene_id < 0 || scene_id >= FD2_SCENE_COUNT) return 0;
    
    if (sm->scenes[scene_id].check_fn) {
        return sm->scenes[scene_id].check_fn(sm);
    }
    return 0;
}

/*
 * 主循环 (对应原游戏 main + sub_25EBB)
 * 
 * 原游戏核心逻辑:
 * 
 * main():
 *   while (1) {
 *       v14 = sub_25977(18, 0);  // 切换音乐
 *       v15 = sub_25EBB(v14);    // 状态管理
 *       v17 = v15;
 *       
 *       if (v15 == 0) {  // 进入游戏循环
 *           do {
 *               i = sub_117E7(v16, n80, i);  // 输入处理
 *               
 *               if (n2_0 == 1) {  // 场景初始化
 *                   byte_51AAC = 0;
 *                   sub_22E5C();
 *                   byte_51AAC = 1;
 *                   n2_0 = 0;
 *                   i = 1;
 *               }
 *               else if (n2_0 == 2) {  // 场景交互
 *                   byte_51AAC = 0;
 *                   sub_25977(-1, 1);  // 停止音乐
 *                   funcs_25E23[n17]();  // 场景初始化
 *                   i = sub_26152();    // 场景交互循环
 *                   
 *                   if (i) {
 *                       v17 = 1;  // 准备退出
 *                   } else {
 *                       funcs_25E3A[n17]();  // 场景结束
 *                       sub_25977(byte_51E63[n17], 0);  // 切换音乐
 *                   }
 *                   byte_51AAC = 1;
 *                   n2_0 = 0;
 *                   sub_4E381();  // 刷新屏幕
 *               }
 *           } while (!i);
 *           
 *           if (i == -1) v17 = 1;
 *       }
 *       
 *       if (v17) {  // 退出游戏
 *           sub_37ED8();
 *           n3 = 3;
 *           int386(16, &n3, &n3);
 *           JUMPOUT(0x16F04);
 *       }
 *   }
 * 
 * sub_25EBB():
 *   v7 = sub_3702F(...);
 *   sub_1F894(v7, ...);  // 开场动画+菜单
 *   
 *   if (!v8) {  // 返回0 = 选择Start
 *       v9 = sub_1F882();  // 淡入效果
 *       n17 = 0;
 *       FDOTHER_DAT = sub_111BA(v9, ..., "FDOTHER.DAT", 0);
 *       n16_1 = 0;
 *       byte_51AAC = 0;
 *       funcs_25E3A[n17]();  // 场景0初始化 (sub_3231B)
 *       sub_25977(byte_51E63[n17], ...);  // 播放音乐
 *       byte_51AAC = 1;
 *       sub_4E381();  // 刷新屏幕
 *       return 0;  // 返回0进入main的游戏循环
 *   }
 *   
 *   if (v8 != 1) {  // 其他选项 = 退出
 *       sub_25977(v8, ..., -1, 0);
 *       sub_10010();
 *       sub_25977(byte_51E63[n17], ...);
 *       return 0;
 *   }
 *   
 *   // 返回1 = 选择Load
 *   FDOTHER_DAT__11 = sub_111BA(..., 13);
 *   v8 = sub_1F882();
 *   FDOTHER_DAT = sub_111BA(v8, ..., "FDOTHER.DAT", 0);
 *   memset(655360, 0, 64000);
 *   sub_11D40(0, 255, 0);
 *   
 *   v10 = malloc(22987);
 *   fopen("FD2.SAV");
 *   fread(v10, 1, 22987);
 *   sub_4DF28(v10, 22987);  // 解密
 *   fclose();
 *   
 *   // 解析存档场景数据
 *   n4_1 = 0;
 *   do {
 *       v14 = sub_29BCB(v11, 0);
 *       if (v14 != -1) {
 *           v16 = &v11[2600*n4_1 + 12587];
 *           memmove(n8_3, v16, 2560);
 *           n17 = *v10;
 *           n16_1 = v10[1];
 *           n999_0 = v10[2..5];
 *           ...
 *           if (n17 == 255) v15 = 0;
 *       }
 *       sub_26996();
 *   } while (!v15);
 *   
 *   free(v11);
 *   free(FDOTHER_DAT__11);
 *   
 *   if (v15 == 1) {
 *       byte_51AAC = 0;
 *       v15 = sub_26152();  // 场景交互
 *       if (!v15) {
 *           funcs_25E3A[n17]();
 *           sub_25977(byte_51E63[n17], 0);
 *       }
 *       byte_51AAC = 1;
 *   }
 *   sub_4E381();
 *   return v15;
 */
int fd2_state_machine_run(fd2_state_machine_t* sm) {
    if (!sm || !sm->initialized) return -1;
    
    int opening_result = 0;
    int v15 = 0;  // sub_25EBB返回值
    int v17 = 0;  // 退出标志
    int i = 0;    // 循环控制变量
    
    /* ====================================================================
     * 第一步: 调用sub_25EBB() - 状态管理(包含开场动画)
     * ==================================================================== */
    printf("[STATE_MACHINE] Calling sub_25EBB - opening animation...\n");
    
    /* 播放开场动画+菜单 */
    opening_result = fd2_play_opening_animation(sm);
    printf("[STATE_MACHINE] Opening animation returned: %d\n", opening_result);
    
    /* 根据返回值处理sub_25EBB逻辑 */
    if (opening_result == 0) {
        /* ---------------------------------------------------------------
         * 选择Start - 初始化场景0，返回0进入main游戏循环
         * 对应原游戏 sub_25EBB() 的 !v8 分支
         * --------------------------------------------------------------- */
        printf("[STATE_MACHINE] User selected Start - init scene 0\n");
        
        /* sub_1F882() - 淡入效果 */
        /* FDOTHER_DAT = sub_111BA(..., 0) */
        
        /* 设置场景0 */
        g_n17 = 0;
        sm->globals.scene_id = 0;
        g_n16_1 = 0;
        g_byte_51AAC = FD2_SCENE_INACTIVE;
        sm->globals.scene_active_flag = FD2_SCENE_INACTIVE;
        
        /* funcs_25E3A[n17]() - 场景0初始化 (sub_3231B) */
        if (sm->scenes[0].init_fn) {
            printf("[STATE_MACHINE] Calling funcs_25E3A[0] (scene 0 init)\n");
            sm->scenes[0].init_fn(sm);
        }
        
        /* sub_25977(byte_51E63[n17], 0) - 播放场景音乐 */
        /* TODO: 实现音乐切换 */
        
        g_byte_51AAC = FD2_SCENE_ACTIVE;
        sm->globals.scene_active_flag = FD2_SCENE_ACTIVE;
        
        /* 设置g_n2_0 = 2 (INTERACT) 进入场景交互 */
        g_n2_0 = FD2_SCENE_STATE_INTERACT;
        printf("[STATE_MACHINE] Set g_n2_0 = INTERACT (2)\n");
        
        /* sub_4E381() - 刷新屏幕 */
        fd2_render_present(&sm->render);
        
        /* 返回0，进入main的游戏循环 */
        v15 = 0;
        
    } else if (opening_result == 1) {
        /* ---------------------------------------------------------------
         * 选择Load - 加载存档（显示存档列表让用户选择slot）
         * 对应原游戏 sub_25EBB() 的 v8 == 1 分支
         * --------------------------------------------------------------- */
        printf("[STATE_MACHINE] User selected Load - showing save slot selection\n");
        
        /* 获取exe所在目录 */
        const char* exe_dir = SDL_GetBasePath();
        char base_path[512] = "";
        if (exe_dir) {
            strncpy(base_path, exe_dir, sizeof(base_path) - 1);
            SDL_free((void*)exe_dir);
        }
        
        /* 阶段1: 加载UI资源 */
        char res_path[512];
        snprintf(res_path, sizeof(res_path), "%sFDOTHER.DAT", base_path);
        void* fdother_13 = fd2_dat_load_resource(res_path, NULL, 13);
        
        /* 阶段2: 加载FDOTHER.DAT索引0 */
        void* fdother_0 = fd2_dat_load_resource(res_path, NULL, 0);
        
        /* 阶段3: 读取并解密存档 */
        char sav_path[512];
        snprintf(sav_path, sizeof(sav_path), "%sFD2.SAV", base_path);
        
        fd2_sav_data_t sav;
        memset(&sav, 0, sizeof(sav));
        
        if (fd2_sav_load(sav_path, &sav) == 0) {
            printf("[STATE_MACHINE] Save loaded successfully\n");
            
            /* 阶段4: 显示存档slot选择界面（对应原游戏 sub_29BCB） */
            /* 加载FDOTHER.DAT索引1获取UI资源 */
            void* fdother_1 = fd2_dat_load_resource(res_path, NULL, 1);
            if (!fdother_1) {
                fprintf(stderr, "[STATE_MACHINE] Failed to load FDOTHER.DAT index 1\n");
                v15 = 1;
                goto load_done;
            }
            
            /* 解析FDOTHER.DAT索引1的4字节偏移表获取UI图像 */
            u8* idx1_data = (u8*)fdother_1;
            u32 idx1_size = fd2_last_loaded_size;
            
            /* 提取18个UI图像资源(每个484字节: 4字节头+480字节像素) */
            fd2_ui_resource_t* ui_res[18];
            int slot_i;
            
            for (slot_i = 1; slot_i <= 18; slot_i++) {
                u32 res_off = slot_i * 4;
                if (res_off + 8 <= idx1_size) {
                    u32 res_start = *(u32*)(idx1_data + res_off);
                    u32 res_next = *(u32*)(idx1_data + res_off + 4);
                    u32 res_size = res_next - res_start;
                    
                    if (res_start < idx1_size && res_size == 484) {
                        ui_res[slot_i-1] = (fd2_ui_resource_t*)(idx1_data + res_start);
                    } else {
                        ui_res[slot_i-1] = NULL;
                    }
                } else {
                    ui_res[slot_i-1] = NULL;
                }
            }
            
            /* 加载FDOTHER.DAT索引6字体资源 */
            void* fdother_6 = fd2_dat_load_resource(res_path, NULL, 6);
            u8* font_data = (u8*)fdother_6;
            
            /* 分配屏幕缓冲区 (320x200) */
            u8* screen_buf = (u8*)malloc(64000);
            if (!screen_buf) {
                fprintf(stderr, "[STATE_MACHINE] Failed to allocate screen buffer\n");
                free(fdother_1);
                if (fdother_6) free(fdother_6);
                v15 = 1;
                goto load_done;
            }
            
            /* 阶段4a: 初始渲染 */
            int selected_slot = 0;
            int load_result = -1;
            
            while (1) {
                /* 清屏 */
                memset(screen_buf, 0, 64000);
                
                /* 绘制标题 "LOAD" */
                fd2_render_string(font_data, "LOAD GAME", screen_buf, 320, 110, 10, 15);
                
                /* 渲染4个存档槽 */
                for (slot_i = 0; slot_i < 4; slot_i++) {
                    u8* slot_data = sav.battleSlots[slot_i].sceneData;
                    fd2_render_slot_ui(screen_buf, 320, slot_i, slot_i == selected_slot,
                                  slot_data, (fd2_ui_resource_t**)ui_res, font_data);
                }
                
                /* 绘制底部提示 "PRESS ENTER TO LOAD" */
                fd2_render_string(font_data, "PRESS ENTER", screen_buf, 320, 80, 180, 14);
                
                /* 将屏幕缓冲区拷贝到渲染器 */
                memcpy(sm->render.screen, screen_buf, 64000);
                fd2_render_present(&sm->render);
                
                /* 等待输入: 对应原游戏 sub_16C57 */
                SDL_Event event;
                int need_refresh = 0;
                
                while (SDL_WaitEvent(&event)) {
                    if (event.type == SDL_QUIT) {
                        load_result = -1;
                        goto load_exit;
                    }
                    if (event.type == SDL_KEYDOWN) {
                        switch (event.key.keysym.scancode) {
                            case SDL_SCANCODE_UP:
                                if (selected_slot > 0) {
                                    selected_slot--;
                                    need_refresh = 1;
                                }
                                break;
                            case SDL_SCANCODE_DOWN:
                                if (selected_slot < 3) {
                                    selected_slot++;
                                    need_refresh = 1;
                                }
                                break;
                            case SDL_SCANCODE_RETURN:
                            case SDL_SCANCODE_SPACE:
                                load_result = selected_slot;
                                goto load_exit;
                            case SDL_SCANCODE_ESCAPE:
                                load_result = -1;
                                goto load_exit;
                            default:
                                break;
                        }
                        if (need_refresh) break;
                    }
                }
            }
            
        load_exit:
            /* 清理资源 */
            if (screen_buf) free(screen_buf);
            if (fdother_1) free(fdother_1);
            if (fdother_6) free(fdother_6);
            
            selected_slot = load_result;
            printf("[STATE_MACHINE] User selected slot %d\n", selected_slot);
            
            /* 检查slot是否有效 */
            if (sav.battleSlots[selected_slot].n17 == 255) {
                printf("[STATE_MACHINE] Slot %d is empty\n", selected_slot);
                v15 = 1;
            } else {
                /* 阶段5: 从选择的slot加载战场数据 */
                /* 对应原游戏 sub_29BCB返回后的处理 */
                printf("[STATE_MACHINE] Loading from slot %d (scene=%d)\n", 
                       selected_slot, sav.battleSlots[selected_slot].n17);
                
                /* 复制slot的场景数据到sav.sceneData */
                memcpy(sav.sceneData, sav.battleSlots[selected_slot].sceneData, 2560);
                
                /* 更新存档状态变量 */
                sav.n17 = sav.battleSlots[selected_slot].n17;
                sav.n16_1 = sav.battleSlots[selected_slot].n16_1;
                sav.n999_0 = sav.battleSlots[selected_slot].n999_0;
                sav.byte_51AAB = sav.battleSlots[selected_slot].byte_51AAB;
                sav.byte_53AF9 = sav.battleSlots[selected_slot].byte_53AF9;
                sav.n127 = sav.battleSlots[selected_slot].n127;
                sav.byte_51E62 = sav.battleSlots[selected_slot].byte_51E62;
                
                /* 应用存档数据到全局变量 */
                fd2_sav_apply(&sav);
                
                /* 阶段6: 释放旧场景资源 */
                if (g_dword_53A45) { free(g_dword_53A45); g_dword_53A45 = NULL; }
                if (g_dword_53A55) { free(g_dword_53A55); g_dword_53A55 = NULL; }
                if (g_n7) { free(g_n7); g_n7 = NULL; }
                if (g_dword_53A51) { free(g_dword_53A51); g_dword_53A51 = NULL; }
                if (g_dword_53A61) { free(g_dword_53A61); g_dword_53A61 = NULL; }
                if (g_n655360_0) { free(g_n655360_0); g_n655360_0 = NULL; }
                
                /* 阶段7: 分配场景资源 */
                char res_path2[512];
                int v11;
                int music_id;
                
                /* 分配FDSHAP_DAT缓冲区 */
                g_n7 = malloc(153216);
                if (!g_n7) {
                    fprintf(stderr, "[STATE_MACHINE] Failed to allocate FDSHAP buffer\n");
                    v15 = 1;
                } else {
                    memset(g_n7, 0, 153216);
                    
                    /* 加载FDOTHER.DAT索引n17 (RLE图形) */
                    snprintf(res_path2, sizeof(res_path2), "%sFDOTHER.DAT", base_path);
                    void* fdother_data = fd2_dat_load_resource(res_path2, NULL, sav.n17);
                    if (fdother_data) {
                        u32 res_size = fd2_last_loaded_size;
                        fd2_rle_decompress_to_buffer((u8*)fdother_data, res_size,
                                                     (u8*)g_n7 + 32904, 0, 456, -1);
                        free(fdother_data);
                    }
                    
                    /* 加载其他资源 */
                    snprintf(res_path2, sizeof(res_path2), "%sFDOTHER.DAT", base_path);
                    g_dword_53A55 = fd2_dat_load_resource(res_path2, NULL, 0);
                    g_dword_53F5A = fd2_dat_load_resource(res_path2, NULL, 10);
                    
                    snprintf(res_path2, sizeof(res_path2), "%sFDFIELD.DAT", base_path);
                    g_dword_53A51 = fd2_dat_load_resource(res_path2, NULL, 3 * sav.n17);
                    if (g_dword_53A51) {
                        fd2_field_data_process((u8*)g_dword_53A51);
                    }
                    g_dword_53A59 = fd2_dat_load_resource(res_path2, NULL, 3 * sav.n17 + 2);
                    
                    snprintf(res_path2, sizeof(res_path2), "%sFDTXT.DAT", base_path);
                    g_FDTXT_DAT__0 = fd2_dat_load_resource(res_path2, NULL, sav.n17 + 1);
                    
                    v11 = 2 * (int)sav.fieldData[0];
                    snprintf(res_path2, sizeof(res_path2), "%sFDSHAP.DAT", base_path);
                    g_FDSHAP_DAT = fd2_dat_load_resource(res_path2, NULL, v11);
                    g_dword_53A69 = fd2_dat_load_resource(res_path2, NULL, v11 + 1);
                    
                    /* 分配显存缓冲区 */
                    g_n655360_0 = malloc(655360);
                    if (g_n655360_0) {
                        memset(g_n655360_0, 0, 64000);
                    }
                    
                    /* 播放场景音乐 */
                    music_id = (unsigned char)g_byte_51E63[sav.n17];
                    fd2_music_play(music_id);
                    
                    /* 设置场景状态 */
                    g_n2_0 = FD2_SCENE_STATE_INTERACT;
                    g_n17 = sav.n17;
                    g_n16_1 = sav.n16_1;
                    g_n5 = 0;
                    
                    printf("[STATE_MACHINE] Load completed: slot=%d, scene=%d, music=%d\n", 
                           selected_slot, sav.n17, music_id);
                    
                    v15 = 0;
                }
            }
        } else {
            printf("[STATE_MACHINE] Failed to load save file\n");
            v15 = 1;
        }
        
    load_done:
        ;
        
    } else {
        /* ---------------------------------------------------------------
         * 其他选项 - 退出/Continue
         * 对应原游戏 sub_25EBB() 的 v8 != 0 && v8 != 1 分支
         * --------------------------------------------------------------- */
        printf("[STATE_MACHINE] Other option: %d - continue/exit\n", opening_result);
        
        /* sub_25977(opening_result, ..., -1, 0) */
        fd2_music_stop();
        
        /* sub_10010() - 加载存档 */
        fd2_sav_data_t sav;
        memset(&sav, 0, sizeof(sav));
        
        /* 获取exe所在目录（sav文件与exe在同一目录） */
        const char* exe_dir = SDL_GetBasePath();
        char base_path[512] = "";
        if (exe_dir) {
            strncpy(base_path, exe_dir, sizeof(base_path) - 1);
            SDL_free((void*)exe_dir);
        }
        
        char sav_path[512];
        snprintf(sav_path, sizeof(sav_path), "%sFD2.SAV", base_path);
        
        if (fd2_sav_continue_load(sav_path, &sav) == 0) {
            /* 应用存档数据到全局变量 */
            fd2_sav_apply(&sav);
            
            /* 对应原游戏 sub_26152 - 场景初始化 */
            
            /* 阶段1: 释放旧场景资源 */
            if (g_dword_53A45) { free(g_dword_53A45); g_dword_53A45 = NULL; }
            if (g_dword_53A55) { free(g_dword_53A55); g_dword_53A55 = NULL; }
            if (g_n7) { free(g_n7); g_n7 = NULL; }
            if (g_dword_53A51) { free(g_dword_53A51); g_dword_53A51 = NULL; }
            if (g_dword_53A61) { free(g_dword_53A61); g_dword_53A61 = NULL; }
            
            /* 阶段2: 构建exe目录路径 */
            char res_path[512];
            int v11;  /* FDSHAP.DAT索引计算 */
            int music_id;  /* 场景音乐ID */
            
            /* 阶段3: 分配FDSHAP_DAT缓冲区 (153216字节) */
            g_n7 = malloc(153216);
            if (!g_n7) {
                fprintf(stderr, "[STATE_MACHINE] Failed to allocate FDSHAP buffer\n");
                v15 = 1;
            } else {
                memset(g_n7, 0, 153216);
                
                /* 阶段4: 加载FDOTHER.DAT索引n17 (RLE图形数据) 并解压到 n7+32904 */
                snprintf(res_path, sizeof(res_path), "%sFDOTHER.DAT", base_path);
                void* fdother_data = fd2_dat_load_resource(res_path, NULL, sav.n17);
                if (fdother_data) {
                    /* sub_4E98D - RLE解压到 n7+32904, 行宽456, palette_offset=-1 */
                    u32 res_size = fd2_last_loaded_size;
                    fd2_rle_decompress_to_buffer((u8*)fdother_data, res_size,
                                                 (u8*)g_n7 + 32904, 0, 456, -1);
                    free(fdother_data);
                }
                
                /* 阶段5: 加载FDOTHER.DAT索引10 */
                snprintf(res_path, sizeof(res_path), "%sFDOTHER.DAT", base_path);
                g_dword_53F5A = fd2_dat_load_resource(res_path, NULL, 10);
                
                /* 阶段6: 加载FDFIELD.DAT索引3*n17 (布局数据) */
                snprintf(res_path, sizeof(res_path), "%sFDFIELD.DAT", base_path);
                g_dword_53A51 = fd2_dat_load_resource(res_path, NULL, 3 * sav.n17);
                if (g_dword_53A51) {
                    fd2_field_data_process((u8*)g_dword_53A51);
                }
                
                /* 阶段7: 加载FDTXT.DAT索引n17+1 */
                snprintf(res_path, sizeof(res_path), "%sFDTXT.DAT", base_path);
                g_FDTXT_DAT__0 = fd2_dat_load_resource(res_path, NULL, sav.n17 + 1);
                
                /* 阶段8: 加载FDFIELD.DAT索引3*n17+2 */
                snprintf(res_path, sizeof(res_path), "%sFDFIELD.DAT", base_path);
                g_dword_53A59 = fd2_dat_load_resource(res_path, NULL, 3 * sav.n17 + 2);
                
                /* 阶段9: 加载FDSHAP.DAT (对应原游戏 sub_10010) */
                /* v11 = 2 * *(u8*)FDFIELD_DAT__1; FDSHAP.DAT索引=v11, FDSHAP.DAT索引=v11+1 */
                /* FDFIELD_DAT__1来自存档前2211字节 */
                v11 = 2 * (int)sav.fieldData[0];
                snprintf(res_path, sizeof(res_path), "%sFDSHAP.DAT", base_path);
                g_FDSHAP_DAT = fd2_dat_load_resource(res_path, NULL, v11);
                g_dword_53A69 = fd2_dat_load_resource(res_path, NULL, v11 + 1);
                
                /* 阶段10: 播放场景音乐 */
                music_id = (unsigned char)g_byte_51E63[sav.n17];
                fd2_music_play(music_id);
                
                /* 设置场景状态 */
                g_n2_0 = FD2_SCENE_STATE_INTERACT;
                g_n17 = sav.n17;
                g_n16_1 = sav.n16_1;
                g_n5 = 0;  /* 菜单索引归零 */
                
                printf("[STATE_MACHINE] Continue loaded: scene=%d, music=%d\n", sav.n17, music_id);
                
                v15 = 0;  /* 返回0进入main的游戏循环 */
            }
        } else {
            fprintf(stderr, "[STATE_MACHINE] Failed to load continue save\n");
            v15 = 1;  /* 加载失败，退出 */
        }
    }
    
    /* ====================================================================
     * 第二步: 如果sub_25EBB返回0，进入main的游戏循环
     * 对应原游戏 main() while(1) { if (v15 == 0) { do...while(!i); } }
     * ==================================================================== */
    if (v15 == 0) {
        printf("[STATE_MACHINE] Entering main game loop (n2_0 state machine)\n");
        
        do {
            /* 处理SDL事件 */
            SDL_Event event;
            while (SDL_PollEvent(&event)) {
                if (event.type == SDL_QUIT) {
                    i = -1;
                    goto exit_loop;
                }
            }
            
            /* 检查退出请求 */
            if (g_sdl_quit_requested) {
                i = -1;
                goto exit_loop;
            }
            
            /* sub_117E7() - 输入处理 */
            i = fd2_input_process(sm);
            
            if (g_n2_0 == FD2_SCENE_STATE_INIT) {
                /* ---------------------------------------------------------------
                 * n2_0 == 1: 场景初始化
                 * 对应原游戏:
                 *   byte_51AAC = 0;
                 *   sub_22E5C();
                 *   byte_51AAC = 1;
                 *   n2_0 = 0;
                 *   i = 1;
                 * --------------------------------------------------------------- */
                printf("[STATE_MACHINE] n2_0==1 - Scene init\n");
                
                g_byte_51AAC = FD2_SCENE_INACTIVE;
                fd2_scene_setup(sm);  /* sub_22E5C */
                g_byte_51AAC = FD2_SCENE_ACTIVE;
                g_n2_0 = FD2_SCENE_STATE_IDLE;
                sm->globals.scene_state = FD2_SCENE_STATE_IDLE;
                i = 1;
                
            } else if (g_n2_0 == FD2_SCENE_STATE_INTERACT) {
                /* ---------------------------------------------------------------
                 * n2_0 == 2: 场景交互
                 * 对应原游戏:
                 *   byte_51AAC = 0;
                 *   sub_25977(-1, 1);  // 停止音乐
                 *   funcs_25E23[n17]();  // 场景初始化
                 *   i = sub_26152();    // 场景交互循环
                 *   
                 *   if (i) {
                 *       v17 = 1;
                 *   } else {
                 *       funcs_25E3A[n17]();  // 场景结束
                 *       sub_25977(byte_51E63[n17], 0);  // 切换音乐
                 *   }
                 *   byte_51AAC = 1;
                 *   n2_0 = 0;
                 *   sub_4E381();  // 刷新屏幕
                 * --------------------------------------------------------------- */
                int scene_id = g_n17;
                printf("[STATE_MACHINE] n2_0==2 - Scene %d interact\n", scene_id);
                
                g_byte_51AAC = FD2_SCENE_INACTIVE;
                sm->globals.scene_active_flag = FD2_SCENE_INACTIVE;
                
                /* sub_25977(-1, 1) - 停止音乐 */
                /* TODO: 停止当前音乐 */
                
                /* funcs_25E23[n17]() - 场景初始化 */
                if (sm->scenes[scene_id].init_fn) {
                    printf("[STATE_MACHINE] Calling funcs_25E23[%d]\n", scene_id);
                    sm->scenes[scene_id].init_fn(sm);
                }
                
                g_byte_51AAC = FD2_SCENE_ACTIVE;
                sm->globals.scene_active_flag = FD2_SCENE_ACTIVE;
                
                /* sub_26152() - 场景交互循环 */
                printf("[STATE_MACHINE] Calling sub_26152 (interact loop)\n");
                i = fd2_state_machine_interact_loop(sm);
                
                if (i) {
                    /* 场景交互返回非0，准备退出 */
                    v17 = 1;
                } else {
                    /* 场景结束 */
                    if (sm->scenes[scene_id].exit_fn) {
                        printf("[STATE_MACHINE] Calling funcs_25E3A[%d]\n", scene_id);
                        sm->scenes[scene_id].exit_fn(sm);
                    }
                    /* sub_25977(byte_51E63[n17], 0) - 切换场景音乐 */
                    /* TODO: 实现音乐切换 */
                }
                
                g_byte_51AAC = FD2_SCENE_ACTIVE;
                g_n2_0 = FD2_SCENE_STATE_IDLE;
                sm->globals.scene_state = FD2_SCENE_STATE_IDLE;
                
                /* sub_4E381() - 刷新屏幕 */
                fd2_render_present(&sm->render);
            }
            
            /* ============================================================
             * 关键修复: IDLE状态时也要刷新屏幕
             * 原游戏在空闲状态也会调用sub_4E381()刷新屏幕
             * ============================================================ */
            fd2_render_present(&sm->render);
            
            /* 控制帧率 */
            SDL_Delay(16);  /* ~60 FPS */
            
        } while (!i);
        
        if (i == -1) {
            v17 = 1;
        }
    }
    
exit_loop:
    if (v17) {
        printf("[STATE_MACHINE] Exit requested\n");
        /* sub_37ED8() - 音频清理 */
        /* n3 = 3; int386(16, &n3, &n3); */
    }
    
    return v17;
}
