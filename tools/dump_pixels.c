/* 测试 tile 10, 14, 16, 18, 19, 55-63 实际解码结果
 * 对比三种解码方法的输出:
 * 1. sub4ebff (RLE)
 * 2. 4e (RLE)
 * 3. uncomp (raw)
 * 输出像素前 16 字节到 output
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

    printf("=== tile 解码像素对比 (uncomp vs sub4ebff vs 4e) ===\n");

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

        printf("\n--- Tile %d (%dx%d, size=%d, total=%d) ---\n", ti, w, h, size, total);
        printf("rle=%d, 4e=%d, uncomp=%d\n", r_rle, r_4e, r_uncomp);

        /* 打印前 16 字节像素 */
        int dump = total < 16 ? total : 16;
        printf("uncomp: ");
        for (int j = 0; j < dump; j++) printf("%02x ", buf_uncomp[j]);
        printf("\n");
        printf("4e:     ");
        for (int j = 0; j < dump; j++) printf("%02x ", buf_4e[j]);
        printf("\n");
        printf("rle:    ");
        for (int j = 0; j < dump; j++) printf("%02x ", buf_rle[j]);
        printf("\n");
        printf("src[4:20]: ");
        for (int j = 0; j < 16 && j+4 < size; j++) printf("%02x ", src[j+4]);
        printf("\n");

        free(buf_rle); free(buf_4e); free(buf_uncomp);
    }
    free(data);
    return 0;
}
