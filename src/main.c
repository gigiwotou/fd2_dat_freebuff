/**
 * FD2 Main Entry Point
 *
 * 使用三层状态机架构 (对应原游戏 main() 0x25BF4)
 * 原游戏核心流程:
 *   main() -> sub_111BA() 加载资源 -> sub_25EBB() 状态管理 -> sub_117E7() 输入处理
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define SDL_MAIN_HANDLED
#include "fd2_state_machine.h"
#include "fd2_globals.h"
#include "fd2_data_loader.h"
#include "fd2_opening_animation.h"

int main(int argc, char** argv) {
    /* 确定数据目录 */
    const char* data_dir = NULL;
    if (argc > 1) {
        data_dir = argv[1];
    } else {
        /* 默认使用game目录 */
        data_dir = "game";
    }

    printf("[DEBUG] Starting initialization...\n");

    /* 初始化SDL */
    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO | SDL_INIT_TIMER) < 0) {
        fprintf(stderr, "SDL_Init failed: %s\n", SDL_GetError());
        return 1;
    }
    printf("[DEBUG] SDL initialized\n");

    /* 初始化全局变量 */
    fd2_globals_init();
    printf("[DEBUG] Globals initialized\n");

    /* 初始化状态机 (对应原游戏 main() 初始化部分) */
    fd2_state_machine_t sm;
    if (fd2_state_machine_init(&sm) != 0) {
        fprintf(stderr, "Failed to initialize state machine\n");
        SDL_Quit();
        return 1;
    }
    printf("[DEBUG] State machine initialized\n");

    /* 加载资源 (对应原游戏 main() 中的sub_111BA调用序列) */
    if (fd2_data_load_all(&sm, data_dir) != 0) {
        fprintf(stderr, "Failed to load game data\n");
        fd2_state_machine_shutdown(&sm);
        SDL_Quit();
        return 1;
    }
    printf("[DEBUG] Resources loaded\n");

    /* 注册所有场景 */
    fd2_register_all_scenes(&sm);
    printf("[DEBUG] Scenes registered\n");

    /* 初始化场景检查系统 */
    fd2_scene_check_init();
    printf("[DEBUG] Scene checks initialized\n");

    printf("炎龙骑士团 2 - Starting (data: %s)\n", data_dir ? data_dir : ".");
    printf("Controls:\n");
    printf("  Arrows: Navigate    Enter/Space: Confirm\n");
    printf("  Tab: Subscene switch   ESC: Back/Quit\n");
    printf("  F11: Fullscreen\n");

    /* 运行状态机主循环 (对应原游戏 main() while(1) 循环) */
    /* 注意: 开场动画由 sub_25EBB() 内部调用 sub_1F894() 播放 */
    printf("[DEBUG] Starting state machine run...\n");
    int result = fd2_state_machine_run(&sm);
    printf("[DEBUG] State machine exited with result: %d\n", result);

    /* 清理 */
    fd2_data_shutdown();
    fd2_globals_shutdown();
    fd2_state_machine_shutdown(&sm);
    SDL_Quit();

    return result;
}
