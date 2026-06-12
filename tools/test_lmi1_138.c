/* test_lmi1_138.c - 测试 FDOTHER.DAT 索引5所有138个tile的解析
 *
 * 读取 game/FDOTHER.DAT, 解析索引5的LMI1数据,
 * 尝试解码每个tile, 统计成功/失败数
 */
#include "../include/fd2_fdother_resources.h"
#include "../include/fd2_rle.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    printf("===== FDOTHER.DAT 索引5 LMI1 全部138个tile测试 =====\n\n");

    if (fdother_load("game/FDOTHER.DAT") != 0) {
        printf("FAIL: 无法加载FDOTHER.DAT\n");
        return 1;
    }

    if (fdother_get_resource_count() <= 5) {
        printf("FAIL: 资源数量不足, 索引5不可用\n");
        return 1;
    }

    /* 读取索引5数据 */
    dword idx5_size = 0;
    const byte* idx5 = fdother_get_resource(5, &idx5_size);
    if (!idx5) {
        printf("FAIL: 无法获取索引5\n");
        return 1;
    }

    if (memcmp(idx5, "LMI1", 4) != 0) {
        printf("FAIL: 索引5不是LMI1格式: %.4s\n", idx5);
        return 1;
    }

    int tile_count = idx5[4] | (idx5[5] << 8);
    printf("索引5: 138个tiles (实际: %d), 原始数据: %u 字节\n\n", tile_count, idx5_size);

    /* 解析LMI1 */
    fdother_lmi1_t lmi1;
    if (fdother_parse_lmi1(idx5, idx5_size, &lmi1) != 0) {
        printf("FAIL: 解析LMI1失败\n");
        return 1;
    }

    printf("tile_count = %d\n", lmi1.tile_count);
    printf("tile_width = %d, tile_height = %d\n\n", lmi1.tile_width, lmi1.tile_height);

    /* 解码每个tile */
    int success = 0, fail = 0, total = 0;
    int fail_idx[200];
    int fail_count = 0;
    int rle_count = 0, raw_count = 0;

    for (int i = 0; i < lmi1.tile_count; i++) {
        const byte* tile_data;
        dword tile_size;
        if (fdother_lmi1_get_tile(&lmi1, i, &tile_data, &tile_size) != 0) {
            fail++;
            if (fail_count < 200) fail_idx[fail_count++] = i;
            continue;
        }
        total++;

        /* 读头 [w:2][h:2] */
        if (tile_size < 4) {
            fail++;
            if (fail_count < 200) fail_idx[fail_count++] = i;
            continue;
        }
        int w = tile_data[0] | (tile_data[1] << 8);
        int h = tile_data[2] | (tile_data[3] << 8);
        int expected = 4 + w * h;

        /* 分配目标缓冲区,初始化为0 */
        int dst_size = w * h;
        byte* dst = (byte*)calloc(dst_size, 1);
        if (!dst) {
            fail++;
            if (fail_count < 200) fail_idx[fail_count++] = i;
            continue;
        }

        /* 解码 */
        int out_w = 0, out_h = 0;
        int ret = fd2_rle_lmi1_decode_tile_auto(tile_data, (int)tile_size, dst, &out_w, &out_h, w);

        if (ret == 0 && out_w == w && out_h == h) {
            success++;
            if (tile_size < (dword)expected) rle_count++;
            else raw_count++;
        } else {
            fail++;
            if (fail_count < 200) fail_idx[fail_count++] = i;
        }
        free(dst);
    }

    printf("===== 解析结果 =====\n");
    printf("总tile数: %d\n", total);
    printf("成功: %d (未压缩: %d, RLE压缩: %d)\n", success, raw_count, rle_count);
    printf("失败: %d\n", fail);

    if (fail > 0) {
        printf("\n失败tile索引: ");
        for (int i = 0; i < fail_count && i < 50; i++) {
            printf("%d ", fail_idx[i]);
        }
        if (fail_count > 50) printf("...(共 %d 个)", fail_count);
        printf("\n");
    }

    fdother_unload();

    printf("\n===== 测试 %s =====\n", fail == 0 ? "通过" : "失败");
    return fail == 0 ? 0 : 1;
}
