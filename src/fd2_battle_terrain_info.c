/**
 * FD2 Battle Terrain Info UI
 *
 * Based on IDA sub_126F7 and sub_4E22A.
 */

#define _GNU_SOURCE
#include "fd2_game.h"
#include "fd2_battle.h"
#include <stdio.h>
#include <string.h>

/*
 * RLE decode function - based on IDA sub_4E22A.
 */
static void rle_decode_terrain_image(const u8* src, u8* dst, int stride) {
    const u8* src_ptr = src;
    u8* dst_ptr = dst;
    int stride_minus_24 = stride - 24;
    
    /* Outer loop: bl = 24 rows */
    for (int row = 0; row < 24; row++) {
        /* Inner: bh = 24 columns remaining */
        int bh = 24;
        
        while (bh > 0) {
            u8 al = *src_ptr++;
            u8 cl = al;
            
            /* shl cl, 1 -> CF = bit 7 */
            if (al & 0x80) {
                /* bit 7 set */
                
                /* shl cl, 1 again -> CF = bit 6 */
                if ((al & 0x40) == 0) {
                    /* bit 6 = 0: copy mode (rep movsb) */
                    int count = (al >> 2) + 1;
                    if (count > bh) count = bh;
                    memcpy(dst_ptr, src_ptr, count);
                    src_ptr += count;
                    dst_ptr += count;
                    bh -= count;
                } else {
                    /* bit 6 = 1: skip mode (dst += count) */
                    int count = (al >> 2) + 1;
                    if (count > bh) count = bh;
                    dst_ptr += count;
                    bh -= count;
                }
            } else {
                /* bit 7 clear */
                
                /* shl cl, 1 again -> CF = bit 6 */
                if ((al & 0x40) == 0) {
                    /* bit 6 = 0: fill mode (rep stosb) */
                    int count = (al >> 2) + 1;
                    if (count > bh) count = bh;
                    u8 fill_color = *src_ptr++;
                    memset(dst_ptr, fill_color, count);
                    dst_ptr += count;
                    bh -= count;
                } else {
                    /* bit 6 = 1: interleave mode */
                    /* 4E262: sub bh, cl; 4E264: sub bh, cl -> bh -= 2*cl */
                    int count = (al >> 2) + 1;
                    bh -= count;
                    bh -= count;
                    
                    u8 fill_color = *src_ptr++;
                    /* 4E267: inc edi; stosb; loop -> 
                     * Each iteration: dst++, *dst++=color -> writes 1 byte, advances 2 bytes
                     * Loop uses ecx which is cl after shr+inc (count-1 iterations since loop decrements first)
                     */
                    for (int i = 0; i < count; i++) {
                        dst_ptr++;
                        *dst_ptr++ = fill_color;
                    }
                }
            }
        }
        
        /* Next row: dst += (stride - 24) */
        dst_ptr += stride_minus_24;
    }
}

int load_terrain_info_data(fd2_game_t* game, state_battle_data_t* data) {
    const fd2_dat_t* fdother_dat = fd2_resources_get_dat(&game->resources, FD2_DAT_FDOTHER);
    if (!fdother_dat) {
        printf("battle terrain: FDOTHER.DAT not available\n");
        return -1;
    }

    u32 resource3_size = 0;
    const u8* resource3_data = fd2_dat_get_resource(fdother_dat, 3, &resource3_size);
    if (resource3_data && resource3_size > 0) {
        data->terrain_info_data = resource3_data;
        data->terrain_info_data_size = resource3_size;
        printf("battle terrain: FDOTHER resource 3 loaded (%u bytes)\n", resource3_size);
        return 0;
    }

    printf("battle terrain: FDOTHER resource 3 not found\n");
    return -1;
}

void battle_render_terrain_info(state_battle_data_t* data, u8* screen, int screen_w, int screen_h) {
    if (!data->terrain_info_data || !data->map.loaded) {
        static int warned = 0;
        if (!warned++) {
            printf("battle terrain: skipping render - terrain_info_data=%p, map.loaded=%d\n", 
                   (void*)data->terrain_info_data, data->map.loaded);
        }
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
    
    /* Resource 3 format (from IDA 12779-12783):
     *   edx = FDOTHER_DAT__3
     *   edx += [edx + a7*4 + 6]
     * So: offset table starts at byte 6, each entry is 4 bytes (little-endian)
     * The value is an offset from the start of resource 3 data
     */
    
    u32 offset_table_start = 6;
    u32 offset_ptr = offset_table_start + 4 * terrain_id;
    
    if (offset_ptr + 4 > data->terrain_info_data_size) {
        static int warned = 0;
        if (!warned++) {
            printf("battle terrain: terrain_id %d offset out of range (size=%u)\n",
                   terrain_id, data->terrain_info_data_size);
        }
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

    /* Decode RLE image */
    int dst_stride = TERRAIN_INFO_WIDTH;  /* 456 */
    u8 decoded_buffer[TERRAIN_INFO_WIDTH * 24];
    memset(decoded_buffer, 0, sizeof(decoded_buffer));
    
    rle_decode_terrain_image(terrain_image_data, decoded_buffer, dst_stride);

    /* Render to screen */
    int box_x = (FD2_SCREEN_W - TERRAIN_INFO_WIDTH) / 2;
    int box_y = FD2_SCREEN_H - 24 - 4;

    for (int y = 0; y < 24; y++) {
        int screen_y = box_y + y;
        if (screen_y < 0 || screen_y >= screen_h) continue;
        for (int x = 0; x < TERRAIN_INFO_WIDTH; x++) {
            int screen_x = box_x + x;
            if (screen_x < 0 || screen_x >= screen_w) continue;
            
            u8 pixel = decoded_buffer[y * dst_stride + x];
            if (pixel != 0) {
                screen[screen_y * screen_w + screen_x] = pixel;
            }
        }
    }
}
