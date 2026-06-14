/* 测试索引2子资源0: 分别用 sub_4E22A 和 sub_4E98D_no_header 解码并对比 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../include/fd2_types.h"
#include "../include/fd2_rle.h"
#include "../include/fd2_fdother_resources.h"
#include "../include/fd2_dat.h"

static void print_image(const char* label, const byte* buf, int w, int h) {
    printf("\n%s (%dx%d):\n", label, w, h);
    for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
            byte v = buf[y * w + x];
            if (v == 0) printf("  .");
            else if (v < 16) printf(" 0%x", v);
            else printf(" %x", v);
        }
        printf("\n");
    }
}

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

    /* 测试 sub 0 */
    int sub_index = (argc > 1) ? atoi(argv[1]) : 0;
    dword sub_size;
    const byte* sub_data = fdother_offset_table_get_resource(&table, sub_index, &sub_size);
    if (!sub_data || sub_size < 5) {
        printf("No data\n");
        return 1;
    }

    printf("=== Sub %d ===\n", sub_index);
    printf("Sub %d: size=%u, header=[%02x %02x %02x %02x %02x]\n",
           sub_index, sub_size, sub_data[0], sub_data[1], sub_data[2], sub_data[3], sub_data[4]);

    word w = sub_data[0] | (sub_data[1] << 8);
    word h = sub_data[2] | (sub_data[3] << 8);
    byte win = sub_data[4];
    const byte* rle = sub_data + 5;
    dword rle_size = sub_size - 5;
    printf("  头: w=%d h=%d win=%d rle_size=%u\n", w, h, win, rle_size);

    /* 打印RLE数据前 80 字节 */
    printf("RLE 前 80 字节: ");
    for (int i = 0; i < 80 && i < (int)rle_size; i++) {
        printf("%02x ", rle[i]);
        if ((i + 1) % 24 == 0) printf("\n                ");
    }
    printf("\n");

    /* 方法1: 用 fd_decompress_sub_4E22A (硬编码24x24) */
    byte sub_buf[24 * 24];
    memset(sub_buf, 0, sizeof(sub_buf));
    int r1 = fd_decompress_sub_4E22A(rle, rle_size, sub_buf, 24, 24, 24);
    printf("sub_4E22A (24x24) 解码结果: %d\n", r1);
    print_image("sub_4E22A (24x24)", sub_buf, 24, 24);

    /* 方法2: 用 fd_decompress_rle (sub_4E98D_no_header), 用 w x h 解码 */
    byte* buf98 = (byte*)calloc(1, w * h);
    int r2 = fd_decompress_rle(rle, rle_size, buf98, w, h, -1);
    printf("\nsub_4E98D_no_header (%dx%d) 解码结果: %d\n", w, h, r2);
    print_image("sub_4E98D_no_header (w x h)", buf98, w, h);
    free(buf98);
    fdother_offset_table_free(&table);
    fdother_unload();
    return 0;
}
