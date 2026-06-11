/*
 * 调试fd_decompress_sub_4E22A：跟踪每一步执行
 */

#include "../include/fd2_dat.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    const char* filepath = "game/FDOTHER.DAT";
    FILE* fp = fopen(filepath, "rb");
    fseek(fp, 0, SEEK_END);
    long file_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    byte* data = (byte*)malloc(file_size);
    fread(data, 1, file_size, fp);
    fclose(fp);

    // 索引1
    dword idx1_start = 0x4A6;
    byte* idx1_data = data + idx1_start;
    dword idx1_size = 0xD61 - idx1_start;

    // 图标0: offset=0x56, size=221
    byte* icon_data = idx1_data + 0x56;
    int icon_size = 221;

    printf("Icon 0 data (first 30 bytes):\n  ");
    for (int i = 0; i < 30; i++) {
        printf("%02X ", icon_data[i]);
    }
    printf("\n\n");

    // 手动模拟汇编执行
    int src_idx = 0;
    int dst_idx = 0;
    int n24 = 24;
    int n24_1;
    int count;
    int step = 0;

    printf("=== 手动模拟汇编 ===\n");
    while (n24 > 0) {
        n24_1 = 24;
        printf("--- 行 %d (n24=%d) ---\n", 24 - n24, n24);

        while (1) {
            if (src_idx >= icon_size) {
                printf("  步骤%d: src_idx=%d >= size=%d, 数据不足!\n", step, src_idx, icon_size);
                return 1;
            }

            byte value = icon_data[src_idx];
            int old_src = src_idx;
            src_idx++;
            int old_dst = dst_idx;
            int old_n24_1 = n24_1;

            // shl cl, 1 (v9)
            byte v9 = (value << 1) & 0xFF;

            // 检查bit7
            if (value & 0x80) {
                // shl cl, 1 (v10)
                byte v10 = (v9 << 1) & 0xFF;
                // 4 * value
                count = (value << 2) & 0xFF;

                // 检查bit6
                if (v10 & 0x100) {  // 不可能，v10是byte
                }

                // 实际上检查v9 & 0x80 (即value的bit6)
                if (v9 & 0x80) {
                    // 11xxxxxx - 跳过模式
                    count = (count >> 2) + 1;
                    dst_idx += count;
                    n24_1 = (n24_1 - count) & 0xFF;
                    printf("  步骤%d [跳过]: src[%d]=0x%02X count=%d, dst_idx: %d->%d, n24_1: %d->%d\n",
                           step, old_src, value, count, old_dst, dst_idx, old_n24_1, n24_1);
                } else {
                    // 10xxxxxx - 复制模式
                    count = (count >> 2) + 1;
                    n24_1 = (n24_1 - count) & 0xFF;
                    printf("  步骤%d [复制]: src[%d]=0x%02X count=%d, src_idx: %d->%d, dst_idx: %d->%d, n24_1: %d->%d\n",
                           step, old_src, value, count, old_src+1, src_idx+count, old_dst, dst_idx+count, old_n24_1, n24_1);
                    src_idx += count;
                    dst_idx += count;
                }
            } else {
                // shl cl, 1 (v10)
                byte v10 = (v9 << 1) & 0xFF;

                // 检查bit6
                if (v9 & 0x40) {
                    // 01xxxxxx - 交替模式
                    count = (value << 2) & 0xFF;
                    count = (count >> 2) + 1;
                    n24_1 = (n24_1 - count) & 0xFF;
                    n24_1 = (n24_1 - count) & 0xFF;
                    if (src_idx < icon_size) {
                        byte pv = icon_data[src_idx];
                        src_idx++;
                        int old_dst2 = dst_idx;
                        for (int i = 0; i < count; i++) {
                            dst_idx++;
                            dst_idx++;
                        }
                        printf("  步骤%d [交替]: src[%d]=0x%02X count=%d pixel=0x%02X, dst_idx: %d->%d, n24_1: %d->%d\n",
                               step, old_src, value, count, pv, old_dst, dst_idx, old_n24_1, n24_1);
                    }
                } else {
                    // 00xxxxxx - 填充模式
                    count = (value << 2) & 0xFF;
                    count = (count >> 2) + 1;
                    n24_1 = (n24_1 - count) & 0xFF;
                    if (src_idx < icon_size) {
                        byte pv = icon_data[src_idx];
                        src_idx++;
                        int old_dst2 = dst_idx;
                        dst_idx += count;
                        printf("  步骤%d [填充]: src[%d]=0x%02X count=%d pixel=0x%02X, dst_idx: %d->%d, n24_1: %d->%d\n",
                               step, old_src, value, count, pv, old_dst, dst_idx, old_n24_1, n24_1);
                    }
                }
            }

            step++;
            if (step > 50) {
                printf("  ... 步骤过多, 中断\n");
                return 1;
            }

            if (n24_1 == 0) {
                printf("  -- 行结束 --\n");
                break;
            }
        }

        n24--;
        if (n24 == 0) break;
    }

    printf("\n=== 完成 ===\n");
    printf("最终: src_idx=%d, dst_idx=%d\n", src_idx, dst_idx);

    free(data);
    return 0;
}
