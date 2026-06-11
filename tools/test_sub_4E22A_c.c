/*
 * 测试fd_decompress_sub_4E22A的输出
 * 对比Python版本的解码结果
 */

#include "../include/fd2_dat.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    const char* filepath = "game/FDOTHER.DAT";
    FILE* fp = fopen(filepath, "rb");
    if (!fp) {
        printf("Cannot open %s\n", filepath);
        return 1;
    }
    
    fseek(fp, 0, SEEK_END);
    long file_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    
    byte* data = (byte*)malloc(file_size);
    fread(data, 1, file_size, fp);
    fclose(fp);
    
    printf("File size: %ld bytes\n\n", file_size);
    
    // 解析FDOTHER头部
    printf("Header: %.6s\n", data);
    
    // 解析资源偏移表
    dword* offsets = (dword*)malloc(file_size);
    int res_count = 0;
    dword pos = 6;
    while (pos + 4 <= (dword)file_size) {
        dword off = *(dword*)(data + pos);
        if (off == 0 || off > (dword)file_size) break;
        offsets[res_count++] = off;
        pos += 4;
    }
    offsets[res_count] = (dword)file_size;
    
    printf("Resource count: %d\n\n", res_count);
    
    // 索引1
    dword idx1_start = offsets[1];
    dword idx1_end = offsets[2];
    dword idx1_size = idx1_end - idx1_start;
    byte* idx1_data = data + idx1_start;
    
    printf("Index 1: offset=0x%X, size=%d\n", idx1_start, idx1_size);
    printf("First 6 bytes: %02X %02X %02X %02X %02X %02X\n",
           idx1_data[0], idx1_data[1], idx1_data[2], 
           idx1_data[3], idx1_data[4], idx1_data[5]);
    
    // 头部解析
    word w = idx1_data[0] | (idx1_data[1] << 8);
    word h = idx1_data[2] | (idx1_data[3] << 8);
    byte pw = idx1_data[4];
    printf("Header: width=%d, height=%d, palette_window=%d\n\n", w, h, pw);
    
    // 解析偏移表
    dword icon_offsets[60];
    int icon_count = 0;
    pos = 6;
    while (pos + 4 <= idx1_size) {
        dword off = *(dword*)(idx1_data + pos);
        if (off == 0 || off > idx1_size) break;
        icon_offsets[icon_count++] = off;
        pos += 4;
    }
    
    printf("Icon count: %d\n", icon_count);
    printf("First 5 offsets: ");
    for (int i = 0; i < 5 && i < icon_count; i++) {
        printf("0x%X ", icon_offsets[i]);
    }
    printf("\n\n");
    
    // 解码第一个图标
    dword icon0_start = icon_offsets[0];
    dword icon0_end = icon_offsets[1];
    dword icon0_size = icon0_end - icon0_start;
    byte* icon0_data = idx1_data + icon0_start;
    
    printf("Icon 0: offset=0x%X, size=%d\n", icon0_start, icon0_size);
    printf("First 20 bytes: ");
    for (int i = 0; i < 20 && i < (int)icon0_size; i++) {
        printf("%02X ", icon0_data[i]);
    }
    printf("\n\n");
    
    // 调用fd_decompress_sub_4E22A
    byte* decoded = (byte*)malloc(24 * 24);
    memset(decoded, 0, 24 * 24);
    
    int ret = fd_decompress_sub_4E22A(icon0_data, icon0_size, decoded, 24, 24, 24);
    printf("fd_decompress_sub_4E22A returned: %d\n\n", ret);
    
    // 输出解码结果
    printf("Decoded 24x24 pixels (raw):\n");
    for (int row = 0; row < 24; row++) {
        printf("  Row %2d: ", row);
        for (int col = 0; col < 24; col++) {
            printf("%02X ", decoded[row * 24 + col]);
        }
        printf("\n");
    }
    
    printf("\nDecoded with palette_window=%d applied:\n", pw);
    for (int row = 0; row < 24; row++) {
        printf("  Row %2d: ", row);
        for (int col = 0; col < 24; col++) {
            byte idx = (decoded[row * 24 + col] + pw) & 0xFF;
            printf("%02X ", idx);
        }
        printf("\n");
    }
    
    free(decoded);
    free(offsets);
    free(data);
    
    return 0;
}
