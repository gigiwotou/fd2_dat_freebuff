/* dump_res3_bytes.c - 详细看资源3的开头几个字节 */
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

    printf("res3 前 32 字节 (hex):\n");
    for (int i = 0; i < 32; i++) {
        printf("%02x ", data[i]);
        if ((i+1) % 16 == 0) printf("\n");
    }
    printf("\n");

    /* 验证 magic */
    if (data[0] == 'L' && data[1] == 'M' && data[2] == 'I' && data[3] == '1') {
        printf("魔数 LMI1: 正确\n");
    } else {
        printf("魔数: 错误 (data[0..3] = '%c%c%c%c' = 0x%02x 0x%02x 0x%02x 0x%02x)\n",
            data[0], data[1], data[2], data[3], data[0], data[1], data[2], data[3]);
    }

    word tile_count = data[4] | (data[5] << 8);
    printf("tile_count = %u\n", tile_count);

    /* 看第一个偏移 */
    dword off0 = data[6] | (data[7]<<8) | (data[8]<<16) | (data[9]<<24);
    printf("tile[0] 偏移 = 0x%x\n", off0);
    printf("tile[0] 处前 16 字节: ");
    for (int i = 0; i < 16; i++) printf("%02x ", data[off0+i]);
    printf("\n");

    fdother_unload();
    return 0;
}
