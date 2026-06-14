/* 对比 Python 和 C 解码子资源0的实际输出 */
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
    const byte* sub0 = data + 312;
    int sub_size = 484;
    int w = 24, h = 20;

    printf("Sub 0 头 5 字节: %02x %02x %02x %02x %02x\n",
           sub0[0], sub0[1], sub0[2], sub0[3], sub0[4]);

    /* C 实现的 sub_4E98D_no_header */
    byte* buf = (byte*)calloc(1, w * h);
    int r = fd2_rle_sub_4E98D_no_header(sub0 + 5, sub_size - 5, buf, w, h, -1);
    printf("C fd2_rle_sub_4E98D_no_header result: %d\n", r);

    int nonzero = 0;
    int unique[256] = {0};
    for (int i = 0; i < w * h; i++) {
        if (buf[i] != 0) nonzero++;
        unique[buf[i]]++;
    }
    printf("非0像素: %d / %d\n", nonzero, w * h);
    printf("唯一像素值分布: ");
    for (int v = 0; v < 256; v++) {
        if (unique[v] > 0) printf("%d(0x%02x)=%d ", v, v, unique[v]);
    }
    printf("\n\n像素矩阵 (24x20):\n");
    for (int y = 0; y < h; y++) {
        printf("  y=%2d: ", y);
        for (int x = 0; x < w; x++) {
            int v = buf[y*w + x];
            if (v == 0) printf(" . ");
            else printf("%3d ", v);
        }
        printf("\n");
    }

    free(buf);
    return 0;
}
