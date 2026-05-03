/**
 * FD2 BATTLE State
 *
 * In-game fight. Uses fd2_map_loader to load and render maps from DAT files.
 */

#define _GNU_SOURCE
#include "fd2_game.h"
#include "fd2_battle.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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
    data->cursor_frame_id = 242;

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

    data->interaction_state = BATTLE_STATE_IDLE;
    data->selected_char_idx = -1;
    data->menu_selected_idx = 0;
    data->menu_item_count = 0;
    data->submenu_selected_idx = 0;
    data->submenu_item_count = 0;
    data->target_tile_x = 0;
    data->target_tile_y = 0;

    fd2_resources_load_dat(&game->resources, FD2_DAT_FDFIELD);
    fd2_resources_load_dat(&game->resources, FD2_DAT_FDSHAP);
    fd2_resources_load_dat(&game->resources, FD2_DAT_FDOTHER);

    const fd2_dat_t* fdother_dat = fd2_resources_get_dat(&game->resources, FD2_DAT_FDOTHER);
    if (fdother_dat) {
        u32 resource5_size = 0;
        const u8* resource5_data = fd2_dat_get_resource(fdother_dat, 5, &resource5_size);

        if (resource5_data && resource5_size > 0) {
            data->fdother_data = resource5_data;
            data->fdother_data_size = resource5_size;
            printf("state_battle: FDOTHER resource index 5 loaded (%u bytes)\n", resource5_size);

            if (load_cursor_image(game, data) == 0) {
                printf("state_battle: cursor image loaded OK, %dx%d\n",
                       data->cursor_image_width, data->cursor_image_height);
            } else {
                printf("state_battle: cursor image load FAILED\n");
            }
        } else {
            printf("state_battle: FDOTHER resource index 5 not found\n");
        }
    } else {
        printf("state_battle: FDOTHER.DAT not available\n");
    }

    int map_id = game->map_index;
    printf("state_battle: loading map %d from DAT files\n", map_id);

    const char* fdfield_path = fd2_resources_dat_path(&game->resources, FD2_DAT_FDFIELD);
    const char* fdshap_path = fd2_resources_dat_path(&game->resources, FD2_DAT_FDSHAP);
    const char* fdother_path = fd2_resources_dat_path(&game->resources, FD2_DAT_FDOTHER);

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

        int num_sprites = game->from_save ? game->save_char_count : data->map.scene.char_pos_count;
        data->sprites = (map_sprite_t*)calloc(num_sprites, sizeof(map_sprite_t));
        data->max_sprites = num_sprites;
        data->sprite_count = 0;

        printf("state_battle: allocating %d sprites (%s)\n", num_sprites,
               game->from_save ? "from SAVE" : "from FDFIELD.DAT");

        for (int i = 0; i < num_sprites && data->sprite_count < num_sprites; i++) {
            int tile_x, tile_y, icon_id;

            if (game->from_save) {
                tile_x = game->save_char_positions[i][0];
                tile_y = game->save_char_positions[i][1];
                icon_id = game->save_char_icons[i];
            } else {
                tile_x = data->map.scene.char_positions[i].x;
                tile_y = data->map.scene.char_positions[i].y;
                icon_id = data->map.scene.char_positions[i].portrait_id;
            }

            if (tile_x == 0 && tile_y == 0) {
                data->sprite_count++;
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

            printf("  sprite[%d]: tile=(%d,%d), icon=%d\n",
                   data->sprite_count, tile_x, tile_y, icon_id);

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

        printf("state_battle: created %d character sprites\n", data->sprite_count);

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

        fd2_map_render(&data->map, game->render.screen, FD2_SCREEN_W, FD2_SCREEN_H,
                       data->camera_x, data->camera_y);

        fd2_render_present(&game->render);
    } else {
        fprintf(stderr, "state_battle: failed to load map %d, showing black screen\n", map_id);
        fd2_render_fill_screen(&game->render, 0);
        fd2_render_present(&game->render);
    }
}

fd2_state_t state_battle_update(fd2_game_t* game) {
    state_battle_data_t* data = (state_battle_data_t*)game->state_data;
    if (!data) {
        return FD2_STATE_MENU;
    }

    if (fd2_action_pressed(&game->input, FD2_ACTION_ESCAPE)) {
        if (data->interaction_state == BATTLE_STATE_MENU ||
            data->interaction_state == BATTLE_STATE_SUBMENU ||
            data->interaction_state == BATTLE_STATE_CHAR_SELECTED) {
            data->interaction_state = BATTLE_STATE_IDLE;
            data->selected_char_idx = -1;
        } else if (data->interaction_state == BATTLE_STATE_IDLE) {
            return FD2_STATE_MENU;
        }
    }

#ifdef FD2_DEBUG
    if (fd2_action_pressed(&game->input, FD2_ACTION_DEBUG_GRID)) {
        data->debug_grid_enabled = !data->debug_grid_enabled;
    }
#endif

    /* Update all sprite animations */
    for (int i = 0; i < data->sprite_count; i++) {
        data->sprites[i].anim_timer++;
        if (data->sprites[i].anim_timer >= 8) {
            data->sprites[i].anim_timer = 0;
            data->sprites[i].anim_frame = (data->sprites[i].anim_frame + 1) % 3;
        }

        int segment = data->sprites[i].direction * 3 + data->sprites[i].anim_frame;

        fd2_icon_decode_segment(data->sprites[i].cache_idx, segment,
                                data->sprites[i].width, data->sprites[i].height,
                                data->sprites[i].pixels);
    }

    int map_width = data->map.width;
    int map_height = data->map.height;

    switch (data->interaction_state) {
        case BATTLE_STATE_IDLE:
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

            if (fd2_action_pressed(&game->input, FD2_ACTION_START)) {
                int char_idx = -1;
                for (int i = 0; i < data->sprite_count; i++) {
                    if (data->sprites[i].loaded &&
                        data->sprites[i].tile_x == data->cursor_x &&
                        data->sprites[i].tile_y == data->cursor_y) {
                        char_idx = i;
                        break;
                    }
                }

                if (char_idx != -1) {
                    data->interaction_state = BATTLE_STATE_CHAR_SELECTED;
                    data->selected_char_idx = char_idx;
                    printf("cursor confirm: selected sprite %d at (%d,%d)\n",
                           char_idx, data->cursor_x, data->cursor_y);
                } else {
                    printf("cursor confirm: no sprite at (%d,%d)\n",
                           data->cursor_x, data->cursor_y);
                }
            }
            break;

        case BATTLE_STATE_CHAR_SELECTED:
            if (fd2_action_pressed(&game->input, FD2_ACTION_START)) {
                battle_init_main_menu(data, data->selected_char_idx);
                data->interaction_state = BATTLE_STATE_MENU;
                data->menu_selected_idx = 0;
            }
            break;

        case BATTLE_STATE_MENU:
            if (fd2_action_pressed(&game->input, FD2_ACTION_UP)) {
                battle_menu_move_up(data);
            }
            if (fd2_action_pressed(&game->input, FD2_ACTION_DOWN)) {
                battle_menu_move_down(data);
            }
            if (fd2_action_pressed(&game->input, FD2_ACTION_START)) {
                printf("menu item selected: %s (action=%d)\n",
                       data->menu_items[data->menu_selected_idx].text,
                       data->menu_items[data->menu_selected_idx].action_id);
                /* TODO: Handle menu item action */
            }
            break;

        case BATTLE_STATE_SUBMENU:
            if (fd2_action_pressed(&game->input, FD2_ACTION_UP)) {
                if (data->submenu_selected_idx > 0) {
                    data->submenu_selected_idx--;
                }
            }
            if (fd2_action_pressed(&game->input, FD2_ACTION_DOWN)) {
                if (data->submenu_selected_idx < data->submenu_item_count - 1) {
                    data->submenu_selected_idx++;
                }
            }
            if (fd2_action_pressed(&game->input, FD2_ACTION_START)) {
                printf("submenu item selected: %s (action=%d)\n",
                       data->submenu_items[data->submenu_selected_idx].text,
                       data->submenu_items[data->submenu_selected_idx].action_id);
                data->interaction_state = BATTLE_STATE_IDLE;
            }
            break;

        case BATTLE_STATE_TARGET_SELECT:
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
            if (fd2_action_pressed(&game->input, FD2_ACTION_START)) {
                data->target_tile_x = data->cursor_x;
                data->target_tile_y = data->cursor_y;
                printf("target selected: (%d,%d)\n", data->target_tile_x, data->target_tile_y);
                data->interaction_state = BATTLE_STATE_IDLE;
            }
            break;

        case BATTLE_STATE_ANIMATING:
            break;
    }

    data->cursor_blink++;

    /* Render map */
    if (data->map.loaded && data->map.map_rendered) {
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

        /* Draw cursor */
        battle_render_cursor(data, game->render.screen, FD2_SCREEN_W, FD2_SCREEN_H);

        /* Draw selected character indicator */
        if (data->interaction_state == BATTLE_STATE_CHAR_SELECTED &&
            data->selected_char_idx >= 0) {
            map_sprite_t* sprite = &data->sprites[data->selected_char_idx];
            int sx = sprite->tile_x * MAP_TILE_SIZE - data->camera_x;
            int sy = sprite->tile_y * MAP_TILE_SIZE - data->camera_y;

            for (int x = 0; x < MAP_TILE_SIZE; x++) {
                int px = sx + x;
                if (px >= 0 && px < FD2_SCREEN_W && sy >= 0 && sy < FD2_SCREEN_H) {
                    game->render.screen[sy * FD2_SCREEN_W + px] = 63;
                }
                int bottom_y = sy + MAP_TILE_SIZE - 1;
                if (px >= 0 && px < FD2_SCREEN_W && bottom_y >= 0 && bottom_y < FD2_SCREEN_H) {
                    game->render.screen[bottom_y * FD2_SCREEN_W + px] = 63;
                }
            }
            for (int y = 0; y < MAP_TILE_SIZE; y++) {
                int py = sy + y;
                if (sx >= 0 && sx < FD2_SCREEN_W && py >= 0 && py < FD2_SCREEN_H) {
                    game->render.screen[py * FD2_SCREEN_W + sx] = 63;
                }
                int right_x = sx + MAP_TILE_SIZE - 1;
                if (right_x >= 0 && right_x < FD2_SCREEN_W && py >= 0 && py < FD2_SCREEN_H) {
                    game->render.screen[py * FD2_SCREEN_W + right_x] = 63;
                }
            }
        }

        /* Draw menu if in menu state */
        if (data->interaction_state == BATTLE_STATE_MENU ||
            data->interaction_state == BATTLE_STATE_SUBMENU) {
            battle_render_menu(data, game->render.screen, FD2_SCREEN_W, FD2_SCREEN_H);
        }

        /* Draw text box for character info */
        if (data->interaction_state == BATTLE_STATE_CHAR_SELECTED) {
            battle_render_text_box(data, game->render.screen, FD2_SCREEN_W, FD2_SCREEN_H);
        }

        fd2_render_present(&game->render);
    }

    return FD2_STATE_BATTLE;
}

void state_battle_exit(fd2_game_t* game) {
    state_battle_data_t* data = (state_battle_data_t*)game->state_data;
    if (data) {
        battle_free_sprites(data->sprites, data->sprite_count);
        fd2_map_free(&data->map);
        free(data);
    }
    game->state_data = NULL;
}
