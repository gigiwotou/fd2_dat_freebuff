/* test_index2_sub0_raw_v2.c - 简化版,只显示 raw 像素 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../include/fd2_types.h"
#include "../include/fd2_rle.h"
#include "../include/fd2_fdother_resources.h"
#include "../include/fd2_dat.h"

int main(int argc, char** argv) {
    if (fdother_load("d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT") != 0) {
        printf("Cannot load\n");
        return 1;
    }

    fdother_offset_table_t table = {0};
    if (fdother_parse_offset_table(2, &table) != 0) {
        printf("Parse error\n");
        return 1;
    }

    dword sub_size;
    const byte* sub_data = fdother_offset_table_get_resource(&table, 0, &sub_size);
    if (!sub_data) {
        printf("No data\n");
        return 1;
    }

    printf("Sub 0: size=%u\n", sub_size);
    printf("Header: [%02x %02x %02x %02x %02x %02x %02x %02x]\n",
           sub_data[0], sub_data[1], sub_data[2], sub_data[3],
           sub_data[4], sub_data[5], sub_data[6], sub_data[7]);
    word w = sub_data[0] | (sub_data[1] << 8);
    word h = sub_data[2] | (sub_data[3] << 8);
    printf("w=%d h=%d, total_pixels=%d\n", w, h, w * h);

    /* A) 4字节头 + 480字节raw pixels */
    printf("\n=== A) 4字节头 + 480字节 raw 24x20 ===\n");
    for (int y = 0; y < 20; y++) {
        printf("row %2d: ", y);
        for (int x = 0; x < 24; x++) {
            byte v = sub_data[4 + y * 24 + x];
            printf("%02x ", v);
        }
        printf("\n");
    }

    fdother_offset_table_free(&table);
    fdother_unload();
    return 0;
}
