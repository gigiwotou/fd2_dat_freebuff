#include "fd2_data_loader.h"
#include "fd2_globals.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ========================================================================
 * sub_25977: 音乐切换函数 (IDA 0x25977)
 *
 * 原游戏行为 (1:1 复制):
 *   1. if (n16 != ::n16) {
 *   2.   ::n16 = n16;
 *   3.   if (n16 == -1) {
 *   4.     sub_3B124(n16_1, dword_53ED0, 0, 4000);  // 停止音乐
 *   5.   } else {
 *   6.     if (n16_0) {
 *   7.       if (FDMUS_DAT) sub_3AF5B(n16_0, dword_53ED0);
 *   8.       FDMUS_DAT = sub_111BA(..., "FDMUS.DAT", FDMUS_DAT, n16);
 *   9.       v8 = sub_3666C(FDMUS_DAT, dword_53BFF);
 *   10.      sub_3ADF5(v8, dword_53ED0, FDMUS_DAT, 0);
 *   11.      sub_3AEEE(dword_53ED0);
 *   12.      if (n127) {
 *   13.        if (n16 == 16 || n16 == 17) n2000 = 0;
 *   14.        else { sub_3B124(..., 0, 0); n2000 = 2000; }
 *   15.        v10 = sub_3B124(..., 127, n2000);
 *   16.      } else {
 *   17.        v10 = sub_3B124(..., 0, 0);
 *   18.      }
 *   19.      sub_3B1A6(v10, dword_53ED0, arg4);
 *   20.    }
 *   21.  }
 *   22. }
 * ======================================================================== */

void fd2_music_switch(int n16, int arg4) {
    static int current_n16 = -1;

    /* 1. 检查音乐ID是否变化 */
    if (current_n16 != n16) {
        current_n16 = n16;

        /* 3. 停止音乐 */
        if (n16 == -1) {
            /* TODO: 调用AIL库停止音乐 sub_3B124(..., dword_53ED0, 0, 4000) */
            /* SDL2实现: 停止当前播放的音乐 */
        }
        else {
            /* 6. 播放新音乐 */
            /* TODO: 完整的AIL音乐加载和播放逻辑
             * - 从FDMUS.DAT加载音乐索引n16
             * - sub_111BA(..., "FDMUS.DAT", FDMUS_DAT, n16)
             * - sub_3666C 检查音乐数据
             * - sub_3ADF5 设置音乐
             * - sub_3AEEE 启动音乐
             * - sub_3B124 设置音量
             * - sub_3B1A6 播放音乐
             */
        }
    }
}

void fd2_music_stop(void) {
    fd2_music_switch(-1, 0);
}

void fd2_music_play(int musicId) {
    fd2_music_switch(musicId, 0);
}

int fd2_music_get_scene_music_id(int sceneId) {
    if (sceneId < 0 || sceneId >= 30) return 0;
    return (unsigned char)g_byte_51E63[sceneId];
}

/* ========================================================================
 * funcs_1197B: 场景完成条件检查函数数组 (IDA 0x51B19)
 *
 * 原游戏: 30个函数指针数组，检查场景是否可以完成
 * 每个函数返回 1=完成, 0=未完成
 * ======================================================================== */

static int scene_0_check(void) {
    /* 场景0完成条件: 用户选择菜单项 */
    /* TODO: 检查对象状态、进度变量等 */
    return 0;
}

static int scene_1_check(void) {
    /* 场景1完成条件 */
    /* TODO: 检查对象状态、进度变量等 */
    return 0;
}

int scene_check_default(void) {
    /* 默认场景完成条件: 永远不完成 */
    return 0;
}

fd2_scene_check_fn funcs_1197B[30];

void fd2_scene_check_init(void) {
    funcs_1197B[0] = scene_0_check;
    funcs_1197B[1] = scene_1_check;

    /* 场景2-29使用默认检查 */
    for (int i = 2; i < 30; i++) {
        funcs_1197B[i] = scene_check_default;
    }
}

/* ========================================================================
 * 数据初始化和清理
 * ======================================================================== */

int fd2_data_init(void) {
    /* 初始化场景检查数组 */
    fd2_scene_check_init();

    /* TODO: 加载FD2.SAV存档数据
     * - 打开FD2.SAV
     * - 解密数据
     * - 解析场景数据
     */

    return 0;
}

void fd2_data_shutdown(void) {
    /* 释放资源指针 */
    if (g_FDOTHER_DAT__2) { free(g_FDOTHER_DAT__2); g_FDOTHER_DAT__2 = NULL; }
    if (g_FDOTHER_DAT__3) { free(g_FDOTHER_DAT__3); g_FDOTHER_DAT__3 = NULL; }
    if (g_FDOTHER_DAT__4) { free(g_FDOTHER_DAT__4); g_FDOTHER_DAT__4 = NULL; }
    if (g_FDOTHER_DAT__5) { free(g_FDOTHER_DAT__5); g_FDOTHER_DAT__5 = NULL; }
    if (g_FDOTHER_DAT__6) { free(g_FDOTHER_DAT__6); g_FDOTHER_DAT__6 = NULL; }
    if (g_FDOTHER_DAT__7) { free(g_FDOTHER_DAT__7); g_FDOTHER_DAT__7 = NULL; }
    if (g_FDOTHER_DAT__8) { free(g_FDOTHER_DAT__8); g_FDOTHER_DAT__8 = NULL; }
    if (g_FDOTHER_DAT__12) { free(g_FDOTHER_DAT__12); g_FDOTHER_DAT__12 = NULL; }
    if (g_FDOTHER_DAT__13) { free(g_FDOTHER_DAT__13); g_FDOTHER_DAT__13 = NULL; }

    if (g_FDTXT_DAT__0) { free(g_FDTXT_DAT__0); g_FDTXT_DAT__0 = NULL; }
    if (g_FDSHAP_DAT) { free(g_FDSHAP_DAT); g_FDSHAP_DAT = NULL; }
    if (g_FDFIELD_DAT__1) { free(g_FDFIELD_DAT__1); g_FDFIELD_DAT__1 = NULL; }
    if (g_FDICON_DAT) { free(g_FDICON_DAT); g_FDICON_DAT = NULL; }
}
