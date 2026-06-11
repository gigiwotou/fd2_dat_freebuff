/**
 * FD2 RLE Decoder - 统一RLE解码模块实现
 *
 * 基于IDA Pro汇编代码1:1还原
 *
 * 包含以下IDA函数:
 *   - sub_4E98D: 通用RLE解码器
 *   - sub_4E22A: 24x24精灵RLE解码器
 *   - sub_36E65: AFM调色板RLE解码
 *   - sub_36F24: AFM帧数据RLE解码
 *   - sub_36F82: AFM像素填充RLE解码
 */

#include "../include/fd2_rle.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ============================================================================
 * 辅助函数: fd2_image_get_dimensions
 * ============================================================================ */

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

/* ============================================================================
 * sub_4E98D: 通用RLE解码器
 *
 * 命令字节格式: [bit7][bit6][count:6]
 *   bit7=1, bit6=1: 跳过(透明)
 *   bit7=1, bit6=0: 复制
 *   bit7=0, bit6=1: 交替填充
 *   bit7=0, bit6=0: 填充
 * ============================================================================ */

int fd2_rle_decompress(const u8* src, u32 src_size,
                      u8* dst, int width, int height) {
    if (!src || !dst || width <= 0 || height <= 0) return -1;

    const u8* p = src;
    const u8* src_end = src + src_size;
    u8* dst_end = dst + width * height;

    for (int row = 0; row < height; row++) {
        u8* row_dst = dst + row * width;
        int count = width;

        while (count > 0 && p < src_end) {
            u8 value = *p++;
            int run_len = (value & 0x3F) + 1;
            int bit7 = (value >> 7) & 1;
            int bit6 = (value >> 6) & 1;

            if (bit7 && bit6) {
                /* 11: 跳过(透明) */
                if (row_dst + run_len <= dst_end) {
                    row_dst += run_len;
                } else {
                    row_dst = dst_end;
                }
                if (count >= run_len) {
                    count -= run_len;
                } else {
                    count = 0;
                }
            } else if (bit7 && !bit6) {
                /* 10: 复制 */
                for (int i = 0; i < run_len && count > 0 && p < src_end; i++) {
                    if (row_dst < dst_end) {
                        *row_dst = *p;
                    }
                    row_dst++;
                    p++;
                    count--;
                }
            } else if (!bit7 && bit6) {
                /* 01: 交替填充 */
                if (p < src_end) {
                    u8 fill = *p++;
                    for (int i = 0; i < run_len && count > 0; i++) {
                        if (count >= 2) {
                            if (row_dst + 1 < dst_end) {
                                row_dst[1] = fill;
                            }
                            row_dst += 2;
                            count -= 2;
                        } else {
                            if (row_dst < dst_end) {
                                *row_dst = fill;
                            }
                            row_dst += 1;
                            count -= 1;
                        }
                    }
                }
            } else {
                /* 00: 填充 */
                if (p < src_end) {
                    u8 fill = *p++;
                    for (int i = 0; i < run_len && count > 0; i++) {
                        if (row_dst < dst_end) {
                            *row_dst = fill;
                        }
                        row_dst++;
                        count--;
                    }
                }
            }
        }
    }

    return 0;
}

int fd2_rle_decompress_to_buffer(const u8* res_data, u32 res_size,
                                 u8* dst_buf, int dst_y, int stride) {
    if (!res_data || res_size < 4 || !dst_buf || stride <= 0) return -1;

    int w, h;
    if (fd2_image_get_dimensions(res_data, res_size, &w, &h) != 0) return -1;

    u8* dst = dst_buf + stride * dst_y;
    const u8* src = res_data + 4;
    const u8* src_end = res_data + res_size;

    for (int row = 0; row < h; row++) {
        u8* row_dst = dst + row * stride;
        int count = w;

        while (count > 0 && src < src_end) {
            u8 value = *src++;
            int run_len = (value & 0x3F) + 1;
            int bit7 = (value >> 7) & 1;
            int bit6 = (value >> 6) & 1;

            if (bit7 && bit6) {
                /* 11: 跳过 */
                row_dst += run_len;
                count -= (count >= run_len) ? run_len : count;
            } else if (bit7 && !bit6) {
                /* 10: 复制 */
                for (int i = 0; i < run_len && count > 0 && src < src_end; i++) {
                    *row_dst++ = *src++;
                    count--;
                }
            } else if (!bit7 && bit6) {
                /* 01: 交替填充 */
                if (src < src_end) {
                    u8 fill = *src++;
                    for (int i = 0; i < run_len && count > 0; i++) {
                        if (count >= 2) {
                            row_dst[1] = fill;
                            row_dst += 2;
                            count -= 2;
                        } else {
                            *row_dst++ = fill;
                            count -= 1;
                        }
                    }
                }
            } else {
                /* 00: 填充 */
                if (src < src_end) {
                    u8 fill = *src++;
                    for (int i = 0; i < run_len && count > 0; i++) {
                        *row_dst++ = fill;
                        count--;
                    }
                }
            }
        }
    }

    return 0;
}

int fd2_rle_decompress_from_resource(const u8* res_data, u32 res_size,
                                     u8** out_pixels, int* out_w, int* out_h) {
    if (!res_data || res_size < 4 || !out_pixels || !out_w || !out_h) return -1;

    int w, h;
    if (fd2_image_get_dimensions(res_data, res_size, &w, &h) != 0) return -1;

    /* 使用calloc初始化为0,处理透明像素 */
    u8* pixels = (u8*)calloc(1, (size_t)(w * h));
    if (!pixels) return -1;

    if (fd2_rle_decompress(res_data + 4, res_size - 4, pixels, w, h) != 0) {
        free(pixels);
        return -1;
    }

    *out_pixels = pixels;
    *out_w = w;
    *out_h = h;
    return 0;
}

/* ============================================================================
 * sub_4E22A: 24x24精灵RLE解码器
 *
 * 固定24x24尺寸的精灵数据解码
 * ============================================================================ */

void fd2_rle_blit_24x24(const u8* src, u8* dst, int dst_stride) {
    for (int y = 0; y < 24; y++) {
        u8* dst_ptr = dst;
        int remaining = 24;

        while (remaining > 0) {
            u8 cmd = *src++;
            u8 type = (cmd >> 6) & 0x03;
            u8 count = ((cmd >> 2) & 0x0F) + 1;

            if (count > remaining) count = remaining;

            switch (type) {
                case 0:
                    /* 跳过 */
                    memset(dst_ptr, 0, count);
                    break;
                case 1:
                    /* 复制数据 */
                    memcpy(dst_ptr, src, count);
                    src += count;
                    break;
                case 2:
                    /* 填充单色 */
                    memset(dst_ptr, *src, count);
                    src++;
                    break;
                case 3:
                    /* 交替填充 */
                    {
                        u8 val = *src++;
                        for (int i = 0; i < count; i += 2) {
                            if (i < count) dst_ptr[i] = val;
                            if (i + 1 < count) dst_ptr[i + 1] = val;
                        }
                    }
                    break;
            }

            dst_ptr += count;
            remaining -= count;
        }

        dst += dst_stride;
    }
}

void fd2_rle_blit_24x24_palette(const u8* src, u8* dst, int dst_stride,
                                 const u8* palette_map) {
    for (int y = 0; y < 24; y++) {
        u8* dst_ptr = dst;
        int remaining = 24;

        while (remaining > 0) {
            u8 cmd = *src++;
            u8 type = (cmd >> 6) & 0x03;
            u8 count = ((cmd >> 2) & 0x0F) + 1;

            if (count > remaining) count = remaining;

            switch (type) {
                case 0:
                    memset(dst_ptr, 0, count);
                    break;
                case 1:
                    {
                        for (int i = 0; i < count; i++) {
                            dst_ptr[i] = palette_map[src[i]];
                        }
                        src += count;
                    }
                    break;
                case 2:
                    memset(dst_ptr, palette_map[*src], count);
                    src++;
                    break;
                case 3:
                    {
                        u8 val = palette_map[*src++];
                        for (int i = 0; i < count; i += 2) {
                            if (i < count) dst_ptr[i] = val;
                            if (i + 1 < count) dst_ptr[i + 1] = val;
                        }
                    }
                    break;
            }

            dst_ptr += count;
            remaining -= count;
        }

        dst += dst_stride;
    }
}

/* ============================================================================
 * 地形/光标图像解码
 * ============================================================================ */

void fd2_rle_decode_terrain(const u8* src, u8* dst, int stride) {
    /* 地形解码使用24x24解码器 */
    fd2_rle_blit_24x24(src, dst, stride);
}

int fd2_rle_decode_cursor(const u8* src, int size, u8* dst, int dst_stride) {
    if (!src || !dst || size < 4) return -1;

    int w, h;
    if (fd2_image_get_dimensions(src, (u32)size, &w, &h) != 0) {
        /* 尝试使用24x24解码 */
        if (size >= 24 * 24) {
            fd2_rle_blit_24x24(src, dst, dst_stride);
            return 0;
        }
        return -1;
    }

    if (w == 24 && h == 24) {
        fd2_rle_blit_24x24(src + 4, dst, dst_stride);
    } else {
        /* 使用通用解码器 */
        fd2_rle_decompress(src + 4, (u32)(size - 4), dst, w, h);
    }

    return 0;
}

/* ============================================================================
 * sub_36E65/sub_36F24: AFM调色板和帧数据RLE解码
 *
 * 格式: 0xC0掩码表示RLE运行
 *   (byte & 0xC0) == 0xC0: count = byte & 0x3F, value = next byte
 *   else: literal byte
 * ============================================================================ */

int fd2_afm_rle_palette(const u8* data, u8* palette) {
    if (!data || !palette) return -1;

    int written = 0;
    int consumed = 0;

    while (written < FD2_PALETTE_BYTES) {
        u8 byte = data[consumed++];
        if ((byte & 0xC0) == 0xC0) {
            /* RLE运行 */
            int count = byte & 0x3F;
            u8 value = data[consumed++];
            int fill = (written + count > FD2_PALETTE_BYTES)
                       ? (FD2_PALETTE_BYTES - written) : count;
            memset(palette + written, value, fill);
            written += count;
        } else {
            /* 字面字节 */
            palette[written++] = byte;
        }
    }

    return consumed;
}

int fd2_afm_rle_frame(const u8* data, u8* frame, int count) {
    if (!data || !frame) return -1;

    int written = 0;
    int consumed = 0;

    while (written < count) {
        u8 byte = data[consumed++];
        if ((byte & 0xC0) == 0xC0) {
            /* RLE运行 */
            int run_count = byte & 0x3F;
            u8 value = data[consumed++];
            int fill = (written + run_count > count)
                       ? (count - written) : run_count;
            memset(frame + written, value, fill);
            written += run_count;
        } else {
            /* 字面字节 */
            if (written < count) {
                frame[written++] = byte;
            }
        }
    }

    return consumed;
}

int fd2_afm_rle_pixel_fill(const u8* data, int count, u8* base, u8* buf) {
    if (!data || !base || !buf) return -1;

    /* IDA sub_36F82实现:
     * 读取(word)count对(offset, value)
     * 在base[offset]处填充value
     */
    const u8* p = data;
    int pairs = count;

    while (pairs > 0) {
        if (p + 2 > data + 1000) break; /* 安全检查 */

        u8 offset = *p++;
        u8 value = *p++;

        if (offset < 200) { /* 安全检查 */
            base[offset] = value;
        }

        pairs--;
    }

    return (int)(p - data);
}

/* ============================================================================
 * FDOTHER.DAT 专用解码器
 *
 * 用于字体、UI元素等特殊格式
 * ============================================================================ */

int fd2_rle_decode_shap(const u8* src, int src_size,
                        u8* dst, int width, int height) {
    if (!src || !dst || src_size < 4) return -1;

    /* 检查是否有4字节头 */
    /* src[0]|src[1]<<8 = width, src[2]|src[3]<<8 = height */

    const u8* compressed = src + 4;
    int comp_size = src_size - 4;

    /* 使用通用解码器 */
    return fd2_rle_decompress(compressed, (u32)comp_size, dst, width, height);
}

int fd2_rle_decode_portrait(const u8* src, int src_size,
                             u8* dst, int max_pixels) {
    if (!src || !dst || src_size < 4) return -1;

    /* 头像解码 - 读取尺寸信息 */
    int w = src[0] | (src[1] << 8);
    int h = src[2] | (src[3] << 8);

    if (w <= 0 || h <= 0 || w * h > max_pixels) {
        return -1;
    }

    const u8* compressed = src + 4;
    int comp_size = src_size - 4;

    if (fd2_rle_decompress(compressed, (u32)comp_size, dst, w, h) != 0) {
        return -1;
    }

    return w * h;
}
