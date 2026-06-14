/* 详细调试 sub0 RLE 解码 */
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
    if (!sub_data || sub_size < 5) {
        printf("No data\n");
        return 1;
    }

    word w = sub_data[0] | (sub_data[1] << 8);
    word h = sub_data[2] | (sub_data[3] << 8);
    byte win = sub_data[4];
    const byte* rle = sub_data + 5;
    dword rle_size = sub_size - 5;
    printf("Sub 0: w=%d h=%d win=%d rle_size=%u\n", w, h, win, rle_size);

    /* 详细解析前 50 字节的RLE控制 */
    printf("\n=== 前 50 字节 RLE 控制解析 ===\n");
    int idx = 0;
    while (idx < 50 && idx < (int)rle_size) {
        byte ctrl = rle[idx++];
        int count = ((ctrl * 4) & 0xFF) >> 2 + 1;
        byte top2 = ctrl & 0xC0;
        const char* mode;
        if (top2 == 0x00) mode = "FILL";
        else if (top2 == 0x40) mode = "ALT ";
        else if (top2 == 0x80) mode = "COPY";
        else mode = "SKIP";
        printf("  [%3d] ctrl=0x%02x (%s) count=%d ", idx-1, ctrl, mode, count);
        if (top2 == 0x00) {
            if (idx < (int)rle_size) printf("v=0x%02x", rle[idx]);
            idx++;
        } else if (top2 == 0x40) {
            if (idx < (int)rle_size) printf("v=0x%02x", rle[idx]);
            idx++;
        } else if (top2 == 0x80) {
            for (int i = 0; i < count && idx < (int)rle_size; i++) {
                printf("0x%02x ", rle[idx]);
                idx++;
            }
        }
        printf("\n");
    }

    /* 解码并打印 */
    byte sub_buf[24 * 24];
    memset(sub_buf, 0, sizeof(sub_buf));
    int r = fd_decompress_sub_4E22A(rle, rle_size, sub_buf, 24, 24, 24);
    printf("\nsub_4E22A 解码结果: %d\n", r);

    printf("\n=== sub_4E22A 解码 24x24 像素 ===\n");
    for (int y = 0; y < 24; y++) {
        printf("row %2d: ", y);
        for (int x = 0; x < 24; x++) {
            byte v = sub_buf[y * 24 + x];
            if (v == 0) printf(" ..");
            else printf(" %02x", v);
        }
        printf("\n");
    }

    fdother_offset_table_free(&table);
    fdother_unload();
    return 0;
}
