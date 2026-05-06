/**
 * DAT File Parser Implementation
 * Parses LLLLLL magic DAT files and extracts resources.
 * 1:1 implementation based on IDA analysis of sub_111BA.
 */

#define _GNU_SOURCE
#include "fd2/data/dat_parser.h"
#include "fd2/platform_file.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

int fd2_dat_load(fd2_dat_file_t* dat, const char* path) {
    if (!dat || !path) return -1;

    memset(dat, 0, sizeof(*dat));

    const fd2_filesys_iface_t* fs = fd2_platform_get_filesys();
    if (!fs) return -1;

    fd2_filesys_t* f = NULL;
    if (fs->init(&f, ".") < 0) return -1;

    dat->data = (u8*)fs->load_file(f, path, &dat->size);
    fs->shutdown(f);

    if (!dat->data || dat->size < FD2_DAT_MAGIC_LEN + 4) {
        fprintf(stderr, "dat_parser: cannot load or invalid size: %s\n", path);
        return -1;
    }

    if (memcmp(dat->data, FD2_DAT_MAGIC, FD2_DAT_MAGIC_LEN) != 0) {
        fprintf(stderr, "dat_parser: invalid magic in %s\n", path);
        free(dat->data);
        dat->data = NULL;
        return -1;
    }

    dat->resource_count = (u32)dat->data[6] |
                          ((u32)dat->data[7] << 8) |
                          ((u32)dat->data[8] << 16) |
                          ((u32)dat->data[9] << 24);

    if (dat->resource_count == 0 || dat->resource_count > 10000) {
        fprintf(stderr, "dat_parser: invalid resource count: %u in %s\n", dat->resource_count, path);
        free(dat->data);
        dat->data = NULL;
        return -1;
    }

    u32 offset_table_start = FD2_DAT_MAGIC_LEN + 4;
    u32 offset_table_size = dat->resource_count * 4;

    if (offset_table_start + offset_table_size > dat->size) {
        fprintf(stderr, "dat_parser: offset table out of bounds in %s\n", path);
        free(dat->data);
        dat->data = NULL;
        return -1;
    }

    dat->offsets = (u32*)malloc(offset_table_size);
    if (!dat->offsets) {
        free(dat->data);
        dat->data = NULL;
        return -1;
    }

    for (u32 i = 0; i < dat->resource_count; i++) {
        u32 base = offset_table_start + i * 4;
        dat->offsets[i] = (u32)dat->data[base] |
                          ((u32)dat->data[base + 1] << 8) |
                          ((u32)dat->data[base + 2] << 16) |
                          ((u32)dat->data[base + 3] << 24);
    }

    return 0;
}

void fd2_dat_free(fd2_dat_file_t* dat) {
    if (!dat) return;
    if (dat->data) free(dat->data);
    if (dat->offsets) free(dat->offsets);
    memset(dat, 0, sizeof(*dat));
}

bool fd2_dat_is_valid(const fd2_dat_file_t* dat) {
    return dat && dat->data && dat->offsets && dat->resource_count > 0;
}

static fd2_dat_resource_t g_resource_cache;

const fd2_dat_resource_t* fd2_dat_get_resource(const fd2_dat_file_t* dat, int index) {
    if (!fd2_dat_is_valid(dat) || index < 0 || (u32)index >= dat->resource_count) {
        return NULL;
    }

    u32 start = dat->offsets[index];
    u32 end = (index + 1 < (int)dat->resource_count) ? dat->offsets[index + 1] : dat->size;

    if (start >= dat->size || end > dat->size || start >= end) {
        return NULL;
    }

    g_resource_cache.data = dat->data + start;
    g_resource_cache.size = end - start;
    g_resource_cache.is_palette = (g_resource_cache.size == 768);
    g_resource_cache.width = 0;
    g_resource_cache.height = 0;

    if (!g_resource_cache.is_palette && g_resource_cache.size >= 4) {
        g_resource_cache.width  = (int)g_resource_cache.data[0] | ((int)g_resource_cache.data[1] << 8);
        g_resource_cache.height = (int)g_resource_cache.data[2] | ((int)g_resource_cache.data[3] << 8);
    }

    return &g_resource_cache;
}

int fd2_dat_get_resource_count(const fd2_dat_file_t* dat) {
    return fd2_dat_is_valid(dat) ? (int)dat->resource_count : 0;
}

/* ---- RLE Decompression ----
 * Original game RLE format (sub_4E22A):
 * Mode 1 (0x00): Fill value_2 times with value_1
 * Mode 2 (0x80): Copy value_2 bytes literally
 * Mode 3 (0x40): Copy from previous data, offset = value_2, count = value_1
 * Mode 4 (0xC0): Fill value_1 times with next byte
 */

int fd2_rle_decompress(const u8* src, u32 src_size, u8* dst, int width, int height) {
    if (!src || !dst || width <= 0 || height <= 0) return -1;

    int dst_size = width * height;
    int src_pos = 0;
    int dst_pos = 0;

    while (src_pos < (int)src_size && dst_pos < dst_size) {
        u8 opcode = src[src_pos++];
        u8 value_1 = src[src_pos++];

        if (opcode == 0x00) {
            u8 value_2 = src[src_pos++];
            for (int i = 0; i < value_2 && dst_pos < dst_size; i++) {
                dst[dst_pos++] = value_1;
            }
        } else if (opcode == 0x80) {
            for (int i = 0; i < value_1 && dst_pos < dst_size && src_pos < (int)src_size; i++) {
                dst[dst_pos++] = src[src_pos++];
            }
        } else if (opcode == 0x40) {
            u8 value_2 = src[src_pos++];
            int offset = value_1 + ((int)value_2 << 8);
            if (dst_pos >= offset) {
                for (int i = 0; i < value_1 && dst_pos < dst_size; i++) {
                    dst[dst_pos] = dst[dst_pos - offset];
                    dst_pos++;
                }
            } else {
                return -1;
            }
        } else if (opcode == 0xC0) {
            for (int i = 0; i < value_1 && dst_pos < dst_size; i++) {
                dst[dst_pos++] = src[src_pos];
            }
            src_pos++;
        } else {
            if (opcode & 0x80) {
                int count = opcode & 0x7F;
                for (int i = 0; i < count && dst_pos < dst_size; i++) {
                    dst[dst_pos++] = value_1;
                }
            } else {
                int count = opcode;
                for (int i = 0; i < count && dst_pos < dst_size && src_pos < (int)src_size; i++) {
                    dst[dst_pos++] = src[src_pos++];
                }
            }
        }
    }

    return (dst_pos == dst_size) ? 0 : -1;
}

int fd2_rle_get_dimensions(const u8* src, u32 src_size, int* out_w, int* out_h) {
    if (!src || src_size < 4 || !out_w || !out_h) return -1;

    *out_w = (int)src[0] | ((int)src[1] << 8);
    *out_h = (int)src[2] | ((int)src[3] << 8);

    if (*out_w <= 0 || *out_w > 1024 || *out_h <= 0 || *out_h > 1024) {
        return -1;
    }

    return 0;
}

/* ---- Palette Operations ---- */

void fd2_palette_6bit_to_8bit(const u8* src_6bit, u8* dst_8bit) {
    if (!src_6bit || !dst_8bit) return;

    for (int i = 0; i < 256; i++) {
        dst_8bit[i * 3 + 0] = (u8)(src_6bit[i] << 2);
        dst_8bit[i * 3 + 1] = (u8)(src_6bit[i] >> 6);
        dst_8bit[i * 3 + 2] = (u8)(src_6bit[i] >> 4);
    }
}

void fd2_palette_set_brightness(u8* palette, int brightness_0_to_63) {
    if (!palette || brightness_0_to_63 < 0) return;
    if (brightness_0_to_63 > 63) brightness_0_to_63 = 63;

    for (int i = 0; i < 256 * 3; i++) {
        palette[i] = (u8)((int)palette[i] * brightness_0_to_63 / 63);
    }
}
