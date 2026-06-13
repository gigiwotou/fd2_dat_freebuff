/* 模拟 viewer 完整流程, 输出实际像素颜色 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../include/fd2_types.h"
#include "../include/fd2_rle.h"
#include "../include/fd2_fdother_resources.h"

int main(int argc, char** argv) {
    if (fdother_load("D:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT") != 0) {
        printf("Cannot load\n");
        return 1;
    }

    fdother_offset_table_t table = {0};
    fdother_parse_offset_table(2, &table);
    printf("offset_count=%u, max_sub_items=%d\n", table.offset_count, (int)table.offset_count-1);

    fdother_palette_t pal;
    fdother_get_palette(0, &pal);
    byte rgb24[768];
    fdother_palette_to_rgb24(&pal, rgb24);

    /* 测试 4 个不同子资源 */
    int sub_indices[] = {0, 1};
    for (int s = 0; s < (int)(sizeof(sub_indices)/sizeof(sub_indices[0])); s++) {
        int idx = sub_indices[s];
        dword sub_size;
        const byte* sub_data = fdother_offset_table_get_resource(&table, idx, &sub_size);

        printf("\n=== Sub %d (sub_size=%u, sub_data=%p) ===\n", idx, sub_size, sub_data);
        if (!sub_data) { printf("No data\n"); continue; }

        /* 模拟 viewer: fdother_parse_tile 假设 5 字节头 */
        word w = sub_data[0] | (sub_data[1] << 8);
        word h = sub_data[2] | (sub_data[3] << 8);
        byte win = sub_data[4];
        printf("  header[0:5]: w=%d h=%d win=%d\n", w, h, win);
        printf("  rle_data=%u bytes\n", sub_size - 5);

        /* 用 sub_4E98D_no_header 解码 (viewer 用 fd_decompress_rle) */
        byte* buf = (byte*)calloc(1, w * h);
        printf("  decode args: src=%p, src_size=%u, dst=%p, w=%d, h=%d\n",
               sub_data + 5, sub_size - 5, buf, w, h);
        int r = fd2_rle_sub_4E98D_no_header(sub_data + 5, sub_size - 5, buf, w, h, -1);
        printf("  decode: %d\n", r);

        /* 应用调色板窗口 win */
        int nonzero = 0;
        for (int y = 0; y < h && y < 5; y++) {
            printf("  y=%d: ", y);
            for (int x = 0; x < w; x++) {
                byte idx_pal = buf[y*w + x];
                if (idx_pal != 0) {
                    byte actual = (idx_pal + win) & 0xFF;
                    int r_v = rgb24[actual*3 + 0];
                    int g_v = rgb24[actual*3 + 1];
                    int b_v = rgb24[actual*3 + 2];
                    printf("(%d,%d)=%3d/%3d ", x, y, actual, idx_pal);
                    nonzero++;
                }
            }
            printf("\n");
            if (nonzero > 20) break;
        }
        printf("  nonzero: %d\n", nonzero);

        free(buf);
    }
    fdother_offset_table_free(&table);
    return 0;
}
