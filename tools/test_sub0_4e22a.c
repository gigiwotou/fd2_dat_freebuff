/* 测试 sub_4E22A 解码 索引2 sub 0, 按 24x24 解码 */
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

    /* 测试 sub 0, 1, 11, 38, 48, 50, 77 */
    int test_subs[] = {0, 1, 11, 38, 48, 50, 77};
    int num_test = sizeof(test_subs) / sizeof(test_subs[0]);

    for (int t = 0; t < num_test; t++) {
        int idx = test_subs[t];
        dword sub_size;
        const byte* sub_data = fdother_offset_table_get_resource(&table, idx, &sub_size);
        if (!sub_data || sub_size < 5) {
            printf("Sub %d: no data\n", idx);
            continue;
        }

        word w = sub_data[0] | (sub_data[1] << 8);
        word h = sub_data[2] | (sub_data[3] << 8);
        byte win = sub_data[4];
        const byte* rle = sub_data + 5;
        dword rle_size = sub_size - 5;
        printf("\n=== Sub %d: w=%d h=%d win=%d rle_size=%u (first 8 RLE bytes: %02x %02x %02x %02x %02x %02x %02x %02x) ===\n",
               idx, w, h, win, rle_size,
               rle[0], rle[1], rle[2], rle[3], rle[4], rle[5], rle[6], rle[7]);

        /* sub_4E22A 要求 width>=24 且 height>=24 */
        int dec_w = 24, dec_h = 24;
        if (w < 24) dec_w = 24;
        if (h < 24) dec_h = 24;
        byte* buf = (byte*)calloc(1, dec_w * dec_h + 1024);
        memset(buf, 0xCC, dec_w * dec_h + 1024);  /* 哨兵 */
        printf("  buf=%p rle_size=%u, calling sub_4E22A(%d, %d, %d)...\n", buf, rle_size, dec_w, dec_h, dec_w);
        fflush(stdout);
        int r = fd_decompress_sub_4E22A(rle, rle_size, buf, dec_w, dec_h, dec_w);
        printf("  sub_4E22A(%dx%d) result: %d\n", dec_w, dec_h, r);
        fflush(stdout);
        /* 打印 */
        for (int y = 0; y < dec_h; y++) {
            for (int x = 0; x < dec_w; x++) {
                byte v = buf[y * dec_w + x];
                if (v == 0) printf(" .");
                else printf("%02x", v);
            }
            printf("\n");
        }
        free(buf);
    }

    fdother_offset_table_free(&table);
    fdother_unload();
    return 0;
}
