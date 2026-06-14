/* test_index2_sub0_raw.c - 直接显示 sub_0 的 480 字节原始像素 (按 24x20) */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../include/fd2_types.h"
#include "../include/fd2_rle.h"
#include "../include/fd2_fdother_resources.h"
#include "../include/fd2_dat.h"

/* 6-bit to 8-bit color conversion */
static int color_6_to_8(int c) {
    return (c << 2) | (c >> 4);
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

    dword sub_size;
    const byte* sub_data = fdother_offset_table_get_resource(&table, 0, &sub_size);
    if (!sub_data || sub_size < 5) {
        printf("No data, size=%u\n", sub_size);
        return 1;
    }

    printf("Sub 0: size=%u\n", sub_size);
    printf("Header bytes: [0]=0x%02x [1]=0x%02x [2]=0x%02x [3]=0x%02x [4]=0x%02x\n",
           sub_data[0], sub_data[1], sub_data[2], sub_data[3], sub_data[4]);
    word w = sub_data[0] | (sub_data[1] << 8);
    word h = sub_data[2] | (sub_data[3] << 8);
    printf("w=%d h=%d\n", w, h);

    /* 加载调色板 */
    fdother_palette_t pal;
    fdother_get_palette(0, &pal);
    byte rgb24[768];
    fdother_palette_to_rgb24(&pal, rgb24);

    /* 尝试 3 种解释:
     * A) 4字节头 + 480字节raw pixels (24x20)
     * B) 5字节头 + 479字节RLE (sub_4E22A格式)
     * C) 4字节头 + 480字节RLE (sub_4E22A格式) */
    int pixels_24x20[480];

    /* A) 4字节头 + 480字节raw */
    printf("\n=== A) 4字节头 + 480字节原始像素 (24x20) ===\n");
    for (int i = 0; i < 480; i++) pixels_24x20[i] = sub_data[4 + i];
    /* 打印前几行 */
    for (int y = 0; y < 8; y++) {
        printf("row %2d: ", y);
        for (int x = 0; x < 24; x++) {
            byte v = sub_data[4 + y * 24 + x];
            printf("%02x ", v);
        }
        printf("\n");
    }

    /* B) 5字节头 + 479字节RLE */
    printf("\n=== B) 5字节头 + 479字节RLE (sub_4E22A) ===\n");
    byte* rle_buf_b = (byte*)malloc(24 * 24);
    memset(rle_buf_b, 0, 24 * 24);
    int ret_b = fd2_rle_sub_4E22A(sub_data + 5, sub_size - 5, rle_buf_b, 24, 24, 24);
    printf("Result: %d\n", ret_b);
    for (int y = 0; y < 8; y++) {
        printf("row %2d: ", y);
        for (int x = 0; x < 24; x++) {
            byte v = rle_buf_b[y * 24 + x];
            printf("%02x ", v);
        }
        printf("\n");
    }

    /* C) 4字节头 + 480字节RLE */
    printf("\n=== C) 4字节头 + 480字节RLE (sub_4E22A) ===\n");
    byte* rle_buf_c = (byte*)malloc(24 * 24);
    memset(rle_buf_c, 0, 24 * 24);
    int ret_c = fd2_rle_sub_4E22A(sub_data + 4, sub_size - 4, rle_buf_c, 24, 24, 24);
    printf("Result: %d\n", ret_c);
    for (int y = 0; y < 8; y++) {
        printf("row %2d: ", y);
        for (int x = 0; x < 24; x++) {
            byte v = rle_buf_c[y * 24 + x];
            printf("%02x ", v);
        }
        printf("\n");
    }

    /* 假设 A 是正确的, 渲染调色板窗口: win=0xC7=199
     * 0xC7 是 SKIP/透明色, 表示这个区域是 199 (主调色板 199 索引)
     * 0x4D = 77, 0x4A = 74, 0xC5 = 197 */

    /* 输出统计 */
    int count_4a = 0, count_4d = 0, count_c5 = 0, count_c7 = 0, count_other = 0;
    for (int i = 0; i < 480; i++) {
        byte v = sub_data[4 + i];
        if (v == 0x4A) count_4a++;
        else if (v == 0x4D) count_4d++;
        else if (v == 0xC5) count_c5++;
        else if (v == 0xC7) count_c7++;
        else count_other++;
    }
    printf("\n像素值统计 (前480字节):\n");
    printf("0x4A: %d, 0x4D: %d, 0xC5: %d, 0xC7: %d, 其他: %d\n",
           count_4a, count_4d, count_c5, count_c7, count_other);

    free(rle_buf_b);
    free(rle_buf_c);
    fdother_offset_table_free(&table);
    fdother_unload();
    return 0;
}
