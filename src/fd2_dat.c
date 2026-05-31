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
    // 按照sub_4EC66 + sub_4EBFF汇编代码1:1实现
    // sub_4EC66: 像素解码（运行长度编码）
    // value_param: 保留参数，当前不使用（palette_window在draw_pixels中应用）
    // 假设src已经跳过了4字节宽高头（由调用者负责）
    
    const byte *pixel_data = src;
    int pixel_data_size = src_size;
    
    if (pixel_data_size <= 0) return -1;
    
    int expected = dst_width * dst_height;
    int dst_idx = 0;
    int src_idx = 0;
    
    // sub_4EC66状态变量
    byte ah = 0;
    byte al = 0;
    
    for (int i = 0; i < expected; i++) {
        // sub_4EC66逻辑开始
        if (ah > 0) {
            // AH > 0: 重复之前的像素值
            // 4ec6a: dec ah
            ah--;
            // 4ec6c: retn - AL保持不变，直接返回
            // AL已经是正确的像素值
        } else {
            // AH == 0: 读取新字节
            // 4ec6d: lodsb
            if (src_idx >= pixel_data_size) break;
            
            al = pixel_data[src_idx];
            src_idx++;
            
            // 4ec6e: cmp al, 0C0h
            if (al > 0xC0) {
                // AL > 0xC0: 运行长度编码
                // 4ec75: mov ah, al; sub ah, 0C1h
                ah = al - 0xC1;
                // 4ec7a: lodsb - 再读取一个字节（像素值）
                if (src_idx < pixel_data_size) {
                    al = pixel_data[src_idx];
                    src_idx++;
                }
                // AL现在是像素值
            } else {
                // AL <= 0xC0: 直接像素值
                // 4ec72: xor ah, ah
                ah = 0;
                // AL已经是像素值
            }
        }
        // sub_4EC66逻辑结束，AL就是解码后的像素值
        
        // 注意：不在这里应用palette_window，由draw_pixels负责
        dst[dst_idx] = al;
        dst_idx++;
    }
    
    return 0;
}

/* 无头RLE解码：直接解码EC66编码的像素数据 */
int fd_decompress_rle_no_header(const byte *src, int src_size, byte *dst, int dst_width, int dst_height, int value_param) {
    // 与fd_decompress_rle相同，但不跳过4字节头
    // 用于索引1的图标数据（无宽高头）
    // value_param: 保留参数，当前不使用（palette_window在draw_pixels中应用）
    
    const byte *pixel_data = src;  // 不跳过任何字节
    int pixel_data_size = src_size;
    
    if (pixel_data_size <= 0) return -1;
    
    int expected = dst_width * dst_height;
    int dst_idx = 0;
    int src_idx = 0;
    
    // sub_4EC66状态变量
    byte ah = 0;
    byte al = 0;
    
    for (int i = 0; i < expected; i++) {
        if (ah > 0) {
            ah--;
        } else {
            if (src_idx >= pixel_data_size) break;
            
            al = pixel_data[src_idx];
            src_idx++;
            
            if (al > 0xC0) {
                ah = al - 0xC1;
                if (src_idx < pixel_data_size) {
                    al = pixel_data[src_idx];
                    src_idx++;
                }
            } else {
                ah = 0;
            }
        }
        
        // 注意：不在这里应用palette_window，由draw_pixels负责
        dst[dst_idx] = al;
        dst_idx++;
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