/**
 * FD2 UI渲染调试程序 - 检测渲染问题
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

/**
 * 简单的tile数据结构
 */
typedef struct {
    u8* tile_data;
    u32 tile_data_size;
    u32* tile_offsets;
    u16* tile_widths;
    u16* tile_heights;
    u16 tile_count;
} debug_tile_set_t;

/**
 * 加载FDOTHER索引4的tile数据
 */
debug_tile_set_t* load_debug_tile_set(const char* data_dir) {
    char path[512];
    snprintf(path, sizeof(path), "%s/FDOTHER.DAT", data_dir);
    
    FILE* f = fopen(path, "rb");
    if (!f) {
        fprintf(stderr, "无法打开 %s\n", path);
        return NULL;
    }
    
    // 检查魔术字节
    char magic[6];
    if (fread(magic, 1, 6, f) != 6 || memcmp(magic, "LLLLLL", 6) != 0) {
        fclose(f);
        fprintf(stderr, "错误的魔术字节\n");
        return NULL;
    }
    
    // 读取资源计数
    u32 resource_count;
    if (fread(&resource_count, 4, 1, f) != 1) {
        fclose(f);
        fprintf(stderr, "无法读取资源计数\n");
        return NULL;
    }
    
    if (resource_count <= 4) {
        fclose(f);
        fprintf(stderr, "资源计数不足\n");
        return NULL;
    }
    
    // 读取偏移表
    u32* offsets = malloc(resource_count * 4);
    if (!offsets) {
        fclose(f);
        return NULL;
    }
    fseek(f, 10, SEEK_SET);
    if (fread(offsets, 4, resource_count, f) != resource_count) {
        free(offsets);
        fclose(f);
        fprintf(stderr, "无法读取偏移表\n");
        return NULL;
    }
    
    // 加载索引4的数据
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
        return NULL;
    }
    
    fseek(f, start, SEEK_SET);
    if (fread(data, 1, size, f) != size) {
        free(data);
        free(offsets);
        fclose(f);
        fprintf(stderr, "无法读取tile数据\n");
        return NULL;
    }
    
    free(offsets);
    fclose(f);
    
    printf("成功加载FDOTHER索引4: size=%u\n", size);
    
    // 验证tile集格式
    if (memcmp(data, "LMI1", 4) != 0) {
        fprintf(stderr, "错误的tile集魔术字节\n");
        free(data);
        return NULL;
    }
    
    debug_tile_set_t* ts = malloc(sizeof(debug_tile_set_t));
    if (!ts) {
        free(data);
        return NULL;
    }
    
    ts->tile_data = data;
    ts->tile_data_size = size;
    ts->tile_count = data[4] | (data[5] << 8);
    
    printf("Tile集数量: %d\n", ts->tile_count);
    
    // 分配偏移和尺寸数组
    ts->tile_offsets = malloc(ts->tile_count * sizeof(u32));
    ts->tile_widths = malloc(ts->tile_count * sizeof(u16));
    ts->tile_heights = malloc(ts->tile_count * sizeof(u16));
    
    if (!ts->tile_offsets || !ts->tile_widths || !ts->tile_heights) {
        free(ts->tile_data);
        free(ts->tile_offsets);
        free(ts->tile_widths);
        free(ts->tile_heights);
        free(ts);
        return NULL;
    }
    
    // 解析偏移表和尺寸
    for (int i = 0; i < ts->tile_count; i++) {
        u32 offset_addr = 6 + i * 4;
        if (offset_addr + 4 > size) break;
        
        u32 tile_offset = data[offset_addr] | 
                          (data[offset_addr + 1] << 8) |
                          (data[offset_addr + 2] << 16) |
                          (data[offset_addr + 3] << 24);
        
        ts->tile_offsets[i] = tile_offset;
        
        u32 tile_addr = tile_offset;
        if (tile_addr + 4 <= size) {
            u16 w = data[tile_addr] | (data[tile_addr + 1] << 8);
            u16 h = data[tile_addr + 2] | (data[tile_addr + 3] << 8);
            ts->tile_widths[i] = w;
            ts->tile_heights[i] = h;
            
            if (i < 10) {  // 仅打印前10个
                printf("  Tile %d: offset=0x%X, %dx%d\n", i, tile_offset, w, h);
            }
        }
    }
    
    return ts;
}

/**
 * 检查特定tile的RLE数据
 */
void debug_tile_rle_data(debug_tile_set_t* ts, int tile_index) {
    if (tile_index < 0 || tile_index >= ts->tile_count) {
        printf("无效的tile索引: %d\n", tile_index);
        return;
    }
    
    u32 tile_offset = ts->tile_offsets[tile_index];
    if (tile_offset + 4 > ts->tile_data_size) {
        printf("tile %d 数据偏移超出范围\n", tile_index);
        return;
    }
    
    u8* tile_data = ts->tile_data + tile_offset;
    u16 w = tile_data[0] | (tile_data[1] << 8);
    u16 h = tile_data[2] | (tile_data[3] << 8);
    
    printf("Tile %d 数据:\n", tile_index);
    printf("  尺寸: %dx%d\n", w, h);
    printf("  头部字节: %02X %02X %02X %02X\n", 
           tile_data[0], tile_data[1], tile_data[2], tile_data[3]);
    
    // 检查前几个RLE字节
    printf("  前20个RLE字节: ");
    for (int i = 4; i < 24 && i < ts->tile_data_size - tile_offset; i++) {
        printf("%02X ", tile_data[i]);
    }
    printf("\n");
    
    // 检查是否有非零像素
    int non_zero_count = 0;
    for (int i = 4; i < ts->tile_data_size - tile_offset && i < 1000; i++) {
        if (tile_data[i] != 0) non_zero_count++;
    }
    printf("  前1000字节中非零字节数: %d\n", non_zero_count);
}

int main(int argc, char** argv) {
    const char* data_dir = "./";
    if (argc > 1) {
        data_dir = argv[1];
    }
    
    printf("FD2 UI渲染调试程序\n");
    printf("==================\n");
    printf("数据目录: %s\n\n", data_dir);
    
    debug_tile_set_t* ts = load_debug_tile_set(data_dir);
    if (!ts) {
        fprintf(stderr, "加载tile数据失败\n");
        return 1;
    }
    
    printf("\n调试关键tile数据:\n");
    
    // 检查角部和边框tile
    printf("\n角部tile:\n");
    debug_tile_rle_data(ts, 1);  // 左上角
    debug_tile_rle_data(ts, 2);  // 右上角
    debug_tile_rle_data(ts, 3);  // 左下角
    debug_tile_rle_data(ts, 4);  // 右下角
    
    printf("\n边框tile:\n");
    debug_tile_rle_data(ts, 5);  // 上边框
    debug_tile_rle_data(ts, 8);  // 下边框
    debug_tile_rle_data(ts, 10); // 左边框
    debug_tile_rle_data(ts, 11); // 右边框
    
    printf("\n内容区域tile:\n");
    debug_tile_rle_data(ts, 13); // 内容区域
    
    // 释放资源
    free(ts->tile_data);
    free(ts->tile_offsets);
    free(ts->tile_widths);
    free(ts->tile_heights);
    free(ts);
    
    printf("\n调试完成。\n");
    return 0;
}