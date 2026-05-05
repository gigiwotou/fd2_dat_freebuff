#ifndef FD2_SCENE_INTERACT_H
#define FD2_SCENE_INTERACT_H

#include "fd2_types.h"
#include "fd2_state_machine.h"

/* 主交互循环 (对应原游戏 sub_26152) */
int fd2_state_machine_interact_loop(fd2_state_machine_t* sm);

/* 场景资源加载 (对应原游戏 sub_11D40) */
void fd2_scene_load_icons(fd2_state_machine_t* sm);

/* 场景图形加载 */
void fd2_scene_load_graphics(fd2_state_machine_t* sm);

/* 场景资源释放 */
void fd2_scene_release_old_resources(fd2_state_machine_t* sm);

/* 渲染更新 (对应原游戏 sub_265EC) */
void fd2_scene_interact_render_update(fd2_state_machine_t* sm);

/* 按键处理 */
int fd2_scene_handle_key(fd2_state_machine_t* sm);

/* 确认键处理 */
int fd2_scene_handle_confirm(fd2_state_machine_t* sm);

/* 场景选择执行 (对应原游戏 sub_2670E) */
int fd2_scene_execute_selection(fd2_state_machine_t* sm, int menuIndex);

/* 特效处理 */
int fd2_scene_process_effect(fd2_state_machine_t* sm, int effectType);

/* 场景完成条件检查 */
int fd2_scene_check_completion(fd2_state_machine_t* sm);

#endif /* FD2_SCENE_INTERACT_H */
