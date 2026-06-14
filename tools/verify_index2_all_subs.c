/* verify_index2_all_subs.c - 验证所有 78 个索引2子资源 */
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

    int total = 0, ok = 0, raw_ok = 0, rle_ok = 0, fail = 0;
    int cnt_24x20 = 0, cnt_24x16 = 0, cnt_other = 0;

    printf("=== 验证索引2全部 %d 个子资源 ===\n", (int)table.offset_count - 1);
    for (int sub = 0; sub < (int)table.offset_count - 1; sub++) {
        dword sub_size;
        const byte* sub_data = fdother_offset_table_get_resource(&table, sub, &sub_size);
        if (!sub_data || sub_size < 4) {
            printf("Sub %d: 无效数据\n", sub);
            fail++;
            continue;
        }

        total++;

        word w = sub_data[0] | (sub_data[1] << 8);
        word h = sub_data[2] | (sub_data[3] << 8);
        dword expected_raw = 4 + (dword)w * (dword)h;

        if (w == 24 && h == 20) cnt_24x20++;
        else if (w == 24 && h == 16) cnt_24x16++;
        else cnt_other++;

        if (w > 0 && w <= 64 && h > 0 && h <= 64 && sub_size == expected_raw) {
            ok++;
            raw_ok++;
        } else {
            /* 尝试 5 字节头 + RLE */
            byte win = sub_data[4];
            word rw = sub_data[5] | (sub_data[6] << 8);
            word rh = sub_data[7] | (sub_data[8] << 8);
            dword rle_size = sub_size - 9;
            if (rw > 0 && rw <= 64 && rh > 0 && rh <= 64 && rle_size > 0 && rle_size < sub_size) {
                ok++;
                rle_ok++;
            } else {
                printf("Sub %d: 失败 w=%d h=%d size=%u (raw? %u, rle? rw=%d rh=%d rs=%u)\n",
                       sub, w, h, sub_size, expected_raw, rw, rh, rle_size);
                fail++;
            }
        }
    }

    printf("\n=== 统计 ===\n");
    printf("总数: %d (期望 77, 索引2有78个偏移值, 子资源数=78-1=77)\n", total);
    printf("24x20: %d\n", cnt_24x20);
    printf("24x16: %d\n", cnt_24x16);
    printf("其他: %d\n", cnt_other);
    printf("成功 (raw): %d\n", raw_ok);
    printf("成功 (rle): %d\n", rle_ok);
    printf("失败: %d\n", fail);

    fdother_offset_table_free(&table);
    fdother_unload();
    return (fail == 0) ? 0 : 1;
}
