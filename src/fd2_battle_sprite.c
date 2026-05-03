/**
 * FD2 Battle Sprite System
 *
 * Map character sprites on the battle map.
 * Based on IDA analysis of sub_2B4FB, sub_2921A, sub_10010, sub_1C2DA.
 */

#define _GNU_SOURCE
#include "fd2_game.h"
#include "fd2_battle.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static inline int tile_to_screen_x(int tile_x, int camera_x) {
    return tile_x * MAP_TILE_SIZE - camera_x;
}

static inline int tile_to_screen_y(int tile_y, int camera_y) {
    return tile_y * MAP_TILE_SIZE - camera_y;
}

static inline bool is_sprite_visible(int screen_x, int screen_y, int width, int height) {
    return (screen_x + width > 0 && screen_x < FD2_SCREEN_W &&
            screen_y + height > 0 && screen_y < FD2_SCREEN_H);
}

static bool load_map_sprite_icon(map_sprite_t* sprite, int icon_id) {
    if (!sprite) return false;

    int cache_idx = fd2_icon_get(icon_id);
    if (cache_idx < 0) {
        printf("load_map_sprite_icon: icon %d not found\n", icon_id);
        return false;
    }

    sprite->icon_id = icon_id;
    sprite->cache_idx = cache_idx;
    sprite->direction = 0;
    sprite->anim_frame = 0;
    sprite->anim_timer = 0;

    sprite->width = 24;
    sprite->height = 24;
    sprite->pixels = (u8*)calloc(1, sprite->width * sprite->height);
    if (!sprite->pixels) return false;

    if (fd2_icon_decode_segment(cache_idx, 0,
                                sprite->width, sprite->height,
                                sprite->pixels) != 0) {
        free(sprite->pixels);
        sprite->pixels = NULL;
        return false;
    }

    sprite->loaded = true;
    return true;
}

static void update_map_sprite_animation(map_sprite_t* sprite) {
    if (!sprite || !sprite->loaded) return;

    sprite->anim_timer++;
    if (sprite->anim_timer >= 8) {
        sprite->anim_timer = 0;
        sprite->anim_frame = (sprite->anim_frame + 1) % 3;
    }

    int segment = sprite->direction * 3 + sprite->anim_frame;

    fd2_icon_decode_segment(sprite->cache_idx, segment,
                            sprite->width, sprite->height,
                            sprite->pixels);
}

static void move_sprite_to_tile(map_sprite_t* sprite, int new_tile_x, int new_tile_y) {
    if (sprite) {
        sprite->tile_x = new_tile_x;
        sprite->tile_y = new_tile_y;
    }
}

void battle_render_sprites(map_sprite_t* sprites, int sprite_count,
                           int camera_x, int camera_y,
                           u8* screen, int screen_w, int screen_h) {
    for (int i = 0; i < sprite_count; i++) {
        map_sprite_t* sprite = &sprites[i];
        if (!sprite->loaded || !sprite->pixels) continue;

        int screen_x = sprite->tile_x * MAP_TILE_SIZE - camera_x;
        int screen_y = sprite->tile_y * MAP_TILE_SIZE - camera_y - 6;

        int draw_x = screen_x;
        int draw_y = screen_y;

        int visible = is_sprite_visible(draw_x, draw_y, sprite->width, sprite->height);

        if (visible) {
            fd2_sprite_frame_t frame;
            frame.pixels = sprite->pixels;
            frame.width = sprite->width;
            frame.height = sprite->height;
            frame.pixel_data_size = sprite->width * sprite->height;

            fd2_sprite_render(&frame, screen, screen_w, draw_x, draw_y);
        }
    }
}

void battle_free_sprites(map_sprite_t* sprites, int sprite_count) {
    if (!sprites) return;
    for (int i = 0; i < sprite_count; i++) {
        if (sprites[i].pixels) {
            free(sprites[i].pixels);
        }
    }
    free(sprites);
}

int battle_load_sprites(fd2_game_t* game, map_sprite_t** out_sprites,
                        int num_sprites, bool from_save,
                        u8 char_positions[64][2], u8 char_icons[64],
                        fd2_map_t* map_data) {
    map_sprite_t* sprites = (map_sprite_t*)calloc(num_sprites, sizeof(map_sprite_t));
    if (!sprites) return 0;

    int sprite_count = 0;

    for (int i = 0; i < num_sprites && sprite_count < num_sprites; i++) {
        int tile_x, tile_y, icon_id;

        if (from_save) {
            tile_x = char_positions[i][0];
            tile_y = char_positions[i][1];
            icon_id = char_icons[i];
        } else {
            tile_x = map_data->scene.char_positions[i].x;
            tile_y = map_data->scene.char_positions[i].y;
            icon_id = map_data->scene.char_positions[i].portrait_id;
        }

        if (tile_x == 0 && tile_y == 0) {
            sprite_count++;
            continue;
        }

        map_sprite_t* sprite = &sprites[sprite_count];
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

        printf("  sprite[%d]: tile=(%d,%d), icon=%d\n", sprite_count, tile_x, tile_y, icon_id);

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

        sprite_count++;
    }

    printf("state_battle: created %d character sprites\n", sprite_count);

    *out_sprites = sprites;
    return sprite_count;
}

void battle_update_sprite_animations(map_sprite_t* sprites, int sprite_count) {
    for (int i = 0; i < sprite_count; i++) {
        /* Update animation frame counter */
        sprites[i].anim_timer++;
        if (sprites[i].anim_timer >= 8) {
            sprites[i].anim_timer = 0;
            sprites[i].anim_frame = (sprites[i].anim_frame + 1) % 3;
        }

        int segment = sprites[i].direction * 3 + sprites[i].anim_frame;

        fd2_icon_decode_segment(sprites[i].cache_idx, segment,
                                sprites[i].width, sprites[i].height,
                                sprites[i].pixels);
    }
}
