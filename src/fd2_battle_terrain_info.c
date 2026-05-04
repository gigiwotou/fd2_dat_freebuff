/**
 * FD2 Battle Terrain Info UI
 *
 * Based on IDA sub_126F7 and sub_4E22A.
 */

#define _GNU_SOURCE
#include "fd2_game.h"
#include "fd2_battle.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/*
 * RLE decode function - based on IDA sub_4E22A.
 */
static void rle_decode_terrain_image(const u8* src, u8* dst, int stride) {
    const u8* src_ptr = src;
    u8* dst_ptr = dst;
    int stride_minus_24 = stride - 24;
    
    for (int row = 0; row < 24; row++) {
        int bh = 24;
        
        while (bh > 0) {
            u8 al = *src_ptr++;
            
            if (al & 0x80) {
                if ((al & 0x40) == 0) {
                    int count = (al >> 2) + 1;
                    if (count > bh) count = bh;
                    memcpy(dst_ptr, src_ptr, count);
                    src_ptr += count;
                    dst_ptr += count;
                    bh -= count;
                } else {
                    int count = (al >> 2) + 1;
                    if (count > bh) count = bh;
                    dst_ptr += count;
                    bh -= count;
                }
            } else {
                if ((al & 0x40) == 0) {
                    int count = (al >> 2) + 1;
                    if (count > bh) count = bh;
                    u8 fill_color = *src_ptr++;
                    memset(dst_ptr, fill_color, count);
                    dst_ptr += count;
                    bh -= count;
                } else {
                    int count = (al >> 2) + 1;
                    bh -= count;
                    bh -= count;
                    
                    u8 fill_color = *src_ptr++;
                    for (int i = 0; i < count; i++) {
                        dst_ptr++;
                        *dst_ptr++ = fill_color;
                    }
                }
            }
        }
        
        dst_ptr += stride_minus_24;
    }
}

int load_terrain_info_data(fd2_game_t* game, state_battle_data_t* data) {
    const char* fdother_path = fd2_resources_dat_path(&game->resources, FD2_DAT_FDOTHER);
    if (!fdother_path) {
        printf("battle terrain: FDOTHER.DAT path not available\n");
        return -1;
    }

    /* Free existing terrain info resource if present */
    if (data->fdother_resource_3) {
        free(data->fdother_resource_3);
        data->fdother_resource_3 = NULL;
        data->terrain_info_data = NULL;
        data->terrain_info_data_size = 0;
    }

    /* Load FDOTHER.DAT resource 3 via sub_111BA */
    data->fdother_resource_3 = fd2_dat_load_resource(fdother_path, NULL, 3);
    if (data->fdother_resource_3) {
        data->terrain_info_data = data->fdother_resource_3;
        data->terrain_info_data_size = fd2_last_loaded_size;
        printf("battle terrain: FDOTHER resource 3 loaded (%u bytes)\n", data->terrain_info_data_size);
        return 0;
    }

    printf("battle terrain: FDOTHER resource 3 failed to load\n");
    return -1;
}

void battle_render_terrain_info(state_battle_data_t* data, u8* screen, int screen_w, int screen_h) {
    if (!data->terrain_info_data || !data->map.loaded) {
        return;
    }

    int cursor_x = data->cursor_x;
    int cursor_y = data->cursor_y;

    if (cursor_x < 0 || cursor_x >= data->map.width ||
        cursor_y < 0 || cursor_y >= data->map.height) {
        return;
    }

    int terrain_id = data->map.tiles[cursor_y][cursor_x].terrain_id;

    const u8* terrain_info_base = data->terrain_info_data;
    
    u32 offset_ptr = 6 + 4 * terrain_id;
    
    if (offset_ptr + 4 > data->terrain_info_data_size) {
        return;
    }

    u32 image_offset = terrain_info_base[offset_ptr] |
                      (terrain_info_base[offset_ptr + 1] << 8) |
                      (terrain_info_base[offset_ptr + 2] << 16) |
                      (terrain_info_base[offset_ptr + 3] << 24);

    if (image_offset >= data->terrain_info_data_size) {
        return;
    }

    const u8* terrain_image_data = terrain_info_base + image_offset;

    /* Decode RLE image to buffer at position based on cursor */
    int dst_stride = TERRAIN_INFO_WIDTH;  /* 456 */
    memset(data->terrain_info_buffer, 0, sizeof(data->terrain_info_buffer));
    
    /* Buffer position: 456 * cursor_y + 24 * cursor_x (from IDA 12747-12774) */
    u8* dst_in_buffer = data->terrain_info_buffer + 456 * cursor_y + 24 * cursor_x;
    
    rle_decode_terrain_image(terrain_image_data, dst_in_buffer, dst_stride);

    /* Render buffer to screen at bottom center */
    int box_x = (FD2_SCREEN_W - TERRAIN_INFO_WIDTH) / 2;
    int box_y = FD2_SCREEN_H - 24 - 4;

    for (int y = 0; y < 24; y++) {
        int screen_y = box_y + y;
        if (screen_y < 0 || screen_y >= screen_h) continue;
        for (int x = 0; x < TERRAIN_INFO_WIDTH; x++) {
            int screen_x = box_x + x;
            if (screen_x < 0 || screen_x >= screen_w) continue;
            
            u8 pixel = data->terrain_info_buffer[y * dst_stride + x];
            if (pixel != 0) {
                screen[screen_y * screen_w + screen_x] = pixel;
            }
        }
    }
}
