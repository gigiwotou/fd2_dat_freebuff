/**
 * FD2 场景管理系统实现
 * 基于原游戏 (FD2.EXE) 的IDA反汇编代码1:1实现
 * 
 * 原游戏核心函数:
 * - sub_25EBB() 0x25EBB - 状态管理主函数
 * - sub_26152() 0x26152 - 场景主逻辑循环
 * - sub_22E5C() 0x22E5C - 场景初始化
 */

#include "fd2_scene_manager.h"
#include "fd2_globals.h"
#include "fd2_data_loader.h"
#include "fd2_render_pipeline.h"
#include "fd2_resources.h"
#include "fd2_icon_b24.h"
#include "fd2_render.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* 外部全局变量 */
extern char g_byte_523E7[30];
extern char g_byte_51E63[30];
extern int g_n5;
extern int g_n3_4;
extern int g_n17;
extern void* g_dword_53A45;
extern int g_dword_53BFB;
extern int g_dword_53BF7;
extern int g_dword_53A51;
extern void* g_dword_53A61;
extern int g_dword_53F56;
extern void* g_dword_53F5A;
extern void* g_dword_53F66;
extern int g_dword_53AE9;
extern int g_dword_53EEC;
extern int g_dword_53EC8;
extern int g_n3_3;
extern void* g_n7;
extern void* g_dword_53A55;

/* ========================================================================
 * 场景管理器初始化/清理
 * ======================================================================== */

int fd2_scene_manager_init(fd2_scene_manager_t* mgr, fd2_state_machine_t* sm) {
    if (!mgr || !sm) return -1;

    memset(mgr, 0, sizeof(*mgr));
    mgr->sm = sm;
    mgr->currentScene = 0;
    mgr->subSceneId = 0;
    mgr->selectedItem = 0;
    mgr->menuIndex = 0;
    mgr->animFrame = 0;
    mgr->n3_3 = 0;

    /* 分配场景数据缓冲区 (22987字节) */
    mgr->sceneDataBuffer = malloc(22987);
    if (!mgr->sceneDataBuffer) {
        fprintf(stderr, "fd2_scene_manager_init: Failed to allocate scene buffer\n");
        return -1;
    }
    memset(mgr->sceneDataBuffer, 255, 22987);

    printf("[SCENE] Manager initialized\n");
    return 0;
}

void fd2_scene_manager_shutdown(fd2_scene_manager_t* mgr) {
    if (!mgr) return;

    if (mgr->sceneDataBuffer) {
        free(mgr->sceneDataBuffer);
        mgr->sceneDataBuffer = NULL;
    }

    printf("[SCENE] Manager shutdown\n");
}

/* ========================================================================
 * FD2.SAV 存档加载 (对应原游戏 sub_25EBB 中的加载逻辑)
 *
 * 原游戏逻辑:
 *   v14 = malloc(22987);
 *   _rb_ = fopen("FD2.SAV", "rb");
 *   if (_rb_) {
 *     sub_373CA(v12, 1u, 22987, _rb_);
 *     sub_4DF28(v12, 22987);  // 解密/处理
 *     fclose(_rb_);
 *   } else {
 *     memset(v12, 255, 22987);  // 无存档时填充255
 *   }
 * ======================================================================== */

int fd2_load_save_data(fd2_scene_manager_t* mgr, const char* filename) {
    if (!mgr) return -1;

    /* 尝试打开FD2.SAV */
    FILE* fp = fopen(filename ? filename : "FD2.SAV", "rb");
    if (fp) {
        /* 读取22987字节存档数据 */
        size_t read = fread(mgr->sceneDataBuffer, 1, 22987, fp);
        fclose(fp);

        if (read == 22987) {
            printf("[SCENE] Loaded FD2.SAV (%zu bytes)\n", read);
            /* TODO: sub_4DF28() - 可能需要解密处理 */
            return 0;
        } else {
            fprintf(stderr, "[SCENE] FD2.SAV read failed (%zu/22987 bytes)\n", read);
        }
    } else {
        printf("[SCENE] No FD2.SAV found, using default data\n");
    }

    /* 无存档或读取失败时填充255 */
    memset(mgr->sceneDataBuffer, 255, 22987);
    return -1;
}

/* ========================================================================
 * sub_25EBB: 状态管理主函数 (原游戏 0x25EBB, 大小0x297)
 *
 * 原游戏逻辑 (1:1 复制):
 *   1. sub_1F894() - 播放开场动画
 *   2. 根据返回值判断状态:
 *      - v8 == 0: 初始化场景 (状态0)
 *        - n17 = 0
 *        - 加载FDOTHER.DAT索引0
 *        - 调用funcs_25E3A[n17]()
 *        - 播放场景音乐
 *        - byte_51AAC = 1
 *        - sub_4E381()
 *      
 *      - v8 != 0 && v8 != 1: 其他状态
 *        - 停止音乐
 *        - sub_10010() - 存档相关
 *        - 播放场景音乐
 *      
 *      - v8 == 1: 主游戏场景 (状态1)
 *        - 加载FDOTHER.DAT索引13
 *        - 清空屏幕
 *        - 设置调色板 (黑色)
 *        - 加载FD2.SAV (22987字节)
 *        - 循环处理存档场景:
 *          - sub_29BCB() - 获取场景
 *          - 解析场景数据 (2600字节/场景)
 *          - 更新n17, dword_53BFB等变量
 *        - 如果v16 == 1:
 *          - byte_51AAC = 0
 *          - sub_26152() - 场景主逻辑
 *          - 如果返回0: 调用funcs_25E3A[n17]()
 *          - byte_51AAC = 1
 *        - sub_4E381()
 *        - 返回v16
 *
 * 参数:
 *   mgr - 场景管理器
 *   state - 状态 (0=初始化, 1=主游戏)
 *
 * 返回:
 *   场景处理结果
 * ======================================================================== */

int fd2_state_management(fd2_scene_manager_t* mgr, int state) {
    if (!mgr) return -1;

    printf("[SCENE] State management called, state=%d\n", state);

    /* 1. 开场动画已在main()中调用，这里跳过 */
    
    if (state == 0) {
        /* 状态0: 初始化场景 */
        printf("[SCENE] Initializing scene 0...\n");

        g_n17 = 0;
        mgr->currentScene = 0;

        /* 加载FDOTHER.DAT索引0 */
        fd2_resources_t* res = fd2_get_resources();
        if (res) {
            u32 s0_size = 0;
            const u8* fdother_0 = fd2_resources_get(res, FD2_DAT_FDOTHER, 0, &s0_size);
            if (fdother_0) {
                /* TODO: 存储到FDOTHER_DAT */
            }
        }

        /* 调用funcs_25E3A[n17]() - 场景初始化 */
        /* TODO: 实现场景初始化函数数组 */

        /* 播放场景音乐 */
        /* TODO: sub_25977(byte_51E63[n17], ...) */

        g_byte_51AAC = 1;

        /* 刷新屏幕 */
        fd2_render_fill_screen(&mgr->sm->render, 0);
        fd2_render_present(&mgr->sm->render);

        return 0;

    } else if (state == 1) {
        /* 状态1: 主游戏场景 */
        printf("[SCENE] Loading main game scene...\n");

        /* 加载FDOTHER.DAT索引13 */
        fd2_resources_t* res = fd2_get_resources();
        if (res) {
            u32 s13_size = 0;
            const u8* fdother_13 = fd2_resources_get(res, FD2_DAT_FDOTHER, 13, &s13_size);
            if (fdother_13) {
                /* TODO: 存储到dword_53F66 */
            }
        }

        /* 清空屏幕 */
        fd2_render_fill_screen(&mgr->sm->render, 0);

        /* 设置调色板 (黑色) */
        /* TODO: sub_11D40(..., 0, 255, 0) */

        /* 加载FD2.SAV */
        fd2_load_save_data(mgr, NULL);

        /* 解析存档场景数据 */
        mgr->n3_3 = 0;
        int sceneResult = 0;

        do {
            /* sub_29BCB() - 获取场景索引 */
            /* TODO: 实现场景解析 */
            
            if (sceneResult != -1) {
                /* 解析场景数据 (2600字节/场景) */
                u8* scenePtr = (u8*)mgr->sceneDataBuffer + 12587 + 2600 * mgr->n3_3;

                /* 拷贝2560字节到当前场景数据 */
                mgr->currentSceneData = scenePtr;

                /* 解析场景头 */
                mgr->currentScene = scenePtr[2560 + 0];  /* n17 */
                mgr->subSceneId = scenePtr[2560 + 1];    /* dword_53BFB */
                mgr->someValue = *(u32*)(scenePtr + 2560 + 2);
                mgr->flag1 = scenePtr[2560 + 6];
                mgr->flag2 = scenePtr[2560 + 7];
                mgr->n127 = scenePtr[2560 + 8];
                mgr->flag3 = scenePtr[2560 + 9];

                if (mgr->currentScene == 255) {
                    sceneResult = 0;
                }
            }

            /* TODO: sub_26996() */

        } while (!sceneResult);

        /* 如果场景加载成功 */
        if (sceneResult == 1) {
            g_byte_51AAC = 0;

            /* 调用sub_26152() - 场景主逻辑 */
            bool loopResult = fd2_scene_main_loop(mgr);

            if (!loopResult) {
                /* 调用funcs_25E3A[n17]() - 场景清理 */
                /* TODO: 实现场景清理函数 */
            }

            g_byte_51AAC = 1;
        }

        /* 刷新屏幕 */
        fd2_render_present(&mgr->sm->render);

        return sceneResult;

    } else {
        /* 其他状态 */
        printf("[SCENE] Unknown state %d\n", state);

        /* 停止音乐 */
        /* TODO: sub_25977(state, ..., -1, 0) */

        /* sub_10010() - 存档相关 */
        /* TODO: 实现存档功能 */

        /* 播放场景音乐 */
        /* TODO: sub_25977(byte_51E63[n17], ...) */

        return 0;
    }
}

/* ========================================================================
 * sub_26152: 场景主逻辑循环 (原游戏 0x26152, 大小0x49A)
 *
 * 原游戏逻辑 (1:1 复制):
 *   1. 释放旧数据 (dword_53A45, dword_53A55, n7, dword_53A51, dword_53A61)
 *   2. 打开FDICON.B24文件
 *   3. 循环加载图标:
 *      - for (i=0; i < dword_53BFB; ++i)
 *        - sub_11019(...)
 *   4. 关闭FDICON.B24
 *   5. 如果byte_523E7[n17]非零:
 *      - 特殊场景处理
 *      - sub_1956B()
 *      - sub_15F84() - 文本渲染
 *      - sub_19953() - 渲染管线
 *      - 返回0
 *   6. 否则: 正常场景
 *      - n7 = malloc(153216)
 *      - sub_4E809(n17) - 获取场景图形
 *      - sub_1F882() - 音效控制
 *      - sub_25977(10, 0) - 播放音乐10
 *      - 加载FDOTHER.DAT索引i
 *      - sub_4E98D() - 渲染图像到n7+32904
 *      - 加载FDOTHER.DAT索引10
 *      - sub_265EC() - 场景特效
 *      - sub_1F525() - 淡入效果
 *      - 主循环:
 *        - sub_265EC() - 更新特效
 *        - 检查DOS定时器 (每4个滴答更新动画)
 *        - 如果sub_10620()非零: 检查键盘输入
 *          - int386(22) - 获取按键
 *          - 根据扫描码处理:
 *            - 0xE0/0x52: 转换为28 (回车)
 *            - 0x22: n16++, 切换音乐
 *            - 0x4D: 右键, n5--
 *            - 0x4B: 左键, n5++
 *            - 28/32: 确认键
 *              - 如果n5 != 2: sub_25A96(..., 1, 3)
 *              - v26 = sub_2670E() - 场景特效
 *        - while (!v26)
 *      - 释放dword_53F5A
 *      - 返回n5 != 2
 *
 * 参数:
 *   mgr - 场景管理器
 *
 * 返回:
 *   true=继续, false=退出场景
 * ======================================================================== */

bool fd2_scene_main_loop(fd2_scene_manager_t* mgr) {
    if (!mgr) return false;

    printf("[SCENE] Main loop starting for scene %d\n", mgr->currentScene);

    /* 1. 释放旧数据 */
    if (g_dword_53A45) { free(g_dword_53A45); g_dword_53A45 = NULL; }
    if (g_dword_53A55) { free(g_dword_53A55); g_dword_53A55 = NULL; }
    if (g_n7) { free(g_n7); g_n7 = NULL; }

    /* 2. 初始化图标系统 */
    /* TODO: fd2_icon_init() */

    /* 检查特殊场景标志 */
    if (g_byte_523E7[mgr->currentScene]) {
        printf("[SCENE] Special scene %d detected\n", mgr->currentScene);

        /* 特殊场景处理 */
        fd2_render_fill_screen(&mgr->sm->render, 0);

        /* TODO: sub_1956B(75) */
        /* TODO: sub_15F84(...) - 文本渲染 */
        /* TODO: sub_19953(...) - 渲染管线 */

        return false;
    }

    /* 4. 正常场景处理 */
    /* 分配图形缓冲区 (153216字节) */
    g_n7 = malloc(153216);
    if (!g_n7) {
        fprintf(stderr, "[SCENE] Failed to allocate graphics buffer\n");
        return false;
    }

    /* TODO: sub_4E809(n17) - 获取场景图形数据 */
    /* TODO: sub_1F882() - 音效控制 */

    /* 播放场景音乐 (轨道10) */
    /* TODO: sub_25977(10, 0) */

    /* 加载场景图像 */
    fd2_resources_t* res = fd2_get_resources();
    if (res) {
        /* TODO: 加载FDOTHER.DAT场景图像 */
        /* TODO: sub_4E98D() - 渲染到n7+32904 */
    }

    /* TODO: sub_265EC() - 场景特效 */
    /* TODO: sub_1F525() - 淡入效果 */

    /* 主循环 */
    u8 v26 = 0;
    Uint32 last_tick = SDL_GetTicks();
    u8 n16 = 0;

    do {
        /* 更新场景特效 */
        /* TODO: sub_265EC() */

        /* 检查DOS定时器 (每4个滴答~220ms更新动画帧) */
        Uint32 current_tick = SDL_GetTicks();
        if (current_tick - last_tick >= 220) {
            last_tick = current_tick;

            /* 更新动画帧 (0-3循环) */
            g_n3_4++;
            if (g_n3_4 >= 4) g_n3_4 = 0;

            /* TODO: sub_265EC() */
        }

        /* 处理SDL事件和键盘输入 */
        SDL_Event event;
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_QUIT) {
                mgr->sm->running = 0;
                v26 = 1;
                break;
            }

            if (event.type == SDL_KEYDOWN && !event.key.repeat) {
                int scan = event.key.keysym.scancode;

                /* 根据原游戏扫描码映射 */
                switch (scan) {
                    case SDL_SCANCODE_ESCAPE:
                    case SDL_SCANCODE_DELETE:
                        mgr->sm->running = 0;
                        v26 = 1;
                        break;

                    case SDL_SCANCODE_TAB:
                        /* 0x22 - 切换音乐 */
                        n16++;
                        if (n16 == 10) n16 = 0;
                        /* TODO: sub_25977(n16, 34, ...) */
                        break;

                    case SDL_SCANCODE_RIGHT:
                        /* 0x4D - 右键 */
                        /* TODO: sub_25A96(..., 77, ...) */
                        if (--mgr->menuIndex < 0) mgr->menuIndex = 5;
                        break;

                    case SDL_SCANCODE_LEFT:
                        /* 0x4B - 左键 */
                        /* TODO: sub_25A96(..., 75, ...) */
                        if (++mgr->menuIndex > 5) mgr->menuIndex = 0;
                        break;

                    case SDL_SCANCODE_RETURN:
                    case SDL_SCANCODE_SPACE:
                        /* 28/32 - 确认键 */
                        if (mgr->menuIndex != 2) {
                            /* TODO: sub_25A96(..., 1, 3) */
                        }
                        v26 = 1;  /* sub_2670E() 返回值 */
                        break;

                    case SDL_SCANCODE_UP:
                        /* 0x48 - 上键 */
                        /* TODO: sub_25A96(..., 0, 1), sub_11B48() */
                        break;

                    case SDL_SCANCODE_DOWN:
                        /* 0x50 - 下键 */
                        /* TODO: sub_25A96(..., 0, 1), sub_11B9B() */
                        break;

                    default:
                        break;
                }
            }
        }

        /* 渲染场景 */
        fd2_render_scene(mgr);

        SDL_Delay(16);  /* ~60fps */

    } while (!v26);

    /* 清理 */
    if (g_dword_53F5A) {
        free(g_dword_53F5A);
        g_dword_53F5A = NULL;
    }

    printf("[SCENE] Main loop exited, menuIndex=%d\n", mgr->menuIndex);

    /* 返回n5 != 2 */
    return (mgr->menuIndex != 2);
}

/* ========================================================================
 * sub_22E5C: 场景初始化 (原游戏 0x22E5C, 大小未知)
 *
 * 原游戏逻辑 (1:1 复制):
 *   1. sub_25977(-1, 1) - 停止音乐
 *   2. sub_17AA9(..., 1) - 子精灵处理
 *   3. sub_1F882() - 音效控制
 *   4. _FDOTHER.DAT_ = sub_111BA(..., FDOTHER.DAT, 79)
 *   5. memset(655360, 0, 64000) - 清空屏幕
 *   6. sub_2EB9F(_FDOTHER.DAT_, 0, 655360, 320, -1) - 渲染图像
 *   7. sub_1F525() - 淡入效果
 *   8. sub_17AA9(..., 9) - 子精灵处理
 *   9. sub_2EB9F(_FDOTHER.DAT_, 1, 655360, 320, -1) - 渲染图像
 *   10. sub_17AA9(..., 36) - 子精灵处理
 *   11. 跳转0x15E94
 *
 * 参数:
 *   mgr - 场景管理器
 * ======================================================================== */

void fd2_scene_initialize(fd2_scene_manager_t* mgr) {
    if (!mgr) return;

    printf("[SCENE] Initializing scene...\n");

    /* 1. 停止音乐 */
    /* TODO: sub_25977(-1, 1) */

    /* 2. 子精灵处理 */
    /* TODO: sub_17AA9(..., 1) */

    /* 3. 音效控制 */
    /* TODO: sub_1F882() */

    /* 4. 加载FDOTHER.DAT索引79 */
    fd2_resources_t* res = fd2_get_resources();
    if (res) {
        u32 s79_size = 0;
        const u8* fdother_79 = fd2_resources_get(res, FD2_DAT_FDOTHER, 79, &s79_size);
        if (fdother_79) {
            /* TODO: 存储到临时变量 */

            /* 5. 清空屏幕 */
            fd2_render_fill_screen(&mgr->sm->render, 0);

            /* 6. 渲染图像 */
            /* TODO: sub_2EB9F(fdother_79, 0, 655360, 320, -1) */

            /* 7. 淡入效果 */
            /* TODO: sub_1F525() */

            /* 8. 子精灵处理 */
            /* TODO: sub_17AA9(..., 9) */

            /* 9. 渲染图像 */
            /* TODO: sub_2EB9F(fdother_79, 1, 655360, 320, -1) */

            /* 10. 子精灵处理 */
            /* TODO: sub_17AA9(..., 36) */

            /* 11. 刷新屏幕 */
            fd2_render_present(&mgr->sm->render);
        }
    }

    printf("[SCENE] Scene initialization complete\n");
}

/* ========================================================================
 * 场景渲染
 * ======================================================================== */

void fd2_render_scene(fd2_scene_manager_t* mgr) {
    if (!mgr || !mgr->sm) return;

    /* 填充基础颜色 */
    fd2_render_fill_screen(&mgr->sm->render, 0);

    /* TODO: 根据场景ID和菜单索引渲染UI元素 */
    /* TODO: sub_25A96() - 渲染光标 */
    /* TODO: sub_15F84() - 渲染文本 */

    /* 刷新屏幕 */
    fd2_render_present(&mgr->sm->render);
}

/* ========================================================================
 * 场景切换
 * ======================================================================== */

void fd2_scene_manager_switch(fd2_scene_manager_t* mgr, int sceneId) {
    if (!mgr) return;

    printf("[SCENE] Switching to scene %d\n", sceneId);

    mgr->currentScene = sceneId;
    g_n17 = sceneId;

    /* TODO: 调用funcs_25E3A[sceneId]() */
}

/* ========================================================================
 * 场景条目处理
 * ======================================================================== */

int fd2_process_scene_item(fd2_scene_manager_t* mgr, int itemIndex) {
    if (!mgr || !mgr->sceneItems) return -1;

    /* 获取场景条目 (80字节/条目) */
    u8* item = mgr->sceneItems + 80 * itemIndex;

    /* 检查条目状态 */
    u8 flags = item[5];
    u8 type = item[6];

    if ((flags & 0x85) == 0 && type == 2) {
        /* 可交互条目 */
        printf("[SCENE] Processing interactive item %d\n", itemIndex);

        /* TODO: sub_12D7B(itemIndex) */
        /* TODO: sub_17AED(itemIndex, ...) */

        mgr->selectedItem = itemIndex + 1;
        if (mgr->selectedItem == mgr->sceneItemCount) {
            mgr->selectedItem = 0;
        }

        return 1;
    }

    return 0;
}
