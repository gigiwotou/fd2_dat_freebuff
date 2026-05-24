/**
 * 测试Tile 13的RLE解压是否正确
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

// 从fd2_rle.c复制的RLE解压函数
int fd2_decode_fdother_resource(u8* src, int length, u8* dst, int width, int height) {
    int v4 = 0;
    int v5 = length - 1;
    int v6 = 0;
    int v7 = 0;
    int v8 = 0;
    int v9 = 0;
    u8 b = 0;
    int x = 0;
    int y = 0;
    
    while (v4 <= v5 && y < height) {
        int flag = (v8 != 0);
        
        if (!flag) {
            v6 = 0;
            v8 = 0;
            v9 = 0;
            
            if (v4 < length) {
                b = src[v4];
                if (b >= 192) {
                    v6 = (b - 192) + 1;
                } else if (b >= 128) {
                    v8 = (b - 128) + 1;
                } else if (b >= 64) {
                    v9 = b - 64;
                    v8 = 1;
                } else {
                    v8 = 1;
                    v9 = b;
                }
            }
            
            x += v6;
            if (x >= width) {
                x = 0;
                y += 1;
            }
        } else {
            int count = v9;
            int i = 0;
            while (i <= count) {
                if (b >= 64 && b < 128) {
                    x += 1;
                }
                if (v4 < length) {
                    u8 index = src[v4];
                    if (x >= 0 && x < width && y >= 0 && y < height) {
                        int pixel_idx = y * width + x;
                        if (pixel_idx < width * height) {
                            dst[pixel_idx] = index;
                        }
                    }
                }
                x += 1;
                if (x >= width) {
                    x = 0;
                    y += 1;
                }
                i++;
            }
            v8--;
        }
        
        v4++;
        
        if (y >= height) {
            break;
        }
    }
    
    return 0;
}

void test_tile_13(const char* data_dir) {
    char path[512];
    snprintf(path, sizeof(path), "%s/FDOTHER.DAT", data_dir);
    
    FILE* f = fopen(path, "rb");
    if (!f) {
        fprintf(stderr, "无法打开 %s\n", path);
        return;
    }
    
    // 读取文件头
    char magic[6];
    fread(magic, 1, 6, f);
    
    u32 resource_count;
    fread(&resource_count, 4, 1, f);
    
    u32* offsets = malloc(resource_count * 4);
    fseek(f, 10, SEEK_SET);
    fread(offsets, 4, resource_count, f);
    
    // 读取索引4
    u32 start = offsets[4];
    u32 end = offsets[5];
    u32 size = end - start;
    
    u8* data = malloc(size);
    fseek(f, start, SEEK_SET);
    fread(data, 1, size, f);
    fclose(f);
    
    // 获取Tile 13
    u32 tile13_offset = data[6 + 13*4] | 
                        (data[6 + 13*4 + 1] << 8) |
                        (data[6 + 13*4 + 2] << 16) |
                        (data[6 + 13*4 + 3] << 24);
    
    u8* tile13_data = data + tile13_offset;
    u16 w = tile13_data[0] | (tile13_data[1] << 8);
    u16 h = tile13_data[2] | (tile13_data[3] << 8);
    
    printf("Tile 13 信息:\n");
    printf("  偏移: 0x%05X\n", tile13_offset);
    printf("  尺寸: %dx%d\n", w, h);
    printf("  头部字节: %02X %02X %02X %02X\n", 
           tile13_data[0], tile13_data[1], tile13_data[2], tile13_data[3]);
    
    // 显示前50个RLE字节
    printf("  前50个RLE字节: ");
    for (int i = 4; i < 54; i++) {
        printf("%02X ", tile13_data[i]);
    }
    printf("\n\n");
    
    // RLE解压
    u8* decoded = malloc(w * h);
    memset(decoded, 0, w * h);
    
    // 计算压缩数据大小（到下一个tile的距离）
    u32 next_offset = data[6 + 14*4] | 
                      (data[6 + 14*4 + 1] << 8) |
                      (data[6 + 14*4 + 2] << 16) |
                      (data[6 + 14*4 + 3] << 24);
    u32 compressed_size = next_offset - tile13_offset;
    
    printf("压缩数据大小: %d 字节\n", compressed_size);
    
    int ret = fd2_decode_fdother_resource(tile13_data, compressed_size, decoded, w, h);
    
    printf("解压结果: %d\n\n", ret);
    
    // 统计像素值分布
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
    
    // 显示前3行的像素值
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
    
    printf("测试Tile 13的RLE解压\n");
    printf("====================\n");
    printf("数据目录: %s\n\n", data_dir);
    
    test_tile_13(data_dir);
    
    return 0;
}