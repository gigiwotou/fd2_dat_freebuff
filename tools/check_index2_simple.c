/* 最简: 模拟 viewer 完整流程, 但不调用 sub_4E98D */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../include/fd2_types.h"
#include "../include/fd2_fdother_resources.h"

#include "../include/fd2_rle.h"

int main(int argc, char** argv) {
    if (fdother_load("D:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT") != 0) {
        printf("Cannot load\n");
        return 1;
    }
    printf("Loaded OK\n");

    fdother_offset_table_t table = {0};
    int ret = fdother_parse_offset_table(2, &table);
    printf("parse_offset_table: ret=%d, count=%u, size=%u\n",
           ret, table.offset_count, table.size);
    if (ret != 0) return 1;

    /* 简单获取子资源 */
    dword sub_size;
    const byte* sub_data = fdother_offset_table_get_resource(&table, 0, &sub_size);
    printf("sub 0: data=%p, size=%u\n", sub_data, sub_size);
    if (sub_data && sub_size >= 5) {
        printf("  header bytes: %02x %02x %02x %02x %02x\n",
               sub_data[0], sub_data[1], sub_data[2], sub_data[3], sub_data[4]);

        /* 调 sub_4E98D_no_header */
        printf("  before sub_4E98D call\n");
        int w = 24, h = 20;
        byte* buf = (byte*)calloc(1, w * h);
        int r = fd2_rle_sub_4E98D_no_header(sub_data + 5, sub_size - 5, buf, w, h, -1);
        printf("  sub_4E98D result: %d\n", r);
        free(buf);
    }

    /* 不调 sub_4E98D */
    printf("  before free\n");
    fdother_offset_table_free(&table);
    printf("  after free\n");
    return 0;
}
