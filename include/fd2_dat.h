#ifndef FD2_DAT_H
#define FD2_DAT_H

#include "fd2_types.h"

byte* fd2_load_dat_resource(const char* filename, byte* prev_buf, int resource_idx, dword* out_size);

/* Palette loading */
int fd_load_palette(const char *filename, byte palette[768]);

/* Image dimensions */
void fd_get_image_dimensions(const byte *data, int *width, int *height);

/* RLE decompression */
int fd_decompress_rle(const byte *src, int src_size, byte *dst, int dst_width, int dst_height, int value_param);

/* Resource analysis for debugging */
int fd_analyze_resource(const byte *data, int size);

/* sub_4EBFF: Render pixel data to screen buffer (1:1 from IDA) */
void sub_4EBFF(byte* dst, byte* src, int pitch);

#endif
