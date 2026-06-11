/*
 * 对比Python和C版本的sub_4E22A解码结果
 * 使用Python的解码结果作为参考，验证C实现
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

typedef uint8_t byte;
typedef uint16_t word;
typedef uint32_t dword;

extern int fd_decompress_sub_4E22A(const byte *src, int src_size, byte *dst, int width, int height, int pitch);

int main() {
    const char* path = "d:\\workspace\\fd2_dat_freebuff\\game\\FDOTHER.DAT";

    FILE* f = fopen(path, "rb");
    if (!f) {
        printf("Cannot open FDOTHER.DAT\n");
        return 1;
    }

    fseek(f, 0, SEEK_END);
    long file_size = ftell(f);
    fseek(f, 0, SEEK_SET);

    byte* data = (byte*)malloc(file_size);
    fread(data, 1, file_size, f);
    fclose(f);

    // 解析偏移表
    dword offsets[200];
    int res_count = 0;
    int pos = 6;
    while (pos + 4 <= file_size && res_count < 200) {
        dword off = *(dword*)(data + pos);
        if (off == 0 || off > (dword)file_size) break;
        offsets[res_count++] = off;
        pos += 4;
    }
    offsets[res_count] = (dword)file_size;

    // 索引1
    dword idx1_start = offsets[1];
    dword idx1_end = offsets[2];
    int idx1_size = idx1_end - idx1_start;
    byte* idx1_data = data + idx1_start;

    // 头部
    word w = idx1_data[0] | (idx1_data[1] << 8);
    word h = idx1_data[2] | (idx1_data[3] << 8);
    byte palette_window = idx1_data[4];
    word icon_count_header = idx1_data[4] | (idx1_data[5] << 8);

    printf("Index 1: %dx%d, palette_window=%d, icon_count=%d\n", w, h, palette_window, icon_count_header);
    printf("Width expected: 24, Height expected: 24\n");

    // 解析图标偏移
    dword icon_offsets[50];
    int icon_count = 0;
    pos = 6;
    while (pos + 4 <= idx1_size && icon_count < 50) {
        dword off = idx1_data[pos] | (idx1_data[pos+1] << 8) | (idx1_data[pos+2] << 16) | (idx1_data[pos+3] << 24);
        if (off == 0 || off > (dword)idx1_size) break;
        icon_offsets[icon_count++] = off;
        pos += 4;
    }
    printf("Number of icons: %d\n\n", icon_count);

    // 对每个图标进行解码并显示
    for (int i = 0; i < icon_count; i++) {
        dword icon_start = icon_offsets[i];
        dword icon_end = (i+1 < icon_count) ? icon_offsets[i+1] : idx1_size;
        int icon_size = icon_end - icon_start;
        byte* icon_data = idx1_data + icon_start;

        byte* decoded = (byte*)malloc(24 * 24);
        memset(decoded, 0, 24 * 24);

        int ret = fd_decompress_sub_4E22A(icon_data, icon_size, decoded, 24, 24, 24);

        // 统计非0像素
        int non_zero = 0;
        for (int p = 0; p < 24*24; p++) if (decoded[p] != 0) non_zero++;

        printf("=== 图标 %d (size=%d, ret=%d, 非0像素=%d) ===\n", i, icon_size, ret, non_zero);
        for (int row = 0; row < 24; row++) {
            printf("  |");
            for (int col = 0; col < 24; col++) {
                byte v = decoded[row * 24 + col];
                if (v == 0) printf(" ");
                else if (v < 16) printf(".");
                else if (v < 32) printf(":");
                else if (v < 64) printf("o");
                else if (v < 128) printf("O");
                else if (v < 192) printf("#");
                else printf("@");
            }
            printf("|\n");
        }
        printf("\n");

        free(decoded);
    }

    free(data);
    return 0;
}
