#ifndef FD2_SPRITE_H
#define FD2_SPRITE_H

#include <stdint.h>

/*
 * fd2_sprite.h - FIGANI.DAT sprite decoder for FD2
 * 
 * Based on IDA analysis of:
 * - sub_4E98D (0x4E98D): Core RLE decoder
 * - sub_2EB9F (0x2EB9F): Sprite frame decoder
 * - sub_2E9A8 (0x2E9A8): Character rendering
 * 
 * FIGANI.DAT contains battle character sprites with RLE compression.
 * Each sprite has multiple frames and directions.
 */

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Sprite frame structure
 */
typedef struct {
    uint16_t width;          /* Frame width in pixels */
    uint16_t height;         /* Frame height in pixels */
    uint8_t* pixels;         /* Decompressed pixel data (palette indices) */
    int pixel_data_size;     /* Size of decompressed pixel data */
} fd2_sprite_frame_t;

/**
 * Sprite structure (single character)
 */
typedef struct {
    int frame_count;         /* Number of frames */
    fd2_sprite_frame_t* frames;
} fd2_sprite_t;

/**
 * Sprite decoder context
 */
typedef struct {
    uint8_t* data;           /* Raw FIGANI.DAT data */
    int data_size;           /* Size of FIGANI.DAT data */
    int sprite_count;        /* Number of sprites */
} fd2_sprite_decoder_t;

/**
 * Initialize sprite decoder with FIGANI.DAT data
 * 
 * @param decoder Decoder context
 * @param data Pointer to FIGANI.DAT data
 * @param data_size Size of FIGANI.DAT data
 * @return 0 on success, -1 on error
 */
int fd2_sprite_decoder_init(fd2_sprite_decoder_t* decoder, 
                            const uint8_t* data, int data_size);

/**
 * Decode a sprite frame from FIGANI.DAT
 * 
 * Based on IDA sub_2EB9F and sub_4E98D.
 * 
 * RLE format:
 * - Read byte 'value'
 * - value << 1: Check carry flag (bit 7 of original value)
 *   - If carry set: Skip pixels (transparent)
 *   - If carry clear: 
 *     - (value << 2) & 0xFF: Count-related value
 *     - Check next carry flag to determine operation
 * 
 * @param decoder Decoder context
 * @param sprite_index Sprite index in FIGANI.DAT
 * @param frame_index Frame index within sprite
 * @param frame Output frame structure (must be pre-allocated)
 * @return 0 on success, -1 on error
 */
int fd2_sprite_decode_frame(fd2_sprite_decoder_t* decoder,
                            int sprite_index, int frame_index,
                            fd2_sprite_frame_t* frame);

/**
 * Decode sprite with palette offset
 * 
 * Based on IDA sub_4E98D with value_1 parameter.
 * When value_1 > 0xFF, palette indices are offset by:
 *   new_index = value_1 + ((value_1 >> 8) + original_index) & 7
 * 
 * @param decoder Decoder context
 * @param sprite_index Sprite index
 * @param frame_index Frame index
 * @param palette_offset Palette offset (0-7 range added to indices)
 * @param frame Output frame structure
 * @return 0 on success, -1 on error
 */
int fd2_sprite_decode_frame_with_palette(fd2_sprite_decoder_t* decoder,
                                         int sprite_index, int frame_index,
                                         int palette_offset,
                                         fd2_sprite_frame_t* frame);

/**
 * Render sprite frame to buffer
 * 
 * @param frame Sprite frame to render
 * @param dest Destination buffer (320 bytes per row)
 * @param dest_width Destination buffer width
 * @param x X position in destination
 * @param y Y position in destination
 * @return 0 on success, -1 on error
 */
int fd2_sprite_render(const fd2_sprite_frame_t* frame,
                      uint8_t* dest, int dest_width,
                      int x, int y);

/**
 * Free sprite frame data
 * 
 * @param frame Frame to free
 */
void fd2_sprite_frame_free(fd2_sprite_frame_t* frame);

/**
 * Cleanup sprite decoder
 * 
 * @param decoder Decoder context
 */
void fd2_sprite_decoder_free(fd2_sprite_decoder_t* decoder);

#ifdef __cplusplus
}
#endif

#endif /* FD2_SPRITE_H */
