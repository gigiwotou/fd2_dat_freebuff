/* test_res3_simple.c - 简单分析资源3 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../include/fd2_types.h"
#include "../include/fd2_rle.h"
#include "../include/fd2_fdother_resources.h"
#include "../include/fd2_dat.h"

int main(int argc, char** argv) {
    printf("[1] start\n"); fflush(stdout);
    if (fdother_load("d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT") != 0) {
        printf("Cannot load\n");
        return 1;
    }
    printf("[2] loaded\n"); fflush(stdout);

    dword size;
    const byte* data = fdother_get_resource(3, &size);
    printf("[3] res3 size=%u data=%p\n", size, (const void*)data); fflush(stdout);

    if (!data || size < 6) return 1;

    printf("First 32 bytes:\n");
    for (int i = 0; i < 32; i++) {
        printf("%02x ", data[i]);
        if ((i+1) % 16 == 0) printf("\n");
    }
    fflush(stdout);

    printf("Magic: %.4s\n", data);
    word tile_count = data[4] | (data[5] << 8);
    printf("tile_count = %u\n", tile_count);
    fflush(stdout);

    /* 打印所有tile偏移 */
    for (int i = 0; i <= tile_count && i < 30; i++) {
        dword addr = 6 + i * 4;
        if (addr + 4 > size) break;
        dword o = data[addr] | (data[addr+1]<<8) | (data[addr+2]<<16) | (data[addr+3]<<24);
        printf("offset[%d] = 0x%x\n", i, o);
    }
    fflush(stdout);

    /* tile 0 */
    dword off0 = data[6] | (data[7]<<8) | (data[8]<<16) | (data[9]<<24);
    dword off1 = data[10] | (data[11]<<8) | (data[12]<<16) | (data[13]<<24);
    printf("\nTile 0: offset=0x%x size=%u\n", off0, off1-off0);
    if (off0 + 4 <= size) {
        word w = data[off0] | (data[off0+1] << 8);
        word h = data[off0+2] | (data[off0+3] << 8);
        printf("  w=%u h=%u (raw 4+w*h=%u)\n", w, h, 4+w*h);
    }
    fflush(stdout);

    fdother_unload();
    printf("Done\n");
    return 0;
}
