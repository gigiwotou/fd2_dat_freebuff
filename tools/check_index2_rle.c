/* 测试RLE解码索引2子资源 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../include/fd2_types.h"
#include "../include/fd2_rle.h"
#include "../include/fd2_fdother_resources.h"

int main(int argc, char** argv) {
    if (fdother_load("D:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT") != 0) {
        printf("Cannot load\n");
        return 1;
    }

    dword size;
    const byte* data = fdother_get_resource(2, &size);
    if (!data) {
        printf("Cannot get index 2\n");
        return 1;
    }

    /* 子资源 0 起始于 312, 长度 484 字节 */
    /* 子资源头: [w:2][h:2][palette_window:1] */
    /* 头: 18 00 14 00 00 -> w=24, h=20, window=0 */
    const byte* sub0 = data + 312;
    int sub_size = 484;

    printf("Sub 0 first 16 bytes: ");
    for (int i = 0; i < 16; i++) printf("%02x ", sub0[i]);
    printf("\n");

    word w = sub0[0] | (sub0[1] << 8);
    word h = sub0[2] | (sub0[3] << 8);
    byte win = sub0[4];
    printf("Header: w=%d h=%d win=%d\n", w, h, win);
    printf("RLE data: src[5..]: ");
    for (int i = 5; i < 32; i++) printf("%02x ", sub0[i]);
    printf("\n");

    /* 用 sub_4E22A 解码 (无头, 直接从 src[0] 开始, 不需头) */
    /* 注意: fd2_rle_sub_4E22A 假设 src 是 raw RLE, 没有 4 字节头 */
    /* 但 tile.rle_data = data+5, 已经是跳过头 5 字节 */
    /* 但是等等, 头是 5 字节? w:2 + h:2 + win:1 = 5 字节 */
    /* 而 sub_4E22A 输出 24x24 像素, 用 sub_4ED0B 格式的 4 字节头 [w:2][h:2] */
    /* 所以头应该是 4 字节而非 5 字节? */
    /* 让我重新分析 */

    /* 尝试方案A: 头4字节 = [w:2][h:2], RLE data 从 src[4] 开始 */
    /* 那么 palette_window 应该是 RLE data 的第一字节? 但第一字节是 0xC7 不是 window */

    /* 让我看其他子资源 */
    /* 子资源 48: offset=23544, w=24 h=16, data[23544+4]=0x4A 0xC7 */
    /* 即 头 [w:2][h:2][window:1]=24,16,74, RLE data[0]=0xC7 */
    /* 所以头确实是 5 字节, window 是 1 字节 */

    /* 4E范围 RLE: 第一个字节 0xC7 = 11000111 = SKIP 模式, count=(0xC7 & 0x3F)+1 = 8 */
    /* 即 8 个透明像素 */

    /* 解码子资源 0: 24x20, window=0, RLE data 从 src[5] 开始 */
    byte* buf = (byte*)calloc(1, 24 * 20);
    int r = fd2_rle_sub_4E22A(sub0 + 5, sub_size - 5, buf, 24, 20, 24);
    printf("\nfd2_rle_sub_4E22A result: %d\n", r);

    /* 输出像素 */
    printf("\nDecoded pixels (24x20):\n");
    for (int y = 0; y < 20; y++) {
        for (int x = 0; x < 24; x++) {
            printf("%3d ", buf[y*24+x]);
        }
        printf("\n");
    }

    /* 也尝试 sub_4E98D_no_header */
    memset(buf, 0, 24*20);
    r = fd2_rle_sub_4E98D_no_header(sub0 + 5, sub_size - 5, buf, 24, 20, -1);
    printf("\nfd2_rle_sub_4E98D_no_header result: %d\n", r);
    printf("First 32 bytes: ");
    for (int i = 0; i < 32; i++) printf("%02x ", buf[i]);
    printf("\n");

    /* 4E98D 不带 SKIP 处理 ?  -  让我们尝试仅用 sub_4E22A */
    memset(buf, 0, 24*20);
    r = fd2_rle_sub_4E22A(sub0, sub_size, buf, 24, 20, 24);
    printf("\nfd2_rle_sub_4E22A (with header): result: %d\n", r);
    printf("First 32 bytes: ");
    for (int i = 0; i < 32; i++) printf("%02x ", buf[i]);
    printf("\n");

    free(buf);
    return 0;
}
