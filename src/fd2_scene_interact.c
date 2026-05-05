#include "fd2_scene_interact.h"
#include "fd2_globals.h"
#include "fd2_data_loader.h"
#include "fd2_decoder.h"
#include "fd2_input.h"
#include "fd2_render.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* 局部变量 */
static unsigned char local_n16_1 = 0;  /* 子场景索引 */
static int local_v21 = 0;              /* 退出标志 */

/*
 * 释放旧场景资源 (对应原游戏 sub_26152 开头部分)
 * 
 * 原游戏代码:
 * if (n8_1) free(n8_1); n8_1 = 0;
 * if (FDFIELD_DAT__1) free(FDFIELD_DAT__1); FDFIELD_DAT__1 = 0;
 * if (FDSHAP_DAT) free(FDSHAP_DAT); FDSHAP_DAT = 0;
 * if (FDFIELD_DAT__0) free(FDFIELD_DAT__0); FDFIELD_DAT__0 = 0;
 * if (dword_53A61) free(dword_53A61);
 */
void fd2_scene_release_old_resources(void) {
    /* 释放场景备份缓冲区 */
    if (g_n8_1) {
        free(g_n8_1);
    }
    g_n8_1 = 0;

    /* 释放场景数据 */
    if (g_FDFIELD_DAT__1) {
        free(g_FDFIELD_DAT__1);
    }
    g_FDFIELD_DAT__1 = 0;

    /* 释放形状数据 */
    if (g_FDSHAP_DAT) {
        free(g_FDSHAP_DAT);
    }
    g_FDSHAP_DAT = 0;

    /* TODO: 释放dword_53A61 (原游戏: if (dword_53A61) free(dword_53A61)) */
}

/*
 * 加载场景图标 (对应原游戏 sub_11019循环)
 * 
 * 原游戏代码:
 * _rb_1 = fopen("fdicon.b24", "rb");
 * for (n16 = 0; n16 < ::n16_1; ++n16) {
 *     sub_11019(*(unsigned __int8 *)(n8_3 + 80 * n16 + 7), ..., n8_3, ..., _rb_);
 * }
 * fclose(_rb_);
 */
int fd2_scene_load_icons(void) {
    FILE* fp;
    int n16;

    /* 打开fdicon.b24文件 */
    fp = fopen("fdicon.b24", "rb");
    if (!fp) {
        fprintf(stderr, "fd2_scene_load_icons: cannot open fdicon.b24\n");
        return -1;
    }

    /* 循环加载图标 */
    for (n16 = 0; n16 < g_n16_1; ++n16) {
        /* 获取图标索引: n8_3 + 80 * n16 + 7 */
        unsigned char icon_index = ((unsigned char*)g_n8_3)[80 * n16 + 7];
        (void)icon_index;  /* 用于后续sub_11019调用 */

        /* TODO: 调用sub_11019加载图标
         * sub_11019(icon_index, fp, n16, g_n8_3, icon_index, fp);
         */
    }

    fclose(fp);
    return 0;
}

/*
 * 加载场景图形 (对应原游戏 sub_26152 非特殊场景部分)
 * 
 * 原游戏代码:
 * FDSHAP_DAT = malloc(153216);
 * dword_53F56 = (int)sub_4E809(n17);
 * sub_1F882(dword_53F56, ..., n16, n8);
 * sub_25977(..., 10, 0);
 * n5 = 0;
 * FDOTHER_DAT__12 = sub_111BA(..., "FDOTHER.DAT", ..., 10);
 * sub_4E98D(FDOTHER_DAT__12, 0, 0, FDSHAP_DAT + 32904, 456, -1);
 * free(FDOTHER_DAT__12);
 * sub_265EC(&v20);
 */
int fd2_scene_load_graphics(void) {
    /* 分配形状数据缓冲区 (153216字节) */
    g_FDSHAP_DAT = malloc(153216);
    if (!g_FDSHAP_DAT) {
        fprintf(stderr, "fd2_scene_load_graphics: out of memory\n");
        return -1;
    }

    /* TODO: 调用sub_4E809加载场景数据
     * dword_53F56 = (int)sub_4E809(g_n17);
     */

    /* TODO: 调用sub_1F882处理场景数据 */

    /* 调用sub_25977切换音乐 (索引10) */
    fd2_music_switch(10, 0);

    /* 初始化菜单索引 */
    g_n5 = 0;

    /* 加载FDOTHER.DAT索引10 */
    g_FDOTHER_DAT__12 = fd2_dat_load_resource(
        "FDOTHER.DAT", 
        0, 
        10
    );
    if (!g_FDOTHER_DAT__12) {
        fprintf(stderr, "fd2_scene_load_graphics: failed to load FDOTHER.DAT index 10\n");
        return -1;
    }

    /* 调用sub_4E98D解压到FDSHAP_DAT + 32904 (456字节行跨度) */
    fd2_rle_decompress_to_buffer(
        (const u8*)g_FDOTHER_DAT__12,
        g_dword_53BFF,
        (u8*)g_FDSHAP_DAT + 32904,
        0,
        456,
        -1  /* palette_offset */
    );

    /* 释放临时数据 */
    free(g_FDOTHER_DAT__12);
    g_FDOTHER_DAT__12 = 0;

    return 0;
}

/*
 * 场景渲染更新 (对应原游戏 sub_265EC)
 * 
 * 原游戏反编译代码:
 * int __usercall sub_265EC@<eax>(unsigned __int8 *a1@<edi>, __int32 a2@<eax>, int a3@<edx>, int a4@<ecx>, int a5@<ebx>)
 * {
 *   sub_3702F(a2, a3, a5, a4, 52);
 *   v10 = *sub_4E809(n17);
 *   v5 = memmove(n655360, FDSHAP_DAT, 153216);
 *   sub_4EBFF((_BYTE *)(n655360 + 107020), (__int16 *)FDOTHER_DAT__12, 456);
 *   sub_15F84(a1, n5 + 495, SHIDWORD(v5), a4, a5, FDTXT_DAT__0, n5 + 495, n655360 + 109764, 456, 205, 76, 74, 19, 0);
 *   n3 = n3_4;
 *   if ( n3_4 == 3 ) n3 = 1;
 *   v7 = n655360 + 32904;
 *   dst = (char *)(456 * (unsigned __int8)byte_52375[6 * v10 + n5] + n655360 + 32904 + (unsigned __int8)byte_52363[6 * v10 + n5]);
 *   sub_4E22A((char *)(dword_53A61 + *(_DWORD *)(dword_53A61 + 4 * n3)), dst, 456);
 *   return sub_11EB0(n655360 + 32904, (int)dst, v7, a4, 656644, 320, n655360 + 32904, 456, 312, 192);
 * }
 */
void fd2_scene_render_update(void* v20) {
    unsigned char scene_type;
    
    (void)v20;

    /* 1. 获取场景类型: v10 = *sub_4E809(n17) */
    /* TODO: sub_4E809返回场景数据指针，解引用获取场景类型 */
    scene_type = 0;  /* 暂时默认 */
    (void)scene_type;

    /* 2. 复制FDSHAP_DAT到后备缓冲区 (153216字节) */
    if (g_FDSHAP_DAT && g_n655360_0) {
        memcpy(g_n655360_0, g_FDSHAP_DAT, 153216);
    }

    /* 3. 渲染FDOTHER_DAT__12图形数据到 n655360 + 107020 */
    /* TODO: sub_4EBFF((_BYTE *)(n655360 + 107020), (__int16 *)FDOTHER_DAT__12, 456) */

    /* 4. 渲染文本 (n5 + 495) */
    /* TODO: sub_15F84(a1, n5 + 495, ..., FDTXT_DAT__0, n5 + 495, n655360 + 109764, 456, 205, 76, 74, 19, 0) */

    /* 5. 计算光标帧 */
    /* TODO: 使用g_n3_4计算光标动画帧 */

    /* 6. 计算光标位置 */
    /* TODO: dst = 456 * byte_52375[6 * scene_type + n5] + n655360 + 32904 + byte_52363[6 * scene_type + n5] */

    /* 7. 复制光标图像 */
    /* TODO: sub_4E22A(dword_53A61 + *(dword_53A61 + 4 * cursor_frame), cursor_dst, 456) */

    /* 8. 执行屏幕区域更新 */
    /* TODO: sub_11EB0(n655360 + 32904, cursor_dst, ..., 656644, 320, ..., 456, 312, 192) */
}

/*
 * 场景特效和选择执行 (对应原游戏 sub_2670E)
 * 
 * 原游戏反编译代码:
 * void __usercall sub_2670E(unsigned __int8 *a1@<edi>, __int32 a2@<eax>, int a3@<edx>, int a4@<ecx>, int a5@<ebx>)
 * {
 *   sub_3702F(a2, a3, a5, a4, 60);
 *   v6 = sub_4E809(n17);
 *   LOBYTE(v6) = *v6;
 *   v15 = (unsigned __int8)v6;
 *   sub_25977(v6, a3, a5, a4, -1, 0);
 *   if ( n5 == 2 ) {
 *     v7 = sub_1956B(75);
 *     sub_15F84(a1, v7, a3, a4, a5, FDTXT_DAT__0, 513, 693535, 320, 205, 76, 74, 19, 1);
 *     FDFIELD_DAT__0 = 1;
 *     v8 = sub_16559(0);
 *     sub_19953(v8, a3, a5, a4);
 *     v10 = v9;
 *     sub_197E5();
 *     FDFIELD_DAT__0 = 0;
 *     sub_26996();
 *     if ( v10 == -1 || n4_1 ) goto LABEL_23;
 *     if ( n17 < 27 && n16_1 > 16 || n17 > 26 && n16_1 > 20 ) {
 *       n8_1 = n8_3;
 *       v11 = sub_2AF28();
 *       n8_1 = 0;
 *       if ( !v11 ) goto LABEL_23;
 *     }
 *   }
 *   n8_1 = n8_3;
 *   n3 = malloc(64000);
 *   v13 = memmove(n3, 655360, 64000);
 *   for ( n10 = 1; n10 <= 10; ++n10 ) {
 *     a4 = 6 * v15 + n5;
 *     sub_2921A(
 *       ((n10 * (byte_52363[a4] - 150) / 10) << 7) + 20480,
 *       ((n10 * (byte_52375[a4] - 100) / 10) << 7) + 12800,
 *       (int)n3,
 *       128 - 9 * n10);
 *     v13 = memmove(655360, n655360, 64000);
 *     sub_11D40(4 * n10, SHIDWORD(v13), n10, a4, 0, 255, 4 * n10);
 *   }
 *   sub_11D40(v13, SHIDWORD(v13), n10, a4, 0, 255, 64);
 *   memset(n10, 655360, 0, 64000);
 *   if ( n5 ) {
 *     if ( n5 == 4 ) {
 *       sub_25977(v13, SHIDWORD(v13), n10, a4, 11, 0);
 *       sub_29DAA(n3);
 *     } else {
 *       if ( n5 == 2 ) {
 *         free(n3);
 *         n8_1 = 0;
 *         goto LABEL_23;
 *       }
 *       if ( n5 == 3 )
 *         sub_25977(v13, SHIDWORD(v13), n10, a4, 15, 0);
 *       else
 *         sub_25977(v13, SHIDWORD(v13), n10, a4, 14, 0);
 *       sub_279BC((int)n3);
 *     }
 *   } else {
 *     sub_25977(v13, SHIDWORD(v13), n10, a4, 13, 0);
 *     sub_29300(n3);
 *   }
 *   sub_25977(v13, SHIDWORD(v13), n10, a4, 10, 0);
 *   free(n3);
 *   n8_1 = 0;
 * }
 */
void fd2_scene_execute_selection(int a5, void* v20) {
    unsigned char scene_type;
    void* effect_buffer;
    int n10;
    
    (void)a5;
    (void)v20;

    /* 1. 获取场景类型 */
    /* TODO: scene_type = *sub_4E809(n17) */
    scene_type = 0;
    (void)scene_type;

    /* 2. 如果是"返回"选项 (n5 == 2) */
    if (g_n5 == 2) {
        /* TODO: sub_1956B(75) - 获取文本索引 */
        /* TODO: sub_15F84渲染文本 */
        /* TODO: FDFIELD_DAT__0 = 1 */
        /* TODO: sub_16559(0) - 进入子状态机 */
        /* TODO: sub_19953 - 主渲染循环 */
        /* TODO: sub_197E5() */
        /* TODO: FDFIELD_DAT__0 = 0 */
        /* TODO: sub_26996() */
        
        /* 检查退出条件 */
        /* TODO: if (v10 == -1 || n4_1) goto LABEL_23 */
        
        /* 检查特殊场景条件 */
        /* TODO: if (n17 < 27 && n16_1 > 16 || n17 > 26 && n16_1 > 20) */
        /* TODO:   n8_1 = n8_3; sub_2AF28(); n8_1 = 0; */
    }

    /* 3. 分配特效缓冲区 (64000字节) */
    effect_buffer = malloc(64000);
    if (!effect_buffer) {
        fprintf(stderr, "fd2_scene_execute_selection: out of memory\n");
        return;
    }

    /* 4. 复制后备缓冲区到特效缓冲区 */
    if (g_n655360_0) {
        memcpy(effect_buffer, g_n655360_0, 64000);
    }

    /* 5. 特效动画循环 (n10 = 1 到 10) */
    for (n10 = 1; n10 <= 10; ++n10) {
        /* TODO: 计算特效坐标并使用sub_2921A */
        /* TODO: effect_x = ((n10 * (g_byte_52363[calc_index] - 150) / 10) << 7) + 20480 */
        /* TODO: effect_y = ((n10 * (g_byte_52375[calc_index] - 100) / 10) << 7) + 12800 */
        /* TODO: sub_2921A(effect_x, effect_y, (int)effect_buffer, 128 - 9 * n10) */
        
        /* 复制后备缓冲区到显示缓冲区 */
        /* TODO: memcpy(显示缓冲区, g_n655360_0, 64000) */
        
        /* TODO: sub_11D40(4 * n10, ..., n10, calc_index, 0, 255, 4 * n10) */
    }

    /* 6. 最终效果 */
    /* TODO: sub_11D40(..., 64) */

    /* 7. 清空显示缓冲区 */
    if (g_n655360_0) {
        memset(g_n655360_0, 0, 64000);
    }

    /* 8. 根据菜单索引执行不同特效 */
    if (g_n5 == 0) {
        /* TODO: sub_25977(..., 13, 0) */
        /* TODO: sub_29300(effect_buffer) */
    } else if (g_n5 == 2) {
        /* 返回选项 - 清理并退出 */
        free(effect_buffer);
        g_n8_1 = 0;
        local_v21 = 1;
        return;
    } else if (g_n5 == 3) {
        /* TODO: sub_25977(..., 15, 0) */
        /* TODO: sub_279BC((int)effect_buffer) */
    } else if (g_n5 == 4) {
        /* TODO: sub_25977(..., 11, 0) */
        /* TODO: sub_29DAA(effect_buffer) */
    } else {
        /* n5 == 1 或 5 */
        /* TODO: sub_25977(..., 14, 0) */
        /* TODO: sub_279BC((int)effect_buffer) */
    }

    /* 9. 切换音乐回索引10 */
    /* TODO: sub_25977(..., 10, 0) */

    /* 10. 清理 */
    free(effect_buffer);
    g_n8_1 = 0;
}

/*
 * 按键处理 (对应原游戏 sub_26152 switch语句)
 * 
 * 原游戏代码:
 * switch (HIBYTE(::n3)) {
 *     case 0xE0: case 0x52: HIBYTE(::n3) = 28; break;
 *     case 0x22: if (++n16_1 == 10) n16_1 = 0; sub_25977(n16_1, 34, ...); break;
 *     case 0x4D: sub_25A96(..., 77, ...); if (--n5 < 0) n5 = 5; break;
 *     case 0x4B: sub_25A96(..., 75, ...); if (++n5 > 5) n5 = 0; break;
 *     default: ... break;
 * }
 */
void fd2_scene_handle_key(int key_code) {
    switch (key_code) {
        case 0xE0:  /* 扩展键前缀 */
        case 0x52:  /* Insert键 */
            /* Insert转换为回车 */
            g_n3 = 28;
            break;

        case 0x22:  /* Tab键 */
            /* 切换子场景 (n16_1 = (n16_1+1)%10) */
            local_n16_1++;
            if (local_n16_1 == 10) {
                local_n16_1 = 0;
            }
            g_n16_1 = local_n16_1;
            /* TODO: 调用sub_25977切换子场景音乐 */
            break;

        case 0x4D:  /* 右箭头 */
            /* 菜单向右移动: n5 = (n5-1)%6 */
            g_n5--;
            if (g_n5 < 0) {
                g_n5 = 5;
            }
            /* TODO: 播放菜单音效 sub_25A96(..., 77, ...) */
            break;

        case 0x4B:  /* 左箭头 */
            /* 菜单向左移动: n5 = (n5+1)%6 */
            g_n5++;
            if (g_n5 > 5) {
                g_n5 = 0;
            }
            /* TODO: 播放菜单音效 sub_25A96(..., 75, ...) */
            break;

        default:
            /* 其他按键处理 */
            /* TODO: 检查特殊菜单项 */
            break;
    }
}

/*
 * 确认键处理 (对应原游戏 sub_26152 确认部分)
 * 
 * 原游戏代码:
 * if (n5 != 2) sub_25A96(..., 1, 3);
 * sub_2670E(a5, &v20);
 * v21 = v17;
 */
void fd2_scene_handle_confirm(void) {
    /* 如果不是"返回"选项 (索引2)，播放确认音效 */
    if (g_n5 != 2) {
        /* TODO: 播放确认音效 sub_25A96(..., 1, 3) */
    }

    /* 执行选择 */
    fd2_scene_execute_selection(0, NULL);
}

/*
 * 主交互循环 (对应原游戏 sub_26152 do-while循环)
 * 
 * 原游戏代码:
 * do {
 *     sub_265EC(&v20);
 *     v13 = MEMORY[0x46C];
 *     while (!sub_10620()) {
 *         if ((MEMORY[0x46C] - v13) >= 4) {
 *             if (++n3_4 == 4) n3_4 = 0;
 *             sub_265EC(&v20);
 *             v13 = MEMORY[0x46C];
 *         }
 *     }
 *     HIBYTE(::n3) = 16;
 *     v14 = int386(22, &::n3, &::n3);
 *     switch (HIBYTE(::n3)) { ... }
 *     n3 = HIBYTE(::n3);
 *     if (HIBYTE(::n3) != 28 && HIBYTE(::n3) != 32) continue;
 *     if (n5 != 2) sub_25A96(..., 1, 3);
 *     sub_2670E(a5, &v20);
 *     v21 = v17;
 * } while (!v21);
 */
void fd2_scene_interact_main_loop(void* v20) {
    int v13;  /* BIOS定时器值 */

    do {
        /* 渲染更新 */
        fd2_scene_render_update(v20);

        /* 获取当前BIOS定时器值 */
        v13 = g_bios_tick_current;

        /* 等待按键 (带动画帧控制) */
        while (1) {
            /* 检查是否有按键输入 */
            /* TODO: 实现sub_10620垂直同步等待 */

            /* 检查BIOS定时器是否过了4个tick */
            int current_tick = g_bios_tick_current;
            if ((unsigned int)(current_tick - v13) >= 4) {
                /* 更新动画帧 */
                g_n3_4++;
                if (g_n3_4 == 4) {
                    g_n3_4 = 0;
                }

                /* 更新渲染 */
                fd2_scene_render_update(v20);

                /* 更新定时器基准 */
                v13 = current_tick;
            }

            /* 短暂延迟，避免CPU占用过高 */
            SDL_Delay(1);

            /* 检查是否有按键输入 */
            /* TODO: 从SDL事件队列获取按键 */
            int key_code = 0;  /* 暂时模拟无按键 */
            if (key_code != 0) {
                g_n3 = key_code;
                break;
            }
        }

        /* 读取按键 */
        /* TODO: 原游戏使用int386(22, &::n3, &::n3) */
        g_n3 = g_n3;  /* 保持当前按键值 */

        /* 按键处理 */
        int high_byte = (g_n3 >> 8) & 0xFF;
        fd2_scene_handle_key(high_byte);

        /* 检查是否为确认键 (回车=28 或 空格=32) */
        high_byte = (g_n3 >> 8) & 0xFF;
        if (high_byte != 28) {
            if ((g_n3 & 0xFF) != 32) {
                continue;  /* 不是确认键，继续循环 */
            }
        }

        /* 确认键处理 */
        fd2_scene_handle_confirm();

    } while (!local_v21);
}

/*
 * sub_26152: 场景交互循环 (原游戏 0x26152)
 * 
 * 返回值: n5 != 2
 */
fd2_scene_result_t fd2_scene_interact_loop(void) {
    unsigned char local_v20 = 0;  /* v20变量 */

    /* 初始化局部变量 */
    local_n16_1 = 0;
    local_v21 = 0;

    /* 阶段1: 释放旧场景资源 */
    fd2_scene_release_old_resources();

    /* 阶段2: 加载场景图标 */
    if (fd2_scene_load_icons() != 0) {
        return 0;
    }

    /* 阶段3: 检查特殊场景 */
    if (g_byte_523E7[g_n17]) {
        /* 特殊场景处理 */
        /* TODO: 实现特殊场景逻辑 (sub_2AF28) */
        return 0;
    }

    /* 阶段4: 加载场景图形 */
    if (fd2_scene_load_graphics() != 0) {
        return 0;
    }

    /* 阶段5: 首次渲染 */
    fd2_scene_render_update(&local_v20);

    /* 阶段6: 主交互循环 */
    fd2_scene_interact_main_loop(&local_v20);

    /* 阶段7: 清理资源 */
    if (g_FDOTHER_DAT__12) {
        free(g_FDOTHER_DAT__12);
        g_FDOTHER_DAT__12 = 0;
    }

    /* 返回值: n5 != 2 */
    return (g_n5 != 2) ? 1 : 0;
}
