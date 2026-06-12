/* 测试 tile 10, 14, 16, 18, 19, 55-63 实际解码结果
 * 对比三种解码方法的输出:
 * 1. sub4ebff (RLE)
 * 2. 4e (RLE)
 * 3. uncomp (raw)
 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../include/fd2_types.h"
#include "../include/fd2_rle.h"

int main(int argc, char** argv) {
    const char* path = "D:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT";
    FILE* f = fopen(path, "rb");
    if (!f) { printf("Cannot open %s\n", path); return 1; }
    fseek(f, 0, SEEK_END);
    long file_size = ftell(f);
    fseek(f, 0, SEEK_SET);
    byte* data = (byte*)malloc(file_size);
    fread(data, 1, file_size, f);
    fclose(f);

    /* 索引5偏移 */
    dword idx5_offset;
    memcpy(&idx5_offset, data + 6 + 5 * 4, 4);
    /* 找结尾 */
    int table_idx = 6 + 5 * 4 + 4;
    dword next_off = 0;
    while (table_idx + 4 <= file_size) {
        memcpy(&next_off, data + table_idx, 4);
        if (next_off == 0 || next_off > file_size) break;
        table_idx += 4;
    }
    memcpy(&next_off, data + table_idx, 4);
    byte* res5 = data + idx5_offset;
    dword res5_size = next_off - idx5_offset;

    word tile_count;
    memcpy(&tile_count, res5 + 4, 2);
    dword* tile_offsets = (dword*)(res5 + 6);

    int test_tiles[] = {10, 14, 16, 18, 19, 55, 56, 57, 58, 59, 60, 61, 62, 63};
    int nt = sizeof(test_tiles) / sizeof(test_tiles[0]);

    printf("=== tile 解码对比 (uncomp / sub4ebff / 4e) ===\n");
    printf("%-3s %-4s %-4s %-5s  %-7s %-7s %-7s %s\n",
           "idx", "w", "h", "size",
           "rle", "4e", "uncomp", "first_data");

    for (int i = 0; i < nt; i++) {
        int ti = test_tiles[i];
        dword off = tile_offsets[ti];
        dword next = tile_offsets[ti + 1];
        dword size = next - off;
        const byte* src = res5 + off;

        word w, h;
        memcpy(&w, src, 2);
        memcpy(&h, src + 2, 2);

        /* 分配三个解码buffer */
        int total = (int)w * (int)h;
        byte* buf_rle = (byte*)calloc(1, total);
        byte* buf_4e = (byte*)calloc(1, total);
        byte* buf_uncomp = (byte*)calloc(1, total);

        int ow, oh;
        int r_rle = fd2_rle_lmi1_decode_tile_rle(src, size, buf_rle, &ow, &oh);
        int r_4e = fd2_rle_lmi1_decode_tile_4e(src, size, buf_4e, &ow, &oh);
        int r_uncomp = -1;
        if (size >= 4 + total) {
            r_uncomp = fd2_rle_lmi1_decode_tile(src, 4 + total, buf_uncomp, &ow, &oh);
        }

        /* 对比 rle 和 uncomp */
        int same = 1;
        if (r_rle == 0 && r_uncomp == 0) {
            for (int j = 0; j < total; j++) {
                if (buf_rle[j] != buf_uncomp[j]) { same = 0; break; }
            }
        }

        printf("%-3d %-4d %-4d %-5d  %-7s %-7s %-7s %s%s\n",
               ti, w, h, size,
               r_rle == 0 ? "OK" : "fail",
               r_4e == 0 ? "OK" : "fail",
               r_uncomp == 0 ? "OK" : "fail",
               (r_rle == 0 && r_uncomp == 0) ? (same ? "[SAME]" : "[DIFF!]") : "",
               "");

        free(buf_rle); free(buf_4e); free(buf_uncomp);
    }
    free(data);
    return 0;
}
