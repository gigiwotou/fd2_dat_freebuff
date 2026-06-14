/* dump_lmi1_res3_simple.c */
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
    printf("res3 size=%u\n", size);

    for (int t = 0; t < 23; t++) {
        dword off = data[6+t*4] | (data[6+t*4+1]<<8) | (data[6+t*4+2]<<16) | (data[6+t*4+3]<<24);
        const byte* tile = data + off;

        int max_v = 0;
        for (int i = 0; i < 256; i++) {
            if (tile[i] > max_v) max_v = tile[i];
        }
        printf("Tile %d offset=0x%x max=%d\n", t, off, max_v);
    }

    fdother_unload();
    return 0;
}
