#ifndef FD2_DATA_DAT_PARSER_H
#define FD2_DATA_DAT_PARSER_H

#include "fd2/types.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ---- DAT File Format ----
 * Header: 6 bytes magic ("LLLLLL")
 *         4 bytes resource count (little-endian)
 * Offset table: N * 4 bytes (little-endian offsets)
 * Resource data: variable size
 */

#define FD2_DAT_MAGIC "LLLLLL"
#define FD2_DAT_MAGIC_LEN 6

typedef struct {
    u8*  data;
    u32  size;
    u32  resource_count;
    u32* offsets;
} fd2_dat_file_t;

typedef struct {
    const u8* data;
    u32       size;
    u8        is_palette;
    int       width;
    int       height;
} fd2_dat_resource_t;

/* ---- DAT File Operations ---- */

int  fd2_dat_load(fd2_dat_file_t* dat, const char* path);
void fd2_dat_free(fd2_dat_file_t* dat);
bool fd2_dat_is_valid(const fd2_dat_file_t* dat);

const fd2_dat_resource_t* fd2_dat_get_resource(const fd2_dat_file_t* dat, int index);
int fd2_dat_get_resource_count(const fd2_dat_file_t* dat);

/* ---- RLE Decompression ---- */

int  fd2_rle_decompress(const u8* src, u32 src_size, u8* dst, int width, int height);
int  fd2_rle_get_dimensions(const u8* src, u32 src_size, int* out_w, int* out_h);

/* ---- Palette Operations ---- */

void fd2_palette_6bit_to_8bit(const u8* src_6bit, u8* dst_8bit);
void fd2_palette_set_brightness(u8* palette, int brightness_0_to_63);

#ifdef __cplusplus
}
#endif

#endif /* FD2_DATA_DAT_PARSER_H */
