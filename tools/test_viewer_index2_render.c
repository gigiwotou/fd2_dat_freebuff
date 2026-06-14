/* test_viewer_index2_render.c - 模拟viewer的新逻辑渲染索引2子资源, 验证像素输出合理性 */
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

    /* 加载主调色板 (RGB24) */
    fdother_palette_t pal;
    if (fdother_get_palette(0, &pal) != 0) {
        printf("Get palette error\n");
        return 1;
    }
    byte rgb24[768];
    fdother_palette_to_rgb24(&pal, rgb24);

    int sub_count = (int)table.offset_count - 1;
    printf("=== 索引2 共 %d 个子资源 ===\n\n", sub_count);
    printf("=== 使用 viewer 新逻辑: 4字节头+raw像素 ===\n\n");

    /* 抽样测试关键子资源 (前面几个、中间几个、后面几个、24x16) */
    int sample_indices[] = {0, 1, 2, 36, 37, 50, 72, 73, 74, 75, 76};
    int sample_count = (int)(sizeof(sample_indices)/sizeof(sample_indices[0]));

    int total_nonzero = 0, total_max = 0;
    int test_count = 0;

    for (int s = 0; s < sample_count; s++) {
        int idx = sample_indices[s];
        if (idx >= sub_count) continue;
        dword sub_size;
        const byte* sub_data = fdother_offset_table_get_resource(&table, idx, &sub_size);
        if (!sub_data || sub_size < 4) continue;

        /* viewer 新逻辑: 4字节头 + raw 像素 */
        word tw = sub_data[0] | (sub_data[1] << 8);
        word th = sub_data[2] | (sub_data[3] << 8);
        dword expected = 4 + (dword)tw * (dword)th;

        if (tw == 0 || th == 0 || tw > 64 || th > 64 || sub_size != expected) {
            printf("Sub %d: 尺寸不匹配 w=%d h=%d size=%u expected=%u\n",
                   idx, tw, th, sub_size, expected);
            continue;
        }

        test_count++;
        printf("Sub %2d: %dx%d size=%u\n", idx, tw, th, sub_size);
        printf("  头4字节: %02x %02x %02x %02x\n",
               sub_data[0], sub_data[1], sub_data[2], sub_data[3]);

        /* 显示前2行像素值 (16进制 + 颜色解释) */
        printf("  前2行 raw 像素:\n");
        for (int y = 0; y < 2 && y < th; y++) {
            printf("    row %d: ", y);
            for (int x = 0; x < tw; x++) {
                byte v = sub_data[4 + y * tw + x];
                printf("%02x ", v);
            }
            printf("\n");
        }

        /* 统计非0像素, 最大值, 调色板颜色 */
        int nonzero = 0;
        int max_v = 0;
        int min_v = 255;
        for (int i = 0; i < tw * th; i++) {
            byte v = sub_data[4 + i];
            if (v != 0) nonzero++;
            if (v > max_v) max_v = v;
            if (v != 0 && v < min_v) min_v = v;
        }
        printf("  非0像素: %d / %d, 值域: %d..%d\n", nonzero, tw*th,
               nonzero > 0 ? min_v : 0, max_v);

        total_nonzero += nonzero;
        if (max_v > total_max) total_max = max_v;

        /* 显示每个不同像素值的调色板颜色样本 */
        int seen[256] = {0};
        int distinct = 0;
        for (int i = 0; i < tw * th && distinct < 5; i++) {
            byte v = sub_data[4 + i];
            if (!seen[v]) {
                seen[v] = 1;
                distinct++;
                int r = rgb24[v*3], g = rgb24[v*3+1], b = rgb24[v*3+2];
                printf("    像素值 0x%02x=%3d -> RGB(%3d,%3d,%3d)\n", v, v, r, g, b);
            }
        }
        printf("\n");
    }

    printf("=== 总计: 测试 %d 个子资源, 累计非0像素 %d, 最大值 %d ===\n",
           test_count, total_nonzero, total_max);
    printf("(若 total_nonzero > 0 且 total_max 介于 0-255, 说明 raw 像素逻辑工作正常)\n");

    fdother_offset_table_free(&table);
    fdother_unload();
    return 0;
}
