#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "fd2_dat.h"

int main() {
    // 测试fd_decompress_rle
    FILE* f = fopen("game/FDOTHER.DAT", "rb");
    if (!f) {
        printf("无法打开FDOTHER.DAT\n");
        return 1;
    }
    
    // 读取文件
    fseek(f, 0, SEEK_END);
    long file_size = ftell(f);
    fseek(f, 0, SEEK_SET);
    
    byte* data = malloc(file_size);
    fread(data, 1, file_size, f);
    fclose(f);
    
    // 读取索引表
    dword offsets[104];
    int offset_count = 0;
    int pos = 6;
    
    while (pos + 4 <= file_size) {
        dword off = data[pos] | (data[pos+1] << 8) | (data[pos+2] << 16) | (data[pos+3] << 24);
        if (off == 0 || off >= file_size) break;
        offsets[offset_count++] = off;
        pos += 4;
        if (offset_count >= 103) break;
    }
    offsets[offset_count] = file_size;
    
    // 索引1
    printf("=== 测试索引1解码 ===\n");
    dword idx1_start = offsets[1];
    dword idx1_end = offsets[2];
    byte* idx1_data = data + idx1_start;
    dword idx1_size = idx1_end - idx1_start;
    
    printf("索引1大小: %u 字节\n", idx1_size);
    
    // 外头
    word outer_w = idx1_data[0] | (idx1_data[1] << 8);
    word outer_h = idx1_data[2] | (idx1_data[3] << 8);
    byte pal_win = idx1_data[4];
    printf("外头: %ux%u, pal_window=%u\n", outer_w, outer_h, pal_win);
    
    // 解析相对偏移表
    dword icon_offsets[20];
    int icon_count = 0;
    pos = 6;
    
    while (pos + 4 <= idx1_size && icon_count < 20) {
        dword rel_off = idx1_data[pos] | (idx1_data[pos+1] << 8) | 
                       (idx1_data[pos+2] << 16) | (idx1_data[pos+3] << 24);
        if (rel_off >= idx1_size) break;
        icon_offsets[icon_count++] = rel_off;
        pos += 4;
    }
    
    printf("图标数量: %d\n\n", icon_count);
    
    // 解码前5个图标
    for (int i = 0; i < 5 && i < icon_count; i++) {
        byte* icon_data = idx1_data + icon_offsets[i];
        dword icon_size = (i + 1 < icon_count) ? 
                         icon_offsets[i+1] - icon_offsets[i] : idx1_size - icon_offsets[i];
        
        printf("图标%d: %u 字节\n", i, icon_size);
        printf("  前16字节: ");
        for (int j = 0; j < 16 && j < icon_size; j++) {
            printf("%02X ", icon_data[j]);
        }
        printf("\n");
        
        // 解码
        byte* dst = calloc(outer_w * outer_h, 1);
        fd_decompress_rle(icon_data, icon_size, dst, outer_w, outer_h, pal_win);
        
        // 统计
        int non_zero = 0;
        int unique_vals[256] = {0};
        for (int j = 0; j < outer_w * outer_h; j++) {
            if (dst[j] != 0) non_zero++;
            unique_vals[dst[j]] = 1;
        }
        int unique = 0;
        for (int j = 0; j < 256; j++) unique += unique_vals[j];
        
        printf("  非零像素: %d/%d\n", non_zero, outer_w * outer_h);
        printf("  唯一值: %d\n\n", unique);
        
        // 输出前3行像素
        for (int row = 0; row < 3 && row < outer_h; row++) {
            printf("  行%d: ", row);
            for (int col = 0; col < outer_w && col < 24; col++) {
                printf("%02X ", dst[row * outer_w + col]);
            }
            printf("\n");
        }
        printf("\n");
        
        free(dst);
    }
    
    free(data);
    return 0;
}
