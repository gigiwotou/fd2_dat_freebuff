/**
 * FD2 BATTLE State
 *
 * In-game fight. Uses fd2_map_loader to load and render maps from DAT files.
 * 
 * Based on IDA sub_1CFF0 (battle main loop):
 * - Press Enter/Space on character:
 *   - Player (unmoved): show move range -> select move target -> move
 *   - Player (moved) / Ally / Enemy: show status screen
 */

#define _GNU_SOURCE
#include "fd2_game.h"
#include "fd2_battle.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Global state flag based on IDA dword_51A83 */
static int g_char_state_flag = 1;

void state_battle_enter(fd2_game_t* game) {
    state_battle_data_t* data = (state_battle_data_t*)calloc(1, sizeof(state_battle_data_t));
    game->state_data = data;

    data->cursor_x = 0;
    data->cursor_y = 0;
    data->scroll_x = 0;
    data->scroll_y = 0;
    data->move_counter_x = 0;
    data->move_counter_y = 0;
    data->cursor_blink = 0;
    data->cursor_char_frame_id = 242;

    data->debug_grid_enabled = false;

    data->camera_x = 0;
    data->camera_y = 0;

    data->character_icon_loaded = false;
    data->character_tile_x = 0;
    data->character_tile_y = 0;
    data->sprites = NULL;
    data->sprite_count = 0;
    data->max_sprites = 0;
    data->from_save = false;
    data->saved_num_fighters = 0;
    data->selected_char_idx = -1;
    data->cursor_char_frame_id = 0;
    data->terrain_info_data = NULL;
    data->terrain_info_data_size = 0;
    memset(data->terrain_info_buffer, 0, sizeof(data->terrain_info_buffer));

    /* Initialize player turn state */
    battle_turn_init(data);

    /* Initialize resource pointers to NULL */
    data->fdother_resource_5 = NULL;
    data->fdother_resource_5_size = 0;
    data->fdother_resource_3 = NULL;
    data->fdother_resource_3_size = 0;
    data->fdother_data = NULL;
    data->fdother_data_size = 0;

    /* Initialize battle phase */
    data->battle_phase = BATTLE_PHASE_SELECT_CHAR;
    data->showing_move_range = false;
    data->move_range_tile_x = 0;
    data->move_range_tile_y = 0;
    data->animating_move = false;
    data->anim_move_progress = 0;

    /* Get paths for map loading */
    const char* fdfield_path = fd2_resources_dat_path(&game->resources, FD2_DAT_FDFIELD);
    const char* fdshap_path = fd2_resources_dat_path(&game->resources, FD2_DAT_FDSHAP);
    const char* fdother_path = fd2_resources_dat_path(&game->resources, FD2_DAT_FDOTHER);

    /* Load FDOTHER.DAT resources via sub_111BA (fd2_dat_load_resource) */
    if (fdother_path) {
        data->fdother_resource_5 = fd2_dat_load_resource(fdother_path, NULL, 5);
        if (data->fdother_resource_5) {
            data->fdother_data = data->fdother_resource_5;
            data->fdother_data_size = fd2_last_loaded_size;
            printf("state_battle: FDOTHER resource index 5 loaded (%u bytes)\n", data->fdother_data_size);

            if (load_cursor_image(game, data) == 0) {
                printf("state_battle: cursor image loaded OK, %dx%d\n",
                       data->cursor_image_width, data->cursor_image_height);
            } else {
                printf("state_battle: cursor image load FAILED\n");
            }
        } else {
            printf("state_battle: FDOTHER resource index 5 failed to load\n");
        }

        data->fdother_resource_3 = fd2_dat_load_resource(fdother_path, NULL, 3);
        if (data->fdother_resource_3) {
            data->terrain_info_data = data->fdother_resource_3;
            data->terrain_info_data_size = fd2_last_loaded_size;
            printf("state_battle: FDOTHER resource index 3 loaded (%u bytes) - terrain info\n", data->terrain_info_data_size);
        } else {
            printf("state_battle: FDOTHER resource index 3 failed to load\n");
        }
    } else {
        printf("state_battle: FDOTHER.DAT path not available\n");
    }

    int map_id = game->map_index;
    printf("state_battle: loading map %d from DAT files\n", map_id);

    if (fd2_map_load_from_dat(&data->map, map_id, fdfield_path, fdshap_path, fdother_path) == 0) {
        printf("state_battle: map %d loaded successfully (%dx%d tiles)\n",
               map_id, data->map.width, data->map.height);

        if (data->map.palette_loaded) {
            fd2_render_set_palette_6bit(&game->render, data->map.palette);
            printf("state_battle: palette applied\n");
        }

        const char* fdicon_path = fd2_game_data_path(game, "FDICON.B24");
        if (fdicon_path && fd2_icon_init(fdicon_path) == 0) {
            printf("state_battle: FDICON.B24 initialized (%d icons)\n", fd2_icon_get_count());
        } else {
            printf("state_battle: FDICON.B24 initialization failed\n");
        }

        data->from_save = game->from_save;
        data->saved_num_fighters = game->save_char_count;

        /* Copy character data from save or map */
        data->total_char_count = game->from_save ? game->save_char_count : data->map.scene.char_pos_count;
        if (data->total_char_count < 0 || data->total_char_count > MAX_BATTLE_CHARS) {
            data->total_char_count = 0;
        }
        
        if (game->from_save) {
            for (int i = 0; i < data->total_char_count; i++) {
                memcpy(&data->char_data[i], game->save_char_full_data[i], sizeof(battle_char_data_t));
            }
        } else {
            for (int i = 0; i < data->total_char_count; i++) {
                fd2_map_char_pos_t* char_pos = &data->map.scene.char_positions[i];
                fd2_map_char_info_t* char_info = NULL;
                
                /* 尝试从char_info获取阵营信息 */
                if (i < data->map.scene.char_info_count) {
                    char_info = &data->map.scene.char_info[i];
                }
                
                data->char_data[i].tile_x = char_pos->x;
                data->char_data[i].tile_y = char_pos->y;
                data->char_data[i].faction = char_info ? char_info->faction : 0;  /* offset+4: 0=enemy, 1=NPC, 2=friendly */
                data->char_data[i].icon_id = char_pos->portrait_id;
                /* IDA sub_1C269: offset+26位掩码判断活跃角色
                   每行8个角色，5行共40个，每位=1表示活跃 */
                data->char_data[i].active_mask = 0x01; /* 角色i活跃 */
                data->char_data[i].active_byte = 0; /* offset+5: 0=存活 */
                /* IDA sub_1CFF0: v10[3]==0 显示移动范围，否则显示属性页
                   只有friendly(faction==2)的角色才是玩家可操作 */
                data->char_data[i].char_type = (char_info && char_info->faction == 2) ? 0 : 1;
                data->char_data[i].moved = 0; /* offset+9: 0=未移动 */
            }
        }

        int num_sprites = data->total_char_count;
        if (num_sprites <= 0) num_sprites = 1; /* Ensure at least 1 for calloc */
        data->sprites = (map_sprite_t*)calloc(num_sprites, sizeof(map_sprite_t));
        data->max_sprites = num_sprites;
        data->sprite_count = 0;

        printf("state_battle: allocating %d sprites (%s)\n", num_sprites,
               game->from_save ? "from SAVE" : "from FDFIELD.DAT");

        for (int i = 0; i < data->total_char_count && data->sprite_count < num_sprites; i++) {
            int tile_x = data->char_data[i].tile_x;
            int tile_y = data->char_data[i].tile_y;
            int icon_id = data->char_data[i].icon_id;

            if (tile_x == 0 && tile_y == 0) {
                continue;
            }

            /* IDA sub_14818: 检查 offset+5 的 bit0
               (v19[5] & 1) == 0 才显示在战场上
               bit0 == 1 表示死亡角色，不显示 */
            if ((data->char_data[i].active_byte & 1) != 0) {
                printf("  char[%d]: SKIP (dead, offset+5=0x%02X bit0=1)\n", i, data->char_data[i].active_byte);
                continue;
            }

            map_sprite_t* sprite = &data->sprites[data->sprite_count];
            sprite->tile_x = tile_x;
            sprite->tile_y = tile_y;
            sprite->icon_id = icon_id;
            sprite->cache_idx = -1;
            sprite->direction = 0;
            sprite->anim_frame = 0;
            sprite->anim_timer = 0;
            sprite->loaded = false;
            sprite->pixels = NULL;
            sprite->width = 24;
            sprite->height = 24;

            printf("  sprite[%d]: tile=(%d,%d), icon=%d, char_data_idx=%d\n",
                   data->sprite_count, tile_x, tile_y, icon_id, i);

            int cache_idx = fd2_icon_get(icon_id);
            if (cache_idx >= 0) {
                sprite->cache_idx = cache_idx;
                sprite->pixels = (u8*)calloc(1, sprite->width * sprite->height);
                if (sprite->pixels) {
                    int segment = 0;
                    if (fd2_icon_decode_segment(cache_idx, segment, sprite->width, sprite->height,
                                               sprite->pixels) == 0) {
                        sprite->loaded = true;
                    } else {
                        free(sprite->pixels);
                        sprite->pixels = NULL;
                    }
                }
            }

            data->sprite_count++;
        }

        printf("state_battle: created %d character sprites (total chars=%d, alive=%d)\n", 
               data->sprite_count, data->total_char_count, data->sprite_count);

        /* Calculate camera position to center on map characters */
        if (data->map.scene.loaded && data->map.scene.char_pos_count > 0) {
            int min_x = 999, min_y = 999, max_x = 0, max_y = 0;
            int valid_count = 0;

            for (int i = 0; i < data->map.scene.char_pos_count; i++) {
                fd2_map_char_pos_t* char_pos = &data->map.scene.char_positions[i];
                if (char_pos->x == 0 && char_pos->y == 0) continue;

                if (char_pos->x < min_x) min_x = char_pos->x;
                if (char_pos->y < min_y) min_y = char_pos->y;
                if (char_pos->x > max_x) max_x = char_pos->x;
                if (char_pos->y > max_y) max_y = char_pos->y;
                valid_count++;
            }

            if (valid_count > 0) {
                int center_tile_x = (min_x + max_x) / 2;
                int center_tile_y = (min_y + max_y) / 2;

                data->camera_x = center_tile_x * MAP_TILE_SIZE - FD2_SCREEN_W / 2;
                data->camera_y = center_tile_y * MAP_TILE_SIZE - FD2_SCREEN_H / 2;

                int max_cam_x = data->map.map_image_width - FD2_SCREEN_W;
                int max_cam_y = data->map.map_image_height - FD2_SCREEN_H;
                if (max_cam_x < 0) max_cam_x = 0;
                if (max_cam_y < 0) max_cam_y = 0;
                if (data->camera_x < 0) data->camera_x = 0;
                if (data->camera_y < 0) data->camera_y = 0;
                if (data->camera_x > max_cam_x) data->camera_x = max_cam_x;
                if (data->camera_y > max_cam_y) data->camera_y = max_cam_y;
            }
        } else {
            data->camera_x = (data->map.map_image_width - FD2_SCREEN_W) / 2;
            data->camera_y = (data->map.map_image_height - FD2_SCREEN_H) / 2;
            if (data->camera_x < 0) data->camera_x = 0;
            if (data->camera_y < 0) data->camera_y = 0;
        }

        /* 调用 battle_entry 初始化战场核心逻辑 (基于 IDA sub_18D8C) */
        int dst[4] = {0};
        int n17 = 0; /* 当前角色索引，从第一个角色开始 */
        int result = battle_entry(game, n17, dst, 0);
        if (result == -1) {
            printf("state_battle: battle_entry failed, returning to menu\n");
        } else {
            printf("state_battle: battle_entry completed (result=%d, dst=[%d,%d,%d])\n",
                   result, dst[0], dst[1], dst[2]);
        }

        fd2_map_render(&data->map, game->render.screen, FD2_SCREEN_W, FD2_SCREEN_H,
                       data->camera_x, data->camera_y);

        fd2_render_present(&game->render);
    } else {
        fprintf(stderr, "state_battle: failed to load map %d, showing black screen\n", map_id);
        fd2_render_fill_screen(&game->render, 0);
        fd2_render_present(&game->render);
    }
}

/**
 * 根据IDA分析，按回车/空格后的完整逻辑：
 * 
 * 1. 获取角色数据 v10 = sub_4E866(active_list[n2_3])
 * 2. dword_51A83 = v10[4] + 2  (阵营标志)
 * 3. n16 = v10[3]  (角色类型)
 * 4. 判断角色类型:
 *    - 玩家未移动 (v10[4]==0 && v10[6]==0):
 *      -> sub_14818 显示移动范围
 *      -> sub_115B6 等待选择移动目标
 *      -> 移动动画
 *    - 友军/敌军/已移动玩家:
 *      -> sub_11CAC 显示属性页
 *      -> sub_2FF01 执行功能
 */
static void handle_character_select(fd2_game_t* game, state_battle_data_t* data, int char_idx) {
    if (char_idx < 0 || char_idx >= data->total_char_count) {
        return;
    }

    battle_char_data_t* ch = &data->char_data[char_idx];
    
    /* IDA: dword_51A83 = v10[4] + 2 */
    /* v10[4] = faction (0=player, 1=ally, 2+=enemy) */
    g_char_state_flag = ch->faction + 2;

    printf("battle: selected char %d, faction=%d, char_type=%d, moved=%d, state_flag=%d\n",
           char_idx, ch->faction, ch->char_type, ch->moved, g_char_state_flag);

    /* IDA: if (!v10[3] || (n11_1 == 23)) - offset+3=0表示玩家未移动
       在我们的80字节结构中，char_type对应offset+6 */
    if (ch->char_type == 0 && ch->moved == 0) {
        /* 玩家未移动角色：显示移动范围 */
        data->battle_phase = BATTLE_PHASE_SHOW_MOVE_RANGE;
        data->selected_char_idx = char_idx;
        data->showing_move_range = true;
        
        /* 设置移动范围的中心位置（角色当前位置） */
        data->move_range_tile_x = ch->tile_x;
        data->move_range_tile_y = ch->tile_y;
        
        /* IDA: sub_14818(...) - 计算并标记可移动瓦片 */
        printf("battle: showing move range for char %d at (%d,%d)\n",
               char_idx, ch->tile_x, ch->tile_y);
    } else {
        /* 友军/敌军/已移动玩家：显示属性页 */
        data->battle_phase = BATTLE_PHASE_SHOW_STATUS;
        data->selected_char_idx = char_idx;
        
        /* IDA: sub_11CAC(...) - 渲染属性页 */
        printf("battle: showing status screen for char %d\n", char_idx);
    }
}

/**
 * 渲染移动范围
 * Based on IDA sub_122DC - 根据dword_51A83绘制不同范围的瓦片
 */
static void render_move_range(state_battle_data_t* data, u8* screen, int screen_w, int screen_h) {
    if (!data->showing_move_range) return;
    
    int center_x = data->move_range_tile_x;
    int center_y = data->move_range_tile_y;
    
    /* 根据角色移动力显示范围 (简化实现：显示3格范围) */
    int move_range = 3;
    
    /* 绘制可移动范围的边框 */
    u8 range_color = 42; /* 淡黄色 */
    
    for (int dy = -move_range; dy <= move_range; dy++) {
        for (int dx = -move_range; dx <= move_range; dx++) {
            /* Manhattan距离检查 */
            int dist = abs(dx) + abs(dy);
            if (dist > move_range) continue;
            
            int tile_x = center_x + dx;
            int tile_y = center_y + dy;
            
            /* 转换为屏幕坐标 */
            int sx = tile_x * MAP_TILE_SIZE - data->camera_x;
            int sy = tile_y * MAP_TILE_SIZE - data->camera_y;
            
            /* 检查是否在屏幕内 */
            if (sx < -MAP_TILE_SIZE || sx >= screen_w || 
                sy < -MAP_TILE_SIZE || sy >= screen_h) {
                continue;
            }
            
            /* 绘制瓦片边框 */
            for (int x = 0; x < MAP_TILE_SIZE; x++) {
                int px = sx + x;
                if (px >= 0 && px < screen_w) {
                    if (sy >= 0 && sy < screen_h) {
                        screen[sy * screen_w + px] = range_color;
                    }
                    int bottom = sy + MAP_TILE_SIZE - 1;
                    if (bottom >= 0 && bottom < screen_h) {
                        screen[bottom * screen_w + px] = range_color;
                    }
                }
            }
            for (int y = 0; y < MAP_TILE_SIZE; y++) {
                int py = sy + y;
                if (py >= 0 && py < screen_h) {
                    if (sx >= 0 && sx < screen_w) {
                        screen[py * screen_w + sx] = range_color;
                    }
                    int right = sx + MAP_TILE_SIZE - 1;
                    if (right >= 0 && right < screen_w) {
                        screen[py * screen_w + right] = range_color;
                    }
                }
            }
        }
    }
}

fd2_state_t state_battle_update(fd2_game_t* game) {
    state_battle_data_t* data = (state_battle_data_t*)game->state_data;
    if (!data) {
        return FD2_STATE_MENU;
    }

    if (fd2_action_pressed(&game->input, FD2_ACTION_ESCAPE)) {
        /* 如果在显示移动范围或属性页状态，返回选择角色状态 */
        if (data->battle_phase != BATTLE_PHASE_SELECT_CHAR) {
            data->battle_phase = BATTLE_PHASE_SELECT_CHAR;
            data->selected_char_idx = -1;
            data->showing_move_range = false;
            data->animating_move = false;
            printf("battle: cancelled, back to select\n");
        } else {
            return FD2_STATE_MENU;
        }
    }

#ifdef FD2_DEBUG
    if (fd2_action_pressed(&game->input, FD2_ACTION_DEBUG_GRID)) {
        data->debug_grid_enabled = !data->debug_grid_enabled;
    }
#endif

    /* Update all sprite animations - frame update every 12 frames (original game 12Hz) */
    for (int i = 0; i < data->sprite_count; i++) {
        data->sprites[i].anim_timer++;
        if (data->sprites[i].anim_timer >= 12) {
            data->sprites[i].anim_timer = 0;
            data->sprites[i].anim_frame = (data->sprites[i].anim_frame + 1) % 3;
        }

        int segment = data->sprites[i].direction * 3 + data->sprites[i].anim_frame;

        fd2_icon_decode_segment(data->sprites[i].cache_idx, segment,
                                data->sprites[i].width, data->sprites[i].height,
                                data->sprites[i].pixels);
    }

    /* Cursor movement - based on IDA sub_11B48, sub_11B9B, sub_11BFA, sub_11C59 */
    int map_width = data->map.width;
    int map_height = data->map.height;

    /* 根据当前阶段处理输入 */
    switch (data->battle_phase) {
        case BATTLE_PHASE_SELECT_CHAR: {
            /* 选择角色阶段：移动光标 */
            if (fd2_action_pressed(&game->input, FD2_ACTION_UP)) {
                cursor_move_up(data, map_height);
                update_camera_from_cursor(data);
            }
            if (fd2_action_pressed(&game->input, FD2_ACTION_DOWN)) {
                cursor_move_down(data, map_height);
                update_camera_from_cursor(data);
            }
            if (fd2_action_pressed(&game->input, FD2_ACTION_LEFT)) {
                cursor_move_left(data, map_width);
                update_camera_from_cursor(data);
            }
            if (fd2_action_pressed(&game->input, FD2_ACTION_RIGHT)) {
                cursor_move_right(data, map_width);
                update_camera_from_cursor(data);
            }

            /* Handle START key - select character at cursor position */
            /* IDA: sub_1D51D case 28/57 (Enter/Space) */
            if (fd2_action_pressed(&game->input, FD2_ACTION_START)) {
                int char_idx = battle_find_char_at_cursor(data);
                if (char_idx != -1) {
                    handle_character_select(game, data, char_idx);
                } else {
                    printf("battle: no valid char at cursor (%d,%d)\n",
                           data->cursor_x, data->cursor_y);
                }
            }
            break;
        }
        
        case BATTLE_PHASE_SHOW_MOVE_RANGE: {
            /* 显示移动范围阶段：选择移动目标 */
            if (fd2_action_pressed(&game->input, FD2_ACTION_UP)) {
                cursor_move_up(data, map_height);
                update_camera_from_cursor(data);
            }
            if (fd2_action_pressed(&game->input, FD2_ACTION_DOWN)) {
                cursor_move_down(data, map_height);
                update_camera_from_cursor(data);
            }
            if (fd2_action_pressed(&game->input, FD2_ACTION_LEFT)) {
                cursor_move_left(data, map_width);
                update_camera_from_cursor(data);
            }
            if (fd2_action_pressed(&game->input, FD2_ACTION_RIGHT)) {
                cursor_move_right(data, map_width);
                update_camera_from_cursor(data);
            }

            /* 按START确认移动目标 */
            /* IDA: sub_115B6 - 等待输入，按回车确认移动 */
            if (fd2_action_pressed(&game->input, FD2_ACTION_START)) {
                /* 开始移动动画 */
                data->animating_move = true;
                data->anim_move_progress = 0;
                data->battle_phase = BATTLE_PHASE_ANIM_MOVE;
                printf("battle: start move animation to (%d,%d)\n",
                       data->cursor_x, data->cursor_y);
            }
            break;
        }
        
        case BATTLE_PHASE_ANIM_MOVE: {
            /* 移动动画阶段 */
            data->anim_move_progress++;
            
            /* 简化动画：8帧后完成移动 */
            if (data->anim_move_progress >= 8) {
                /* 更新角色位置 */
                battle_char_data_t* ch = &data->char_data[data->selected_char_idx];
                
                /* 更新sprite位置 */
                if (data->selected_char_idx < data->sprite_count) {
                    data->sprites[data->selected_char_idx].tile_x = data->cursor_x;
                    data->sprites[data->selected_char_idx].tile_y = data->cursor_y;
                }
                
                /* 更新char_data位置 */
                ch->tile_x = data->cursor_x;
                ch->tile_y = data->cursor_y;
                
                /* 标记为已移动 */
                ch->moved = 1;
                
                /* 移动完成，显示属性页 */
                data->animating_move = false;
                data->showing_move_range = false;
                data->battle_phase = BATTLE_PHASE_SHOW_STATUS;
                printf("battle: move complete, showing status\n");
            }
            break;
        }
        
        case BATTLE_PHASE_SHOW_STATUS: {
            /* 显示属性页阶段：按X/B取消 */
            if (fd2_action_pressed(&game->input, FD2_ACTION_B) ||
                fd2_action_pressed(&game->input, FD2_ACTION_X)) {
                /* 标记回合结束，返回选择角色 */
                data->battle_phase = BATTLE_PHASE_SELECT_CHAR;
                data->selected_char_idx = -1;
                printf("battle: status closed, back to select\n");
            }
            break;
        }
    }

    data->cursor_blink++;

    /* Render map */
    if (data->map.loaded && data->map.map_rendered) {
        /* 常规渲染：地图+精灵+光标+地形信息 */
        fd2_map_render(&data->map, game->render.screen, FD2_SCREEN_W, FD2_SCREEN_H,
                       data->camera_x, data->camera_y);

#ifdef FD2_DEBUG
        if (data->debug_grid_enabled) {
            battle_render_debug_grid(data, game->render.screen, FD2_SCREEN_W, FD2_SCREEN_H);
        }
#endif

        /* Draw sprites */
        battle_render_sprites(data->sprites, data->sprite_count,
                              data->camera_x, data->camera_y,
                              game->render.screen, FD2_SCREEN_W, FD2_SCREEN_H);

        /* Draw selected character highlight */
        if (data->selected_char_idx >= 0 && data->selected_char_idx < data->sprite_count) {
            map_sprite_t* sprite = &data->sprites[data->selected_char_idx];
            int sx = sprite->tile_x * MAP_TILE_SIZE - data->camera_x;
            int sy = sprite->tile_y * MAP_TILE_SIZE - data->camera_y;

            u8 highlight_color;
            /* 根据阶段使用不同颜色 */
            switch (data->battle_phase) {
                case BATTLE_PHASE_SHOW_MOVE_RANGE:
                    highlight_color = 60; /* 黄色 - 正在选择移动 */
                    break;
                case BATTLE_PHASE_SHOW_STATUS:
                    highlight_color = 63; /* 白色 - 显示属性 */
                    break;
                default:
                    highlight_color = 63; /* 白色 */
                    break;
            }

            /* Draw border */
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

        /* 渲染移动范围 */
        if (data->showing_move_range) {
            render_move_range(data, game->render.screen, FD2_SCREEN_W, FD2_SCREEN_H);
        }

        /* Draw cursor */
        battle_render_cursor(data, game->render.screen, FD2_SCREEN_W, FD2_SCREEN_H);

        /* Draw terrain info UI - based on IDA sub_126F7 */
        battle_render_terrain_info(data, game->render.screen, FD2_SCREEN_W, FD2_SCREEN_H);

        /* 渲染角色信息面板 */
        if (data->selected_char_idx >= 0) {
            if (data->fdfield_layout && data->fdshap_data && data->backbuffer) {
                battle_render_info_panel(
                    data->selected_char_idx,
                    (const u8*)data->char_data,
                    data->fdfield_layout,
                    data->fdshap_flags,
                    data->fdother_palette_map,
                    data->fdshap_data,
                    data->backbuffer,
                    data->layout_width,
                    data->palette_anim_frame,
                    data->n3_1
                );
            }
        }

        fd2_render_present(&game->render);
    }

    return FD2_STATE_BATTLE;
}

void state_battle_exit(fd2_game_t* game) {
    state_battle_data_t* data = (state_battle_data_t*)game->state_data;
    if (data) {
        /* Free player turn resources */
        battle_turn_cleanup(data);
        
        /* Free resources loaded via sub_111BA */
        if (data->fdother_resource_5) {
            free(data->fdother_resource_5);
            data->fdother_resource_5 = NULL;
        }
        if (data->fdother_resource_3) {
            free(data->fdother_resource_3);
            data->fdother_resource_3 = NULL;
        }
        battle_free_sprites(data->sprites, data->sprite_count);
        fd2_map_free(&data->map);
        free(data);
    }
    game->state_data = NULL;
}
