/* 详细分析 - 定位崩溃点 */
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
    if (fdother_parse_offset_table(2, &table) != 0) {
        printf("parse_offset_table failed\n");
        return 1;
    }

    int max_w = 24, max_h = 20;
    int max_buf_size = 24 * 20;  /* 始终分配最大尺寸的缓冲区 */
    byte* buf = (byte*)calloc(1, max_buf_size);
    if (!buf) { printf("calloc failed\n"); return 1; }

    for (dword i = 0; i < table.offset_count; i++) {
        dword sub_size;
        const byte* sub_data = fdother_offset_table_get_resource(&table, i, &sub_size);
        if (!sub_data || sub_size < 5) continue;
        word w = sub_data[0] | (sub_data[1] << 8);
        word h = sub_data[2] | (sub_data[3] << 8);
        byte win = sub_data[4];
        dword rle_size = sub_size - 5;

        /* 跳过非法尺寸 */
        if (w == 0 || h == 0 || w > 100 || h > 100) {
            printf("  [Skipping %u: invalid size %ux%u]\n", i, w, h);
            continue;
        }

        memset(buf, 0, max_buf_size);
        fflush(stdout);
        printf("Sub %u: w=%u h=%u win=%u rle_size=%u ... ", i, w, h, win, rle_size);
        fflush(stdout);
        int r = fd2_rle_sub_4E98D_no_header(sub_data + 5, rle_size, buf, w, h, -1);
        int nonzero = 0;
        for (int j = 0; j < w * h; j++) if (buf[j] != 0) nonzero++;
        printf("r=%d nonzero=%d\n", r, nonzero);
        fflush(stdout);
    }

    free(buf);
    fdother_offset_table_free(&table);
    fdother_unload();
    return 0;
}
