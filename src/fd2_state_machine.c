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
#include <SDL2/SDL.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

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
    
    return 0;
}

void fd2_state_machine_shutdown(fd2_state_machine_t* sm) {
    if (!sm) return;
    sm->running = 0;
    sm->initialized = 0;
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
    /* TODO: 实现SDL按键扫描码读取 */
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
 * 第三层状态机: 场景交互循环 (对应原游戏 sub_26152)
 * 
 * 原游戏核心逻辑:
 * 1. 释放旧场景资源
 * 2. 加载场景配置 (fdicon.b24)
 * 3. 检查特殊场景 (byte_523E7[n17])
 * 4. 加载图形数据
 * 5. 主交互循环:
 *    - sub_265EC() 渲染更新
 *    - 等待按键 (BIOS定时器控制动画帧)
 *    - switch (按键) 处理导航/确认
 *    - sub_2670E() 执行选择
 * 6. 返回是否退出场景
 */
int fd2_state_machine_interact_loop(fd2_state_machine_t* sm) {
    if (!sm || !sm->initialized) return 0;
    
    int exit_flag = 0;
    int scene_id = sm->globals.scene_id;
    
    /* 阶段1: 释放旧场景资源 (对应原游戏 if (n8_1) free(n8_1); ...) */
    if (sm->globals.backup_buffer) {
        free(sm->globals.backup_buffer);
        sm->globals.backup_buffer = NULL;
    }
    if (sm->globals.fdfield_data) {
        free(sm->globals.fdfield_data);
        sm->globals.fdfield_data = NULL;
    }
    if (sm->globals.fdshap_data) {
        free(sm->globals.fdshap_data);
        sm->globals.fdshap_data = NULL;
    }
    
    /* 阶段2: 加载场景配置 (对应原游戏 fopen("fdicon.b24")) */
    /* TODO: 加载fdicon.b24 */
    
    /* 阶段3: 检查特殊场景 (对应原游戏 if (byte_523E7[n17])) */
    if (sm->scenes[scene_id].is_special) {
        /* TODO: 实现特殊场景处理 */
        return 0;
    }
    
    /* 阶段4: 普通场景 - 加载图形数据 */
    sm->globals.fdshap_data = malloc(153216);
    if (!sm->globals.fdshap_data) return 0;
    
    g_n5 = 0;
    sm->globals.menu_index = 0;
    
    /* TODO: 加载场景图形 */
    
    if (sm->interaction.render_update) {
        sm->interaction.render_update(sm);
    }
    
    /* 阶段5: 主交互循环 (对应原游戏 do-while (!v21)) */
    do {
        if (sm->interaction.render_update) {
            sm->interaction.render_update(sm);
        }
        
        /* 等待按键 (带BIOS定时器控制动画帧) */
        while (1) {
            if (fd2_check_anim_frame(sm)) {
                if (sm->interaction.render_update) {
                    sm->interaction.render_update(sm);
                }
                break;
            }
            int key = fd2_get_key_code();
            if (key != 0) {
                g_n3 = key;
                sm->globals.key_code = key;
                break;
            }
            SDL_Delay(1);
        }
        
        /* 按键处理 (对应原游戏 switch (HIBYTE(n3))) */
        int key_code = sm->globals.key_code;
        
        switch (key_code) {
            case FD2_KEY_EXTEND:
            case FD2_KEY_INSERT:
                key_code = FD2_KEY_MAP_INSERT;
                break;
                
            case FD2_KEY_TAB:
                if (sm->interaction.handle_subscene_switch) {
                    sm->interaction.handle_subscene_switch(sm);
                } else {
                    g_n16_1++;
                    if (g_n16_1 >= FD2_SUBSCENE_COUNT) g_n16_1 = 0;
                    fd2_switch_subscene(sm, g_n16_1);
                }
                break;
                
            case FD2_KEY_RIGHT:
                if (sm->interaction.handle_menu_nav) {
                    sm->interaction.handle_menu_nav(sm, 1);
                } else {
                    fd2_menu_navigate(sm, 1);
                }
                break;
                
            case FD2_KEY_LEFT:
                if (sm->interaction.handle_menu_nav) {
                    sm->interaction.handle_menu_nav(sm, -1);
                } else {
                    fd2_menu_navigate(sm, -1);
                }
                break;
                
            default:
                if (sm->interaction.handle_key) {
                    sm->interaction.handle_key(sm, key_code);
                }
                break;
        }
        
        /* 确认处理 */
        if (key_code != FD2_KEY_ENTER && key_code != FD2_KEY_SPACE) {
            continue;
        }
        
        if (sm->globals.menu_index != FD2_MENU_ITEM_BACK) {
            if (sm->interaction.handle_confirm) {
                sm->interaction.handle_confirm(sm);
            }
        }
        
        if (sm->interaction.process_selection) {
            sm->interaction.process_selection(sm);
        }
        
        exit_flag = sm->globals.exit_flag;
        
    } while (!exit_flag);
    
    /* 清理资源 */
    if (sm->globals.fdother_data[12]) {
        free(sm->globals.fdother_data[12]);
        sm->globals.fdother_data[12] = NULL;
    }
    
    return (sm->globals.menu_index != FD2_MENU_ITEM_BACK);
}

/*
 * 场景渲染更新 (对应原游戏 sub_265EC)
 */
void fd2_scene_render_update(fd2_state_machine_t* sm) {
    if (!sm) return;
    /* TODO: 实现 sub_265EC() 的完整逻辑 */
}

/*
 * 主循环 (对应原游戏 main)
 * 
 * 原游戏核心逻辑:
 * while (1) {
 *     v14 = sub_25977(18, 0);
 *     v15 = sub_25EBB(v14);
 *     if (v15 == 0) {
 *         do {
 *             i = sub_117E7(...);
 *             if (n2_0 == 1) { 场景初始化 }
 *             else if (n2_0 == 2) {
 *                 funcs_25E23[n17]();  // 场景初始化
 *                 i = sub_26152();     // 场景交互
 *                 if (i) { v17 = 1; }
 *                 else {
 *                     funcs_25E3A[n17]();  // 场景结束
 *                     sub_25977(...);      // 切换音乐
 *                 }
 *             }
 *         } while (!i);
 *     }
 *     if (v17) { 退出游戏 }
 * }
 */
int fd2_state_machine_run(fd2_state_machine_t* sm) {
    if (!sm || !sm->initialized) return -1;
    
    int v15 = 0;
    int v17 = 0;
    int i = 0;
    
    while (sm->running) {
        v15 = fd2_get_game_state(sm);
        
        if (v15 == 0) {
            do {
                i = fd2_input_process(sm);
                
                if (g_n2_0 == FD2_SCENE_STATE_INIT) {
                    g_byte_51AAC = FD2_SCENE_INACTIVE;
                    fd2_scene_setup(sm);
                    g_byte_51AAC = FD2_SCENE_ACTIVE;
                    g_n2_0 = FD2_SCENE_STATE_IDLE;
                    i = 1;
                }
                else if (g_n2_0 == FD2_SCENE_STATE_INTERACT) {
                    g_byte_51AAC = FD2_SCENE_INACTIVE;
                    
                    int scene_id = sm->globals.scene_id;
                    fd2_scene_init(sm, scene_id);
                    i = fd2_state_machine_interact_loop(sm);
                    
                    if (i) {
                        v17 = 1;
                    } else {
                        fd2_scene_exit(sm, scene_id);
                        fd2_music_switch(g_byte_51E63[g_n17], 0);
                    }
                    
                    g_byte_51AAC = FD2_SCENE_ACTIVE;
                    g_n2_0 = FD2_SCENE_STATE_IDLE;
                    fd2_update_screen(sm);
                }
            } while (!i);
            
            if (i == -1) {
                v17 = 1;
            }
        }
        
        if (v17) {
            break;
        }
    }
    
    return 0;
}
