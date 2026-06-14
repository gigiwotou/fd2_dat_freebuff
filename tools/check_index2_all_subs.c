/* 分析索引2所有子资源的结构 */
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
    printf("offset_count=%u\n\n", table.offset_count);

    /* 打印所有子资源信息 */
    printf("子资源表格:\n");
    printf("Idx | Offset   | Size     | W   | H   | Win | RLE  | Non0 | Status\n");
    printf("----+----------+----------+-----+-----+-----+------+------+-------\n");

    int total_size = 0;
    int total_nonzero = 0;
    for (dword i = 0; i < table.offset_count - 1; i++) {
        dword sub_size;
        const byte* sub_data = fdother_offset_table_get_resource(&table, i, &sub_size);
        if (!sub_data || sub_size < 5) {
            printf("%3u | (invalid)\n", i);
            continue;
        }

        word w = sub_data[0] | (sub_data[1] << 8);
        word h = sub_data[2] | (sub_data[3] << 8);
        byte win = sub_data[4];
        dword rle_size = sub_size - 5;
        total_size += sub_size;

        byte* buf = (byte*)calloc(1, w * h);
        int r = fd2_rle_sub_4E98D_no_header(sub_data + 5, rle_size, buf, w, h, -1);
        int nonzero = 0;
        for (int j = 0; j < w * h; j++) if (buf[j] != 0) nonzero++;
        total_nonzero += nonzero;
        free(buf);

        printf("%3u | 0x%06x | %6u   | %3d | %3d | %3d | %4u | %4d | %s\n",
               i, table.offsets[i], sub_size, w, h, win, rle_size, nonzero,
               (r == 0) ? "OK" : "ERR");
    }

    printf("\n总字节: %d, 总非0像素: %d\n", total_size, total_nonzero);
    printf("索引2总大小: %u 字节\n", table.size);

    fdother_offset_table_free(&table);
    fdother_unload();
    return 0;
}
