#ifndef FD2_OPENING_ANIMATION_H
#define FD2_OPENING_ANIMATION_H

#include "fd2_types.h"
#include "fd2_state_machine.h"
#include "fd2_resources.h"
#include "fd2_render.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================
 * 开场动画系统 (对应原游戏 sub_1F894)
 *
 * 原游戏 sub_1F894 地址: 0x1F894, 大小: ~0xA00
 * 调用者: sub_25EBB (状态管理)
 * 
 * 开场动画流程:
 * 1. 加载FDOTHER.DAT资源 (索引77, 76, 74等)
 * 2. 设置调色板 (sub_11D40)
 * 3. 使用sub_4E98D渲染图像到屏幕
 * 4. 播放AFM动画 (sub_20421)
 * 5. 淡入淡出效果 (sub_2DF01)
 * 6. 等待按键退出
 * ======================================================================== */

/* 开场动画播放函数 */
int fd2_play_opening_animation(fd2_state_machine_t* sm);

#ifdef __cplusplus
}
#endif

#endif /* FD2_OPENING_ANIMATION_H */
