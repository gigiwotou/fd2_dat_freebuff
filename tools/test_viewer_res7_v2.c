/* test_viewer_res7_v2.c - 1:1 复刻 viewer 新的 NESTED_DAT 处理
 * 偏移表从 +6 开始, 4 字节头 (w, h) + RLE 数据, 用 fd2_rle_decompress
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "fd2_types.h"
#include "fd2_fdother_resources.h"
#include "fd2_decoder.h"

int main(int argc, char* argv[]) {
    const char* filepath = "game/FDOTHER.DAT";
    if (argc > 1) filepath = argv[1];

    if (fdother_load(filepath) != 0) {
        printf("Failed to load %s\n", filepath);
        return 1;
    }

    /* 加载调色板 - 资源7用菜单调色板(索引8), 其他用主调色板(索引0)
     * 1:1 复刻 fd2_opening_animation.c sub_1F894: FDOTHER_DAT=8 */
    fdother_palette_t pal;
    int pal_idx = 7;  /* 资源 7 用调色板 8 */
    if (fdother_get_palette(pal_idx, &pal) != 0) {
        if (fdother_get_palette(0, &pal) != 0) {
            printf("Failed to load palette\n");
            return 1;
        }
    }
    byte palette_rgb24[768];
    fdother_palette_to_rgb24(&pal, palette_rgb24);

    dword res_size;
    const byte* res_data = fdother_get_resource(7, &res_size);
    if (!res_data) {
        printf("Resource 7 not found\n");
        return 1;
    }

    printf("Res 7 size=%u, magic=%.6s\n", res_size, res_data);

    /* 沿 sub_16886 公式计算 valid_count */
    int valid_count = 0;
    for (int i = 0; i < 64; i++) {
        if ((dword)(6 + i * 4) + 4 > res_size) break;
        dword sub_offset = res_data[6 + i * 4] |
                           (res_data[6 + i * 4 + 1] << 8) |
                           (res_data[6 + i * 4 + 2] << 16) |
                           (res_data[6 + i * 4 + 3] << 24);
        if (sub_offset >= res_size) break;
        valid_count++;
    }
    printf("Viewer Res 7: valid_count=%d\n", valid_count);

    /* 遍历所有子资源 (sub_index 0..6) */
    for (int i = 0; i < valid_count; i++) {
        dword sub_offset = res_data[6 + i * 4] |
                           (res_data[6 + i * 4 + 1] << 8) |
                           (res_data[6 + i * 4 + 2] << 16) |
                           (res_data[6 + i * 4 + 3] << 24);
        if (sub_offset >= res_size) {
            printf("Sub %d: offset=0x%04x OUT OF BOUNDS\n", i, sub_offset);
            continue;
        }
        const byte* sub_data = res_data + sub_offset;
        dword sub_size = res_size - sub_offset;

        if (sub_size < 4) {
            printf("Sub %d: sub_size<4\n", i);
            continue;
        }

        int w = sub_data[0] | (sub_data[1] << 8);
        int h = sub_data[2] | (sub_data[3] << 8);
        printf("Sub %d: offset=0x%04x, header w=%d, h=%d, sub_size=%u\n",
               i, sub_offset, w, h, sub_size);

        if (w > 0 && h > 0) {
            byte* buf = (byte*)calloc(1, (size_t)w * h);
            int ret = fd2_rle_decompress(sub_data + 4, sub_size - 4,
                                          buf, 0, 0, w, w, h, -1);
            if (ret == 0) {
                char fname[64];
                sprintf(fname, "output/res7v2_sub%d_%dx%d.ppm", i, w, h);
                FILE* f = fopen(fname, "wb");
                if (f) {
                    fprintf(f, "P6\n%d %d\n255\n", w, h);
                    for (int y = 0; y < h; y++) {
                        for (int x = 0; x < w; x++) {
                            byte idx = buf[y * w + x];
                            fputc(palette_rgb24[idx*3 + 0], f);
                            fputc(palette_rgb24[idx*3 + 1], f);
                            fputc(palette_rgb24[idx*3 + 2], f);
                        }
                    }
                    fclose(f);
                    printf("  -> OK -> %s\n", fname);
                }
            } else {
                printf("  -> FAIL ret=%d\n", ret);
            }
            free(buf);
        }
    }

    fdother_unload();
    return 0;
}
