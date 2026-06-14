/* check_res3_tiles.c - 检查资源3所有23个tile的宽高头 */
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

    /* 解析LMI1头 */
    word tile_count = data[4] | (data[5] << 8);
    printf("tile_count=%u\n", tile_count);

    for (int t = 0; t < tile_count; t++) {
        dword off = data[6+t*4] | (data[6+t*4+1]<<8) | (data[6+t*4+2]<<16) | (data[6+t*4+3]<<24);
        dword next_off;
        if (t + 1 < tile_count) {
            next_off = data[6+(t+1)*4] | (data[6+(t+1)*4+1]<<8) | (data[6+(t+1)*4+2]<<16) | (data[6+(t+1)*4+3]<<24);
        } else {
            next_off = size;
        }
        dword tile_size = next_off - off;
        const byte* tile = data + off;

        word w0 = tile[0] | (tile[1] << 8);
        word h0 = tile[2] | (tile[3] << 8);
        printf("Tile %2d: off=0x%x size=%u  头[w=%u h=%u]  前8字节=", t, off, tile_size, w0, h0);
        for (int i = 0; i < 8 && i < (int)tile_size; i++) printf("%02x ", tile[i]);
        printf("\n");
    }

    fdother_unload();
    return 0;
}
