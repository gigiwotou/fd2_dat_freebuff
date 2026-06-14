/* dump_lmi1_res3.c - 直接打印资源3所有23个tile的实际像素数据 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../include/fd2_types.h"
#include "../include/fd2_rle.h"
#include "../include/fd2_fdother_resources.h"
#include "../include/fd2_dat.h"

int main(int argc, char** argv) {
    if (fdother_load("d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT") != 0) return 1;

    dword size;
    const byte* data = fdother_get_resource(3, &size);
    if (!data) return 1;

    printf("=== 资源3 直接 dump (无RLE) ===\n");
    for (int t = 0; t < 23; t++) {
        dword off = data[6+t*4] | (data[6+t*4+1]<<8) | (data[6+t*4+2]<<16) | (data[6+t*4+3]<<24);
        const byte* tile = data + off;

        printf("\n--- Tile %d (offset=0x%x) ---\n", t, off);
        printf("前 32 字节 (16进制):\n");
        for (int i = 0; i < 32; i++) {
            printf("%02x ", tile[i]);
            if ((i+1) % 16 == 0) printf("\n");
        }
        /* 显示为 16x16 ASCII 图像 */
        printf("像素 (raw 256字节, 16x16):\n");
        for (int y = 0; y < 16; y++) {
            for (int x = 0; x < 16; x++) {
                byte v = tile[y * 16 + x];
                if (v == 0) printf(" .");
                else if (v < 16) printf(" %x", v);
                else printf("%02x", v);
            }
            printf("\n");
        }
    }
    fdother_unload();
    return 0;
}
