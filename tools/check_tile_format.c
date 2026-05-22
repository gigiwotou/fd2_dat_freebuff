#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;

int main(int argc, char** argv) {
    if (argc < 2) {
        printf("Usage: %s <fdother.dat>\n", argv[0]);
        return 1;
    }

    FILE* fp = fopen(argv[1], "rb");
    if (!fp) {
        perror("fopen");
        return 1;
    }

    // 查找索引7的位置
    fseek(fp, 0, SEEK_END);
    u32 file_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    // 读取索引表
    u32 index_count;
    fread(&index_count, sizeof(u32), 1, fp);
    printf("索引总数: %u\n", index_count);

    // 索引7的偏移
    fseek(fp, 8 + 7 * 8, SEEK_SET);
    u32 offset_7;
    u32 size_7;
    fread(&offset_7, sizeof(u32), 1, fp);
    fread(&size_7, sizeof(u32), 1, fp);
    
    printf("索引7: 偏移=0x%08X, 大小=%u\n", offset_7, size_7);

    // 读取索引7数据
    u8* data = (u8*)malloc(size_7);
    fseek(fp, offset_7, SEEK_SET);
    fread(data, 1, size_7, fp);
    fclose(fp);

    // 解析头部
    u16 total_width = data[0] | (data[1] << 8);
    u16 total_height = data[2] | (data[3] << 8);
    u16 tile_count = data[4] | (data[5] << 8);
    
    printf("总宽度: %d, 总高度: %d, tile数量: %d\n", total_width, total_height, tile_count);

    // 输出tile 1-17的信息
    for (int i = 0; i < 18 && i < tile_count; i++) {
        u32 offset_addr = 6 + i * 4;
        if (offset_addr + 4 > size_7) break;

        u32 tile_offset = data[offset_addr] | 
                         (data[offset_addr + 1] << 8) |
                         (data[offset_addr + 2] << 16) |
                         (data[offset_addr + 3] << 24);
        
        if (tile_offset >= size_7) continue;

        u16 tw = data[tile_offset] | (data[tile_offset + 1] << 8);
        u16 th = data[tile_offset + 2] | (data[tile_offset + 3] << 8);
        
        printf("Tile %d: 偏移=0x%04X, 宽度=%d, 高度=%d, 数据大小=%d字节\n", 
               i, tile_offset, tw, th, tw * th);

        // 输出前16字节数据
        if (tw * th > 0) {
            printf("  前16字节: ");
            for (int j = 0; j < 16 && j < tw * th; j++) {
                printf("%02X ", data[tile_offset + 4 + j]);
            }
            printf("\n");
        }
    }

    free(data);
    return 0;
}
