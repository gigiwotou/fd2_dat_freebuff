/* 测试 sub_4E98D_no_header 解码 */
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

    /* 获取索引2的 sub 0 */
    fdother_offset_table_t table = {0};
    if (fdother_parse_offset_table(2, &table) != 0) {
        printf("Parse error\n");
        return 1;
    }

    dword sub_size;
    const byte* sub_data = fdother_offset_table_get_resource(&table, 0, &sub_size);
    if (!sub_data || sub_size < 5) {
        printf("No data\n");
        return 1;
    }

    printf("Sub 0: size=%u, header=[%02x %02x %02x %02x %02x]\n",
           sub_size, sub_data[0], sub_data[1], sub_data[2], sub_data[3], sub_data[4]);

    word w = sub_data[0] | (sub_data[1] << 8);
    word h = sub_data[2] | (sub_data[3] << 8);
    byte win = sub_data[4];
    const byte* rle = sub_data + 5;
    dword rle_size = sub_size - 5;
    printf("  w=%d h=%d win=%d rle_size=%u\n", w, h, win, rle_size);

    /* 打印RLE数据前 100 字节 */
    printf("RLE 前 100 字节: ");
    for (int i = 0; i < 100 && i < (int)rle_size; i++) {
        printf("%02x ", rle[i]);
        if ((i + 1) % 24 == 0) printf("\n                ");
    }
    printf("\n");

    /* 用 fd_decompress_rle 解码 (等同于 sub_4E98D_no_header) */
    byte* buf = (byte*)calloc(1, w * h);
    int r = fd_decompress_rle(rle, rle_size, buf, w, h, -1);
    printf("解码结果: %d\n", r);

    /* 打印解码后的图像 */
    printf("\n解码后图像 (%dx%d):\n", w, h);
    for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
            byte v = buf[y * w + x];
            if (v == 0) printf(" .");
            else printf("%02x", v);
        }
        printf("\n");
    }

    free(buf);
    fdother_offset_table_free(&table);
    fdother_unload();
    return 0;
}
