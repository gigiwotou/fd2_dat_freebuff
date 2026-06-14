/* test_min.c */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../include/fd2_types.h"
#include "../include/fd2_rle.h"
#include "../include/fd2_fdother_resources.h"
#include "../include/fd2_dat.h"

int main(int argc, char** argv) {
    fprintf(stderr, "STEP 1: start\n"); fflush(stderr);
    if (fdother_load("d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT") != 0) return 1;
    fprintf(stderr, "STEP 2: loaded\n"); fflush(stderr);

    fdother_lmi1_t lmi1;
    fprintf(stderr, "STEP 3: before get_lmi1\n"); fflush(stderr);
    int r = fdother_get_lmi1(3, &lmi1);
    fprintf(stderr, "STEP 4: get_lmi1 ret=%d\n", r); fflush(stderr);

    if (r == 0) {
        fprintf(stderr, "  tile_count=%u, tile_w=%u, tile_h=%u\n",
                lmi1.tile_count, lmi1.tile_width, lmi1.tile_height);
        fprintf(stderr, "  data=%p, size=%u\n", (const void*)lmi1.data, lmi1.size);
        fflush(stderr);
    }

    fdother_unload();
    fprintf(stderr, "STEP 5: done\n"); fflush(stderr);
    return 0;
}
