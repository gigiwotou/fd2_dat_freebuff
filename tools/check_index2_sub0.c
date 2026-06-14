/* 简化测试: 直接解码索引2子资源0 */
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

    /* 子资源 0: 起始 312, 长度 484 */
    const byte* sub0 = data + 312;
    int sub_size = 484;
    int w = 24, h = 20;

    printf("Sub 0 头 5 字节: %02x %02x %02x %02x %02x\n",
           sub0[0], sub0[1], sub0[2], sub0[3], sub0[4]);
    printf("RLE data 头 64 字节: ");
    for (int i = 5; i < 69; i++) printf("%02x ", sub0[i]);
    printf("\n");

    /* 用 sub_4E98D_no_header (不读 4字节头) */
    /* 头部 5 字节, RLE data 从 src[5] 开始 */
    byte* buf = (byte*)calloc(1, w * h);
    int r = fd2_rle_sub_4E98D_no_header(sub0 + 5, sub_size - 5, buf, w, h, -1);
    printf("\nfd2_rle_sub_4E98D_no_header(无头) result: %d\n", r);
    int nonzero = 0;
    for (int i = 0; i < w * h; i++) if (buf[i] != 0) nonzero++;
    printf("非0像素: %d\n", nonzero);
    if (nonzero < 50) {
        for (int i = 0; i < w * h; i++) {
            if (buf[i] != 0) {
                printf("  [%d] = %3d\n", i, buf[i]);
            }
        }
    }

    free(buf);
    return 0;
}
