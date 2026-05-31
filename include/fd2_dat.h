#ifndef FD2_DAT_H
#define FD2_DAT_H

#include "fd2_types.h"

byte* fd2_load_dat_resource(const char* filename, byte* prev_buf, int resource_idx, dword* out_size);

/* Palette loading */
int fd_load_palette(const char *filename, byte palette[768]);

/* Image dimensions */
void fd_get_image_dimensions(const byte *data, int *width, int *height);

/* RLE decompression (skips 4-byte header) */
int fd_decompress_rle(const byte *src, int src_size, byte *dst, int dst_width, int dst_height, int value_param);

/* RLE decompression without header (pure EC66 encoded pixel data) */
int fd_decompress_rle_no_header(const byte *src, int src_size, byte *dst, int dst_width, int dst_height, int value_param);

/* sub_4E22A: 24x24图标专用RLE解码（与sub_4EC66完全不同）
 * 编码格式（2位控制）：
 * - 00xxxxxx: 填充模式 - memset(dst, color, count)
 * - 01xxxxxx: 交替模式 - 间隔写入像素（dst+=2）
 * - 10xxxxxx: 复制模式 - memcpy(dst, src, count)
 * - 11xxxxxx: 跳过模式 - dst += count（透明像素）
 */
int fd_decompress_sub_4E22A(const byte *src, int src_size, byte *dst, int width, int height, int pitch);

/* Resource analysis for debugging */
int fd_analyze_resource(const byte *data, int size);

/* sub_4EBFF: Render pixel data to screen buffer (1:1 from IDA) */
void sub_4EBFF(byte* dst, byte* src, int pitch);

#endif
