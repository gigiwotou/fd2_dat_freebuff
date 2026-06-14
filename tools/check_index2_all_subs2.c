/* 分析索引2所有子资源的结构 - 修复版 */
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
    printf("offset_count=%u, max_subs=%u\n\n", table.offset_count, table.offset_count - 1);

    int max_w = 0, max_h = 0;
    for (dword i = 0; i < table.offset_count - 1; i++) {
        dword sub_size;
        const byte* sub_data = fdother_offset_table_get_resource(&table, i, &sub_size);
        if (!sub_data || sub_size < 5) continue;
        word w = sub_data[0] | (sub_data[1] << 8);
        word h = sub_data[2] | (sub_data[3] << 8);
        if (w > max_w) max_w = w;
        if (h > max_h) max_h = h;
    }
    printf("最大尺寸: %dx%d\n\n", max_w, max_h);

    int max_buf_size = max_w * max_h;
    if (max_buf_size < 480) max_buf_size = 480;
    byte* buf = (byte*)calloc(1, max_buf_size);
    if (!buf) { printf("calloc failed\n"); return 1; }

    /* 打印所有子资源信息 */
    printf("子资源表格:\n");
    printf("Idx | Offset   | Size     | W   | H   | Win | RLE  | Non0 | Status\n");
    printf("----+----------+----------+-----+-----+-----+------+------+-------\n");

    for (dword i = 0; i < table.offset_count - 1; i++) {
        dword sub_size;
        const byte* sub_data = fdother_offset_table_get_resource(&table, i, &sub_size);
        if (!sub_data || sub_size < 5) continue;
        word w = sub_data[0] | (sub_data[1] << 8);
        word h = sub_data[2] | (sub_data[3] << 8);
        byte win = sub_data[4];
        dword rle_size = sub_size - 5;

        memset(buf, 0, max_buf_size);
        int r = fd2_rle_sub_4E98D_no_header(sub_data + 5, rle_size, buf, w, h, -1);
        int nonzero = 0;
        for (int j = 0; j < w * h; j++) if (buf[j] != 0) nonzero++;

        printf("%3u | 0x%06x | %6u   | %3d | %3d | %3d | %4u | %4d | %s\n",
               i, table.offsets[i], sub_size, w, h, win, rle_size, nonzero,
               (r == 0) ? "OK" : "ERR");
    }

    free(buf);
    fdother_offset_table_free(&table);
    fdother_unload();
    return 0;
}
