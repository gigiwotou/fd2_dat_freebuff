/* dump_index2_sub0_rle.c - 详细输出索引2子资源0的RLE原始数据和控制字节分布 */
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

    /* 输出前 10 个子资源的元信息 */
    printf("=== Index 2 前 10 个子资源 ===\n");
    for (int sub = 0; sub < 10 && sub < (int)table.offset_count; sub++) {
        dword sub_size;
        const byte* sub_data = fdother_offset_table_get_resource(&table, sub, &sub_size);
        if (!sub_data || sub_size < 5) {
            printf("Sub %d: 失败\n", sub);
            continue;
        }
        word w = sub_data[0] | (sub_data[1] << 8);
        word h = sub_data[2] | (sub_data[3] << 8);
        byte win = sub_data[4];
        printf("Sub %d: offset=%u, w=%d, h=%d, win=%d, rle_size=%u\n",
               sub, table.offsets[sub], w, h, win, sub_size - 5);
    }

    /* 详细分析 sub 0 */
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
    printf("\n=== Sub 0 详细分析 ===\n");
    printf("w=%d h=%d win=%d rle_size=%u\n", w, h, win, rle_size);

    /* 输出 RLE 原始 hex dump (前 256 字节) */
    printf("\nRLE Hex Dump (前 256 字节):\n");
    for (dword i = 0; i < rle_size && i < 256; i++) {
        if (i % 16 == 0) printf("  %04x: ", i);
        printf("%02x ", rle[i]);
        if (i % 16 == 15) printf("\n");
    }
    if (rle_size > 256) printf("... (剩余 %u 字节)\n", rle_size - 256);

    /* 分析控制字节分布 */
    printf("\n控制字节统计:\n");
    int cnt_fill = 0, cnt_alt = 0, cnt_copy = 0, cnt_skip = 0;
    for (dword i = 0; i < rle_size; i++) {
        byte b = rle[i];
        byte top2 = b & 0xC0;
        if (top2 == 0x00) cnt_fill++;
        else if (top2 == 0x40) cnt_alt++;
        else if (top2 == 0x80) cnt_copy++;
        else cnt_skip++;
    }
    printf("FILL(00): %d, ALT(40): %d, COPY(80): %d, SKIP(C0): %d\n",
           cnt_fill, cnt_alt, cnt_copy, cnt_skip);
    printf("控制字节总数: %d\n", cnt_fill + cnt_alt + cnt_copy + cnt_skip);

    /* 输出所有控制字节的 hex + 类型 */
    printf("\n所有控制字节 (src_idx -> byte -> mode(count)):\n");
    int line = 0;
    for (dword i = 0; i < rle_size; i++) {
        byte b = rle[i];
        byte top2 = b & 0xC0;
        int count = (((4 * b) & 0xFF) >> 2) + 1;
        const char* mode = "?";
        if (top2 == 0x00) mode = "FILL";
        else if (top2 == 0x40) mode = "ALT ";
        else if (top2 == 0x80) mode = "COPY";
        else mode = "SKIP";
        if (i < 200) {  /* 只输出前 200 条 */
            printf("[%3u] 0x%02x %s cnt=%d\n", i, b, mode, count);
        }
    }

    fdother_offset_table_free(&table);
    fdother_unload();
    return 0;
}
