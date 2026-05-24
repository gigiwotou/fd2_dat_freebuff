/**
 * 详细分析FDOTHER索引4的tile数据结构
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

void analyze_tile_structure(const char* data_dir) {
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
    
    // 分析tile集结构
    printf("FDOTHER索引4 Tile集结构分析:\n");
    printf("==========================\n");
    printf("数据起始偏移: 0x%05X\n", start);
    printf("数据大小: %d 字节\n", size);
    printf("\n");
    
    // 魔术字节 (4字节)
    printf("字节 0-3: 魔术字节 = '%.4s'\n", data);
    
    // Tile数量 (2字节)
    u16 tile_count = data[4] | (data[5] << 8);
    printf("字节 4-5: Tile数量 = %d\n", tile_count);
    printf("\n");
    
    // 偏移表 (从偏移6开始，每4字节一个)
    printf("偏移表 (从偏移6开始):\n");
    for (int i = 0; i < 20 && i < tile_count; i++) {
        u32 offset_addr = 6 + i * 4;
        if (offset_addr + 4 > size) break;
        
        u32 tile_offset = data[offset_addr] | 
                          (data[offset_addr + 1] << 8) |
                          (data[offset_addr + 2] << 16) |
                          (data[offset_addr + 3] << 24);
        
        printf("  Tile %2d: 偏移表项[%d] = 0x%05X (%d)\n", i, i, tile_offset, tile_offset);
    }
    
    printf("\n");
    
    // 分析前几个tile的数据
    printf("Tile数据详情:\n");
    for (int i = 0; i < 10 && i < tile_count; i++) {
        u32 offset_addr = 6 + i * 4;
        if (offset_addr + 4 > size) break;
        
        u32 tile_offset = data[offset_addr] | 
                          (data[offset_addr + 1] << 8) |
                          (data[offset_addr + 2] << 16) |
                          (data[offset_addr + 3] << 24);
        
        if (tile_offset >= size) {
            printf("  Tile %d: 偏移超出范围\n", i);
            continue;
        }
        
        u8* tile_data = data + tile_offset;
        if (tile_offset + 4 > size) {
            printf("  Tile %d: 数据不足\n", i);
            continue;
        }
        
        u16 w = tile_data[0] | (tile_data[1] << 8);
        u16 h = tile_data[2] | (tile_data[3] << 8);
        
        printf("  Tile %2d (偏移0x%05X): 尺寸=%dx%d, 前4字节=%02X %02X %02X %02X\n", 
               i, tile_offset, w, h, 
               tile_data[0], tile_data[1], tile_data[2], tile_data[3]);
        
        // 显示前几个RLE字节
        printf("           RLE数据: ");
        for (int j = 4; j < 20 && tile_offset + j < size; j++) {
            printf("%02X ", tile_data[j]);
        }
        printf("\n");
    }
    
    free(data);
}

int main(int argc, char** argv) {
    const char* data_dir = "./";
    if (argc > 1) {
        data_dir = argv[1];
    }
    
    printf("FD2 FDOTHER索引4 Tile数据结构详细分析\n");
    printf("======================================\n");
    printf("数据目录: %s\n\n", data_dir);
    
    analyze_tile_structure(data_dir);
    
    return 0;
}