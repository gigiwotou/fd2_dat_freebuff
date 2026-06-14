/* 详细追踪 sub0 RLE 每一个指令 (扁平化版) */
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

    /* 1:1 复现 sub_4E22A 汇编逻辑 (扁平化).
     * 严格按汇编: 硬编码 n24=24, n24_1=24. 头中 h 可能是显示裁剪高度. */
    byte pixels[24 * 24];
    memset(pixels, 0, sizeof(pixels));
    int src_idx = 0;
    int dst_idx = 0;
    int n24 = 24;  /* 汇编硬编码 24 (0x4E23E mov bl, 18h) */
    int n24_1;
    int count;
    byte value, v;

    while (n24 != 0) {
        n24_1 = 24;
        while (n24_1 != 0) {
            /* 读控制字节 */
            if (src_idx >= (int)rle_size) {
                printf("[%d] src overflow at dst=%d\n", src_idx, dst_idx);
                goto done;
            }
            value = rle[src_idx++];
            int v9 = (2 * value) & 0xFF;
            int cfs_value = (value & 0x80) ? 1 : 0;  /* bit 7 */
            int cfs_v9 = (v9 & 0x80) ? 1 : 0;       /* bit 6 */

            if (cfs_value) {
                /* bit 7 = 1: COPY/SKIP */
                count = ((4 * value) & 0xFF);
                count = (count >> 2) + 1;
                if (cfs_v9) {
                    /* SKIP */
                    printf("[%3d] SKIP count=%d  dst %d -> %d, n24_1 %d -> %d\n",
                           src_idx-1, count, dst_idx, dst_idx+count, n24_1, n24_1-count);
                    dst_idx += count;
                    n24_1 -= count;
                    if (n24_1 == 0) goto label15;
                } else {
                    /* COPY */
                    printf("[%3d] COPY count=%d  dst %d -> %d:",
                           src_idx-1, count, dst_idx, dst_idx+count);
                    n24_1 -= count;
                    for (int k = 0; k < count; k++) {
                        if (src_idx >= (int)rle_size) goto done;
                        printf(" %02x", rle[src_idx]);
                        pixels[dst_idx] = rle[src_idx];
                        src_idx++;
                        dst_idx++;
                    }
                    printf("\n");
                    if (n24_1 == 0) goto label15;
                }
            } else {
                /* bit 7 = 0: FILL/ALT */
                count = ((4 * value) & 0xFF);
                count = (count >> 2) + 1;
                if (cfs_v9) {
                    /* ALT */
                    n24_1 = n24_1 - count - count;
                    if (src_idx >= (int)rle_size) goto done;
                    v = rle[src_idx++];
                    printf("[%3d] ALT count=%d v=0x%02x  dst=%d, n24_1=%d\n",
                           src_idx-2, count, v, dst_idx, n24_1);
                    for (int k = 0; k < count; k++) {
                        pixels[dst_idx + 1] = v;
                        dst_idx += 2;
                    }
                    /* ALT 后无 n24_1 检查, 继续外层 while */
                    if (n24_1 == 0) goto label15;
                } else {
                    /* FILL */
                    n24_1 -= count;
                    if (src_idx >= (int)rle_size) goto done;
                    v = rle[src_idx++];
                    printf("[%3d] FILL count=%d v=0x%02x  dst %d -> %d, n24_1 %d\n",
                           src_idx-2, count, v, dst_idx, dst_idx+count, n24_1);
                    for (int k = 0; k < count; k++) {
                        pixels[dst_idx++] = v;
                    }
                    if (n24_1 == 0) goto label15;
                }
            }
        }
        /* 内层 while 结束 (n24_1 == 0) */
label15:
        printf("  LABEL_15: dst %d += %d, n24 %d -> %d\n", dst_idx, 0, n24, n24-1);
        dst_idx += 0;  /* arg8=24, dst += 24-24 = 0 */
        n24--;
    }

done:
    printf("\n=== 解码结果 %dx%d ===\n", w, h);
    for (int y = 0; y < h; y++) {
        printf("row %2d: ", y);
        for (int x = 0; x < w; x++) {
            byte v = pixels[y * w + x];
            if (v == 0) printf(" ..");
            else printf(" %02x", v);
        }
        printf("\n");
    }

    fdother_offset_table_free(&table);
    fdother_unload();
    return 0;
}
