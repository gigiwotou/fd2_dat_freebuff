/*
 * 分析FDOTHER.DAT资源0 - 对话框tile结构
 * 目标：理解对话框如何由tile组成
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

static uint8_t* load_file(const char* filename, size_t* out_size)
{
    FILE* fp = fopen(filename, "rb");
    if (!fp) return NULL;
    fseek(fp, 0, SEEK_END);
    size_t size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    uint8_t* data = (uint8_t*)malloc(size);
    if (data) fread(data, 1, size, fp);
    fclose(fp);
    if (out_size) *out_size = size;
    return data;
}

int main(void)
{
    const char* dat_path = "game/FDOTHER.DAT";
    size_t dat_size;
    uint8_t* dat = load_file(dat_path, &dat_size);
    if (!dat) {
        printf("无法加载 %s\n", dat_path);
        return 1;
    }

    printf("=== FDOTHER.DAT 资源0分析 ===\n\n");

    /* 解析资源0 */
    uint32_t off0, off1;
    memcpy(&off0, dat + 10, 4);
    memcpy(&off1, dat + 14, 4);
    uint32_t res0_size = off1 - off0;
    
    printf("资源0偏移: 0x%06X - 0x%06X\n", off0, off1);
    printf("资源0大小: %d 字节\n\n", res0_size);

    uint8_t* res0 = dat + off0;

    /* 头部: 宽2B 高2B */
    int16_t w, h;
    memcpy(&w, res0, 2);
    memcpy(&h, res0 + 2, 2);
    printf("Tile尺寸: %dx%d 像素\n\n", w, h);

    /* 偏移表从byte 6开始，DWORD */
    printf("偏移表 (DWORD, 从byte 6开始):\n");
    printf("  每个条目占用4字节\n\n");

    int max_tiles = 20;  /* 根据IDA，最多19个tile */
    for (int i = 0; i < max_tiles; i++) {
        int pos = 6 + i * 4;
        if (pos + 4 > res0_size) {
            printf("  Tile %d: 超出范围\n", i);
            break;
        }
        
        uint32_t off;
        memcpy(&off, res0 + pos, 4);
        
        printf("  Tile ID %2d: 偏移=0x%04X (相对资源0), 绝对=0x%06X\n", 
               i + 1, off, off0 + off);
        
        /* 检查tile数据 */
        if (off + 4 <= res0_size) {
            uint8_t* tile_data = res0 + off;
            int16_t tw, th;
            memcpy(&tw, tile_data, 2);
            memcpy(&th, tile_data + 2, 2);
            
            /* 计算下一个tile的偏移 */
            uint32_t next_off = res0_size;
            if (i + 1 < max_tiles) {
                int next_pos = 6 + (i + 1) * 4;
                if (next_pos + 4 <= res0_size) {
                    memcpy(&next_off, res0 + next_pos, 4);
                }
            }
            
            uint32_t tile_data_size = next_off - (off + 4);
            
            printf("           尺寸=%dx%d, 压缩数据=%d字节", tw, th, tile_data_size);
            
            /* 检查是否是RLE数据 */
            if (tile_data_size > 0 && tile_data[0] < 0x80) {
                printf(" (RLE格式)");
            }
            printf("\n");
        }
    }

    /* 根据IDA分析，sub_165AC使用的tile序列 */
    printf("\n=== IDA分析的对话框动画序列 ===\n");
    printf("sub_165AC中的调用顺序:\n");
    printf("  sub_168B6(..., tile_id=4,  rows=2);  // 第1帧：2行\n");
    printf("  sub_168B6(..., tile_id=8,  rows=3);  // 第2帧：3行\n");
    printf("  sub_168B6(..., tile_id=12, rows=4);  // 第3帧：4行\n");
    printf("  sub_168B6(..., tile_id=16, rows=5);  // 第4帧：5行\n");
    printf("  sub_168B6(..., tile_id=19, rows=5);  // 第5帧：5行(完整)\n");
    
    printf("\n=== sub_168B6的tile布局逻辑 ===\n");
    printf("对于rows=5, cols=19的对话框:\n");
    printf("  Tile 1: 左上角\n");
    printf("  Tile 2: 右上角\n");
    printf("  Tile 3: 左下角\n");
    printf("  Tile 4: 右下角\n");
    printf("  Tile 5: 上边中间\n");
    printf("  Tile 6: 下边中间\n");
    printf("  Tile 7: 左边中间\n");
    printf("  Tile 8: 右边中间\n");
    printf("  Tile 9: 上边扩展部分\n");
    printf("  Tile 10: 左边扩展\n");
    printf("  Tile 11: 右边扩展\n");
    printf("  Tile 12: 下边扩展部分\n");
    printf("  Tile 13: 中间填充\n");
    printf("  Tile 14-19: 其他位置\n");

    free(dat);
    return 0;
}
