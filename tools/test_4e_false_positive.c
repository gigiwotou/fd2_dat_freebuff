/* 测试 4e RLE 解码对未压缩数据的"误判"问题
 * 4e RLE 模式: 0x00-0x3F FILL count=(b&0x3F)+1, 0x40-0x7F ALT, 0x80-0xBF COPY, 0xC0-0xFF SKIP
 * tile 10 数据 0x63 控制字节 -> count=36, FILL 36 像素
 * 两个控制字节就能覆盖 48 像素, 错误地"成功"
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

    /* 索引5 */
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

    int test_tiles[] = {10, 14, 16, 18, 19, 55, 60};
    int nt = sizeof(test_tiles) / sizeof(test_tiles[0]);

    printf("=== 4e RLE false-positive test on uncompressed tiles ===\n");
    printf("%-3s %-4s %-4s %-5s  %-7s %-7s %-7s\n", "idx", "w", "h", "size", "4e", "uncomp", "same?");
    for (int i = 0; i < nt; i++) {
        int ti = test_tiles[i];
        dword off = tile_offsets[ti];
        dword next = tile_offsets[ti + 1];
        dword size = next - off;
        const byte* src = res5 + off;
        word w, h;
        memcpy(&w, src, 2);
        memcpy(&h, src + 2, 2);
        int total = (int)w * (int)h;

        byte* buf_4e = (byte*)calloc(1, total);
        byte* buf_uncomp = (byte*)calloc(1, total);
        int ow, oh;

        int r_4e = fd2_rle_lmi1_decode_tile_4e(src, size, buf_4e, &ow, &oh);
        int r_uncomp = -1;
        if (size >= 4 + total) {
            r_uncomp = fd2_rle_lmi1_decode_tile(src, 4 + total, buf_uncomp, &ow, &oh);
        }

        int same = 0;
        if (r_4e == 0 && r_uncomp == 0) {
            same = 1;
            for (int j = 0; j < total; j++) {
                if (buf_4e[j] != buf_uncomp[j]) { same = 0; break; }
            }
        }

        printf("%-3d %-4d %-4d %-5d  %-7s %-7s %s\n",
               ti, w, h, size,
               r_4e == 0 ? "OK" : "fail",
               r_uncomp == 0 ? "OK" : "fail",
               same ? "SAME" : "DIFF!");
        free(buf_4e); free(buf_uncomp);
    }
    free(data);
    return 0;
}
