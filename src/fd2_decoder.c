/**
 * FD2 Decoder - DAT文件加载和资源分类
 *
 * 基于IDA Pro汇编代码1:1还原
 *
 * 注意: 所有RLE解码函数已移至fd2_rle.c
 * 请包含fd2_decoder.h或fd2_rle.h使用RLE功能
 */

#include "fd2_decoder.h"
#include "../include/fd2_rle.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ============================================================================
 * DAT File System
 * ============================================================================ */

int fd2_dat_load(fd2_dat_t* dat, const char* path) {
    if (!dat || !path) return -1;

    memset(dat, 0, sizeof(*dat));
    strncpy(dat->filename, path, sizeof(dat->filename) - 1);

    FILE* f = fopen(path, "rb");
    if (!f) {
        fprintf(stderr, "fd2_dat_load: cannot open '%s'\n", path);
        return -1;
    }

    fseek(f, 0, SEEK_END);
    long file_size = ftell(f);
    fseek(f, 0, SEEK_SET);

    if (file_size < 10) {
        fprintf(stderr, "fd2_dat_load: file too small (%ld bytes)\n", file_size);
        fclose(f);
        return -1;
    }

    u8* data = (u8*)malloc((size_t)file_size);
    if (!data) {
        fclose(f);
        return -1;
    }

    if ((size_t)fread(data, 1, (size_t)file_size, f) != (size_t)file_size) {
        fprintf(stderr, "fd2_dat_load: read error\n");
        free(data);
        fclose(f);
        return -1;
    }
    fclose(f);

    if (memcmp(data, FD2_DAT_MAGIC, FD2_DAT_MAGIC_LEN) != 0) {
        fprintf(stderr, "fd2_dat_load: invalid magic\n");
        free(data);
        return -1;
    }

    u32 resource_count;
    memcpy(&resource_count, data + 6, 4);

    fd2_resource_t* resources = (fd2_resource_t*)calloc(resource_count, sizeof(fd2_resource_t));
    if (!resources) {
        free(data);
        return -1;
    }

    /* Pass 1: read all offsets */
    for (u32 i = 0; i < resource_count; i++) {
        u32 offset;
        memcpy(&offset, data + 10 + i * 4, 4);
        resources[i].start = offset;
    }

    /* Pass 2: compute sizes */
    for (u32 i = 0; i < resource_count; i++) {
        if (i + 1 < resource_count) {
            resources[i].end = resources[i + 1].start;
        } else {
            resources[i].end = (u32)file_size;
        }
        resources[i].size = resources[i].end - resources[i].start;
    }

    dat->data = data;
    dat->file_size = (u32)file_size;
    dat->resource_count = resource_count;
    dat->resources = resources;

    return 0;
}

void fd2_dat_free(fd2_dat_t* dat) {
    if (!dat) return;
    free(dat->data);
    free(dat->resources);
    memset(dat, 0, sizeof(*dat));
}

const u8* fd2_dat_get_resource(const fd2_dat_t* dat, int index, u32* out_size) {
    if (!dat || index < 0 || (u32)index >= dat->resource_count) {
        if (out_size) *out_size = 0;
        return NULL;
    }
    if (out_size) *out_size = dat->resources[index].size;
    return dat->data + dat->resources[index].start;
}

/* Global variable set by fd2_dat_load_resource (matches dword_53BFF). */
u32 fd2_last_loaded_size = 0;

/* ============================================================================
 * sub_111BA: Single Resource Loader (IDA 0x111BA)
 *
 * Original assembly behavior (1:1 replication):
 *   1. Free old_ptr if non-NULL
 *   2. fopen(filename, "rb")
 *   3. fseek(fp, 4 * index + 6, SEEK_SET)
 *   4. fread 8 bytes: offset(4) + next_offset(4)
 *   5. size = next_offset - offset
 *   6. malloc(size)
 *   7. fseek(fp, offset, SEEK_SET)
 *   8. fread resource data
 *   9. fclose(fp)
 *   10. return pointer
 * ============================================================================ */

u8* fd2_dat_load_resource(const char* filename, void* old_ptr, int index) {
    FILE* fp;
    u8* buffer;
    u32 offset, next_offset, size;
    u32 offsets[2];

    /* Free old resource pointer if provided (IDA: if (a6) free(a6)) */
    if (old_ptr) {
        free(old_ptr);
    }

    /* Open DAT file */
    fp = fopen(filename, "rb");
    if (!fp) {
        fprintf(stderr, "\n\n File not found %s!!! \n\n", filename);
        return NULL;
    }

    /* Seek to offset table entry: 4 * index + 6 */
    fseek(fp, 4 * index + 6, SEEK_SET);

    /* Read 8 bytes: offset (4 bytes) + next_offset (4 bytes) */
    if (fread(offsets, 1, 8, fp) != 8) {
        fprintf(stderr, "fd2_dat_load_resource: failed to read offset table for index %d\n", index);
        fclose(fp);
        return NULL;
    }

    offset = offsets[0];
    next_offset = offsets[1];
    size = next_offset - offset;

    /* Store size in global (matches dword_53BFF) */
    fd2_last_loaded_size = size;

    /* Allocate memory for the resource */
    buffer = (u8*)malloc(size);
    if (!buffer) {
        fprintf(stderr, "Out of Memory at Load %s Number:%d!!\n", filename, index);
        fclose(fp);
        return NULL;
    }

    /* Seek to resource data */
    fseek(fp, offset, SEEK_SET);

    /* Read resource data */
    if (fread(buffer, 1, size, fp) != size) {
        fprintf(stderr, "fd2_dat_load_resource: failed to read resource %d (size=%u)\n", index, size);
        free(buffer);
        fclose(fp);
        return NULL;
    }

    fclose(fp);

    return buffer;
}

/* ============================================================================
 * Palette
 * ============================================================================ */

void fd2_palette_6bit_to_8bit(const u8* palette_6bit, u8* palette_8bit) {
    if (!palette_6bit || !palette_8bit) return;

    for (int i = 0; i < FD2_PALETTE_COLORS; i++) {
        for (int c = 0; c < 3; c++) {
            u8 v6 = palette_6bit[i * 3 + c] & 0x3F;
            palette_8bit[i * 3 + c] = (u8)((v6 << 2) | (v6 >> 4));
        }
    }
}

void fd2_palette_set_brightness(u8* palette_8bit, int brightness) {
    if (!palette_8bit || brightness < 0) return;
    if (brightness > 63) brightness = 63;

    float factor = (float)brightness / 63.0f;
    for (int i = 0; i < FD2_PALETTE_BYTES; i++) {
        palette_8bit[i] = (u8)(palette_8bit[i] * factor);
    }
}

void fd2_palette_fade(const u8* src, const u8* dst,
                      u8* out, int steps, int current) {
    if (!src || !dst || !out || steps <= 0) return;
    if (current <= 0) {
        memcpy(out, src, FD2_PALETTE_BYTES);
        return;
    }
    if (current >= steps) {
        memcpy(out, dst, FD2_PALETTE_BYTES);
        return;
    }

    float t = (float)current / (float)steps;
    for (int i = 0; i < FD2_PALETTE_BYTES; i++) {
        out[i] = (u8)(src[i] * (1.0f - t) + dst[i] * t);
    }
}

void fd2_palette_add_6bit(u8* palette_8bit, int add_6bit) {
    if (!palette_8bit || add_6bit <= 0) return;

    for (int i = 0; i < FD2_PALETTE_COLORS; i++) {
        for (int c = 0; c < 3; c++) {
            int v6 = palette_8bit[i * 3 + c] >> 2;
            v6 += add_6bit;
            if (v6 > 63) v6 = 63;
            palette_8bit[i * 3 + c] = (u8)((v6 << 2) | (v6 >> 4));
        }
    }
}

/* ============================================================================
 * Resource Classification
 * ============================================================================ */

int fd2_is_dat_magic(const u8* data, u32 size) {
    return (size >= FD2_DAT_MAGIC_LEN &&
            memcmp(data, FD2_DAT_MAGIC, FD2_DAT_MAGIC_LEN) == 0);
}

int fd2_dat_validate_offsets(const u8* data, u32 file_size, u32 resource_count) {
    if (!data || file_size < 10) return 0;

    u32 min_size = 10 + resource_count * 4;
    if (file_size < min_size) return 0;

    for (u32 i = 0; i < resource_count; i++) {
        u32 offset;
        memcpy(&offset, data + 10 + i * 4, 4);
        if (offset >= file_size) return 0;
    }
    return 1;
}

void fd2_resource_classify(const u8* data, u32 size, fd2_resource_info_t* info) {
    if (!info) return;
    memset(info, 0, sizeof(*info));

    if (size == 0) {
        info->type = FD2_RES_UNKNOWN;
        return;
    }

    if (size == FD2_PALETTE_BYTES) {
        info->type = FD2_RES_PALETTE;
        return;
    }

    if (size < 4) {
        info->type = FD2_RES_RAW;
        return;
    }

    if (fd2_is_dat_magic(data, size)) {
        u32 inner_count;
        memcpy(&inner_count, data + 6, 4);
        u32 min_size = 10 + inner_count * 4;
        if (size >= min_size && fd2_dat_validate_offsets(data, size, inner_count)) {
            info->type = FD2_RES_NESTED_DAT;
            info->inner_resource_count = (int)inner_count;
            return;
        }
    }

    int w, h;
    if (fd2_image_get_dimensions(data, size, &w, &h) == 0) {
        info->type = FD2_RES_RLE_IMAGE;
        info->width = w;
        info->height = h;
        return;
    }

    int printable = 0;
    u32 check = size < 100 ? size : 100;
    for (u32 i = 0; i < check; i++) {
        u8 b = data[i];
        if ((b >= 32 && b <= 126) || b == 10 || b == 13 || b == 9) {
            printable++;
        }
    }
    if (printable > (int)(check * 0.7)) {
        info->type = FD2_RES_TEXT;
        return;
    }

    info->type = FD2_RES_RAW;
}

/* ============================================================================
 * BG.DAT Background Decoding
 * (使用fd2_rle_decompress_from_resource)
 * ============================================================================ */

int fd2_bg_decode(const u8* res_data, u32 res_size,
                  u8** out_pixels, int* out_w, int* out_h) {
    return fd2_rle_decompress_from_resource(res_data, res_size,
                                            out_pixels, out_w, out_h);
}

/* ============================================================================
 * FDSHAP.DAT Sprite Decoding
 * ============================================================================ */

int fd2_shap_extract_palette(const u8* res_data, u32 res_size,
                             fd2_shap_palette_t* out) {
    if (!res_data || !out || res_size < sizeof(fd2_shap_palette_t)) return -1;

    memset(out, 0, sizeof(*out));
    memcpy(out->palette, res_data, FD2_PALETTE_BYTES);
    memcpy(out->metadata, res_data + FD2_PALETTE_BYTES,
           res_size - FD2_PALETTE_BYTES < 432 ? res_size - FD2_PALETTE_BYTES : 432);
    return 0;
}

/* ============================================================================
 * FIGANI.DAT Animation Decoding
 * ============================================================================ */

int fd2_ani_decode_frame(const u8* res_data, u32 res_size,
                         fd2_ani_frame_t* frame) {
    if (!frame) return -1;
    memset(frame, 0, sizeof(*frame));

    if (fd2_rle_decompress_from_resource(res_data, res_size,
                                         &frame->pixels,
                                         &frame->width, &frame->height) != 0) {
        return -1;
    }

    frame->pixel_count = (u32)(frame->width * frame->height);
    frame->frame_delay = 10;
    return 0;
}

int fd2_ani_read_timing(const u8* res_data, u32 res_size) {
    if (!res_data || res_size != 3) return -1;
    return (res_data[0] << 16) | (res_data[1] << 8) | res_data[2];
}

/* ============================================================================
 * FDTXT.DAT Text/Font Decoding
 * ============================================================================ */

int fd2_text_decode_glyph(const u8* res_data, u32 res_size,
                          fd2_text_glyph_t* glyph) {
    if (!glyph) return -1;
    memset(glyph, 0, sizeof(*glyph));

    return fd2_rle_decompress_from_resource(res_data, res_size,
                                            &glyph->pixels,
                                            &glyph->width, &glyph->height);
}

/* ============================================================================
 * TAI.DAT Portrait Decoding
 * ============================================================================ */

int fd2_tai_decode_portrait(const u8* res_data, u32 res_size,
                            u8** out_pixels, int* out_w, int* out_h) {
    return fd2_rle_decompress_from_resource(res_data, res_size,
                                            out_pixels, out_w, out_h);
}
