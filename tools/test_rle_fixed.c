/**
 * 测试修复后的RLE解压算法
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

/**
 * 修复后的RLE解压函数
 * 关键修复：在COPY命令（64-127）的循环中正确递增num4
 */
int fd2_decode_fdother_resource_fixed(u8* src, int src_size, u8* dst, int width, int height) {
    if (src_size < 4) return -1;
    int w = src[0] | (src[1] << 8);
    int h = src[2] | (src[3] << 8);
    if (src_size <= 4) return -1;
    
    u8* compressed = src + 4;
    int comp_size = src_size - 4;
    int expected = width * height;
    
    int num4 = 0;
    int num3 = comp_size - 1;
    int num7 = 0;
    int num8 = 0;
    int num9 = 0;
    u8 b = 0;
    int num10 = 0;
    int num11 = 0;
    
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
                    num4++;  // 修复：在COPY命令循环中递增num4
                }
                if (num4 < comp_size) {
                    u8 index = compressed[num4];
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

void test_tile_13_fixed(const char* data_dir) {
    char path[512];
    snprintf(path, sizeof(path), "%s/FDOTHER.DAT", data_dir);
    
    FILE* f = fopen(path, "rb");
    if (!f) {
        fprintf(stderr, "无法打开 %s\n", path);
        return;
    }
    
    char magic[6];
    fread(magic, 1, 6, f);
    
    u32 resource_count;
    fread(&resource_count, 4, 1, f);
    
    u32* offsets = malloc(resource_count * 4);
    fseek(f, 10, SEEK_SET);
    fread(offsets, 4, resource_count, f);
    
    u32 start = offsets[4];
    u32 end = offsets[5];
    u32 size = end - start;
    
    u8* data = malloc(size);
    fseek(f, start, SEEK_SET);
    fread(data, 1, size, f);
    fclose(f);
    
    u32 tile13_offset = data[6 + 13*4] | 
                        (data[6 + 13*4 + 1] << 8) |
                        (data[6 + 13*4 + 2] << 16) |
                        (data[6 + 13*4 + 3] << 24);
    
    u8* tile13_data = data + tile13_offset;
    u16 w = tile13_data[0] | (tile13_data[1] << 8);
    u16 h = tile13_data[2] | (tile13_data[3] << 8);
    
    printf("Tile 13 信息:\n");
    printf("  尺寸: %dx%d\n", w, h);
    
    u32 next_offset = data[6 + 14*4] | 
                      (data[6 + 14*4 + 1] << 8) |
                      (data[6 + 14*4 + 2] << 16) |
                      (data[6 + 14*4 + 3] << 24);
    u32 compressed_size = next_offset - tile13_offset;
    
    u8* decoded = malloc(w * h);
    memset(decoded, 0, w * h);
    
    int ret = fd2_decode_fdother_resource_fixed(tile13_data, compressed_size, decoded, w, h);
    
    printf("解压结果: %d\n\n", ret);
    
    printf("像素值分布:\n");
    int counts[256] = {0};
    for (int i = 0; i < w * h; i++) {
        counts[decoded[i]]++;
    }
    
    for (int i = 0; i < 256; i++) {
        if (counts[i] > 0) {
            printf("  像素值 %3d (0x%02X): %5d 个 (%.1f%%)\n", 
                   i, i, counts[i], 100.0 * counts[i] / (w * h));
        }
    }
    
    printf("\n前3行像素值:\n");
    for (int y = 0; y < 3 && y < h; y++) {
        printf("  行%2d: ", y);
        for (int x = 0; x < w && x < 32; x++) {
            printf("%02X ", decoded[y * w + x]);
        }
        printf("\n");
    }
    
    free(decoded);
    free(data);
    free(offsets);
}

int main(int argc, char** argv) {
    const char* data_dir = "./";
    if (argc > 1) {
        data_dir = argv[1];
    }
    
    printf("测试修复后的RLE解压算法\n");
    printf("========================\n");
    printf("数据目录: %s\n\n", data_dir);
    
    test_tile_13_fixed(data_dir);
    
    return 0;
}