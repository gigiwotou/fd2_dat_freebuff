/**
 * FD2 Battle Core Logic
 * 
 * Implements core battlefield functions based on IDA Pro MCP analysis:
 * - sub_18D8C: Battle entry function
 * - sub_1CFF0: Battle main loop
 * - sub_115B6: Attack handler
 * - sub_1C269: Active character list
 * - sub_14818: Display list builder
 */

#define _GNU_SOURCE
#include "fd2_game.h"
#include "fd2_battle.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Global variables based on IDA analysis */
static int g_battle_count = 0;          /* dword_53EC8 */
static int g_char_state_flag = 1;       /* dword_51A83 */

/* Render buffers - based on IDA sub_1CFF0 */
static u8* g_render_buf1 = NULL;        /* dword_53C5B - 64000 bytes */
static u8* g_render_buf2 = NULL;        /* dword_53C5F - 64000 bytes */
static u8* g_render_main = NULL;        /* n16 - 64000 bytes */

/* Map data address - based on IDA */
#define MAP_DATA_ADDR 655360

/* Character array base - based on IDA dword_53A45 */
/* Used globally in the original game */

/* ========================================================================
 * sub_1C269: Get active character IDs
 * 
 * Based on IDA decompiler output:
 * Iterates through 5 rows x 8 columns (40 characters)
 * Checks active_mask at offset+26 for each row
 * If bit n is set, character index (n + 8*row) is active
 * ======================================================================== */
int battle_get_active_char_ids(state_battle_data_t* data, int* out_ids, int max_ids) {
    if (!data) return 0;
    
    int count = 0;
    
    /* v7 = 80 * a5 + dword_53A45 */
    /* For each row (5 rows) */
    for (int row = 0; row < 5; row++) {
        /* v8 = *(unsigned __int8 *)(n5 + v7 + 26) */
        /* Get active mask for this row */
        int char_idx_base = row * 8; /* 8 characters per row */
        
        if (char_idx_base < MAX_BATTLE_CHARS) {
            uint8_t active_mask = data->char_data[char_idx_base].active_mask;
            
            /* For each bit in the mask (8 bits) */
            for (int bit = 0; bit < 8; bit++) {
                /* if (((v8 >> n8) & 1) != 0) */
                if (((active_mask >> bit) & 1) != 0) {
                    int char_id = bit + 8 * row;
                    
                    /* if (a6) *(_BYTE *)(a6 + v6) = n8 + 8 * n5 */
                    if (out_ids && count < max_ids) {
                        out_ids[count] = char_id;
                    }
                    count++;
                }
            }
        }
    }
    
    return count;
}

/* ========================================================================
 * sub_14818: Build display list / movement range
 * 
 * Based on IDA decompiler output:
 * - Marks tiles within movement range
 * - Filters characters by position and type
 * - Returns count of valid characters
 * ======================================================================== */
int battle_build_display_list(state_battle_data_t* data, int n16, int n19, int n2, u8* out_list) {
    if (!data) return 0;
    
    int count = 0;
    
    /* Movement range logic */
    /* if (n16 >= 16) */
    if (n16 >= 16) {
        /* Mark tiles outside movement range */
        /* Original: checks abs(v15 - a5) <= v16 */
        /* Simplified: mark all tiles in range */
    } else {
        /* Use pathfinding for movement range */
        /* Calls sub_4E390 with movement data */
    }
    
    /* Filter characters */
    /* for (n6 = 0; n6 < n6_0; ++n6) */
    for (int i = 0; i < data->total_char_count; i++) {
        battle_char_data_t* v19 = &data->char_data[i];
        
        /* Check conditions:
         * 1. (v19[5] & 1) == 0 - not dead
         * 2. Layout tile not 255
         * 3. Character type matches n2 filter
         */
        int is_alive = ((v19->active_byte & 1) == 0);
        int type_match = 0;
        
        if (n2 == 0 && v19->char_type == 0) type_match = 1;
        else if (n2 == 1 && v19->char_type != 0) type_match = 1;
        else if (n2 == 2 && v19->char_type == 1) type_match = 1;
        else if (n2 == 3 && v19->char_type == 2) type_match = 1;
        else if (n2 == 0) type_match = 1; /* No filter */
        
        if (is_alive && type_match) {
            /* if (a7) *(_BYTE *)(v22 + a7) = n6 */
            if (out_list && count < 100) {
                out_list[count] = (u8)i;
            }
            count++;
        }
    }
    
    return count;
}

/* ========================================================================
 * sub_18D8C: Battle entry function
 * 
 * Based on IDA decompiler output:
 * 1. Initialize battle state
 * 2. Get character battle data
 * 3. Build active character list
 * 4. Initialize menu system
 * 5. Check battle state
 * 6. Wait for user input
 * 7. Select battle mode based on n2_3
 * ======================================================================== */
int battle_entry(fd2_game_t* game, int n17, int* dst, int a6) {
    state_battle_data_t* data = (state_battle_data_t*)game->state_data;
    if (!data) return -1;
    
    printf("battle_entry: n17=%d, a6=%d\n", n17, a6);
    
    /* sub_3702F(a1, SHIDWORD(a1), n19, a3, 176) - stack setup */
    
    /* *dst = 0 */
    if (dst) *dst = 0;
    
    /* dword_53EC8 = 0 */
    g_battle_count = 0;
    
    /* LODWORD(a1) = sub_1B83D(n17, 0) */
    /* Get battle data for character n17 */
    int battle_data_idx = -1; /* Simulated: would call sub_1B83D */
    
    /* if ((_DWORD)a1 == -1) */
    if (battle_data_idx == -1) {
        if (dst) *dst = 1;
    } else {
        /* LODWORD(a1) = sub_1B722(a1, SHIDWORD(a1), n19, 0, n17, a1) */
        /* Process battle data */
        
        /* LODWORD(a1) = sub_4E8BC(a1) */
        /* Get character pointer */
        
        /* n19 = *(unsigned __int8 *)(a1 + 11) */
        /* n16 = *(unsigned __int8 *)(a1 + 12) */
        
        /* sub_14818(n16, SHIDWORD(a1), n19, 0, n9_0, n34_0, 0, n16, n19, 0) */
        /* Build initial active character list */
        u8 temp_list[100];
        int active_count = battle_build_display_list(data, 0, 0, 0, temp_list);
        
        /* if (!v6) *dst = 1 */
        if (!active_count && dst) {
            *dst = 1;
        }
        
        /* sub_4DF4C((unsigned __int8 *)dword_53A51) */
        /* Clear layout data */
    }
    
    /* Menu system initialization */
    /* sub_173E7(dst) */
    /* sub_1741C((__int32)dst_, SHIDWORD(a1), n19, 0, (int)dst_, (int)dst, ...) */
    
    /* LODWORD(a1) = sub_1B8A6(n17) */
    /* Check battle state */
    int battle_state = 1; /* Simulated: would call sub_1B8A6 */
    
    /* if (!(_DWORD)a1) dst[2] = 1 */
    if (!battle_state && dst) {
        dst[2] = 1;
    }
    
    /* sub_1C269(a1, SHIDWORD(a1), n19, 0, n17, 0) */
    /* Get active character index list */
    int active_ids[40];
    int active_count = battle_get_active_char_ids(data, active_ids, 40);
    
    /* if (!v7) dst[1] = 1 */
    if (!active_count && dst) {
        dst[1] = 1;
    }
    
    /* v8 = (unsigned __int8 *)(80 * n17 + dword_53A45) */
    /* if (v8[39]) dst[1] = 1 */
    if (n17 >= 0 && n17 < data->total_char_count) {
        if (data->char_data[n17].death_flag) {
            if (dst) dst[1] = 1;
        }
    }
    
    /* sub_173E7(dst) */
    
    /* 在初始化模式中，不等待用户输入
       输入等待应该在 state_battle_update 的主循环中处理
       原始IDA代码的 sub_177FC 是等待输入，但我们的架构是分帧处理的 */
    int input_result = 0;
    
    /* sub_176B4((__int32)dst_, SHIDWORD(a1), n19, 0, (int)dst_, (int)dst) */
    /* Process input */
    
    /* LODWORD(a1) = sub_11CAC(a1, SHIDWORD(a1), n19, 0, 0) */
    /* Update character state */
    
    /* if (n19 == -1) return -1 */
    if (input_result == -1) {
        return -1;
    }
    
    /* Battle mode selection based on n2_3 */
    /* 注意：在 state_battle_enter 中，我们只做初始化
       实际的战斗循环在 state_battle_update 中处理 */
    int n2_3 = 0; /* 初始化为初始化模式 */
    
    /* if (n2_3) */
    if (n2_3) {
        /* 战斗模式不会在 enter 中执行 */
    }
    /* else */
    else {
        /* Initialization mode - 只做初始化，不阻塞 */
        /* n9 = n9_0 */
        /* n34 = n34_0 */
        
        printf("battle_entry: initialization mode (building display list)\n");
        
        /* 在初始化模式中，只构建显示列表
           实际的移动和攻击选择在 state_battle_update 中处理 */
    }
    
    /* return 1 */
    return 1;
}

/* ========================================================================
 * sub_1CFF0: Battle main loop
 * 
 * Based on IDA decompiler output:
 * 1. Initialize render buffers (3x 64000 bytes)
 * 2. Copy map data to buffers
 * 3. Preprocess character data
 * 4. Render UI
 * 5. Render pipeline (reverse 11→0, forward 0→11)
 * 6. Character battle logic
 * 7. Battle result processing
 * ======================================================================== */
int battle_main_loop(fd2_game_t* game, int n19, int n17) {
    state_battle_data_t* data = (state_battle_data_t*)game->state_data;
    if (!data) return -1;
    
    printf("battle_main_loop: n19=%d, n17=%d\n", n19, n17);
    
    /* sub_3702F(a1, a2, n19, a4, 264) - stack setup */
    
    /* dword_53C5B = malloc(64000) */
    g_render_buf1 = (u8*)malloc(64000);
    g_render_buf2 = (u8*)malloc(64000);
    g_render_main = (u8*)malloc(64000);
    
    if (!g_render_buf1 || !g_render_buf2 || !g_render_main) {
        free(g_render_buf1);
        free(g_render_buf2);
        free(g_render_main);
        return -1;
    }
    
    /* memmove(dword_53C5F, 655360, 64000) */
    /* memmove(::n16_1, dword_53C5F, 64000) */
    /* Copy map data to render buffers */
    if (data->map.loaded && data->map.map_image) {
        /* Copy from map image buffer */
        u32 map_size = (u32)data->map.map_image_width * (u32)data->map.map_image_height;
        memcpy(g_render_buf2, data->map.map_image, SDL_min(64000, map_size));
        memcpy(g_render_main, g_render_buf2, 64000);
    }
    
    /* LODWORD(n16) = sub_17EEF(n17, ::n16_1) */
    /* Preprocess character data */
    /* This would process character animations and positions */
    
    /* sub_1CEED(n16, SHIDWORD(n16), n19, a4, n17, -1, ::n16_1) */
    /* Render battle UI */
    
    /* for (n11 = 11; n11 >= 0; --n11) */
    /*     sub_18409(n11, dword_53C5B, ::n16_1, dword_53C5F) */
    /* Reverse render pipeline setup (layers 11 to 0) */
    for (int layer = 11; layer >= 0; layer--) {
        /* Render layer */
        /* Would call sub_18409 with layer data */
    }
    
    /* n2_3 = 0 */
    /* do */
    /*     sub_1D51D(n16, SHIDWORD(n16), n11, a4, n17) */
    /*     n16_1 = n16 */
    /* while (!(_DWORD)n16) */
    /* Render frame loop - 简化为单帧渲染 */
    int render_result = 1; /* 始终返回成功 */
    
    /* 渲染当前帧 - 只渲染一次避免闪烁 */
    if (data->map.loaded && data->map.map_rendered) {
        fd2_map_render(&data->map, game->render.screen, FD2_SCREEN_W, FD2_SCREEN_H,
                      data->camera_x, data->camera_y);
        
        battle_render_sprites(data->sprites, data->sprite_count,
                             data->camera_x, data->camera_y,
                             game->render.screen, FD2_SCREEN_W, FD2_SCREEN_H);
        
        battle_render_cursor(data, game->render.screen, FD2_SCREEN_W, FD2_SCREEN_H);
        
        /* 渲染角色信息面板 (基于 IDA sub_12D7B, sub_12CEA) */
        battle_render_info_panel(data, game);
        
        fd2_render_present(&game->render);
    }
    
    /* for (n11_1 = 0; n11_1 <= 11; ++n11_1) */
    /*     sub_18409(n11_1, dword_53C5B, ::n16_1, dword_53C5F) */
    /* Forward render pipeline cleanup (layers 0 to 11) */
    for (int layer = 0; layer <= 11; layer++) {
        /* Cleanup layer */
    }
    
    /* memmove(655360, dword_53C5F, 64000) */
    /* Write back map data */
    
    /* free(dword_53C5B) */
    /* free(dword_53C5F) */
    /* free(::n16_1) */
    free(g_render_buf1);
    free(g_render_buf2);
    free(g_render_main);
    g_render_buf1 = NULL;
    g_render_buf2 = NULL;
    g_render_main = NULL;
    
    /* if (n16_1 == -1) return -1 */
    if (render_result == -1) {
        return -1;
    }
    
    /* sub_1C269((__int32)v27, SHIDWORD(n16), n11_1, a4, n17, (int)v27) */
    /* Get active character index list */
    /* 注意：这里使用当前选中的角色，而不是从活跃列表获取
       因为 n2_3 = 0，使用第一个活跃角色 */
    
    /* v10 = (unsigned __int8 *)sub_4E866((unsigned __int8)v27[n2_3]) */
    /* Get character data - 使用传入的 n17 作为角色索引 */
    battle_char_data_t* char_data = NULL;
    if (n17 >= 0 && n17 < data->total_char_count) {
        char_data = &data->char_data[n17];
    }
    
    if (!char_data) {
        return -1;
    }
    
    /* dword_51A83 = v10[4] + 2 */
    g_char_state_flag = char_data->portrait_id + 2;
    
    /* Battle logic branches based on character type and state */
    int attack_result = 0;
    
    /* if (v10[3] && (n11_1 = (unsigned __int8)v27[n2_3], n11_1 == 23)) */
    if (char_data->active_mask && char_data->char_type == 23) {
        /* Branch 1: Special type 23, has attack target */
        
        /* sub_14818(..., n16, 1, v10[6]) */
        u8 attack_list[100];
        int attack_count = battle_build_display_list(data, 0, 0, 1, attack_list);
        
        /* sub_115B6(v10[6], SHIDWORD(n16), (int)p_n6, a4, v10[6], n16, (unsigned __int8 *)p_n6) */
        attack_result = battle_attack_handler(game, char_data->char_type, attack_count, attack_list);
        
        /* sub_4DF4C((unsigned __int8 *)dword_53A51) */
        
        /* sub_14818(..., v10[4], 0, v10[6]) */
        /* Additional display list */
        
        /* if (n16_2 != -1) */
        if (attack_result != -1) {
            /* sub_115B6(LOBYTE(p_n6[0]), SHIDWORD(n16), (int)p_n6, a4, 6, LOBYTE(p_n6[0]), 0) */
            attack_result = battle_attack_handler(game, 6, attack_count, attack_list);
        }
        
        /* if (n16_3 != -1) */
        if (attack_result != -1) {
            /* dword_51A83 = 0 */
            g_char_state_flag = 0;
            
            /* sub_12D7B(n34_0, SHIDWORD(n16), (int)p_n6, a4, n17) */
            /* Process attack result */
            
            /* dword_51A83 = 1 */
            g_char_state_flag = 1;
        }
    }
    /* else if (!v10[3] || (n11_1 = (unsigned __int8)v27[n2_3], n11_1 == 23)) */
    else if (!char_data->active_mask || char_data->char_type == 23) {
        /* Branch 2: No attack target or type 23 */
        
        /* LODWORD(n16) = dword_51A83 - 2 */
        /* dword_51A83 = 1 */
        int n16_val = g_char_state_flag - 2;
        g_char_state_flag = 1;
        
        /* sub_14818(..., n11_1, a4, n9_0, n34_0, (int)p_n6, n16, 0, 0) */
        u8 move_list[100];
        int move_count = battle_build_display_list(data, n16_val, 0, 0, move_list);
        
        /* n4 = 4 */
        /* if (!n30_2) n4 = 5 */
        int n4 = 4;
        if (!move_count) n4 = 5;
        
        /* sub_115B6((__int32)p_n6, SHIDWORD(n16), n11_1, a4, n4, 0, (unsigned __int8 *)p_n6) */
        attack_result = battle_attack_handler(game, n4, 0, move_list);
    }
    /* else */
    else {
        /* Branch 3: Normal battle */
        
        /* sub_14818(..., v10[6], a4, n9_0, n34_0, (int)p_n6, n16, 0, v10[6]) */
        u8 battle_list[100];
        int battle_count = battle_build_display_list(data, 0, 0, 0, battle_list);
        
        /* sub_115B6(v11[6], SHIDWORD(n16), (int)p_n6, a4, v11[6], n16, (unsigned __int8 *)p_n6) */
        attack_result = battle_attack_handler(game, char_data->char_type, battle_count, battle_list);
        
        /* sub_4DF4C((unsigned __int8 *)dword_53A51) */
        
        /* if (v27[n2_3] == 30) */
        if (char_data->char_type == 30) {
            /* sub_149F8(n9_0, n34_0, p_n6, n9, n34, v11[3] - 16, 1) */
            /* Special attack type 30 */
        }
        /* else */
        else {
            /* sub_14818(..., v11[4], 0, v11[6]) */
        }
    }
    
    /* LOBYTE(n16) = sub_4DF4C((unsigned __int8 *)dword_53A51) */
    
    /* if (n16_3 == -1) */
    if (attack_result == -1) {
        /* Battle failed / fled */
        
        /* dword_51A83 = 0 */
        g_char_state_flag = 0;
        
        /* sub_12D7B(n16, SHIDWORD(n16), n11_1, a4, n17) */
        /* Process failure */
        
        /* dword_51A83 = 1 */
        g_char_state_flag = 1;
        
        /* return 0 */
        return 0;
    }
    /* else */
    else {
        /* Battle continues */
        
        /* dword_51A83 = 0 */
        g_char_state_flag = 0;
        
        /* sub_11CAC(n16, SHIDWORD(n16), n11_1, a4, 0) */
        /* Update state */
        
        /* LODWORD(n16) = (unsigned __int8)v27[n2_3] */
        int char_type = char_data->char_type;
        
        /* if ((unsigned int)n16 < 9 || (_DWORD)n16 == 24 || (unsigned __int8)v27[n2_3] > 0x1Bu) */
        if (char_type < 9 || char_type == 24 || char_type > 0x1B) {
            /* sub_2FF01(...) */
            /* Special type handler */
        }
        /* else */
        else {
            /* sub_1D4CB(n16, SHIDWORD(n16), n11_1, a4) */
            /* sub_1D6C8((unsigned __int8)v27[n2_3], SHIDWORD(n16), n11_1, a4, (unsigned __int8)v27[n2_3]) */
            
            /* LODWORD(n16) = funcs_1541F[(unsigned __int8)v27[n2_3]](n17, n30, (int)p_n6) */
            /* Function pointer array call - not implemented yet */
            
            /* sub_1D4F6(n16, SHIDWORD(n16), (int)p_n6, a4) */
        }
        
        /* v23 = sub_1B6B7(v26) */
        /* v24 = v23 */
        /* sub_1DB65(v23, HIDWORD(v23), v23) */
        /* sub_1AA1D(__SPAIR64__(v24, n17), (int)v26, p_n6[0], p_n6[1], p_n6[2], p_n6[3]) */
        
        /* dword_51A83 = 1 */
        g_char_state_flag = 1;
        
        /* return 1 */
        return 1;
    }
}

/* ========================================================================
 * sub_115B6: Attack handler
 * 
 * Based on IDA decompiler output:
 * 1. Initialize attack type
 * 2. Target selection loop
 * 3. Key mapping (72=confirm, 80=next, 75=cancel, 77=prev)
 * 4. Position check logic
 * ======================================================================== */
int battle_attack_handler(fd2_game_t* game, int n6, int n6_3, u8* a7) {
    state_battle_data_t* data = (state_battle_data_t*)game->state_data;
    if (!data) return -1;
    
    printf("battle_attack_handler: n6=%d, n6_3=%d\n", n6, n6_3);
    
    /* sub_3702F(a1, a2, a3, a4, 60) - stack setup */
    
    /* n6_4 = n6_3 */
    int n6_4 = n6_3;
    
    /* v8 = 0 */
    int v8 = 0;
    
    /* if (n6 == 6) */
    int n6_2 = n6_3;
    if (n6 == 6) {
        /* n6_2 = n6_3 */
        /* n6_4 = 0 */
        n6_4 = 0;
    }
    
    /* v18 = ::n6_2 */
    /* if (::n6_2 > 1) --v18 */
    int v18 = n6_2;
    if (n6_2 > 1) {
        v18--;
    }
    
    /* if (n6_4) */
    int target_idx = 0;
    if (n6_4) {
        /* v9 = *a7 */
        target_idx = a7[0];
        /* goto LABEL_7 */
    }
    
    /* while (1) */
    /* 注意：在当前的游戏架构中，不应该有阻塞的输入等待循环
       这里简化为直接返回，攻击选择逻辑应该在 state_battle_update 中分帧处理 */
    
    /* 如果 n6_4 > 0，表示有目标列表，返回第一个目标 */
    if (n6_4 > 0 && a7) {
        target_idx = a7[0];
    }
    
    return target_idx;
}
