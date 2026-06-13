/* 检查索引1的调色板应用情况
 * 索引1 实际数据: header=6字节
 *   [0-1] width=312
 *   [2-3] height=0
 *   [4] palette_window=28
 *   [5] padding
 *   [6+] 4字节偏移表 -> RLE数据
 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../include/fd2_types.h"
#include "../include/fd2_rle.h"
#include "../include/fd2_fdother_resources.h"
#include "../include/fd2_dat.h"

int main(int argc, char** argv) {
    const char* path = "D:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT";
    FILE* f = fopen(path, "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long file_size = ftell(f);
    fseek(f, 0, SEEK_SET);
    byte* data = (byte*)malloc(file_size);
    fread(data, 1, file_size, f);
    fclose(f);

    /* 加载主调色板 (索引0) */
    if (fdother_load(path) != 0) {
        printf("Cannot load FDOTHER.DAT\n");
        return 1;
    }
    fdother_palette_t main_pal;
    int pal_ret = fdother_get_palette(0, &main_pal);
    if (pal_ret != 0) {
        printf("Cannot load palette\n");
        return 1;
    }
    /* 转为 8bit RGB */
    byte rgb24[768];
    fdother_palette_to_rgb24(&main_pal, rgb24);

    /* 索引1 资源 */
    dword idx1_offset;
    memcpy(&idx1_offset, data + 6 + 1 * 4, 4);
    int table_idx = 6 + 1 * 4 + 4;
    dword next_off = 0;
    while (table_idx + 4 <= file_size) {
        memcpy(&next_off, data + table_idx, 4);
        if (next_off == 0 || next_off > file_size) break;
        table_idx += 4;
    }
    memcpy(&next_off, data + table_idx, 4);
    dword idx1_size = next_off - idx1_offset;
    byte* res1 = data + idx1_offset;
    printf("Index 1: offset=%u, size=%u\n", idx1_offset, idx1_size);
    printf("Header bytes: ");
    for (int i = 0; i < 10; i++) printf("%02x ", res1[i]);
    printf("\n");
    printf("width=%d, height=%d, palette_window=%d, padding=%d\n",
           res1[0] | (res1[1] << 8),
           res1[2] | (res1[3] << 8),
           res1[4], res1[5]);

    /* 偏移表 */
    int num_icons = (idx1_size - 6) / 4;
    printf("Number of icons (estimated): %d\n", num_icons);

    dword* offsets = (dword*)(res1 + 6);

    /* 解码第一个图标 */
    dword off0 = offsets[0];
    dword off1 = offsets[1];
    dword icon_size = off1 - off0;
    printf("\nIcon 0: offset=%u, size=%u\n", off0, icon_size);
    printf("First 32 bytes: ");
    for (int i = 0; i < 32 && i < (int)icon_size; i++) printf("%02x ", res1[off0 + i]);
    printf("\n");

    /* 解码 */
    byte* buf = (byte*)calloc(1, 24 * 24);
    int r = fd_decompress_sub_4E22A(res1 + off0, icon_size, buf, 24, 24, 24);
    printf("Decompress result: %d\n", r);

    /* 输出像素值（按调色板索引和 RGB） */
    printf("\nIcon 0 pixels (idx + rgb) [WITHOUT window offset]:\n");
    for (int y = 0; y < 24; y++) {
        for (int x = 0; x < 24; x++) {
            int idx = buf[y * 24 + x];
            int r_val = (idx == 0) ? 0 : rgb24[idx * 3 + 0];
            int g_val = (idx == 0) ? 0 : rgb24[idx * 3 + 1];
            int b_val = (idx == 0) ? 0 : rgb24[idx * 3 + 2];
            printf("(%02x:%3d,%3d,%3d) ", idx, r_val, g_val, b_val);
        }
        printf("\n");
    }
    printf("\n--- Only non-zero pixels ---\n");
    for (int y = 0; y < 24; y++) {
        for (int x = 0; x < 24; x++) {
            int idx = buf[y * 24 + x];
            if (idx != 0) {
                int r_val = rgb24[idx * 3 + 0];
                int g_val = rgb24[idx * 3 + 1];
                int b_val = rgb24[idx * 3 + 2];
                printf("(y=%d,x=%d) %02x: %3d,%3d,%3d\n", y, x, idx, r_val, g_val, b_val);
            }
        }
    }

    /* 列出调色板中偏移前 64 色的内容 */
    printf("\nMain palette colors 0-63:\n");
    for (int i = 0; i < 64; i++) {
        int r6 = main_pal.colors[i*3];
        int g6 = main_pal.colors[i*3+1];
        int b6 = main_pal.colors[i*3+2];
        int r8 = r6 << 2 | (r6 >> 4);
        int g8 = g6 << 2 | (g6 >> 4);
        int b8 = b6 << 2 | (b6 >> 4);
        printf("%2d: %3d,%3d,%3d (6bit: %2d,%2d,%2d)\n", i, r8, g8, b8, r6, g6, b6);
    }

    /* 列出调色板 60-220 范围 */
    printf("\nMain palette colors 60-220:\n");
    for (int i = 60; i <= 220; i++) {
        int r6 = main_pal.colors[i*3];
        int g6 = main_pal.colors[i*3+1];
        int b6 = main_pal.colors[i*3+2];
        int r8 = r6 << 2 | (r6 >> 4);
        int g8 = g6 << 2 | (g6 >> 4);
        int b8 = b6 << 2 | (b6 >> 4);
        printf("%3d: %3d,%3d,%3d (6bit: %2d,%2d,%2d)\n", i, r8, g8, b8, r6, g6, b6);
    }
    free(buf);
    free(data);
    return 0;
}
