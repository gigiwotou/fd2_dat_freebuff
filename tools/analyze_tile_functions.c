/**
 * 分析FDOTHER索引4中各个tile的功能
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

// 简单的RLE解压函数（来自fd2_rle.c）
int simple_rle_decode(u8* src, int src_size, u8* dst, int width, int height) {
    if (src_size < 4) return -1;
    
    int w = src[0] | (src[1] << 8);
    int h = src[2] | (src[3] << 8);
    
    if (w != width || h != height) {
        // 尝试使用传入的宽高
        w = width;
        h = height;
    }
    
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

/**
 * 分析tile功能
 */
void analyze_tile_functionality(const char* data_dir) {
    char path[512];
    snprintf(path, sizeof(path), "%s/FDOTHER.DAT", data_dir);
    
    FILE* f = fopen(path, "rb");
    if (!f) {
        fprintf(stderr, "无法打开 %s\n", path);
        return;
    }
    
    // 读取文件头
    char magic[6];
    if (fread(magic, 1, 6, f) != 6 || memcmp(magic, "LLLLLL", 6) != 0) {
        fclose(f);
        fprintf(stderr, "错误的魔术字节\n");
        return;
    }
    
    u32 resource_count;
    if (fread(&resource_count, 4, 1, f) != 1) {
        fclose(f);
        return;
    }
    
    if (resource_count <= 4) {
        fclose(f);
        return;
    }
    
    // 读取偏移表
    u32* offsets = malloc(resource_count * 4);
    if (!offsets) {
        fclose(f);
        return;
    }
    fseek(f, 10, SEEK_SET);
    if (fread(offsets, 4, resource_count, f) != resource_count) {
        free(offsets);
        fclose(f);
        return;
    }
    
    // 读取索引4的数据
    u32 start = offsets[4];
    u32 end = (4 + 1 < resource_count) ? offsets[4 + 1] : 0;
    if (end == 0) {
        fseek(f, 0, SEEK_END);
        long file_size = ftell(f);
        end = (u32)file_size;
    }
    
    u32 size = end - start;
    u8* data = malloc(size);
    if (!data) {
        free(offsets);
        fclose(f);
        return;
    }
    
    fseek(f, start, SEEK_SET);
    if (fread(data, 1, size, f) != size) {
        free(data);
        free(offsets);
        fclose(f);
        return;
    }
    
    free(offsets);
    fclose(f);
    
    // 验证tile集格式
    if (memcmp(data, "LMI1", 4) != 0) {
        fprintf(stderr, "错误的tile集魔术字节\n");
        free(data);
        return;
    }
    
    u16 tile_count = data[4] | (data[5] << 8);
    printf("FDOTHER索引4 tile分析:\n");
    printf("=====================\n");
    printf("Tile总数: %d\n\n", tile_count);
    
    // 分析关键tile (0-20)
    for (int i = 0; i < 20 && i < tile_count; i++) {
        u32 offset_addr = 6 + i * 4;
        if (offset_addr + 4 > size) break;
        
        u32 tile_offset = data[offset_addr] | 
                          (data[offset_addr + 1] << 8) |
                          (data[offset_addr + 2] << 16) |
                          (data[offset_addr + 3] << 24);
        
        if (tile_offset + 4 > size) continue;
        
        u8* tile_data = data + tile_offset;
        u16 w = tile_data[0] | (tile_data[1] << 8);
        u16 h = tile_data[2] | (tile_data[3] << 8);
        
        // 尝试解压前几个像素以查看内容
        u8* temp_buffer = malloc(w * h);
        if (temp_buffer) {
            // 计算到下一个tile的距离作为数据大小
            u32 data_size = 1000; // 默认大小
            if (i + 1 < tile_count) {
                u32 next_offset = data[6 + (i+1) * 4] | 
                                  (data[6 + (i+1) * 4 + 1] << 8) |
                                  (data[6 + (i+1) * 4 + 2] << 16) |
                                  (data[6 + (i+1) * 4 + 3] << 24);
                if (next_offset > tile_offset) {
                    data_size = next_offset - tile_offset;
                }
            }
            
            int ret = simple_rle_decode(tile_data, data_size < size-tile_offset ? data_size : size-tile_offset, 
                                      temp_buffer, w, h);
            
            // 统计非零像素数量
            int non_zero_pixels = 0;
            for (int p = 0; p < w*h && p < 100; p++) { // 只检查前100个像素
                if (temp_buffer[p] != 0) non_zero_pixels++;
            }
            
            printf("Tile %2d: %2dx%-2d, 偏移:0x%05X, 非零像素:%3d", i, w, h, tile_offset, non_zero_pixels);
            
            // 根据尺寸和内容推断功能
            if (w == 3 && h == 3) {
                printf(" -> 角部tile");
            } else if (w == 16 && h == 3) {
                printf(" -> 水平边框tile");
            } else if (w == 3 && h == 16) {
                printf(" -> 垂直边框tile");
            } else if (w == 16 && h == 16) {
                printf(" -> 内容区tile");
            } else {
                printf(" -> 其他功能tile");
            }
            
            printf("\n");
            free(temp_buffer);
        }
    }
    
    free(data);
}

int main(int argc, char** argv) {
    const char* data_dir = "./";
    if (argc > 1) {
        data_dir = argv[1];
    }
    
    printf("FD2 FDOTHER索引4 Tile功能分析\n");
    printf("===============================\n");
    printf("数据目录: %s\n\n", data_dir);
    
    analyze_tile_functionality(data_dir);
    
    return 0;
}