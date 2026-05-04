#ifndef FD2_DECODER_H
#define FD2_DECODER_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================
 * FD2 Resource Decoder Library
 * 
 * Provides functions to load, parse, and decode all FD2 DAT file formats.
 * Based on reverse engineering of FD2.EXE (IDA Pro analysis).
 * ======================================================================== */

/* ---- Types ---- */
typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int8_t   s8;
typedef int16_t  s16;
typedef int32_t  s32;

/* ---- Constants ---- */
#define FD2_SCREEN_W       320
#define FD2_SCREEN_H       200
#define FD2_SCREEN_SIZE    (FD2_SCREEN_W * FD2_SCREEN_H)
#define FD2_PALETTE_COLORS 256
#define FD2_PALETTE_BYTES  (FD2_PALETTE_COLORS * 3)
#define FD2_DAT_MAGIC      "LLLLLL"
#define FD2_DAT_MAGIC_LEN  6
#define FD2_VIDEO_BUFFER   0x655360  /* Original DOS address (for reference) */

/* ---- DAT File System ---- */

typedef struct {
    u32  start;   /* Offset in file */
    u32  end;     /* Offset of next resource (or file size) */
    u32  size;    /* end - start */
} fd2_resource_t;

typedef struct {
    char           filename[256];
    u8*            data;        /* Mapped file data */
    u32            file_size;
    u32            resource_count;
    fd2_resource_t* resources;  /* Array of resource_count entries */
} fd2_dat_t;

/*
 * Load a DAT file into memory and parse the resource table.
 * Returns 0 on success, -1 on error.
 */
int fd2_dat_load(fd2_dat_t* dat, const char* path);

/*
 * Free all resources associated with a loaded DAT file.
 */
void fd2_dat_free(fd2_dat_t* dat);

/*
 * Get raw resource data by index.
 * Returns pointer into mapped file (do not free), or NULL if invalid.
 * Sets *out_size to the resource size.
 *
 * @deprecated Use fd2_dat_load_resource instead (matches sub_111BA).
 */
const u8* fd2_dat_get_resource(const fd2_dat_t* dat, int index, u32* out_size);

/* ---- sub_111BA: Single Resource Loader ---- */

/*
 * Load a single resource from a DAT file (IDA sub_111BA).
 *
 * This is the ORIGINAL game's resource loading mechanism:
 * - Opens the DAT file
 * - Reads the offset table entry for the given index
 * - Allocates memory for the resource
 * - Reads the resource data
 * - Closes the file
 * - Returns pointer to the loaded resource
 *
 * If old_ptr is non-NULL, it is freed first (for resource switching).
 * The global fd2_last_loaded_size is set to the resource size.
 *
 * filename: DAT file path (e.g., "FDOTHER.DAT")
 * old_ptr:  previous resource pointer to free (can be NULL)
 * index:    resource index within the DAT file
 *
 * Returns: pointer to loaded resource data, or NULL on error.
 *          The caller is responsible for freeing the returned pointer.
 */
u8* fd2_dat_load_resource(const char* filename, void* old_ptr, int index);

/* Global variable set by fd2_dat_load_resource (matches dword_53BFF). */
extern u32 fd2_last_loaded_size;

/* ---- RLE Decompression (IDA sub_4E98D) ---- */

/*
 * Decompress FD2 RLE data (IDA sub_4E98D) - FULL 1:1 implementation.
 *
 * This function has 3 modes controlled by palette_offset:
 *
 * Mode 1: palette_offset == -1 (direct pixel mode)
 *   - 00: read 1 byte from src, fill dst with it
 *   - 10: copy bytes from src to dst
 *   - 01: read 1 byte from src, write at every 2nd position
 *   - 11: skip (transparent)
 *
 * Mode 2: palette_offset 0-255 (color fill mode)
 *   - All operations write palette_offset as the color value
 *   - Used for fonts and overlays
 *
 * Mode 3: palette_offset > 255 (palette offset mode)
 *   - value = (palette_offset & 0xFF) + (((palette_offset >> 8) + src_byte) & 7)
 *   - Used for character sprites with palette shifting
 *
 * Parameters (matching original sub_4E98D):
 *   src:        compressed data (after 4-byte width/height header)
 *   src_size:   compressed data size
 *   dst:        destination buffer (pre-allocated, width * height bytes)
 *   dst_x:      X offset in destination (argC)
 *   dst_y:      Y offset in destination (arg8)
 *   stride:     bytes per row (arg10, typically 320)
 *   width:      image width (*arg0)
 *   height:     image height (word_627B6)
 *   palette_offset: value_1 (-1, 0-255, or >255)
 *
 * Returns 0 on success, -1 on error.
 */
int fd2_rle_decompress(const u8* src, u32 src_size,
                       u8* dst, int dst_x, int dst_y, int stride,
                       int width, int height, int palette_offset);

/*
 * Convenience: decompress a resource that starts with a 4-byte header
 * (2-byte width + 2-byte height, little-endian).
 *
 * palette_offset: -1 for direct pixels, 0-255 for color fill, >255 for palette offset
 * Allocates the destination buffer. Caller must free *out_pixels.
 * Sets *out_w, *out_h to the dimensions.
 * Returns 0 on success, -1 on error.
 */
int fd2_rle_decompress_from_resource(const u8* res_data, u32 res_size,
                                     u8** out_pixels, int* out_w, int* out_h,
                                     int palette_offset);

/*
 * Convenience: decompress RLE data directly into a buffer with given stride.
 * Matches original sub_4E98D behavior for scroll buffer construction.
 *
 * dst_buf: destination buffer (must be pre-allocated and zero-initialized)
 * dst_y: Y offset in destination buffer (dst_buf + stride * dst_y)
 * stride: bytes per row in destination buffer (typically 320)
 * palette_offset: -1 for direct mode (most common for scroll buffers)
 * Returns 0 on success, -1 on error.
 */
int fd2_rle_decompress_to_buffer(const u8* res_data, u32 res_size,
                                  u8* dst_buf, int dst_y, int stride,
                                  int palette_offset);

/* ---- Palette ---- */

/*
 * Convert 6-bit VGA palette values to 8-bit RGB.
 * 
 * DOS VGA palette uses 6-bit values (0-63). This function converts
 * to 8-bit (0-255) by multiplying by 4 (or using the formula:
 * value_8bit = (value_6bit << 2) | (value_6bit >> 4)).
 * 
 * palette_6bit: 768 bytes (256 colors * 3 channels)
 * palette_8bit: 768 bytes output (or 256*3 RGB array)
 */
void fd2_palette_6bit_to_8bit(const u8* palette_6bit, u8* palette_8bit);

/*
 * Set brightness for a palette.
 * 
 * brightness: 0 (black) to 63 (full)
 * Modifies palette_8bit in place.
 */
void fd2_palette_set_brightness(u8* palette_8bit, int brightness);

/*
 * Fade between two palettes.
 * 
 * src, dst: 768-byte palette buffers
 * out: output palette
 * steps: total number of fade steps
 * current: current step (0 = src, steps = dst)
 */
void fd2_palette_fade(const u8* src, const u8* dst,
                      u8* out, int steps, int current);

/*
 * Add a 6-bit value to every palette entry (sub_11DF2).
 *
 * Operates in 6-bit space for accuracy: converts each 8-bit entry back to
 * 6-bit, adds add_6bit, clamps to 63, converts back to 8-bit.
 * When add_6bit >= 64, every entry becomes 63 (max white).
 * Modifies palette_8bit in place.
 */
void fd2_palette_add_6bit(u8* palette_8bit, int add_6bit);

/* ---- Image Dimensions ---- */

/*
 * Read width and height from a resource with a 4-byte header.
 * Returns 0 on success, -1 if the header is invalid.
 */
int fd2_image_get_dimensions(const u8* data, u32 data_size,
                             int* out_w, int* out_h);

/* ---- Resource Classification ---- */

typedef enum {
    FD2_RES_UNKNOWN,
    FD2_RES_RLE_IMAGE,     /* Starts with valid width/height header */
    FD2_RES_PALETTE,       /* Exactly 768 bytes */
    FD2_RES_NESTED_DAT,    /* Starts with LLLLLL and has valid inner table */
    FD2_RES_TEXT,          /* High ratio of printable ASCII */
    FD2_RES_RAW,           /* Everything else */
} fd2_resource_type_t;

typedef struct {
    fd2_resource_type_t type;
    int                 width;
    int                 height;
    int                 inner_resource_count;  /* For nested DATs */
} fd2_resource_info_t;

/*
 * Classify a resource and fill in the info structure.
 */
void fd2_resource_classify(const u8* data, u32 size, fd2_resource_info_t* info);

/* ---- BG.DAT Background Decoding ---- */

/*
 * Decode a BG.DAT background resource.
 * 
 * BG.DAT backgrounds are 320x100 RLE images with the standard format.
 * This is a convenience wrapper around fd2_rle_decompress_from_resource.
 */
int fd2_bg_decode(const u8* res_data, u32 res_size,
                  u8** out_pixels, int* out_w, int* out_h);

/* ---- FDSHAP.DAT Sprite Decoding ---- */

/*
 * FDSHAP.DAT contains alternating palette/sprite data:
 *   - Even indices: 1200-byte palette/aux data
 *   - Odd indices: 24x24 RLE sprites (may contain multiple frames)
 * 
 * The 1200-byte resources contain 256 palette entries (768 bytes) plus
 * additional metadata (432 bytes).
 */

typedef struct {
    u8  palette[FD2_PALETTE_BYTES];  /* 768 bytes */
    u8  metadata[432];               /* Unknown purpose */
} fd2_shap_palette_t;

/*
 * Extract palette data from a FDSHAP.DAT even-indexed resource.
 * Returns 0 on success.
 */
int fd2_shap_extract_palette(const u8* res_data, u32 res_size,
                             fd2_shap_palette_t* out);

/* ---- FIGANI.DAT Animation Decoding ---- */

/*
 * FIGANI.DAT contains character animation frames:
 *   - Even indices: RLE image frames (various sizes)
 *   - Odd indices: 3-byte timing data (always 00 00 0A = 10)
 */

typedef struct {
    int  width;
    int  height;
    u8*  pixels;      /* Decompressed pixel data (width * height bytes) */
    u32  pixel_count;
    int  frame_delay; /* From associated timing resource (default 10) */
} fd2_ani_frame_t;

/*
 * Decode a single FIGANI.DAT animation frame resource.
 * Returns 0 on success. Caller must free frame->pixels.
 */
int fd2_ani_decode_frame(const u8* res_data, u32 res_size,
                         fd2_ani_frame_t* frame);

/*
 * Read the timing value from a FIGANI.DAT timing resource.
 * Returns the timing value (always 10 in known data), or -1 on error.
 */
int fd2_ani_read_timing(const u8* res_data, u32 res_size);

/* ---- FDTXT.DAT Text/Font Decoding ---- */

/*
 * FDTXT.DAT contains font glyph images as RLE data.
 * Each resource is a single glyph or text block.
 */

typedef struct {
    int  width;
    int  height;
    u8*  pixels;
} fd2_text_glyph_t;

/*
 * Decode a FDTXT.DAT text resource.
 * Returns 0 on success. Caller must free glyph->pixels.
 */
int fd2_text_decode_glyph(const u8* res_data, u32 res_size,
                          fd2_text_glyph_t* glyph);

/* ---- TAI.DAT Portrait Decoding ---- */

/*
 * TAI.DAT contains 155x42 portrait images (character faces).
 */

int fd2_tai_decode_portrait(const u8* res_data, u32 res_size,
                            u8** out_pixels, int* out_w, int* out_h);

/* ---- Utility ---- */

/*
 * Check if data starts with the DAT magic bytes.
 */
int fd2_is_dat_magic(const u8* data, u32 size);

/*
 * Validate that a DAT file's offset table is consistent.
 * Returns 1 if valid, 0 if not.
 */
int fd2_dat_validate_offsets(const u8* data, u32 file_size, u32 resource_count);

#ifdef __cplusplus
}
#endif

#endif /* FD2_DECODER_H */
