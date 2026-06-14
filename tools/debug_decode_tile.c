/* debug_decode_tile.c - 调试单个tile的解码 */
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

    /* Tile 0 数据 */
    dword off = data[6] | (data[7]<<8) | (data[8]<<16) | (data[9]<<24);
    dword next_off = data[6+4] | (data[7+4]<<8) | (data[8+4]<<16) | (data[9+4]<<24);
    dword tile_size = next_off - off;
    const byte* tile = data + off;

    printf("Tile 0:\n");
    printf("  offset=0x%x size=%u\n", off, tile_size);
    printf("  前 16 字节: ");
    for (int i = 0; i < 16; i++) printf("%02x ", tile[i]);
    printf("\n");

    word w = tile[0] | (tile[1] << 8);
    word h = tile[2] | (tile[3] << 8);
    printf("  4字节头: w=%u h=%u\n", w, h);
    printf("  w<=1024: %d, h<=1024: %d\n", w <= 1024, h <= 1024);

    /* 调用 decode_tile */
    fdother_lmi1_t lmi1;
    if (fdother_get_lmi1(3, &lmi1) != 0) return 1;
    printf("  lmi1.tile_count=%u, lmi1.tile_width=%u, lmi1.tile_height=%u\n",
        lmi1.tile_count, lmi1.tile_width, lmi1.tile_height);

    byte buf[16*16];
    memset(buf, 0, sizeof(buf));
    int ret = fdother_lmi1_decode_tile(&lmi1, 0, buf, 16);
    printf("  decode_tile 返回: %d (0x%x)\n", ret, ret);
    printf("    解析: w=%d h=%d\n", ret & 0xFFFF, (ret >> 16) & 0xFFFF);

    /* 显示前 16 字节 */
    printf("  解码后前 16 字节: ");
    for (int i = 0; i < 16; i++) printf("%02x ", buf[i]);
    printf("\n");

    /* 显示为 16x16 图像 */
    printf("  16x16 ASCII (行8-15):\n");
    for (int y = 0; y < 16; y++) {
        printf("    ");
        for (int x = 0; x < 16; x++) {
            byte v = buf[y*16+x];
            if (v == 0) printf(".");
            else printf("%x", v & 0xF);
        }
        printf("\n");
    }

    fdother_unload();
    return 0;
}
