/**
 * FD2 Battle Cursor System
 *
 * Map cursor movement, rendering, and RLE decoding.
 * Based on IDA sub_11B48, sub_11B9B, sub_11C59, sub_11BFA, sub_4E98D, sub_1ACF3.
 */

#define _GNU_SOURCE
#include "fd2_game.h"
#include "fd2_battle.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

void cursor_move_up(state_battle_data_t* data, int map_height) {
    if (data->cursor_y > 0) {
        if (data->move_counter_y < 2 && data->scroll_y > 0) {
            data->cursor_y--;
            data->scroll_y--;
        } else {
            data->cursor_y--;
            data->move_counter_y--;
        }
    }
}

void cursor_move_down(state_battle_data_t* data, int map_height) {
    if (data->cursor_y < map_height - 1) {
        if (data->move_counter_y <= 5 || data->scroll_y == map_height - 8) {
            data->cursor_y++;
            data->move_counter_y++;
        } else {
            data->cursor_y++;
            data->scroll_y++;
        }
    }
}

void cursor_move_left(state_battle_data_t* data, int map_width) {
    if (data->cursor_x > 0) {
        if (data->move_counter_x < 2 && data->scroll_x > 0) {
            data->cursor_x--;
            data->scroll_x--;
        } else {
            data->cursor_x--;
            data->move_counter_x--;
        }
    }
}

void cursor_move_right(state_battle_data_t* data, int map_width) {
    if (data->cursor_x < map_width - 1) {
        if (data->move_counter_x <= 10 || data->scroll_x == map_width - 13) {
            data->cursor_x++;
            data->move_counter_x++;
        } else {
            data->cursor_x++;
            data->scroll_x++;
        }
    }
}

void update_camera_from_cursor(state_battle_data_t* data) {
    data->camera_x = data->scroll_x * MAP_TILE_SIZE;
    data->camera_y = data->scroll_y * MAP_TILE_SIZE;

    int max_cam_x = data->map.map_image_width - FD2_SCREEN_W;
    int max_cam_y = data->map.map_image_height - FD2_SCREEN_H;
    if (max_cam_x < 0) max_cam_x = 0;
    if (max_cam_y < 0) max_cam_y = 0;
    if (data->camera_x < 0) data->camera_x = 0;
    if (data->camera_y < 0) data->camera_y = 0;
    if (data->camera_x > max_cam_x) data->camera_x = max_cam_x;
    if (data->camera_y > max_cam_y) data->camera_y = max_cam_y;
}

int decode_rle_image(
    const u8* src,
    u8* dst,
    int dst_stride,
    int width,
    int height
) {
    const u8* p = src;
    u8* dst_row = dst;

    for (int row = 0; row < height; row++) {
        int col = 0;
        while (col < width) {
            u8 opcode = *p++;
            int count = (opcode & 0x3F) + 1;

            int bit7 = (opcode >> 7) & 1;
            int bit6 = (opcode >> 6) & 1;

            if (bit7 && bit6) {
                col += count;
            } else if (bit7 && !bit6) {
                int i;
                for (i = 0; i < count && col < width; i++) {
                    dst_row[col++] = *p++;
                }
            } else if (!bit7 && bit6) {
                u8 color = *p++;
                int i;
                for (i = 0; i < count && col < width; i++) {
                    col++;
                    if (col < width) {
                        dst_row[col] = color;
                    }
                    col++;
                }
            } else {
                u8 color = *p++;
                int i;
                for (i = 0; i < count && col < width; i++) {
                    dst_row[col++] = color;
                }
            }
        }
        dst_row += dst_stride;
    }

    return 0;
}

int load_cursor_image(fd2_game_t* game, state_battle_data_t* data) {
    (void)game;

    const u8* fdother_raw = data->fdother_data;
    u32 fdother_size = data->fdother_data_size;

    printf("load_cursor_image: FDOTHER raw data at %p, size=%u\n",
           (void*)fdother_raw, fdother_size);

    if (fdother_size < 10) {
        printf("load_cursor_image: FDOTHER data too small\n");
        return -1;
    }

    if (memcmp(fdother_raw, "LLLLLL", 6) != 0) {
        printf("load_cursor_image: invalid header\n");
        return -1;
    }

    u32 resource_count = *(const u32*)(fdother_raw + 6);
    printf("load_cursor_image: FDOTHER resource count=%u\n", resource_count);

    if (resource_count < 2) {
        printf("load_cursor_image: not enough resources\n");
        return -1;
    }

    u32 res1_offset = *(const u32*)(fdother_raw + 10);
    u32 res2_offset = *(const u32*)(fdother_raw + 14);
    printf("load_cursor_image: resource 1 at offset %u (0x%04X)\n",
           res1_offset, res1_offset);

    const u8* res1_data = fdother_raw + res1_offset;
    u32 res1_size = res2_offset - res1_offset;
    printf("load_cursor_image: resource 1 size=%u bytes\n", res1_size);

    u32 sub0_start = *(const u32*)(res1_data + 0);
    u32 sub0_end = *(const u32*)(res1_data + 4);
    printf("load_cursor_image: sub0 start=%u, end=%u\n", sub0_start, sub0_end);

    if (sub0_start >= res1_size || sub0_end > res1_size) {
        printf("load_cursor_image: invalid sub0 offsets\n");
        return -1;
    }

    const u8* cursor_data = res1_data + sub0_start;
    u16 width = *(const u16*)(cursor_data + 0);
    u16 height = *(const u16*)(cursor_data + 2);

    printf("load_cursor_image: cursor dimensions=%dx%d\n", width, height);

    if (width == 0 || height == 0 || width > 64 || height > 64) {
        printf("load_cursor_image: invalid dimensions\n");
        return -1;
    }

    data->cursor_image_data = cursor_data + 4;
    data->cursor_image_width = width;
    data->cursor_image_height = height;

    printf("load_cursor_image: first 16 RLE bytes: ");
    for (int i = 0; i < 16; i++) {
        printf("%02X ", data->cursor_image_data[i]);
    }
    printf("\n");

    return 0;
}

void battle_render_cursor(state_battle_data_t* data, u8* screen, int screen_w, int screen_h) {
    int cursor_screen_x = data->cursor_x * MAP_TILE_SIZE - data->camera_x;
    int cursor_screen_y = data->cursor_y * MAP_TILE_SIZE - data->camera_y;

    if (cursor_screen_x >= -MAP_TILE_SIZE && cursor_screen_x < FD2_SCREEN_W &&
        cursor_screen_y >= -MAP_TILE_SIZE && cursor_screen_y < FD2_SCREEN_H) {
        bool cursor_visible = (data->cursor_blink % 30) < 25;

        if (cursor_visible) {
            if (data->cursor_image_data) {
                data->cursor_frame_id = (data->move_counter_y <= 5 || data->move_counter_x >= 3) ?
                    ((data->move_counter_y > 5 && data->move_counter_x > 9) ? 1 : data->cursor_frame_id) : 242;

                u8 cursor_pixels[576];
                int img_w = data->cursor_image_width;
                int img_h = data->cursor_image_height;

                decode_rle_image(
                    data->cursor_image_data,
                    cursor_pixels,
                    img_w,
                    img_w,
                    img_h
                );

                int start_x = cursor_screen_x;
                int start_y = cursor_screen_y;

                for (int y = 0; y < img_h; y++) {
                    for (int x = 0; x < img_w; x++) {
                        int sx = start_x + x;
                        int sy = start_y + y;

                        if (sx >= 0 && sx < FD2_SCREEN_W && sy >= 0 && sy < FD2_SCREEN_H) {
                            u8 pixel = cursor_pixels[y * img_w + x];
                            if (pixel != 0) {
                                screen[sy * FD2_SCREEN_W + sx] = pixel;
                            }
                        }
                    }
                }
            } else {
                u8 cursor_color = 15;
                for (int x = 0; x < MAP_TILE_SIZE; x++) {
                    int px = cursor_screen_x + x;
                    if (px >= 0 && px < FD2_SCREEN_W && cursor_screen_y >= 0 && cursor_screen_y < FD2_SCREEN_H) {
                        screen[cursor_screen_y * FD2_SCREEN_W + px] = cursor_color;
                    }
                    int bottom_y = cursor_screen_y + MAP_TILE_SIZE - 1;
                    if (px >= 0 && px < FD2_SCREEN_W && bottom_y >= 0 && bottom_y < FD2_SCREEN_H) {
                        screen[bottom_y * FD2_SCREEN_W + px] = cursor_color;
                    }
                }
                for (int y = 0; y < MAP_TILE_SIZE; y++) {
                    int py = cursor_screen_y + y;
                    if (cursor_screen_x >= 0 && cursor_screen_x < FD2_SCREEN_W && py >= 0 && py < FD2_SCREEN_H) {
                        screen[py * FD2_SCREEN_W + cursor_screen_x] = cursor_color;
                    }
                    int right_x = cursor_screen_x + MAP_TILE_SIZE - 1;
                    if (right_x >= 0 && right_x < FD2_SCREEN_W && py >= 0 && py < FD2_SCREEN_H) {
                        screen[py * FD2_SCREEN_W + right_x] = cursor_color;
                    }
                }
            }
        }
    }
}

void battle_render_debug_grid(state_battle_data_t* data, u8* screen, int screen_w, int screen_h) {
    int start_tile_x = data->camera_x / MAP_TILE_SIZE;
    int start_tile_y = data->camera_y / MAP_TILE_SIZE;
    int end_tile_x = (data->camera_x + FD2_SCREEN_W) / MAP_TILE_SIZE + 1;
    int end_tile_y = (data->camera_y + FD2_SCREEN_H) / MAP_TILE_SIZE + 1;

    for (int ty = start_tile_y; ty <= end_tile_y; ty++) {
        for (int tx = start_tile_x; tx <= end_tile_x; tx++) {
            int screen_x = tx * MAP_TILE_SIZE - data->camera_x;
            int screen_y = ty * MAP_TILE_SIZE - data->camera_y;

            u8 grid_color = 63;

            if (screen_y >= 0 && screen_y < FD2_SCREEN_H) {
                int x_start = (screen_x < 0) ? 0 : screen_x;
                int x_end = (screen_x + MAP_TILE_SIZE > FD2_SCREEN_W) ? FD2_SCREEN_W : (screen_x + MAP_TILE_SIZE);
                for (int x = x_start; x < x_end; x++) {
                    screen[screen_y * FD2_SCREEN_W + x] = grid_color;
                }
            }

            if (screen_x >= 0 && screen_x < FD2_SCREEN_W) {
                int y_start = (screen_y < 0) ? 0 : screen_y;
                int y_end = (screen_y + MAP_TILE_SIZE > FD2_SCREEN_H) ? FD2_SCREEN_H : (screen_y + MAP_TILE_SIZE);
                for (int y = y_start; y < y_end; y++) {
                    screen[y * FD2_SCREEN_W + screen_x] = grid_color;
                }
            }
        }
    }
}
