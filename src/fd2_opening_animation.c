/**
 * FD2 开场动画系统
 * 对应原游戏 sub_1F894 (地址: 0x1F894)
 * 
 * 原游戏启动时调用此函数播放开场动画序列
 */

#include "fd2_opening_animation.h"
#include "fd2_afm.h"
#include "fd2_globals.h"
#include "fd2_render.h"
#include "fd2_resources.h"
#include "fd2_data_loader.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <string.h>

/* ========================================================================
 * sub_1F894: 开场动画播放函数 (原游戏 0x1F894)
 *
 * 原游戏逻辑 (1:1 复制):
 *   1. sub_3702F(..., 136) - 初始化
 *   2. _FDOTHER.DAT_ = sub_111BA(..., FDOTHER.DAT, 77) - 加载FDOTHER索引77
 *   3. memset(655360, 0, 64000) - 清空屏幕
 *   4. FDOTHER_DAT = sub_111BA(..., FDOTHER.DAT, 76) - 加载FDOTHER索引76
 *   5. sub_11D40(FDOTHER_DAT, 0, 255, 64) - 设置调色板 (偏移64)
 *   6. _FDOTHER.DAT__1 = sub_111BA(..., FDOTHER.DAT, 74) - 加载FDOTHER索引74
 *   7. sub_4E98D(_FDOTHER.DAT__1, 0, 0, 655360, 320, -1) - 渲染图像
 *   8. sub_1F525() - 淡入效果
 *   9. sub_17AA9(..., 1) / sub_17AA9(..., 30) - 子精灵渲染
 *   10. sub_1F882() - 音效/音乐控制
 *   11. FDOTHER_DAT = sub_111BA(..., FDOTHER.DAT, 99) - 加载FDOTHER索引99
 *   12. memset(655360, 0, 64000) - 清空屏幕
 *   13. sub_11D40(..., 0, 255, 0) - 设置调色板 (黑色)
 *   14. sub_20421(3, 90, 1) - 播放AFM动画索引3, 延迟90ms
 *   15. sub_1F882() - 音效控制
 *   16. memset(655360, 0, 64000) - 清空屏幕
 *   17. FDOTHER_DAT = sub_111BA(..., FDOTHER.DAT, 101) - 加载FDOTHER索引101
 *   18. sub_11D40(..., 0, 255, 64) - 设置调色板 (偏移64)
 *   19. 加载FDOTHER索引69-73 (5个图像) 到缓冲区
 *   20. sub_4E98D 渲染这些图像
 *   21. sub_4E381() - 刷新屏幕
 *   22. 动画循环 (n535从535递减到0)
 *   23. 淡入淡出效果 (sub_2DF01)
 *   24. 等待按键选择菜单项
 *
 * 参数:
 *   sm - 状态机
 *
 * 返回: 0=正常播放完成, 1=用户中断
 * ======================================================================== */
int fd2_play_opening_animation(fd2_state_machine_t* sm) {
    if (!sm) return -1;

    printf("[OPENING] Starting opening animation sequence...\n");

    /* 简化实现: 播放AFM动画索引1 (开场动画) */
    /* 原游戏使用更复杂的sub_1F894逻辑，这里先用AFM播放器实现核心功能 */

    /* 1. 填充黑色屏幕 */
    fd2_render_fill_screen(&sm->render, 0);
    fd2_render_present(&sm->render);
    SDL_Delay(500);

    /* 2. 尝试播放AFM动画 (索引1是开场动画) */
    fd2_resources_t* res = fd2_get_resources();
    int result = fd2_afm_play(1, 90, 1, &sm->render, res);

    if (result == 1) {
        printf("[OPENING] Animation interrupted by user\n");
    } else if (result == 0) {
        printf("[OPENING] Animation completed normally\n");
    } else {
        printf("[OPENING] Animation failed (result=%d)\n", result);
        /* 如果动画失败，至少显示黑屏过渡 */
        fd2_render_fill_screen(&sm->render, 0);
        fd2_render_present(&sm->render);
        SDL_Delay(1000);
    }

    /* 3. 淡出到黑色 */
    fd2_render_fade_to_black(&sm->render, 20, 50);

    return result;
}
