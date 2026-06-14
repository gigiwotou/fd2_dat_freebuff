/* analyze_resource3.c - 分析资源3实际是什么类型 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../include/fd2_types.h"
#include "../include/fd2_rle.h"
#include "../include/fd2_fdother_resources.h"
#include "../include/fd2_dat.h"

int main(int argc, char** argv) {
    if (fdother_load("d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT") != 0) {
        printf("Cannot load\n");
        return 1;
    }

    /* 检查资源3的原始数据 */
    dword size;
    const byte* data = fdother_get_resource(3, &size);
    if (!data || size == 0) {
        printf("Resource 3 not found\n");
        return 1;
    }
    printf("Resource 3 size: %u bytes\n", size);
    printf("First 64 bytes:\n");
    for (int i = 0; i < 64 && i < (int)size; i++) {
        printf("%02x ", data[i]);
        if ((i + 1) % 16 == 0) printf("\n");
    }
    printf("\n");

    /* 检查魔数 */
    if (size >= 4 && memcmp(data, "LMI1", 4) == 0) {
        printf("Magic: LMI1 (LMI1 Tile集)\n");
        word tile_count = data[4] | (data[5] << 8);
        printf("Tile count: %u\n", tile_count);
    }
    if (size >= 6 && memcmp(data, "LLLLLL", 6) == 0) {
        printf("Magic: LLLLLL (Nested DAT)\n");
        dword count = *(dword*)(data + 6);
        printf("Resource count: %u\n", count);
    }

    /* 类型判断 */
    fdother_res_type_t type = fdother_get_resource_type(data, size);
    printf("Detected type: %d\n", type);

    /* 也分析资源0确认 */
    printf("\n=== Resource 0 ===\n");
    data = fdother_get_resource(0, &size);
    if (data && size > 0) {
        printf("Size: %u\n", size);
        printf("First 16 bytes: ");
        for (int i = 0; i < 16 && i < (int)size; i++) printf("%02x ", data[i]);
        printf("\n");
    }

    /* 列出所有资源类型 */
    printf("\n=== 所有资源类型 ===\n");
    int count = fdother_get_resource_count();
    for (int i = 0; i < count; i++) {
        data = fdother_get_resource(i, &size);
        if (!data) continue;
        fdother_res_type_t t = fdother_get_resource_type(data, size);
        const char* tname = "?";
        switch (t) {
            case FDOTHER_RES_TYPE_PALETTE: tname = "PALETTE"; break;
            case FDOTHER_RES_TYPE_TILE: tname = "TILE"; break;
            case FDOTHER_RES_TYPE_LMI1: tname = "LMI1"; break;
            case FDOTHER_RES_TYPE_NESTED_DAT: tname = "NESTED_DAT"; break;
            case FDOTHER_RES_TYPE_RAW: tname = "RAW"; break;
        }
        printf("  Res %3d: %-10s size=%u\n", i, tname, size);
    }

    fdother_unload();
    return 0;
}
