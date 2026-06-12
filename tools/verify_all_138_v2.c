/* 全 138 个 tile 测试 - 确保修复后所有 tile 都正确解码
 * 输出每个 tile 的 (idx, w, h, size, decode_method)
 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../include/fd2_types.h"
#include "../include/fd2_rle.h"

int main(int argc, char** argv) {
    const char* path = "D:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT";
    FILE* f = fopen(path, "rb");
    if (!f) { printf("Cannot open\n"); return 1; }
    fseek(f, 0, SEEK_END);
    long file_size = ftell(f);
    fseek(f, 0, SEEK_SET);
    byte* data = (byte*)malloc(file_size);
    fread(data, 1, file_size, f);
    fclose(f);

    dword idx5_offset;
    memcpy(&idx5_offset, data + 6 + 5 * 4, 4);
    int table_idx = 6 + 5 * 4 + 4;
    dword next_off = 0;
    while (table_idx + 4 <= file_size) {
        memcpy(&next_off, data + table_idx, 4);
        if (next_off == 0 || next_off > file_size) break;
        table_idx += 4;
    }
    memcpy(&next_off, data + table_idx, 4);
    byte* res5 = data + idx5_offset;

    word tile_count;
    memcpy(&tile_count, res5 + 4, 2);
    dword* tile_offsets = (dword*)(res5 + 6);

    int ok = 0, fail = 0;
    int method_rle = 0, method_4e = 0, method_uncomp = 0;
    printf("idx  w    h    size   method\n");
    for (int ti = 0; ti < tile_count; ti++) {
        dword off = tile_offsets[ti];
        dword next = tile_offsets[ti + 1];
        dword size = next - off;
        const byte* src = res5 + off;
        if (off + 4 > (dword)file_size) {
            printf("%-3d  ERR (off %u > %ld)\n", ti, off, file_size);
            fail++;
            continue;
        }
        word w, h;
        memcpy(&w, src, 2);
        memcpy(&h, src + 2, 2);
        if (w == 0 || h == 0 || w > 1024 || h > 1024) {
            printf("%-3d  ERR (bad header w=%d h=%d)\n", ti, w, h);
            fail++;
            continue;
        }
        int total = (int)w * (int)h;
        byte* buf = (byte*)calloc(1, total);
        int ow, oh;

        /* 模拟 auto: 1) sub4ebff, 2) 4e, 3) uncomp */
        const char* method = "FAIL";
        int r = fd2_rle_lmi1_decode_tile_rle(src, size, buf, &ow, &oh);
        if (r == 0) { method = "rle"; method_rle++; ok++; }
        else {
            r = fd2_rle_lmi1_decode_tile_4e(src, size, buf, &ow, &oh);
            if (r == 0) { method = "4e"; method_4e++; ok++; }
            else if (size >= 4 + total) {
                r = fd2_rle_lmi1_decode_tile(src, 4 + total, buf, &ow, &oh);
                if (r == 0) { method = "uncomp"; method_uncomp++; ok++; }
                else { fail++; method = "ALL_FAIL"; }
            } else { fail++; method = "ALL_FAIL"; }
        }

        if (ti < 30 || ti >= tile_count - 5 || (ti >= 55 && ti <= 65) ||
            ti == 10 || ti == 14 || ti == 16 || ti == 18 || ti == 19) {
            printf("%-3d  %-4d %-4d %-5d %s\n", ti, w, h, size, method);
        }
        free(buf);
    }
    printf("\n=== Summary ===\n");
    printf("Total: %d, OK: %d, FAIL: %d\n", tile_count, ok, fail);
    printf("Methods: rle=%d, 4e=%d, uncomp=%d\n", method_rle, method_4e, method_uncomp);
    free(data);
    return fail > 0 ? 1 : 0;
}
