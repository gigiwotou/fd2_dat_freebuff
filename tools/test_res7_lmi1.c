/* test_res7_lmi1.c - 验证 viewer 资源 7 (LLLL 嵌套) 的子资源格式 */
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

    /* viewer 资源 7 (LLLL 嵌套 DAT, 38 个子资源) */
    fdother_nested_dat_t nested;
    ret = fdother_get_nested_dat(7, &nested);
    if (ret != 0) {
        printf("Failed to parse nested DAT at index 7\n");
        return 1;
    }

    printf("Viewer Resource 7: NESTED DAT with %u sub-resources, size=%u\n\n",
           nested.resource_count, nested.size);

    /* 验证前 5 个子资源 */
    for (int i = 0; i < 5 && i < (int)nested.resource_count; i++) {
        dword sub_size;
        const byte* sub_data = fdother_nested_get_resource(&nested, i, &sub_size);

        printf("=== Sub %d (size=%u) ===\n", i, sub_size);
        printf("  First 16 bytes: ");
        for (int j = 0; j < 16 && j < (int)sub_size; j++) {
            printf("%02x ", sub_data[j]);
        }
        printf("\n");

        /* 4 字节头 w, h */
        word w = sub_data[0] | (sub_data[1] << 8);
        word h = sub_data[2] | (sub_data[3] << 8);
        printf("  4-byte w,h header: w=%d, h=%d, expected_pixels=%d\n", w, h, w*h);

        /* 试 LMI1 自动检测 */
        byte buf[256 * 256];
        int out_w, out_h;
        ret = fd2_rle_lmi1_decode_tile_auto(sub_data, (int)sub_size, buf, &out_w, &out_h, 0);
        if (ret == 0) {
            printf("  LMI1 auto decode: %dx%d (OK)\n", out_w, out_h);
        } else {
            printf("  LMI1 auto decode: FAILED (ret=%d)\n", ret);
        }
    }

    return 0;
}
