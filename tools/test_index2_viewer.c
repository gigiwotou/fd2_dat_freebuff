/* 模拟 viewer 的索引2 处理逻辑, 输出详细诊断 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../include/fd2_types.h"
#include "../include/fd2_rle.h"
#include "../include/fd2_fdother_resources.h"
#include "../include/fd2_dat.h"

int main(int argc, char** argv) {
    printf("[1] start\n");
    fflush(stdout);
    if (fdother_load("d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT") != 0) {
        printf("Cannot load\n");
        return 1;
    }
    printf("[2] loaded\n");
    fflush(stdout);

    /* 模拟 viewer 逻辑: 加载偏移表 */
    fdother_offset_table_t table = {0};
    printf("[3] before parse\n");
    fflush(stdout);
    int ret = fdother_parse_offset_table(2, &table);
    printf("[4] ret=%d\n", ret);
    fflush(stdout);
    printf("fdother_parse_offset_table ret=%d, offset_count=%u, size=%u\n",
           ret, table.offset_count, table.size);
    printf("Viewer 显示 max_sub_items = %d\n", (int)table.offset_count - 1);

    /* 加载主调色板 */
    fdother_palette_t pal;
    fdother_get_palette(0, &pal);
    byte rgb24[768];
    fdother_palette_to_rgb24(&pal, rgb24);

    /* 模拟 viewer 渲染: 对每个子资源 (0, 1, 5, 10, 20, 30, 48, 50, 77) 解析 */
    int sub_indices[] = {0, 1, 5, 10, 20, 30, 48, 49, 50, 51, 52, 77};
    for (int s = 0; s < (int)(sizeof(sub_indices)/sizeof(sub_indices[0])); s++) {
        int idx = sub_indices[s];
        dword sub_size;
        const byte* sub_data = fdother_offset_table_get_resource(&table, idx, &sub_size);
        fflush(stdout);

        printf("\n=== Sub %d (size=%u, data=%p) ===\n", idx, sub_size, (const void*)sub_data);
        fflush(stdout);
        if (!sub_data || sub_size < 5) {
            printf("  无效数据\n");
            fflush(stdout);
            continue;
        }
        printf("  头 5 字节: ");
        for (int i = 0; i < 5; i++) printf("%02x ", sub_data[i]);
        printf("\n");
        fflush(stdout);

        fdother_tile_t tile;
        if (fdother_parse_tile(sub_data, sub_size, &tile) != 0) {
            printf("  fdother_parse_tile 失败\n");
            fflush(stdout);
            continue;
        }
        printf("  tile w=%d h=%d win=%d rle_size=%u\n",
               tile.width, tile.height, tile.palette_window, tile.rle_size);
        fflush(stdout);

        /* 模拟 viewer: 用 fd_decompress_rle 解码 */
        byte* buf = (byte*)calloc(1, tile.width * tile.height);
        int r = fd_decompress_rle(tile.rle_data, tile.rle_size, buf,
                                  tile.width, tile.height, -1);
        printf("  fd_decompress_rle: %d\n", r);
        if (r == 0) {
            /* 统计非0像素 */
            int nonzero = 0;
            int first10[10] = {-1};
            for (int i = 0; i < tile.width * tile.height; i++) {
                if (buf[i] != 0) {
                    if (nonzero < 10) first10[nonzero] = i;
                    nonzero++;
                }
            }
            printf("  非0像素: %d\n", nonzero);
            for (int i = 0; i < 10 && first10[i] >= 0; i++) {
                int p = first10[i];
                printf("    pixel[%d] = %3d\n", p, buf[p]);
            }
        }
        free(buf);
    }

    fdother_offset_table_free(&table);
    return 0;
}
