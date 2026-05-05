#ifndef FD2_SCENES_H
#define FD2_SCENES_H

/*
 * FD2 场景生命周期函数
 * 对应原游戏 funcs_25E23[] 和 funcs_25E3A[]
 * 
 * 场景0-29对应原游戏的30个场景
 */

#include "fd2_state_machine.h"

/* 前置声明 */
struct fd2_state_machine;

/* 场景0: 主菜单/标题场景 (对应原游戏 sub_3231B) */
void scene_0_init(struct fd2_state_machine* sm);
void scene_0_exit(struct fd2_state_machine* sm);
int scene_0_check(struct fd2_state_machine* sm);

/* 场景1: 默认处理 (对应原游戏 sub_22EF6) */
void scene_1_init(struct fd2_state_machine* sm);
void scene_1_exit(struct fd2_state_machine* sm);

/* 场景2-29: 默认处理 (对应原游戏 sub_21206) */
void scene_default_init(struct fd2_state_machine* sm);
void scene_default_exit(struct fd2_state_machine* sm);

/* 注册所有场景到状态机 */
void fd2_register_all_scenes(fd2_state_machine_t* sm);

#endif /* FD2_SCENES_H */
