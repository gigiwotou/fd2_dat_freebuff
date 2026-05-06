/**
 * FD2 BATTLE Player Turn Logic
 *
 * 基于IDA反编译代码1:1实现玩家回合逻辑
 * - sub_1C269: 获取活跃单位列表
 * - sub_1D51D: 角色选择循环
 * - sub_14818: 移动范围计算
 * - sub_115B6: 移动目标选择
 * - sub_18D8C: 菜单显示与选择
 * - sub_177FC: 菜单选择处理
 * - sub_1CFF0: 主战斗循环
 */

#define _GNU_SOURCE
#include "fd2_game.h"
#include "fd2_battle.h"
#include "fd2_input.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* ============================================================
 * sub_1C269: 获取活跃单位列表
 * 基于IDA 0x1C269
 * 
 * 原函数签名:
 * void __fastcall sub_1C269(a1, a2, a3, a4, a5, a6)
 * 
 * 功能: 遍历单位数据(dword_53A45)，根据位标志提取活跃单位ID
 * - 5行 x 8列 = 40个可能的位置
 * - 偏移+26处有位标志，每位代表一个单位是否活跃
 * - 将活跃单位ID存入a6指向的缓冲区
 * ============================================================ */
int battle_get_active_chars(state_battle_data_t* data, int* out_ids, int max_ids) {
    int count = 0;
    
    /* IDA sub_1C269: 遍历所有角色，检查active_mask位掩码
     * 简化实现: 直接遍历角色，检查active_mask */
    for (int i = 0; i < data->total_char_count && count < max_ids; ++i) {
        /* 检查是否已移动 */
        if (!data->char_moved[i]) {
            if (out_ids) {
                out_ids[count] = i;
            }
            ++count;
        }
    }
    
    return count;
}

/* ============================================================
 * sub_1D51D: 角色选择处理
 * 基于IDA 0x1D51D
 * 
 * 原函数签名:
 * void __fastcall sub_1D51D(a1, a2, n6_1, a4, n6, a6, a7, a8, a9, a10, a11)
 * 
 * 功能: 处理角色选择输入，更新n3_3(当前角色索引)
 * - 72: ↑ 上一个角色
 * - 80: ↓ 下一个角色
 * - 75: ← 上一行(减4)
 * - 77: → 下一行(加4)
 * - 28/57: Enter/Space 确认选择
 * ============================================================ */
int battle_char_selection(state_battle_data_t* data, fd2_game_t* game) {
    /* 渲染当前角色高亮 - sub_1CEED */
    battle_render_char_list(data, game);
    
    /* 检测输入 */
    fd2_input_begin_frame(&game->input);
    
    if (fd2_action_pressed(&game->input, FD2_ACTION_UP)) {
        /* case 72: ↑ */
        if (data->current_char_idx > 0) {
            --data->current_char_idx;
        } else {
            data->current_char_idx = data->active_char_count - 1;
        }
        return 0; /* 继续选择 */
    }
    
    if (fd2_action_pressed(&game->input, FD2_ACTION_DOWN)) {
        /* case 80: ↓ */
        if (data->active_char_count - 1 == data->current_char_idx) {
            data->current_char_idx = 0;
        } else {
            ++data->current_char_idx;
        }
        return 0; /* 继续选择 */
    }
    
    if (fd2_action_pressed(&game->input, FD2_ACTION_LEFT)) {
        /* case 75: ← */
        if (data->current_char_idx >= 4) {
            data->current_char_idx -= 4;
        }
        return 0; /* 继续选择 */
    }
    
    if (fd2_action_pressed(&game->input, FD2_ACTION_RIGHT)) {
        /* case 77: → */
        if (data->active_char_count - 4 > data->current_char_idx) {
            data->current_char_idx += 4;
        }
        return 0; /* 继续选择 */
    }
    
    if (fd2_action_pressed(&game->input, FD2_ACTION_START)) {
        /* case 28/57: Enter/Space 确认 */
        /* sub_1C269 + sub_4E866 */
        if (data->current_char_idx >= 0 && data->current_char_idx < data->active_char_count) {
            int char_id = data->active_char_ids[data->current_char_idx];
            printf("turn: selected char %d\n", char_id);
            return 1; /* 确认选择 */
        }
    }
    
    return 0; /* 继续选择 */
}

/* ============================================================
 * sub_14818: 计算移动范围
 * 基于IDA 0x14818
 * 
 * 原函数签名:
 * void __fastcall sub_14818(a1, a2, a3, a4, a5, a6, a7, n16, a9, n2)
 * 
 * 功能: 根据移动力计算可移动瓦块
 * - 使用曼哈顿距离: |x-a5| + |y-a6| < a9(移动力)
 * - 标记dword_53A51偏移+7处: 0=不可移动, -1=可移动
 * - n2: 过滤条件 (0=未移动, 1=已移动, 2=移动中, 3=其他)
 * ============================================================ */
int battle_calc_move_range(state_battle_data_t* data, int start_x, int start_y, int move_power) {
    int valid_count = 0;
    
    /* 清除之前的移动范围标记 */
    if (data->move_range_data) {
        memset(data->move_range_data, 0, data->map.width * data->map.height);
    } else {
        data->move_range_data = (u8*)calloc(data->map.width * data->map.height, 1);
    }
    
    /* 标记可移动范围 - 曼哈顿距离 < move_power */
    for (int y = 0; y < data->map.height; ++y) {
        for (int x = 0; x < data->map.width; ++x) {
            int dist = abs(x - start_x) + abs(y - start_y);
            if (dist < move_power) {
                data->move_range_data[y * data->map.width + x] = 1; /* 标记为-1 */
            }
        }
    }
    
    /* 检查哪些单位在移动范围内且满足条件 */
    for (int i = 0; i < data->sprite_count; ++i) {
        /* 检查: 
         * 1. (v19[5] & 1) == 0 (未移动标志)
         * 2. 瓦块值 != 255 (不是障碍物)
         * 3. n2条件匹配
         */
        if (data->sprites[i].loaded && !data->char_moved[i]) {
            int tile_x = data->sprites[i].tile_x;
            int tile_y = data->sprites[i].tile_y;
            
            if (tile_x >= 0 && tile_x < data->map.width &&
                tile_y >= 0 && tile_y < data->map.height) {
                if (data->move_range_data[tile_y * data->map.width + tile_x] == 1) {
                    ++valid_count;
                }
            }
        }
    }
    
    return valid_count;
}

/* ============================================================
 * sub_115B6: 移动目标选择
 * 基于IDA 0x115B6
 * 
 * 原函数签名:
 * void __fastcall sub_115B6(a1, a2, a3, a4, n6, n6_3, a7)
 * 
 * 功能: 等待玩家选择移动目标瓦块
 * - n6=4: 移动模式
 * - n6=5: 其他模式
 * - n6=6: 确认移动模式
 * - 检测方向键移动光标
 * - Enter/Space确认选择
 * ============================================================ */
int battle_select_move_target(state_battle_data_t* data, fd2_game_t* game, 
                               int mode, int* out_x, int* out_y) {
    /* 等待玩家输入循环 */
    while (1) {
        fd2_input_begin_frame(&game->input);
        
        /* sub_12DAC: 获取键盘输入 */
        
        if (fd2_action_pressed(&game->input, FD2_ACTION_ESCAPE)) {
            /* case 1: ESC 取消 */
            return -1;
        }
        
        if (fd2_action_pressed(&game->input, FD2_ACTION_START)) {
            /* case 28/57: Enter/Space 确认 */
            if (mode == 6) {
                /* 确认模式: 验证目标位置 */
                int target_x = data->cursor_x;
                int target_y = data->cursor_y;
                
                /* 检查是否有其他单位在目标位置 */
                bool occupied = false;
                for (int i = 0; i < data->sprite_count; ++i) {
                    if (i != data->selected_char_idx &&
                        data->sprites[i].tile_x == target_x &&
                        data->sprites[i].tile_y == target_y) {
                        occupied = true;
                        break;
                    }
                }
                
                if (!occupied) {
                    /* 验证地形可通行 */
                    if (data->move_range_data && 
                        target_y * data->map.width + target_x < data->map.width * data->map.height) {
                        if (data->move_range_data[target_y * data->map.width + target_x] == 1) {
                            *out_x = target_x;
                            *out_y = target_y;
                            return 1; /* 确认移动 */
                        }
                    }
                }
            } else if (mode == 4) {
                /* 移动模式: 直接确认 */
                *out_x = data->cursor_x;
                *out_y = data->cursor_y;
                return 1;
            }
        }
        
        /* 方向键移动光标 */
        if (fd2_action_pressed(&game->input, FD2_ACTION_UP)) {
            /* case 72: ↑ */
            cursor_move_up(data, data->map.height);
        } else if (fd2_action_pressed(&game->input, FD2_ACTION_DOWN)) {
            /* case 80: ↓ */
            cursor_move_down(data, data->map.height);
        } else if (fd2_action_pressed(&game->input, FD2_ACTION_LEFT)) {
            /* case 75: ← */
            cursor_move_left(data, data->map.width);
        } else if (fd2_action_pressed(&game->input, FD2_ACTION_RIGHT)) {
            /* case 77: → */
            cursor_move_right(data, data->map.width);
        }
        
        SDL_Delay(50);
    }
}

/* ============================================================
 * sub_177FC: 菜单选择处理
 * 基于IDA 0x177FC
 * 
 * 原函数签名:
 * int __fastcall sub_177FC(a1, a2, a3, a4, a5, a6)
 * 
 * 功能: 处理4选项菜单选择
 * - 1: ESC 取消，返回-1
 * - 28/57: Enter/Space 确认，返回1
 * - 72: ↑ 选择攻击(0)
 * - 80: ↓ 选择魔法(3)
 * - 75: ← 选择道具(1)
 * - 77: → 选择休息(2)
 * ============================================================ */
int battle_menu_selection(state_battle_data_t* data, fd2_game_t* game, int* menu_state) {
    fd2_input_begin_frame(&game->input);
    
    /* sub_17898: 获取输入 */
    if (fd2_action_pressed(&game->input, FD2_ACTION_ESCAPE)) {
        /* case 1: ESC */
        return -1;
    }
    
    if (fd2_action_pressed(&game->input, FD2_ACTION_START)) {
        /* case 28/57: Enter/Space */
        return 1; /* 确认选择 */
    }
    
    if (fd2_action_pressed(&game->input, FD2_ACTION_UP)) {
        /* case 72: ↑ */
        if (!menu_state[0]) {
            data->menu_selected = 0; /* 攻击 */
            return 0;
        }
    }
    
    if (fd2_action_pressed(&game->input, FD2_ACTION_DOWN)) {
        /* case 80: ↓ */
        if (!menu_state[3]) {
            data->menu_selected = 3; /* 魔法 */
            return 0;
        }
    }
    
    if (fd2_action_pressed(&game->input, FD2_ACTION_LEFT)) {
        /* case 75: ← */
        data->menu_selected = 1; /* 道具 */
        return 0;
    }
    
    if (fd2_action_pressed(&game->input, FD2_ACTION_RIGHT)) {
        /* case 77: → */
        if (!menu_state[2]) {
            data->menu_selected = 2; /* 休息 */
            return 0;
        }
    }
    
    return 0;
}

/* ============================================================
 * sub_18D8C: 菜单显示与执行
 * 基于IDA 0x18D8C
 * 
 * 原函数签名:
 * int __fastcall sub_18D8C(a1, a2, a3, a4, n6, dst, a7)
 * 
 * 功能: 
 * 1. 初始化菜单 (sub_173E7)
 * 2. 渲染菜单 (sub_1741C)
 * 3. 循环等待选择 (sub_177FC)
 * 4. 根据选择执行功能
 *    - n3_3==0: 移动
 *    - n3_3==1: 攻击 (sub_1CFF0)
 *    - n3_3==2: 道具 (sub_1BBDC)
 *    - n3_3==3: 魔法 (sub_190AC)
 * ============================================================ */
int battle_action_menu(state_battle_data_t* data, fd2_game_t* game) {
    int menu_state[4] = {0, 0, 0, 0}; /* 菜单选项状态 */
    data->menu_visible = true;
    data->menu_selected = 0;
    
    /* sub_173E7: 初始化菜单选择 */
    int menu_idx = 0;
    for (int i = 0; i < 4; ++i) {
        menu_idx = i;
        if (!menu_state[i]) break;
    }
    
    /* 菜单循环 */
    int result = 0;
    do {
        /* sub_1741C: 渲染4x4菜单 */
        battle_render_menu(data, game, menu_state);
        
        /* sub_176B4: 高亮当前选项 */
        battle_highlight_menu_option(data, menu_idx);
        
        /* sub_177FC: 处理菜单输入 */
        result = battle_menu_selection(data, game, menu_state);
        
        SDL_Delay(50);
    } while (!result);
    
    data->menu_visible = false;
    
    if (result == -1) {
        return -1; /* 取消 */
    }
    
    /* 根据选择执行功能 */
    switch (data->menu_selected) {
        case 0: /* 攻击 */
            printf("turn: attack action selected\n");
            /* sub_1BBDC 或相关攻击逻辑 */
            break;
            
        case 1: /* 道具 */
            printf("turn: item action selected\n");
            /* sub_1CFF0 或道具逻辑 */
            break;
            
        case 2: /* 休息 */
            printf("turn: rest action selected\n");
            /* 直接恢复状态 */
            break;
            
        case 3: /* 魔法 */
            printf("turn: magic action selected\n");
            /* sub_190AC 魔法选择 */
            break;
    }
    
    /* sub_13512: 标记角色移动完毕 */
    if (data->selected_char_idx >= 0 && data->selected_char_idx < data->sprite_count) {
        data->char_moved[data->selected_char_idx] = true;
        printf("turn: char %d marked as moved\n", data->selected_char_idx);
    }
    
    return 1;
}

/* ============================================================
 * 渲染辅助函数
 * ============================================================ */

void battle_render_char_list(state_battle_data_t* data, fd2_game_t* game) {
    /* 渲染角色列表，高亮当前选择的角色 */
    if (!data->map.loaded || !data->map.map_rendered) return;
    
    /* 渲染地图 */
    fd2_map_render(&data->map, game->render.screen, FD2_SCREEN_W, FD2_SCREEN_H,
                   data->camera_x, data->camera_y);
    
    /* 渲染精灵 */
    battle_render_sprites(data->sprites, data->sprite_count,
                          data->camera_x, data->camera_y,
                          game->render.screen, FD2_SCREEN_W, FD2_SCREEN_H);
    
    /* 高亮当前选择的角色 */
    if (data->current_char_idx >= 0 && data->current_char_idx < data->active_char_count) {
        int char_id = data->active_char_ids[data->current_char_idx];
        if (char_id >= 0 && char_id < data->sprite_count) {
            map_sprite_t* sprite = &data->sprites[char_id];
            int sx = sprite->tile_x * MAP_TILE_SIZE - data->camera_x;
            int sy = sprite->tile_y * MAP_TILE_SIZE - data->camera_y;
            
            /* 白色高亮边框 */
            u8 highlight_color = 63;
            for (int x = 0; x < MAP_TILE_SIZE; x++) {
                int px = sx + x;
                if (px >= 0 && px < FD2_SCREEN_W) {
                    if (sy >= 0 && sy < FD2_SCREEN_H) {
                        game->render.screen[sy * FD2_SCREEN_W + px] = highlight_color;
                    }
                    int bottom = sy + MAP_TILE_SIZE - 1;
                    if (bottom >= 0 && bottom < FD2_SCREEN_H) {
                        game->render.screen[bottom * FD2_SCREEN_W + px] = highlight_color;
                    }
                }
            }
            for (int y = 0; y < MAP_TILE_SIZE; y++) {
                int py = sy + y;
                if (py >= 0 && py < FD2_SCREEN_H) {
                    if (sx >= 0 && sx < FD2_SCREEN_W) {
                        game->render.screen[py * FD2_SCREEN_W + sx] = highlight_color;
                    }
                    int right = sx + MAP_TILE_SIZE - 1;
                    if (right >= 0 && right < FD2_SCREEN_W) {
                        game->render.screen[py * FD2_SCREEN_W + right] = highlight_color;
                    }
                }
            }
        }
    }
    
    fd2_render_present(&game->render);
}

void battle_render_menu(state_battle_data_t* data, fd2_game_t* game, int* menu_state) {
    /* 渲染4选项菜单: 攻击、道具、休息、魔法 */
    if (!data->map.loaded || !data->map.map_rendered) return;
    
    (void)menu_state;  /* 菜单状态用于后续扩展 */
    
    /* 渲染地图和精灵作为背景 */
    fd2_map_render(&data->map, game->render.screen, FD2_SCREEN_W, FD2_SCREEN_H,
                   data->camera_x, data->camera_y);
    battle_render_sprites(data->sprites, data->sprite_count,
                          data->camera_x, data->camera_y,
                          game->render.screen, FD2_SCREEN_W, FD2_SCREEN_H);
    
    /* 绘制菜单背景 */
    int menu_x = FD2_SCREEN_W / 2 - 100;
    int menu_y = FD2_SCREEN_H - 80;
    int menu_w = 200;
    int menu_h = 60;
    
    /* 黑色背景 */
    for (int y = menu_y; y < menu_y + menu_h && y < FD2_SCREEN_H; ++y) {
        for (int x = menu_x; x < menu_x + menu_w && x < FD2_SCREEN_W; ++x) {
            game->render.screen[y * FD2_SCREEN_W + x] = 0;
        }
    }
    
    /* 绘制边框 */
    for (int x = menu_x; x < menu_x + menu_w && x < FD2_SCREEN_W; ++x) {
        if (menu_y >= 0) game->render.screen[menu_y * FD2_SCREEN_W + x] = 63;
        if (menu_y + menu_h - 1 < FD2_SCREEN_H) 
            game->render.screen[(menu_y + menu_h - 1) * FD2_SCREEN_W + x] = 63;
    }
    for (int y = menu_y; y < menu_y + menu_h && y < FD2_SCREEN_H; ++y) {
        if (menu_x >= 0) game->render.screen[y * FD2_SCREEN_W + menu_x] = 63;
        if (menu_x + menu_w - 1 < FD2_SCREEN_W) 
            game->render.screen[y * FD2_SCREEN_W + (menu_x + menu_w - 1)] = 63;
    }
    
    /* TODO: 绘制菜单文字 "攻击" "道具" "休息" "魔法" */
    /* 需要字体渲染支持，暂时留空 */
    
    fd2_render_present(&game->render);
}

void battle_highlight_menu_option(state_battle_data_t* data, int option_idx) {
    /* 高亮当前菜单选项 */
    /* TODO: 实现菜单高亮效果 */
    (void)data;
    (void)option_idx;
}

/* ============================================================
 * 回合状态初始化
 * ============================================================ */

void battle_turn_init(state_battle_data_t* data) {
    /* 初始化回合状态 */
    data->turn_phase = 0; /* 0=选择角色 */
    data->current_char_idx = 0;
    data->active_char_count = 0;
    data->selected_char_idx = -1;
    data->menu_visible = false;
    data->menu_selected = 0;
    data->move_range = 0;
    data->move_start_x = 0;
    data->move_start_y = 0;
    data->move_range_data = NULL;
    
    /* 初始化移动标记 */
    memset(data->char_moved, 0, sizeof(data->char_moved));
    
    /* 获取活跃角色列表 */
    data->active_char_count = battle_get_active_chars(data, data->active_char_ids, 40);
    
    printf("turn: initialized with %d active characters\n", data->active_char_count);
}

void battle_turn_cleanup(state_battle_data_t* data) {
    /* 清理回合状态 */
    if (data->move_range_data) {
        free(data->move_range_data);
        data->move_range_data = NULL;
    }
}
