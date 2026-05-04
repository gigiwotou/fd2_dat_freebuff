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
    data->selected_char_idx = -1;
    data->cursor_char_frame_id = 0;
    data->terrain_info_data = NULL;
    data->terrain_info_data_size = 0;
    memset(data->terrain_info_buffer, 0, sizeof(data->terrain_info_buffer));

    /* Initialize resource pointers to NULL */
    data->fdother_resource_5 = NULL;
    data->fdother_resource_5_size = 0;
    data->fdother_resource_3 = NULL;
    data->fdother_resource_3_size = 0;
    data->fdother_data = NULL;
    data->fdother_data_size = 0;

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
        return FD2_STATE_MENU;
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

    data->cursor_blink++;

    /* Handle START key - select character at cursor position (based on IDA sub_12C0D) */
    if (fd2_action_pressed(&game->input, FD2_ACTION_START)) {
        int char_idx = battle_find_char_at_cursor(data);
        if (char_idx != -1) {
            data->selected_char_idx = char_idx;
            map_sprite_t* sprite = &data->sprites[char_idx];
            printf("battle: selected char %d at (%d,%d) icon=%d\n",
                   char_idx, sprite->tile_x, sprite->tile_y, sprite->icon_id);
        } else {
            data->selected_char_idx = -1;
            printf("battle: no valid char at cursor (%d,%d)\n",
                   data->cursor_x, data->cursor_y);
        }
    }

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

        /* Draw selected character highlight - white border */
        if (data->selected_char_idx >= 0 && data->selected_char_idx < data->sprite_count) {
            map_sprite_t* sprite = &data->sprites[data->selected_char_idx];
            int sx = sprite->tile_x * MAP_TILE_SIZE - data->camera_x;
            int sy = sprite->tile_y * MAP_TILE_SIZE - data->camera_y;

            u8 highlight_color = 63; /* White */

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

        /* Draw cursor */
        battle_render_cursor(data, game->render.screen, FD2_SCREEN_W, FD2_SCREEN_H);

        /* Draw terrain info UI - based on IDA sub_126F7 */
        battle_render_terrain_info(data, game->render.screen, FD2_SCREEN_W, FD2_SCREEN_H);

        fd2_render_present(&game->render);
    }

    return FD2_STATE_BATTLE;
}

void state_battle_exit(fd2_game_t* game) {
    state_battle_data_t* data = (state_battle_data_t*)game->state_data;
    if (data) {
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
