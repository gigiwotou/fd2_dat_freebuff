/* simulate_viewer_res3.c - 模拟 viewer 对资源3的显示 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../include/fd2_types.h"
#include "../include/fd2_rle.h"
#include "../include/fd2_fdother_resources.h"
#include "../include/fd2_dat.h"

int main(int argc, char** argv) {
    if (fdother_load("d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT") != 0) return 1;

    fdother_lmi1_t lmi1;
    if (fdother_get_lmi1(3, &lmi1) != 0) return 1;
    fprintf(stderr, "LMI1: tile_count=%u, tile_w=%u, tile_h=%u, data=%p, size=%u\n",
           lmi1.tile_count, lmi1.tile_width, lmi1.tile_height,
           (const void*)lmi1.data, lmi1.size);
    fflush(stderr);

    /* 模拟viewer对所有23个tile的处理 - 使用类型B (16x16无头) 直接memcpy */
    for (int t = 0; t < 5; t++) {
        fprintf(stderr, "iter %d start\n", t); fflush(stderr);

        /* 直接从 data + offset 拷贝 256 字节 */
        const byte* data = lmi1.data;
        fprintf(stderr, "  data=%p\n", (const void*)data); fflush(stderr);
        dword offset = data[6+t*4] | (data[6+t*4+1]<<8) | (data[6+t*4+2]<<16) | (data[6+t*4+3]<<24);
        fprintf(stderr, "  offset=0x%x\n", offset); fflush(stderr);
        const byte* tile = data + offset;
        fprintf(stderr, "  tile=%p\n", (const void*)tile); fflush(stderr);

        byte buf[64*64];
        memcpy(buf, tile, 256);

        int aw = 16, ah = 16;
        int nz = 0;
        int max_v = 0;
        for (int i = 0; i < aw*ah; i++) {
            if (buf[i]) nz++;
            if (buf[i] > max_v) max_v = buf[i];
        }
        printf("Tile %2d: w=%d h=%d nz=%d/%d max=%d\n",
               t, aw, ah, nz, aw*ah, max_v);
        if (t < 3 || t == 22) {
            printf("  ASCII:\n");
            for (int y = 0; y < ah; y++) {
                printf("    ");
                for (int x = 0; x < aw; x++) {
                    byte v = buf[y * aw + x];
                    if (v == 0) printf(" .");
                    else if (v < 16) printf(" %x", v);
                    else printf("%02x", v);
                }
                printf("\n");
            }
        }
    }

    fdother_unload();
    return 0;
}
