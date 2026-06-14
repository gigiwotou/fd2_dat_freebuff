/* test_viewer_res7_dump.c - 模拟 viewer 资源7的关键处理路径
 *
 * 这个测试直接复刻 viewer.c 中 NESTED_DAT 分支的逻辑(从 line 603 到 668),
 * 不启动 SDL 窗口, 直接把渲染前的解码数据 dump 到 output/ 目录的 PNG 文件.
 *
 * 目的: 在不改 GUI 程序的情况下验证 viewer 修复后能正确解析资源7.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "fd2_types.h"
#include "fd2_fdother_resources.h"
#include "fd2_rle.h"

/* viewer 中的辅助函数 (1:1 复制) */
static int fdother_nested_calculate_valid_count(const byte* data, dword size, dword declared_count) {
    if (!data || size < 10 || memcmp(data, "LLLLLL", 6) != 0) {
        return 0;
    }
    dword offset_table_end = 10 + declared_count * 4;
    int valid_count = 0;
    for (dword j = 0; j < declared_count; j++) {
        if (10 + j * 4 + 4 > size) break;
        dword off = data[10 + j * 4] |
                    (data[10 + j * 4 + 1] << 8) |
                    (data[10 + j * 4 + 2] << 16) |
                    (data[10 + j * 4 + 3] << 24);
        if (off < offset_table_end || off > size) {
            break;
        }
        valid_count++;
    }
    if (valid_count > 0) {
        dword last_off = data[10 + (valid_count - 1) * 4] |
                         (data[10 + (valid_count - 1) * 4 + 1] << 8) |
                         (data[10 + (valid_count - 1) * 4 + 2] << 16) |
                         (data[10 + (valid_count - 1) * 4 + 3] << 24);
        if (last_off == size && valid_count > 1) {
            valid_count--;
        }
    }
    return valid_count;
}

/* viewer 实际调用的解码流程 */
static int decode_res7_sub(int sub_idx, int* out_w, int* out_h, byte* decode_buf) {
    dword res_size;
    const byte* res_data = fdother_get_resource(7, &res_size);
    if (!res_data) return -1;

    dword declared_count = (dword)(res_data[6] | (res_data[7] << 8) |
                                    (res_data[8] << 16) | (res_data[9] << 24));
    int valid_count = fdother_nested_calculate_valid_count(res_data, res_size, declared_count);
    if (sub_idx < 0 || sub_idx >= valid_count) return -1;

    dword offset_addr = 10 + sub_idx * 4;
    dword sub_offset = res_data[offset_addr] |
                       (res_data[offset_addr + 1] << 8) |
                       (res_data[offset_addr + 2] << 16) |
                       (res_data[offset_addr + 3] << 24);

    dword sub_end;
    if (sub_idx + 1 < valid_count) {
        dword next_addr = 10 + (sub_idx + 1) * 4;
        sub_end = res_data[next_addr] |
                  (res_data[next_addr + 1] << 8) |
                  (res_data[next_addr + 2] << 16) |
                  (res_data[next_addr + 3] << 24);
    } else {
        sub_end = res_size;
    }
    if (sub_offset >= res_size || sub_end > res_size || sub_end <= sub_offset) return -1;

    dword sub_size = sub_end - sub_offset;
    const byte* sub_data = res_data + sub_offset;

    if (sub_size < 4) return -1;

    int ret = fd2_rle_lmi1_decode_tile_auto(sub_data, (int)sub_size, decode_buf, out_w, out_h, 0);
    return ret;
}

int main(int argc, char* argv[]) {
    const char* filepath = "game/FDOTHER.DAT";
    if (argc > 1) filepath = argv[1];

    int ret = fdother_load(filepath);
    if (ret != 0) {
        printf("Failed to load %s\n", filepath);
        return 1;
    }

    /* 加载调色板 */
    fdother_palette_t pal;
    if (fdother_get_palette(0, &pal) != 0) {
        printf("Failed to load palette\n");
        return 1;
    }
    byte palette_rgb24[768];
    fdother_palette_to_rgb24(&pal, palette_rgb24);

    /* 验证所有有效子资源 */
    dword res_size;
    const byte* res_data = fdother_get_resource(7, &res_size);
    dword declared = (dword)(res_data[6] | (res_data[7] << 8) |
                             (res_data[8] << 16) | (res_data[9] << 24));
    int valid = fdother_nested_calculate_valid_count(res_data, res_size, declared);

    printf("Viewer Res 7: declared=%u, valid=%d\n", declared, valid);
    printf("--- Decode Each Sub (viewer logic) ---\n");

    for (int i = 0; i < valid; i++) {
        int w = 0, h = 0;
        byte buf[256 * 256];
        int r = decode_res7_sub(i, &w, &h, buf);
        if (r == 0) {
            /* 写到 PPM 文件以便查看 */
            char fname[64];
            sprintf(fname, "output/res7_sub%d_%dx%d.ppm", i, w, h);
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
                printf("Sub %d: %dx%d OK -> %s\n", i, w, h, fname);
            }
        } else {
            printf("Sub %d: FAIL (ret=%d)\n", i, r);
        }
    }

    fdother_unload();
    return 0;
}
