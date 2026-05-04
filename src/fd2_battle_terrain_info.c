/**
 * FD2 Battle Terrain Info UI
 *
 * Based on IDA sub_126F7 and sub_4E22A.
 * 
 * Original assembly analysis:
 * - sub_126F7: Renders terrain info image for cursor position
 *   - Parameters: a5=x, a6=y, a7=terrain_image_index
 *   - Bounds check: x >= qword_53AA9 && x < dword_51A87+qword_53AA9
 *                 && y >= HIDWORD(qword_53AA9) && y < dword_51A8B+HIDWORD(qword_53AA9)
 *   - Get terrain image: FDOTHER_DAT__3 + *(DWORD*)(FDOTHER_DAT__3 + 4*a7 + 6)
 *   - Call sub_4E22A to decode RLE image to buffer at n655360 + 32904, width 456
 * 
 * - sub_4E22A: RLE decode function for 24x24 images
 *   - Outer loop: 24 rows (n24=24)
 *   - Inner loop: 24 columns (n24_1=24)
 *   - RLE format: byte value with flags in high bits
 *     - bit 7 set (CF=1 after shl): skip/run mode
 *     - bit 6 set: copy mode from source
 *     - otherwise: fill mode with single color
 *   - Run length = (value >> 2) + 1
 *   - After each row: dst += arg8 - 24 (stride adjustment)
 */

#define _GNU_SOURCE
#include "fd2_game.h"
#include "fd2_battle.h"
#include <stdio.h>
#include <string.h>

/*
 * RLE decode function - based on IDA sub_4E22A.
 * Decodes 24x24 RLE-compressed terrain image to destination buffer.
 * 
 * @param src - source RLE data
 * @param dst - destination buffer (width=456 stride)
 * @param dst_stride - destination row stride (456)
 */
static void rle_decode_terrain_image(const u8* src, u8* dst, int dst_stride) {
    const u8* src_ptr = src;
    u8* dst_ptr = dst;
    
    /* Outer loop: 24 rows */
    for (int row = 0; row < 24; row++) {
        int col_remaining = 24;  /* n24_1 = 24 */
        
        /* Inner loop: decode until 24 pixels filled */
        while (col_remaining > 0) {
            u8 value = *src_ptr++;
            u8 value_shl1 = value << 1;
            
            /* Check bit 7 (CF after shl) */
            if (value_shl1 & 0x100) {
                /* Skip/run mode - advance destination without writing */
                int count = (value >> 2) + 1;
                if (count > col_remaining) count = col_remaining;
                dst_ptr += count;
                col_remaining -= count;
            }
            /* Check bit 6 (CF after second shl) */
            else if ((value_shl1 << 1) & 0x100) {
                /* Copy mode - copy 'count' bytes from source */
                int count = (value >> 2) + 1;
                if (count > col_remaining) count = col_remaining;
                memcpy(dst_ptr, src_ptr, count);
                src_ptr += count;
                dst_ptr += count;
                col_remaining -= count;
            }
            else {
                /* Fill mode - fill 'count' bytes with single color */
                int count = (value >> 2) + 1;
                u8 fill_color = *src_ptr++;
                if (count > col_remaining) count = col_remaining;
                memset(dst_ptr, fill_color, count);
                dst_ptr += count;
                col_remaining -= count;
            }
        }
        
        /* Move to next row: dst += dst_stride - 24 */
        dst_ptr += (dst_stride - 24);
    }
}

/*
 * Load terrain info data from FDOTHER.DAT resource 3.
 * Based on IDA FDOTHER_DAT__3 reference in sub_126F7.
 */
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

/*
 * Render terrain info for cursor position.
 * Based on IDA sub_126F7:
 *   - Gets tile at cursor position
 *   - Gets terrain image from FDOTHER_DAT__3 + *(DWORD*)(FDOTHER_DAT__3 + 4*terrain_id + 6)
 *   - Decodes RLE image to buffer using sub_4E22A
 *   - Buffer offset: n655360 + 32904, width 456
 */
void battle_render_terrain_info(state_battle_data_t* data, u8* screen, int screen_w, int screen_h) {
    if (!data->terrain_info_data || !data->map.loaded) {
        return;
    }

    int cursor_x = data->cursor_x;
    int cursor_y = data->cursor_y;

    /* Check bounds */
    if (cursor_x < 0 || cursor_x >= data->map.width ||
        cursor_y < 0 || cursor_y >= data->map.height) {
        return;
    }

    /* Get terrain ID from map tile data */
    int terrain_id = data->map.tiles[cursor_y][cursor_x].terrain_id;

    /* Get terrain image offset from FDOTHER resource 3 */
    const u8* terrain_info_base = data->terrain_info_data;
    
    /* Parse resource 3 header to get image count */
    u16 image_count = 0;
    if (data->terrain_info_data_size >= 2) {
        image_count = terrain_info_base[0] | (terrain_info_base[1] << 8);
    }

    if (terrain_id < 0 || terrain_id >= image_count) {
        return;
    }

    /* Get image offset: FDOTHER_DAT__3 + *(DWORD*)(FDOTHER_DAT__3 + 4*terrain_id + 6) */
    u32 header_offset = 6;
    u32 image_offset_ptr = header_offset + 4 * terrain_id;
    
    if (image_offset_ptr + 4 > data->terrain_info_data_size) {
        return;
    }

    u32 image_offset = terrain_info_base[image_offset_ptr] |
                      (terrain_info_base[image_offset_ptr + 1] << 8) |
                      (terrain_info_base[image_offset_ptr + 2] << 16) |
                      (terrain_info_base[image_offset_ptr + 3] << 24);

    if (image_offset >= data->terrain_info_data_size) {
        return;
    }

    const u8* terrain_image_data = terrain_info_base + image_offset;

    /* Decode RLE image to buffer (sub_4E22A) */
    int dst_stride = TERRAIN_INFO_WIDTH;  /* 456 */
    u8 decoded_buffer[TERRAIN_INFO_WIDTH * 24];
    memset(decoded_buffer, 0, sizeof(decoded_buffer));
    
    rle_decode_terrain_image(terrain_image_data, decoded_buffer, dst_stride);

    /* Render to screen at bottom center */
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
