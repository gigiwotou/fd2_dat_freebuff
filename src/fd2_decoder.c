#include "fd2_decoder.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ========================================================================
 * DAT File System
 * ======================================================================== */

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

/* fd2_dat_load_resource is now implemented in fd2_data_loader.c */

/* ========================================================================
 * RLE Decompression (IDA sub_4E98D) - FULL 1:1 implementation
 *
 * Original signature:
 *   char __cdecl sub_4E98D(__int16 *arg0, int arg4, int arg8, int argC, int arg10, int value_1)
 *   arg0[0] = width
 *   arg0[1] = height (stored to word_627B6)
 *   arg0+2    = src (compressed data after header)
 *   arg4      = dst_base
 *   arg8      = dst_y
 *   argC      = dst_x
 *   arg10     = stride
 *   value_1   = palette_offset (-1, 0-255, or >255)
 *
 * Three modes:
 *   value_1 == -1:        Direct pixel mode (read/write actual pixel values)
 *   (u16)value_1 > 0xFF:  Palette offset mode (value = base + ((high + src) & 7))
 *   else (0-255):         Color fill mode (all writes use value_1 as color)
 * ======================================================================== */

/* Helper: compute color for palette offset mode */
static u8 compute_palette_color(int palette_offset, u8 src_byte) {
    /* value = value_1 + ((BYTE1(value_1) + src_byte) & 7) */
    return (u8)(palette_offset + (((palette_offset >> 8) + src_byte) & 7));
}

int fd2_rle_decompress(const u8* src, u32 src_size,
                       u8* dst, int dst_x, int dst_y, int stride,
                       int width, int height, int palette_offset) {
    if (!src || !dst || width <= 0 || height <= 0 || stride <= 0) return -1;

    u8* dst_ptr = dst + stride * dst_y + dst_x;
    int row_skip = stride - width;

    if (palette_offset == -1) {
        const u8* src_end = src + src_size;
        for (int row = 0; row < height; row++) {
            int count = width;

            while (count > 0 && src < src_end) {
                u8 ctrl = *src++;
                int count_1 = (ctrl & 0x3F) + 1;
                int bit7 = (ctrl >> 7) & 1;
                int bit6 = (ctrl >> 6) & 1;

                if (bit7 && bit6) {
                    dst_ptr += count_1;
                    count -= count_1;
                } else if (bit7 && !bit6) {
                    if (src + count_1 > src_end) return -1;
                    count -= count_1;
                    memcpy(dst_ptr, src, count_1);
                    src += count_1;
                    dst_ptr += count_1;
                } else if (!bit7 && bit6) {
                    if (src >= src_end) return -1;
                    count = count - count_1 - count_1;
                    u8 fill = *src++;
                    for (int i = 0; i < count_1; i++) {
                        dst_ptr[1] = fill;
                        dst_ptr += 2;
                    }
                } else {
                    if (src >= src_end) return -1;
                    count -= count_1;
                    u8 fill = *src++;
                    memset(dst_ptr, fill, count_1);
                    dst_ptr += count_1;
                }
            }
            dst_ptr += row_skip;
        }
    } else if ((unsigned short)palette_offset > 0xFF) {
        const u8* src_end = src + src_size;
        for (int row = 0; row < height; row++) {
            int count = width;

            while (count > 0 && src < src_end) {
                u8 ctrl = *src++;
                int count_1 = (ctrl & 0x3F) + 1;
                int bit7 = (ctrl >> 7) & 1;
                int bit6 = (ctrl >> 6) & 1;

                if (bit7 && bit6) {
                    dst_ptr += count_1;
                    count -= count_1;
                } else if (bit7 && !bit6) {
                    if (src + count_1 > src_end) return -1;
                    count -= count_1;
                    for (int i = 0; i < count_1; i++) {
                        *dst_ptr++ = compute_palette_color(palette_offset, *src++);
                    }
                } else if (!bit7 && bit6) {
                    if (src >= src_end) return -1;
                    count = count - count_1 - count_1;
                    u8 src_byte = *src++;
                    u8 color = compute_palette_color(palette_offset, src_byte);
                    for (int i = 0; i < count_1; i++) {
                        dst_ptr[1] = color;
                        dst_ptr += 2;
                    }
                } else {
                    if (src >= src_end) return -1;
                    count -= count_1;
                    u8 src_byte = *src++;
                    u8 color = compute_palette_color(palette_offset, src_byte);
                    memset(dst_ptr, color, count_1);
                    dst_ptr += count_1;
                }
            }
            dst_ptr += row_skip;
        }
    } else {
        const u8* src_end = src + src_size;
        u8 fill = (u8)palette_offset;
        for (int row = 0; row < height; row++) {
            int count = width;

            while (count > 0 && src < src_end) {
                u8 ctrl = *src++;
                int count_1 = (ctrl & 0x3F) + 1;
                int bit7 = (ctrl >> 7) & 1;
                int bit6 = (ctrl >> 6) & 1;

                if (bit7 && bit6) {
                    dst_ptr += count_1;
                    count -= count_1;
                } else if (bit7 && !bit6) {
                    if (src + count_1 > src_end) return -1;
                    count -= count_1;
                    src += count_1;
                    memset(dst_ptr, fill, count_1);
                    dst_ptr += count_1;
                } else if (!bit7 && bit6) {
                    if (src >= src_end) return -1;
                    count = count - count_1 - count_1;
                    src++;
                    for (int i = 0; i < count_1; i++) {
                        dst_ptr[1] = fill;
                        dst_ptr += 2;
                    }
                } else {
                    if (src >= src_end) return -1;
                    count -= count_1;
                    src++;
                    memset(dst_ptr, fill, count_1);
                    dst_ptr += count_1;
                }
            }
            dst_ptr += row_skip;
        }
    }

    return 0;
}

/* ========================================================================
 * RLE Decompression with stride (for scroll buffer)
 * Decompresses RLE data directly into a buffer with given stride.
 * Matches original sub_4E98D behavior.
 * ======================================================================== */

int fd2_rle_decompress_to_buffer(const u8* res_data, u32 res_size,
                                  u8* dst_buf, int dst_y, int stride,
                                  int palette_offset) {
    if (!res_data || res_size < 4 || !dst_buf || stride <= 0) return -1;

    int w, h;
    if (fd2_image_get_dimensions(res_data, res_size, &w, &h) != 0) return -1;

    /* Skip 4-byte header, decompress with stride */
    return fd2_rle_decompress(res_data + 4, res_size - 4,
                              dst_buf, 0, dst_y, stride,
                              w, h, palette_offset);
}

/* ========================================================================
 * RLE Decompression from resource (convenience wrapper)
 * Allocates destination buffer and decompresses RLE data.
 * ======================================================================== */

int fd2_rle_decompress_from_resource(const u8* res_data, u32 res_size,
                                     u8** out_pixels, int* out_w, int* out_h,
                                     int palette_offset) {
    if (!res_data || res_size < 4 || !out_pixels || !out_w || !out_h) return -1;

    int w, h;
    if (fd2_image_get_dimensions(res_data, res_size, &w, &h) != 0) return -1;

    /* Use calloc: RLE skip operations leave pixels as 0 (black) */
    u8* pixels = (u8*)calloc(1, (size_t)(w * h));
    if (!pixels) return -1;

    /* Decompress with stride == width (no padding) */
    if (fd2_rle_decompress(res_data + 4, res_size - 4,
                           pixels, 0, 0, w,
                           w, h, palette_offset) != 0) {
        free(pixels);
        return -1;
    }

    *out_pixels = pixels;
    *out_w = w;
    *out_h = h;
    return 0;
}

/* ========================================================================
 * Palette
 * ======================================================================== */

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
    if (brightness > 63) brightness = 63;  /* sub_11D40 uses 64 for full, clamp to 63 */

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
            /* Convert 8-bit back to 6-bit: v6 = v8 >> 2 */
            int v6 = palette_8bit[i * 3 + c] >> 2;
            v6 += add_6bit;
            if (v6 > 63) v6 = 63;
            /* Convert back to 8-bit */
            palette_8bit[i * 3 + c] = (u8)((v6 << 2) | (v6 >> 4));
        }
    }
}

/* ========================================================================
 * Image Dimensions
 * ======================================================================== */

int fd2_image_get_dimensions(const u8* data, u32 data_size,
                             int* out_w, int* out_h) {
    if (!data || data_size < 4 || !out_w || !out_h) return -1;

    u16 w, h;
    memcpy(&w, data, 2);
    memcpy(&h, data + 2, 2);

    if (w == 0 || w > 640 || h == 0 || h > 480) return -1;

    *out_w = w;
    *out_h = h;
    return 0;
}

/* ========================================================================
 * Resource Classification
 * ======================================================================== */

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

/* ========================================================================
 * BG.DAT Background Decoding
 * ======================================================================== */

int fd2_bg_decode(const u8* res_data, u32 res_size,
                  u8** out_pixels, int* out_w, int* out_h) {
    return fd2_rle_decompress_from_resource(res_data, res_size,
                                            out_pixels, out_w, out_h, -1);
}

/* ========================================================================
 * FDSHAP.DAT Sprite Decoding
 * ======================================================================== */

int fd2_shap_extract_palette(const u8* res_data, u32 res_size,
                             fd2_shap_palette_t* out) {
    if (!res_data || !out || res_size < sizeof(fd2_shap_palette_t)) return -1;

    memset(out, 0, sizeof(*out));
    memcpy(out->palette, res_data, FD2_PALETTE_BYTES);
    memcpy(out->metadata, res_data + FD2_PALETTE_BYTES,
           res_size - FD2_PALETTE_BYTES < 432 ? res_size - FD2_PALETTE_BYTES : 432);
    return 0;
}

/* ========================================================================
 * FIGANI.DAT Animation Decoding
 * ======================================================================== */

int fd2_ani_decode_frame(const u8* res_data, u32 res_size,
                         fd2_ani_frame_t* frame) {
    if (!frame) return -1;
    memset(frame, 0, sizeof(*frame));

    if (fd2_rle_decompress_from_resource(res_data, res_size,
                                         &frame->pixels,
                                         &frame->width, &frame->height, -1) != 0) {
        return -1;
    }

    frame->pixel_count = (u32)(frame->width * frame->height);
    frame->frame_delay = 10; /* Default */
    return 0;
}

int fd2_ani_read_timing(const u8* res_data, u32 res_size) {
    if (!res_data || res_size != 3) return -1;
    return (res_data[0] << 16) | (res_data[1] << 8) | res_data[2];
}

/* ========================================================================
 * FDTXT.DAT Text/Font Decoding
 * ======================================================================== */

int fd2_text_decode_glyph(const u8* res_data, u32 res_size,
                          fd2_text_glyph_t* glyph) {
    if (!glyph) return -1;
    memset(glyph, 0, sizeof(*glyph));

    return fd2_rle_decompress_from_resource(res_data, res_size,
                                            &glyph->pixels,
                                            &glyph->width, &glyph->height, 0);
}

/* ========================================================================
 * TAI.DAT Portrait Decoding
 * ======================================================================== */

int fd2_tai_decode_portrait(const u8* res_data, u32 res_size,
                            u8** out_pixels, int* out_w, int* out_h) {
    return fd2_rle_decompress_from_resource(res_data, res_size,
                                            out_pixels, out_w, out_h, -1);
}
