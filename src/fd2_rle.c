#include "../include/fd2_rle.h"
#include <string.h>

int fd2_decode_fdother_resource(byte* src, int src_size, byte* dst, int width, int height) {
    if (src_size < 4) return -1;
    // Read width and height from header (little-endian)
    int w = src[0] | (src[1] << 8);
    int h = src[2] | (src[3] << 8);
    if (src_size <= 4) return -1;
    byte* compressed = src + 4;
    int comp_size = src_size - 4;
    int expected = width * height;
    
    // RLE decompression algorithm - fixed version
    int num4 = 0;
    int num3 = comp_size - 1;
    int num7 = 0;
    int num8 = 0;
    int num9 = 0;
    byte b = 0;
    int num10 = 0; // x coordinate
    int num11 = 0; // y coordinate
    
    int pixel_idx = 0;
    
    while (num4 <= num3 && pixel_idx < expected) {
        int flag = num8 != 0;
        
        if (!flag) {
            num7 = 0;
            num8 = 0;
            num9 = 0;
            
            if (num4 < comp_size) {
                b = compressed[num4];
                if (b >= 192) {
                    num7 = b - 192 + 1;
                } else if (b >= 128) {
                    num8 = b - 128 + 1;
                } else if (b >= 64) {
                    num9 = b - 64;
                    num8 = 1;
                } else {
                    num8 = 1;
                    num9 = b;
                }
            }
            
            num10 += num7;
            if (num10 >= width) {
                num10 = 0;
                num11 += 1;
            }
        } else {
            int num12 = num9;
            int num13 = 0;
            while (num13 <= num12) {
                if (b >= 64 && b < 128) {
                    num10 += 1;
                    num4++;  // FIX: increment num4 in COPY command loop
                }
                if (num4 < comp_size) {
                    byte index = compressed[num4];
                    if (num10 >= 0 && num10 < width && num11 >= 0 && num11 < height) {
                        if (pixel_idx < expected) {
                            dst[pixel_idx] = index;
                            pixel_idx++;
                        }
                    }
                }
                num10 += 1;
                if (num10 >= width) {
                    num10 = 0;
                    num11 += 1;
                }
                num13++;
            }
            num8--;
        }
        
        num4++;
        
        if (num11 >= height) {
            break;
        }
    }
    
    return 0;
}

int fd2_decode_bg_resource(byte* src, int length, byte* palette, byte* dst, int stride) {
    // TODO: implement BG.DAT decompression
    return -1;
}