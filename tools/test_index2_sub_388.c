/* test_index2_sub_388.c - 验证 388 字节子资源 (24x16) 格式 */
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

    /* 找到 388 字节的子资源 (24x16) */
    printf("查找 388 字节 (24x16) 子资源:\n");
    for (int sub = 0; sub < (int)table.offset_count - 1; sub++) {
        dword sub_size;
        const byte* sub_data = fdother_offset_table_get_resource(&table, sub, &sub_size);
        if (!sub_data || sub_size < 4) continue;
        word w = sub_data[0] | (sub_data[1] << 8);
        word h = sub_data[2] | (sub_data[3] << 8);
        if (sub_size == 388 && w == 24 && h == 16) {
            printf("\n=== Sub %d: w=%d h=%d size=%u ===\n", sub, w, h, sub_size);
            /* 4 字节头 + 24*16=384 像素 */
            for (int y = 0; y < 16; y++) {
                printf("row %2d: ", y);
                for (int x = 0; x < 24; x++) {
                    byte v = sub_data[4 + y * 24 + x];
                    printf("%02x ", v);
                }
                printf("\n");
            }
            /* 验证 4 + 24*16 = 388 */
            printf("header+raw: 4 + %d = %d (size=%d)\n", w*h, 4 + w*h, sub_size);
        }
    }

    /* 同时验证 484 字节子资源 */
    printf("\n\n验证 484 字节子资源 (24x20):\n");
    int count = 0;
    for (int sub = 0; sub < (int)table.offset_count - 1; sub++) {
        dword sub_size;
        const byte* sub_data = fdother_offset_table_get_resource(&table, sub, &sub_size);
        if (!sub_data || sub_size < 4) continue;
        word w = sub_data[0] | (sub_data[1] << 8);
        word h = sub_data[2] | (sub_data[3] << 8);
        if (sub_size == 484 && w == 24 && h == 20) {
            count++;
            if (count <= 3) {
                printf("\nSub %d: 4 + %d = %d (size=%d, match=%s)\n",
                       sub, w*h, 4 + w*h, sub_size, (4 + w*h == sub_size) ? "YES" : "NO");
            }
        }
    }
    printf("Total 484-byte (24x20) sub: %d\n", count);

    fdother_offset_table_free(&table);
    fdother_unload();
    return 0;
}
