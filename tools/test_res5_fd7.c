/* test_res5_fd7.c - 验证 FDOTHER_DAT__7 (资源5) 的 tile 数据 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "fd2_types.h"
#include "fd2_fdother_resources.h"
#include "fd2_rle.h"

int main(int argc, char* argv[]) {
    const char* filepath = "game/FDOTHER.DAT";
    if (argc > 1) filepath = argv[1];

    int ret = fdother_load(filepath);
    if (ret != 0) {
        printf("Failed to load %s\n", filepath);
        return 1;
    }

    /* FDOTHER_DAT__7 -> 资源 5 (LMI1, 230 tiles) */
    fdother_lmi1_t lmi1;
    ret = fdother_get_lmi1(5, &lmi1);
    if (ret != 0) {
        printf("Failed to get LMI1 index 5\n");
        return 1;
    }

    printf("Resource 5: LMI1 with %d tiles, size=%u\n", lmi1.tile_count, lmi1.size);
    printf("Format: sub_4ED0B uses [width:2][height:2][pixels:width*height]\n\n");

    /* 验证前 10 个 tile 的尺寸 */
    for (int i = 0; i < 10 && i < (int)lmi1.tile_count; i++) {
        word tw, th;
        ret = fdother_lmi1_get_tile_size(&lmi1, i, &tw, &th);
        printf("  Tile %d: w=%d, h=%d\n", i, tw, th);
    }

    /* 解码第 0 个 tile 并打印前 16 字节像素 */
    printf("\n=== 解码 Tile 0 ===\n");
    byte buf[256 * 256];
    ret = fdother_lmi1_decode_tile(&lmi1, 0, buf, 24);
    if (ret > 0) {
        int w = ret & 0xFFFF;
        int h = (ret >> 16) & 0xFFFF;
        printf("Decoded Tile 0: %dx%d (ret=0x%x)\n", w, h, ret);
        printf("First 48 bytes:\n");
        for (int y = 0; y < h && y < 24; y++) {
            for (int x = 0; x < w && x < 16; x++) {
                printf("%02x ", buf[y * w + x]);
            }
            printf("\n");
        }
    }

    /* 也看下 tile 1 是什么样的 */
    printf("\n=== 解码 Tile 1 ===\n");
    ret = fdother_lmi1_decode_tile(&lmi1, 1, buf, 24);
    if (ret > 0) {
        int w = ret & 0xFFFF;
        int h = (ret >> 16) & 0xFFFF;
        printf("Decoded Tile 1: %dx%d (ret=0x%x)\n", w, h, ret);
    }

    return 0;
}
