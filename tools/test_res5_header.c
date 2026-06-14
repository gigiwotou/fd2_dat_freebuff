/* test_res5_header.c - 详细打印 LMI1 头部字节 */
#include <stdio.h>
#include "fd2_types.h"
#include "fd2_fdother_resources.h"

int main(int argc, char* argv[]) {
    const char* filepath = "game/FDOTHER.DAT";
    if (argc > 1) filepath = argv[1];

    int ret = fdother_load(filepath);
    if (ret != 0) {
        printf("Failed to load %s\n", filepath);
        return 1;
    }

    for (int idx = 0; idx < 12; idx++) {
        dword size;
        const byte* data = fdother_get_resource(idx, &size);
        if (!data) {
            printf("Resource %d: NULL\n", idx);
            continue;
        }
        printf("Resource %d: size=%u (0x%x)\n", idx, size, size);
        printf("  First 16 bytes: ");
        for (int i = 0; i < 16 && i < (int)size; i++) {
            printf("%02x ", data[i]);
        }
        printf("\n");
        printf("  Magic: %.4s\n", data);
    }

    return 0;
}
