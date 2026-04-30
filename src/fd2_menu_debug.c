/**
 * FD2 Menu Debug Tool - 验证菜单资源加载
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "fd2_dat.h"
#include "fd2_resources.h"
#include "fd2_decoder.h"

int main(int argc, char* argv[]) {
    fd2_resources_t res;
    const char* game_dir = "game";

    if (argc > 1) {
        game_dir = argv[1];
    }

    fd2_resources_init(&res, game_dir);
    fd2_resources_load_all(&res);

    printf("=== FDOTHER Menu Resources Debug ===\n\n");

    /* Check resource #7 (palette or resource set?) */
    u32 res7_size;
    const u8* res7 = fd2_resources_get(&res, FD2_DAT_FDOTHER, 7, &res7_size);
    printf("Resource #7: size=%u bytes\n", res7_size);
    if (res7 && res7_size >= 4) {
        printf("  First 4 bytes: %02x %02x %02x %02x\n", res7[0], res7[1], res7[2], res7[3]);
        printf("  As 16-bit: w=%u, h=%u\n", res7[0] | (res7[1] << 8), res7[2] | (res7[3] << 8));
        if (res7_size == 768) {
            printf("  -> This is a PALETTE (256 colors)\n");
        }
    }

    /* Check resources #1-6 */
    printf("\nResources #1-6 (Menu Items):\n");
    for (int i = 1; i <= 6; i++) {
        u32 item_size;
        const u8* item = fd2_resources_get(&res, FD2_DAT_FDOTHER, i, &item_size);
        printf("  Resource #%d: size=%u\n", i, item_size);
        if (item && item_size >= 4) {
            printf("    First 4 bytes: %02x %02x %02x %02x\n", item[0], item[1], item[2], item[3]);
            printf("    As 16-bit: w=%u, h=%u\n", item[0] | (item[1] << 8), item[2] | (item[3] << 8));
        }
    }

    /* Check resource #101 (menu background?) */
    u32 bg_size;
    const u8* bg = fd2_resources_get(&res, FD2_DAT_FDOTHER, 101, &bg_size);
    printf("\nResource #101: size=%u\n", bg_size);
    if (bg && bg_size >= 4) {
        printf("  First 4 bytes: %02x %02x %02x %02x\n", bg[0], bg[1], bg[2], bg[3]);
        printf("  As 16-bit: w=%u, h=%u\n", bg[0] | (bg[1] << 8), bg[2] | (bg[3] << 8));
    }

    /* Check resource #73, #74 (title screen) */
    printf("\nTitle screen resources:\n");
    for (int i = 73; i <= 74; i++) {
        u32 size;
        const u8* data = fd2_resources_get(&res, FD2_DAT_FDOTHER, i, &size);
        printf("  Resource #%d: size=%u\n", i, size);
        if (data && size >= 4) {
            printf("    Header: %02x %02x %02x %02x\n", data[0], data[1], data[2], data[3]);
            printf("    W=%u, H=%u\n", data[0] | (data[1] << 8), data[2] | (data[3] << 8));
        }
    }

    /* Test decompression of resource #1 */
    printf("\n=== Testing RLE Decompression ===\n");
    u32 test_size;
    const u8* test_res = fd2_resources_get(&res, FD2_DAT_FDOTHER, 1, &test_size);
    if (test_res) {
        u8* pixels = NULL;
        int w, h;
        int ret = fd2_rle_decompress_from_resource(test_res, test_size, &pixels, &w, &h);
        if (ret == 0) {
            printf("Resource #1: decompressed to %dx%d\n", w, h);
            free(pixels);
        } else {
            printf("Resource #1: decompression FAILED (ret=%d)\n", ret);
        }
    }

    // fd2_resources_destroy(&res);
    return 0;
}
