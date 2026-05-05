/*
 * fd2_sprite.c - FIGANI.DAT sprite decoder for FD2
 * 
 * Based on IDA analysis and actual file structure analysis:
 * 
 * FIGANI.DAT structure (Format 2 with LLLLLL header):
 * - 410 resources total
 * - Valid sprites have header 0x00040004
 * - Sprite header format:
 *   - DWORD[0]: 0x00040004 (magic)
 *   - DWORD[1]: 0 (unknown)
 *   - DWORD[2]: Height (e.g., 24 pixels)
 *   - DWORD[3+]: Frame offsets (relative to resource start)
 * - Each sprite typically has 3 frames
 * - Frame data: RLE-compressed pixel data
 * 
 * RLE format (from IDA sub_4E98D and decoder implementation):
 *   Each byte encodes a command via bits 7-6:
 *   - 11xxxxxx: Skip pixels (transparent)
 *   - 10xxxxxx: Copy pixels from source
 *   - 01xxxxxx: Sparse fill (every 2nd pixel)
 *   - 00xxxxxx: Regular fill
 *   Count = (value & 0x3F) + 1
 */

#include "fd2_sprite.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* FIGANI.DAT internal structure */
typedef struct {
    uint32_t header;        /* 0x00040004 */
    uint16_t width;         /* Calculated from frame size */
    uint16_t height;        /* DWORD[2] */
    uint32_t frame_count;   /* Number of frames */
    uint32_t* frame_offsets; /* Offsets to frame data */
} figani_sprite_internal_t;

/*
 * Parse a single sprite resource from FIGANI.DAT
 */
static int parse_sprite_resource(const uint8_t* data, int size,
                                 figani_sprite_internal_t* sprite) {
    if (size < 16) {
        return -1;  /* Too small for header */
    }
    
    sprite->header = *(uint32_t*)(data + 0);
    
    /* Check for valid sprite header */
    if (sprite->header != 0x00040004 && sprite->header != 0x40004) {
        return -1;
    }
    
    sprite->height = (uint16_t)(*(uint32_t*)(data + 8) & 0xFFFF);
    sprite->width = 0;  /* Will be calculated from frame data */
    
    /* Count frame offsets (starting at offset 12) */
    int frame_count = 0;
    int offset = 12;
    
    while (offset + 4 <= size) {
        uint32_t frame_offset = *(uint32_t*)(data + offset);
        if (frame_offset >= (uint32_t)size || frame_offset < (uint32_t)offset + 4) {
            break;  /* Invalid offset */
        }
        frame_count++;
        offset += 4;
    }
    
    sprite->frame_count = frame_count;
    sprite->frame_offsets = (uint32_t*)malloc(frame_count * sizeof(uint32_t));
    if (!sprite->frame_offsets) {
        return -1;
    }
    
    for (int i = 0; i < frame_count; i++) {
        sprite->frame_offsets[i] = *(uint32_t*)(data + 12 + i * 4);
    }
    
    return 0;
}

/*
 * Free internal sprite data
 */
static void free_sprite_internal(figani_sprite_internal_t* sprite) {
    if (sprite && sprite->frame_offsets) {
        free(sprite->frame_offsets);
        sprite->frame_offsets = NULL;
    }
}

/*
 * Decode sprite frame with given width
 */
static int decode_sprite_frame(const uint8_t* frame_data, int frame_size,
                               uint16_t width, uint16_t height,
                               uint8_t* pixels, int pixel_size) {
    if (!frame_data || !pixels || width == 0 || height == 0) {
        return -1;
    }
    
    int expected_size = width * height;
    if (pixel_size < expected_size) {
        return -1;
    }
    
    /* Clear output buffer */
    memset(pixels, 0, expected_size);
    
    const uint8_t* src_ptr = frame_data;
    const uint8_t* src_end = frame_data + frame_size;
    uint8_t* dst = pixels;
    int dst_end = expected_size;
    
    for (int y = 0; y < height; y++) {
        int remaining = width;
        
        while (remaining > 0 && src_ptr < src_end) {
            uint8_t value = *src_ptr++;
            
            /* Extract bits 7-6 for command type */
            int bit7 = (value >> 7) & 1;
            int bit6 = (value >> 6) & 1;
            int count = (value & 0x3F) + 1;
            
            if (count > remaining) {
                count = remaining;
            }
            
            if (bit7 && bit6) {
                /* 11xxxxxx: Skip pixels (transparent) */
                dst += count;
                remaining -= count;
            } else if (bit7 && !bit6) {
                /* 10xxxxxx: Copy pixels from source */
                if (src_ptr + count > src_end) {
                    return -1;  /* Not enough data */
                }
                for (int i = 0; i < count; i++) {
                    if (dst < pixels + dst_end) {
                        *dst = *src_ptr++;
                    }
                    dst++;
                }
                remaining -= count;
            } else if (!bit7 && bit6) {
                /* 01xxxxxx: Sparse fill (every pixel) */
                if (src_ptr >= src_end) {
                    return -1;
                }
                uint8_t fill_value = *src_ptr++;
                
                for (int i = 0; i < count && remaining > 0; i++) {
                    if (dst < pixels + dst_end) {
                        *dst = fill_value;
                    }
                    dst++;
                    remaining--;
                }
            } else {
                /* 00xxxxxx: Regular fill */
                if (src_ptr >= src_end) {
                    return -1;
                }
                uint8_t fill_value = *src_ptr++;
                
                for (int i = 0; i < count && remaining > 0; i++) {
                    if (dst < pixels + dst_end) {
                        *dst = fill_value;
                    }
                    dst++;
                    remaining--;
                }
            }
        }
        
        /* Move to next row */
        if (y < height - 1) {
            int row_end = (y + 1) * width;
            int current_pos = (int)(dst - pixels);
            if (current_pos < row_end) {
                dst = pixels + row_end;
            }
        }
    }
    
    return 0;
}

/*
 * Initialize sprite decoder with FIGANI.DAT data
 */
int fd2_sprite_decoder_init(fd2_sprite_decoder_t* decoder,
                            const uint8_t* data, int data_size) {
    if (!decoder || !data || data_size <= 0) {
        return -1;
    }
    
    decoder->data = (uint8_t*)data;
    decoder->data_size = data_size;
    decoder->sprite_count = 0;
    
    printf("fd2_sprite_decoder_init: FIGANI.DAT size=%d bytes\n", data_size);
    
    return 0;
}

/*
 * Decode a sprite frame from FIGANI.DAT
 */
int fd2_sprite_decode_frame(fd2_sprite_decoder_t* decoder,
                            int sprite_index, int frame_index,
                            fd2_sprite_frame_t* frame) {
    return fd2_sprite_decode_frame_with_palette(decoder, sprite_index, 
                                                 frame_index, -1, frame);
}

/*
 * Decode sprite with palette offset
 */
int fd2_sprite_decode_frame_with_palette(fd2_sprite_decoder_t* decoder,
                                         int sprite_index, int frame_index,
                                         int palette_offset,
                                         fd2_sprite_frame_t* frame) {
    if (!decoder || !frame || !decoder->data) {
        return -1;
    }
    
    if (sprite_index < 0 || frame_index < 0) {
        return -1;
    }
    
    /* Navigate to sprite resource using DAT offset table */
    /* Note: This assumes decoder->data points to full FIGANI.DAT */
    /* We need to parse the DAT structure to find the sprite */
    
    /* For now, assume FIGANI.DAT Format 2 with offset table */
    if (decoder->data_size < 10) {
        return -1;
    }
    
    /* Check for LLLLLL magic */
    if (memcmp(decoder->data, "LLLLLL", 6) != 0) {
        fprintf(stderr, "fd2_sprite_decode_frame: invalid DAT magic\n");
        return -1;
    }
    
    /* Parse resource count */
    uint32_t resource_count;
    memcpy(&resource_count, decoder->data + 6, 4);
    
    if ((uint32_t)sprite_index >= resource_count) {
        fprintf(stderr, "fd2_sprite_decode_frame: sprite_index %d out of range (%u)\n",
                sprite_index, resource_count);
        return -1;
    }
    
    /* Get resource offset */
    uint32_t res_offset;
    memcpy(&res_offset, decoder->data + 10 + sprite_index * 4, 4);
    
    if (res_offset >= (uint32_t)decoder->data_size) {
        return -1;
    }
    
    /* Get next resource offset (or file size) */
    uint32_t next_offset;
    if ((uint32_t)sprite_index + 1 < resource_count) {
        memcpy(&next_offset, decoder->data + 10 + (sprite_index + 1) * 4, 4);
    } else {
        next_offset = decoder->data_size;
    }
    
    uint32_t res_size = next_offset - res_offset;
    const uint8_t* res_data = decoder->data + res_offset;
    
    /* Parse sprite resource */
    figani_sprite_internal_t sprite;
    memset(&sprite, 0, sizeof(sprite));
    
    if (parse_sprite_resource(res_data, res_size, &sprite) != 0) {
        fprintf(stderr, "fd2_sprite_decode_frame: failed to parse sprite resource\n");
        return -1;
    }
    
    if (frame_index >= (int)sprite.frame_count) {
        fprintf(stderr, "fd2_sprite_decode_frame: frame_index %d out of range (%u)\n",
                frame_index, sprite.frame_count);
        free_sprite_internal(&sprite);
        return -1;
    }
    
    /* Get frame data */
    uint32_t frame_start = sprite.frame_offsets[frame_index];
    uint32_t frame_end = ((uint32_t)frame_index + 1 < sprite.frame_count) ? 
                         sprite.frame_offsets[frame_index + 1] : res_size;
    
    if (frame_start >= frame_end || frame_end > res_size) {
        fprintf(stderr, "fd2_sprite_decode_frame: invalid frame offsets\n");
        free_sprite_internal(&sprite);
        return -1;
    }
    
    const uint8_t* frame_data = res_data + frame_start;
    uint32_t frame_size = frame_end - frame_start;
    
    /* Determine width from frame data size and height */
    /* For 24x24 sprites: 576 pixels, frame size ~5000-6000 bytes (compressed) */
    uint16_t width, height;
    height = sprite.height;
    
    /* Common widths: 24, 32, 36, 48 */
    uint16_t test_widths[] = {24, 32, 36, 48, 64, 16};
    int num_widths = sizeof(test_widths) / sizeof(test_widths[0]);
    
    /* Allocate pixel buffer */
    uint8_t* pixels = NULL;
    int decoded = 0;
    
    for (int i = 0; i < num_widths; i++) {
        width = test_widths[i];
        int pixel_size = width * height;
        
        if (pixel_size > 100000) {
            continue;  /* Too large */
        }
        
        pixels = (uint8_t*)calloc(1, pixel_size);
        if (!pixels) {
            free_sprite_internal(&sprite);
            return -1;
        }
        
        if (decode_sprite_frame(frame_data, frame_size, width, height,
                                pixels, pixel_size) == 0) {
            decoded = 1;
            break;
        }
        
        free(pixels);
        pixels = NULL;
    }
    
    free_sprite_internal(&sprite);
    
    if (!decoded || !pixels) {
        fprintf(stderr, "fd2_sprite_decode_frame: failed to decode frame\n");
        return -1;
    }
    
    /* Fill output frame */
    frame->width = width;
    frame->height = height;
    frame->pixels = pixels;
    frame->pixel_data_size = width * height;
    
    return 0;
}

/*
 * Render sprite frame to buffer
 */
int fd2_sprite_render(const fd2_sprite_frame_t* frame,
                      uint8_t* dest, int dest_width,
                      int x, int y) {
    if (!frame || !frame->pixels || !dest) {
        return -1;
    }
    
    /* Calculate destination position */
    int dst_x = x;
    int dst_y = y;
    int copy_width = frame->width;
    int copy_height = frame->height;
    int src_x_offset = 0;  /* Offset into source sprite when clipped */
    int src_y_offset = 0;  /* Offset into source sprite when clipped */
    
    /* Clip to destination bounds */
    if (dst_x < 0) {
        src_x_offset = -dst_x;  /* Skip the clipped left portion */
        copy_width += dst_x;
        dst_x = 0;
    }
    if (dst_y < 0) {
        src_y_offset = -dst_y;  /* Skip the clipped top portion */
        copy_height += dst_y;
        dst_y = 0;
    }
    
    if (copy_width <= 0 || copy_height <= 0) {
        return -1;
    }
    
    if (dst_x + copy_width > dest_width) {
        copy_width = dest_width - dst_x;
    }
    if (dst_y + copy_height > 200) {
        copy_height = 200 - dst_y;
    }
    
    if (copy_width <= 0 || copy_height <= 0) {
        return -1;
    }
    
    /* Copy pixels row by row, skip transparent pixels (value == 0) */
    uint8_t* dst = dest + dst_y * dest_width + dst_x;
    const uint8_t* src = frame->pixels + src_y_offset * frame->width + src_x_offset;
    
    for (int row = 0; row < copy_height; row++) {
        for (int col = 0; col < copy_width; col++) {
            uint8_t pixel = src[col];
            if (pixel != 0) {  /* Skip transparent pixels */
                dst[col] = pixel;
            }
        }
        src += frame->width;
        dst += dest_width;
    }
    
    return 0;
}

/*
 * Free sprite frame data
 */
void fd2_sprite_frame_free(fd2_sprite_frame_t* frame) {
    if (frame && frame->pixels) {
        free(frame->pixels);
        frame->pixels = NULL;
    }
}

/*
 * Cleanup sprite decoder
 */
void fd2_sprite_decoder_free(fd2_sprite_decoder_t* decoder) {
    if (decoder) {
        decoder->data = NULL;
        decoder->data_size = 0;
        decoder->sprite_count = 0;
    }
}
