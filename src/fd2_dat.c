/**
 * FD2游戏RLE解码函数
 * 
 * 根据IDA Pro MCP分析，FD2使用两种RLE格式：
 * 1. sub_4E98D: 通用RLE解码（索引11等Tile图像）
 *    - 控制字节格式: bit7=1为压缩命令，bit6区分跳过/复制
 *    - count = (ctrl & 0x3F) + 1
 * 2. sub_4E22A: 24x24图标专用RLE解码（索引1）
 *    - 4种模式：填充、交替、复制、跳过
 */

#include "../include/fd2_dat.h"
#include "../include/fd2_rle.h"
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

/* fd_decompress_rle: 通用RLE解码函数 (兼容旧接口)
 *
 * 已重构: 实际实现委托给 fd2_rle.c 中的 fd2_rle_sub_4E98D_no_header
 * (基于 sub_4E98D 通用RLE, 无4字节头版本, 与旧行为完全一致)
 *
 * RLE控制字节格式:
 * - bit7=1, bit6=0: COPY - 从源数据复制count个字节
 * - bit7=1, bit6=1: SKIP - 跳过count个像素（透明）
 * - bit7=0:        FILL - 用指定颜色填充count个像素
 *
 * value_1参数:
 * - value_1 == -1: 直接模式，直接使用原始像素值
 * - value_1 > 0xFF: 调色板偏移模式，使用变换公式
 * - value_1 <= 0xFF: 单色模式，使用固定颜色
 */
int fd_decompress_rle(const byte *src, int src_size, byte *dst, int width, int height, int value_1) {
    return fd2_rle_sub_4E98D_no_header(src, src_size, dst, width, height, value_1);
}

int fd_analyze_resource(const byte *data, int size) {
    // Placeholder for debugging
    return 0;
}

/* fd_decompress_sub_4E22A: 24x24图标专用RLE解码（兼容旧接口）
 *
 * 已重构: 实际实现委托给 fd2_rle.c 中的 fd2_rle_sub_4E22A
 * 编码格式（2位控制）：
 * - 00xxxxxx: 填充模式 - memset(dst, color, count)
 * - 01xxxxxx: 交替模式 - 间隔写入像素（dst+=2）
 * - 10xxxxxx: 复制模式 - memcpy(dst, src, count)
 * - 11xxxxxx: 跳过模式 - dst += count（透明像素）
 * count = (value & 0x3F) + 1
 */
int fd_decompress_sub_4E22A(const byte *src, int src_size, byte *dst, int width, int height, int pitch) {
    return fd2_rle_sub_4E22A(src, src_size, dst, width, height, pitch);
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
    int pixel_data_size = (width * height * 2); /* 估算大小 */
    
    /* sub_4EC66状态变量 */
    byte ah = 0;        /* 运行长度计数器 */
    byte prev_al = 0;   /* 上次读取的像素值 */
    int src_idx = 0;
    
    /* 外层循环: 遍历每一行 */
    for (int y = 0; y < height; y++) {
        byte* row_start = dst;  /* push edi - 记录当前行起始位置 */
        
        /* 内层循环: 遍历当前行的每个像素 */
        for (int x = 0; x < width; x++) {
            /* call sub_4EC66 - 获取解码后的像素值 */
            if (ah > 0) {
                /* AH > 0: 重复之前的像素值 */
                ah--;
            } else {
                /* AH == 0: 读取新字节 */
                if (src_idx < pixel_data_size) {
                    byte al = pixel_data[src_idx];
                    src_idx++;
                    
                    if (al > 0xC0) {
                        /* AL > 0xC0: 运行长度编码 */
                        ah = al - 0xC1;
                        if (src_idx < pixel_data_size) {
                            al = pixel_data[src_idx];
                            src_idx++;
                        }
                        prev_al = al;
                    } else {
                        /* AL <= 0xC0: 直接像素值 */
                        ah = 0;
                        prev_al = al;
                    }
                }
            }
            /* stosb: 存储像素值到目标缓冲区 */
            *dst++ = prev_al;
        }
        
        /* pop edi + add edi, ebx - 恢复到行起始，然后移动到下一行 */
        dst = row_start + pitch;
    }
}