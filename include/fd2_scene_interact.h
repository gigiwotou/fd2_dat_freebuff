#ifndef FD2_SCENE_INTERACT_H
#define FD2_SCENE_INTERACT_H

/*
 * FD2 场景交互系统
 * 基于原游戏 (FD2.EXE) 的IDA反汇编代码1:1实现
 * 
 * 原游戏核心函数:
 * - sub_26152() 0x26152 - 场景交互循环
 * - sub_265EC() - 场景渲染更新
 * - sub_2670E() 0x2670E - 场景特效和选择执行
 */

#include "fd2_types.h"
#include "fd2_globals.h"
#include "fd2_data_loader.h"

/* 函数返回类型 */
typedef int fd2_scene_result_t;

/*
 * sub_26152: 场景交互循环 (原游戏 0x26152)
 *
 * 原游戏签名:
 *   bool __usercall sub_26152@<eax>(__int32 a1@<eax>, int a2@<edx>, int n8@<ecx>, int a4@<ebx>, int a5@<ebp>)
 *
 * 功能流程:
 * 1. 释放旧场景资源 (n8_1, FDFIELD_DAT__1, FDSHAP_DAT, FDFIELD_DAT__0, dword_53A61)
 * 2. 打开fdicon.b24，循环调用sub_11019加载图标
 * 3. 检查特殊场景 (byte_523E7[n17])
 * 4. 如果是特殊场景: 执行特殊处理 (sub_2AF28)
 * 5. 否则: 
 *    - 分配FDSHAP_DAT (153216字节)
 *    - 调用sub_4E809加载场景数据
 *    - 调用sub_25977切换音乐 (索引10)
 *    - 初始化n5 = 0
 *    - 加载FDOTHER.DAT索引10
 *    - 调用sub_4E98D解压到FDSHAP_DAT+32904
 *    - 调用sub_265EC渲染
 *    - 主交互循环 (do-while)
 *
 * 返回值:
 *   n5 != 2 (如果菜单索引==2则返回0，否则返回1)
 */
fd2_scene_result_t fd2_scene_interact_loop(void);

/*
 * sub_265EC: 场景渲染更新 (被sub_26152调用)
 *
 * 功能:
 * - 复制FDSHAP_DAT到后备缓冲区
 * - 渲染FDOTHER_DAT__12图形数据
 * - 根据动画帧 (n3_4) 更新光标/图标
 * - 执行屏幕区域更新
 */
void fd2_scene_render_update(void* v20);

/*
 * sub_2670E: 场景特效和选择执行 (原游戏 0x2670E)
 *
 * 功能:
 * - 执行用户选择后的操作
 * - 播放特效动画
 * - 更新退出标志
 */
void fd2_scene_execute_selection(int a5, void* v20);

/* 辅助函数 */
void fd2_scene_release_old_resources(void);
int fd2_scene_load_icons(void);
int fd2_scene_load_graphics(void);
void fd2_scene_interact_main_loop(void* v20);
void fd2_scene_handle_key(int key_code);
void fd2_scene_handle_confirm(void);

#endif /* FD2_SCENE_INTERACT_H */
