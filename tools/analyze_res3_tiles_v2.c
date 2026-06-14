/* analyze_res3_tiles_v2.c - 详细分析资源3每个tile的结构 */
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

    word tile_count = data[4] | (data[5] << 8);
    printf("res3 size=%u tile_count=%u\n\n", size, tile_count);

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

        word w_h = tile[0] | (tile[1] << 8);
        word h_h = tile[2] | (tile[3] << 8);

        /* 检查 tile_size 和头的关系 */
        int tile_size_4 = tile_size - 4;
        int matches_16x16 = (tile_size == 256);
        int header_says_16x16 = (w_h == 16 && h_h == 16);
        int header_says_24x24 = (w_h == 24 && h_h == 24);

        /* 最大像素值 */
        int max_v = 0;
        int non_zero = 0;
        for (int i = 0; i < (int)tile_size && i < 256; i++) {
            if (tile[i] > max_v) max_v = tile[i];
            if (tile[i] != 0) non_zero++;
        }

        printf("Tile %2d: off=0x%x size=%u 头[w=%u h=%u] tile_size==256:%d 头是16x16:%d 头是24x24:%d max=%d non_zero=%d\n",
            t, off, tile_size, w_h, h_h, matches_16x16, header_says_16x16, header_says_24x24, max_v, non_zero);
    }

    fdother_unload();
    return 0;
}
