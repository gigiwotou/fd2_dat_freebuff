/*
 * FD2 场景生命周期实现
 * 对应原游戏 funcs_25E23[] 和 funcs_25E3A[] 函数指针数组
 * 
 * 原游戏数据:
 * - funcs_25E3A[0] = sub_3231B (主菜单场景初始化)
 * - funcs_25E3A[1-29] = sub_21206 (默认处理)
 * - funcs_25E23[0-29] = sub_22EF6 (默认处理)
 */

#include "fd2_scenes.h"
#include "fd2_resources.h"
#include <stdlib.h>
#include <stdio.h>

/*
 * 场景0: 主菜单/标题场景初始化 (对应原游戏 sub_3231B)
 * 地址: 0x3231B, 大小: 0x65A (1626字节)
 */
void scene_0_init(struct fd2_state_machine* sm) {
    if (!sm) return;
    
    sm->globals.scene_id = 32;
    /* TODO: sub_205DA(); sub_135DD(3, 34); sub_1366A(..., 99); */
    
    for (int i = 0; i < 15; i++) {
        /* TODO: sub_13185(2); */
    }
    
    for (int i = 0; i < 13; i++) {
        /* TODO: sub_13185(2); */
    }
    
    /* TODO: sub_25977(..., -1, 0); sub_1366A(..., 100); */
    
    /* TODO: 完整的sub_3231B逻辑 */
    
    sm->globals.progress = 0;
}

void scene_0_exit(struct fd2_state_machine* sm) {
    if (!sm) return;
}

int scene_0_check(struct fd2_state_machine* sm) {
    if (!sm) return 0;
    return 0;
}

/*
 * 场景1: 默认处理 (对应原游戏 sub_22EF6)
 * 地址: 0x22EF6, 大小: 0x41 (65字节)
 */
void scene_1_init(struct fd2_state_machine* sm) {
    if (!sm) return;
    sm->globals.scene_id = 1;
}

void scene_1_exit(struct fd2_state_machine* sm) {
    if (!sm) return;
}

/*
 * 场景2-29: 默认处理 (对应原游戏 sub_21206)
 * 地址: 0x21206, 大小: 0x21 (33字节)
 */
void scene_default_init(struct fd2_state_machine* sm) {
    if (!sm) return;
}

void scene_default_exit(struct fd2_state_machine* sm) {
    if (!sm) return;
}

/*
 * 注册所有场景到状态机
 * 对应原游戏 funcs_25E23[] 和 funcs_25E3A[] 数组初始化
 */
int fd2_register_all_scenes(fd2_state_machine_t* sm) {
    if (!sm) return -1;
    
    /* 场景0: 主菜单/标题场景 */
    fd2_register_scene(sm, 0, scene_0_init, scene_0_exit, scene_0_check,
                       0, 0, "main_menu");
    
    /* 场景1: 默认处理 */
    fd2_register_scene(sm, 1, scene_1_init, scene_1_exit, NULL,
                       0, 0, "scene_1");
    
    /* 场景2-29: 默认处理 */
    for (int i = 2; i < FD2_SCENE_COUNT; i++) {
        char name[32];
        snprintf(name, sizeof(name), "scene_%d", i);
        fd2_register_scene(sm, i, scene_default_init, scene_default_exit, NULL,
                           0, 0, name);
    }
    
    return 0;
}
