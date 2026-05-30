#include "../include/fd2_dat.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define DAT_MAGIC "LLLLLL"

byte* fd2_load_dat_resource(const char* filename, byte* prev_buf, int resource_idx, dword* out_size) {
    FILE* f = fopen(filename, "rb");
    if (!f) return NULL;
    
    // Read header
    char magic[6];
    if (fread(magic, 1, 6, f) != 6) {
        fclose(f);
        return NULL;
    }
    if (memcmp(magic, DAT_MAGIC, 6) != 0) {
        fclose(f);
        return NULL;
    }
    
    dword resource_count;
    if (fread(&resource_count, 4, 1, f) != 1) {
        fclose(f);
        return NULL;
    }
    
    if (resource_idx < 0 || resource_idx >= resource_count) {
        fclose(f);
        return NULL;
    }
    
    // Read offset table
    dword* offsets = malloc(resource_count * 4);
    if (!offsets) {
        fclose(f);
        return NULL;
    }
    fseek(f, 10, SEEK_SET); // skip magic (6) + count (4)
    if (fread(offsets, 4, resource_count, f) != resource_count) {
        free(offsets);
        fclose(f);
        return NULL;
    }
    
    dword start = offsets[resource_idx];
    dword end = (resource_idx + 1 < resource_count) ? offsets[resource_idx + 1] : -1;
    dword size;
    if (end == -1) {
        // Get file size
        fseek(f, 0, SEEK_END);
        long file_size = ftell(f);
        size = file_size - start;
    } else {
        size = end - start;
    }
    
    byte* data = malloc(size);
    if (!data) {
        free(offsets);
        fclose(f);
        return NULL;
    }
    
    fseek(f, start, SEEK_SET);
    if (fread(data, 1, size, f) != size) {
        free(data);
        free(offsets);
        fclose(f);
        return NULL;
    }
    
    free(offsets);
    fclose(f);
    
    *out_size = size;
    return data;
}

int fd_load_palette(const char *filename, byte palette[768]) {
    FILE* f = fopen(filename, "rb");
    if (!f) return -1;
    
    // Find palette resource (resource 0 or 7)
    char magic[6];
    if (fread(magic, 1, 6, f) != 6) {
        fclose(f);
        return -1;
    }
    if (memcmp(magic, DAT_MAGIC, 6) != 0) {
        fclose(f);
        return -1;
    }
    
    dword resource_count;
    if (fread(&resource_count, 4, 1, f) != 1) {
        fclose(f);
        return -1;
    }
    
    dword* offsets = malloc(resource_count * 4);
    if (!offsets) {
        fclose(f);
        return -1;
    }
    fseek(f, 10, SEEK_SET);
    if (fread(offsets, 4, resource_count, f) != resource_count) {
        free(offsets);
        fclose(f);
        return -1;
    }
    
    // Try resource 7 first (palette)
    int palette_res = 7;
    if (palette_res >= resource_count) {
        palette_res = 0;
    }
    
    dword start = offsets[palette_res];
    fseek(f, start, SEEK_SET);
    size_t read = fread(palette, 1, 768, f);
    free(offsets);
    fclose(f);
    
    return (read == 768) ? 0 : -1;
}

void fd_get_image_dimensions(const byte *data, int *width, int *height) {
    if (!data) {
        *width = *height = 0;
        return;
    }
    // Assuming data starts with 4-byte header: little-endian width (2 bytes) and height (2 bytes)
    *width = data[0] | (data[1] << 8);
    *height = data[2] | (data[3] << 8);
}

int fd_decompress_rle(const byte *src, int src_size, byte *dst, int dst_width, int dst_height, int value_param) {
    // 按照sub_4E98D汇编代码1:1实现
    // value_param == -1时: 不应用调色板窗口（在渲染时应用）
    // value_param != -1时: 应用调色板窗口 (value_param + pixel) & 0xFF
    
    int expected = dst_width * dst_height;
    int dst_idx = 0;
    int src_idx = 0;
    
    // 按行处理 (arg8 = height)
    for (int row = 0; row < dst_height; row++) {
        int remaining = dst_width;  // bx = width
        
        while (remaining > 0 && src_idx < src_size) {
            // 读取控制字节
            byte ctrl = src[src_idx];
            src_idx++;
            
            int bit7 = (ctrl >> 7) & 1;
            int bit6 = (ctrl >> 6) & 1;
            int count = (ctrl & 0x3F) + 1;
            
            if (bit7 == 0) {
                if (bit6 == 0) {
                    // FILL (0x4E9EE): 读取1个值，连续填充count个位置
                    int actual_count = (count < remaining) ? count : remaining;
                    
                    if (src_idx < src_size) {
                        byte fill_val = src[src_idx];
                        src_idx++;
                        
                        if (value_param != -1) {
                            fill_val = (value_param + fill_val) & 0xFF;
                        }
                        
                        for (int i = 0; i < actual_count && dst_idx < expected; i++) {
                            dst[dst_idx] = fill_val;
                            dst_idx++;
                        }
                    }
                    
                    remaining -= actual_count;
                    
                } else {
                    // COPY_SPEC (0x4EA00): 读取1个值，间隔写入
                    // 关键: sub bx, cx 执行两次 = 消耗2*count个位置
                    // 但每次循环只写入1个值，dst前进2 (inc edi + stosb)
                    
                    int total_consume = count * 2;
                    int actual_count = count;
                    
                    if (total_consume > remaining) {
                        actual_count = remaining / 2;
                        total_consume = actual_count * 2;
                    }
                    
                    if (src_idx < src_size) {
                        byte val = src[src_idx];
                        src_idx++;
                        
                        if (value_param != -1) {
                            val = (value_param + val) & 0xFF;
                        }
                        
                        // loop: inc edi; stosb
                        // 每次循环: dst前进2
                        for (int i = 0; i < actual_count && dst_idx < expected; i++) {
                            dst[dst_idx] = val;
                            dst_idx += 2;  // inc edi + stosb
                        }
                    }
                    
                    remaining -= total_consume;
                }
            } else {
                if (bit6 == 0) {
                    // COPY_STD (0x4EA17): 从src复制count个字节
                    int actual_count = (count < remaining) ? count : remaining;
                    actual_count = (actual_count < (src_size - src_idx)) ? actual_count : (src_size - src_idx);
                    
                    for (int i = 0; i < actual_count && dst_idx < expected && src_idx < src_size; i++) {
                        byte val = src[src_idx];
                        src_idx++;
                        
                        if (value_param != -1) {
                            val = (value_param + val) & 0xFF;
                        }
                        
                        dst[dst_idx] = val;
                        dst_idx++;
                    }
                    
                    remaining -= actual_count;
                    
                } else {
                    // SKIP (0x4EA2C): 跳过count个位置
                    int actual_count = (count < remaining) ? count : remaining;
                    
                    dst_idx += actual_count;
                    remaining -= actual_count;
                }
            }
        }
        
        // 行结束: add edi, edx (edx = stride - width)
        // 这里假设stride = width，所以不需要额外前进
    }
    
    return 0;
}

int fd_analyze_resource(const byte *data, int size) {
    // Placeholder for debugging
    return 0;
}

/* sub_4EBFF: 渲染像素数据到屏幕缓冲区 */
/* 根据IDA Pro MCP反编译代码1:1实现 */
/* 参数: dst=目标缓冲区, src=源数据(包含4字节宽高头), pitch=行间距 */
void sub_4EBFF(byte* dst, byte* src, int pitch) {
    /* 解析源数据头部的宽高信息 */
    word width = src[0] | (src[1] << 8);
    word height = src[2] | (src[3] << 8);
    
    /* 像素数据从偏移4开始 */
    byte* pixel_data = src + 4;
    
    /* 外层循环: 遍历每一行 */
    for (int y = 0; y < height; y++) {
        byte* row_start = dst;  /* 记录当前行起始位置 */
        
        /* 内层循环: 遍历当前行的每个像素 */
        for (int x = 0; x < width; x++) {
            *dst++ = *pixel_data++;  /* 将像素值写入目标缓冲区 */
        }
        
        /* 移动到下一行 (根据目标缓冲区的pitch) */
        dst = row_start + pitch;
    }
}