/* test_decode_res19_5x5.c - 测试 fd2_rle_decode_char_grid_5x5 函数
 *
 * 用法: test_decode_res19_5x5 <FDOTHER.DAT> <resource_idx>
 *   resource_idx: 资源索引(默认 19)
 *
 * 输出:
 *   res<idx>_5x5_16x16_c.ppm - 5x5 字符位图 PPM 图像
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/fd2_rle.h"

#pragma pack(push, 1)
typedef struct {
    int start;
    int size;
} FdotherEntry;
#pragma pack(pop)

int main(int argc, char* argv[]) {
    const char* dat_path = (argc >= 2) ? argv[1] : "d:/workspace/fd2ida/FD2/FDOTHER.DAT";
    int res_idx = (argc >= 3) ? atoi(argv[2]) : 19;
    int char_w = 16, char_h = 16;  /* 资源 19 实际字符尺寸 */

    /* 读取FDOTHER.DAT */
    FILE* fp = fopen(dat_path, "rb");
    if (!fp) {
        fprintf(stderr, "无法打开: %s\n", dat_path);
        return 1;
    }
    fseek(fp, 0, SEEK_END);
    long dat_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    unsigned char* dat = (unsigned char*)malloc(dat_size);
    fread(dat, 1, dat_size, fp);
    fclose(fp);

    /* 验证魔数 */
    if (dat_size < 6 || memcmp(dat, "LLLLLL", 6) != 0) {
        fprintf(stderr, "魔数错误\n");
        free(dat);
        return 1;
    }

    /* 读取资源表 */
    int num_entries = (dat_size - 6) / 8;
    if (res_idx < 0 || res_idx >= num_entries) {
        fprintf(stderr, "资源索引 %d 超出范围 [0, %d)\n", res_idx, num_entries);
        free(dat);
        return 1;
    }
    FdotherEntry* entries = (FdotherEntry*)(dat + 6);
    int start = entries[res_idx].start;
    int size = entries[res_idx].size;
    printf("资源 %d: start=0x%x, size=0x%x (%d 字节)\n", res_idx, start, size, size);

    const unsigned char* res = dat + start;
    if (start + size > dat_size) {
        fprintf(stderr, "资源范围超出文件\n");
        free(dat);
        return 1;
    }

    /* 头部信息 */
    int w = res[0] | (res[1] << 8);
    int h = res[2] | (res[3] << 8);
    printf("头部: w=%d, h=%d\n", w, h);

    /* 5 行偏移表 */
    int row_offsets[5];
    for (int j = 0; j < 5; j++) {
        int o = 8 + j * 4;
        row_offsets[j] = res[o] | (res[o+1] << 8) | (res[o+2] << 16) | (res[o+3] << 24);
        printf("  行 %d 偏移: 0x%x\n", j, row_offsets[j]);
    }

    /* 解码 */
    int grid_w = 5 * char_w;
    int grid_h = 5 * char_h;
    unsigned char* canvas = (unsigned char*)calloc(grid_w * grid_h, 1);

    int ret = fd2_rle_decode_char_grid_5x5(res, size, canvas, char_w, char_h);
    printf("解码结果: %d (%s)\n", ret, ret == 0 ? "成功" : "失败");

    if (ret != 0) {
        /* 详细调试: 尝试手动解码,定位错误 */
        printf("\n--- 详细调试 ---\n");
        for (int row = 0; row < 5; row++) {
            int row_start = row_offsets[row];
            int row_end = (row < 4) ? row_offsets[row+1] : size;
            if (row_start > row_end) {
                printf("行 %d: 偏移错误 (0x%x > 0x%x)\n", row, row_start, row_end);
                continue;
            }
            int si = row_start;
            for (int col = 0; col < 5; col++) {
                if (si >= row_end) {
                    printf("  字符 (%d,%d): 行结束 at 0x%x\n", row, col, si);
                    break;
                }
                int local_si = 0;
                int local_size = row_end - si;
                int err_y = -1, err_x = -1;
                int err_code = 0;  /* 0=ok, 1=src, 2=fill, 3=alt, 4=copy */
                for (int y = 0; y < char_h; y++) {
                    int x = 0;
                    while (x < char_w) {
                        if (local_si >= local_size) {
                            err_y = y; err_x = x; err_code = 1;
                            goto err_done;
                        }
                        unsigned char ctrl = res[si + local_si];
                        local_si++;
                        int count = (((ctrl * 4) & 0xFF) >> 2) + 1;
                        unsigned char top2 = ctrl & 0xC0;
                        if (top2 == 0x00) {
                            if (local_si >= local_size) {
                                err_y = y; err_x = x; err_code = 2;
                                goto err_done;
                            }
                            local_si++;
                            x += count;
                        } else if (top2 == 0x40) {
                            if (local_si >= local_size) {
                                err_y = y; err_x = x; err_code = 3;
                                goto err_done;
                            }
                            local_si++;
                            x += count * 2;
                        } else if (top2 == 0x80) {
                            for (int k = 0; k < count; k++) {
                                if (local_si >= local_size) {
                                    err_y = y; err_x = x; err_code = 4;
                                    goto err_done;
                                }
                                local_si++;
                            }
                            x += count;
                        } else {
                            x += count;
                        }
                    }
                }
                err_done:
                if (err_code == 0) {
                    printf("  字符 (%d,%d) si=0x%x: ok, 消耗 %d 字节\n",
                           row, col, si, local_si);
                    si += local_si;
                } else {
                    const char* names[] = {"ok", "src_overflow", "fill_overflow", "alt_overflow", "copy_overflow"};
                    printf("  字符 (%d,%d) si=0x%x: ❌ %s at (%d,%d), 消耗 %d 字节\n",
                           row, col, si, names[err_code], err_x, err_y, local_si);
                    break;
                }
            }
        }
    }

    if (ret == 0) {
        /* 输出 PPM */
        char ppm_path[256];
        sprintf(ppm_path, "res%d_5x5_%dx%d_c.ppm", res_idx, char_w, char_h);
        FILE* fout = fopen(ppm_path, "wb");
        if (fout) {
            fprintf(fout, "P6\n%d %d\n255\n", grid_w, grid_h);
            for (int y = 0; y < grid_h; y++) {
                for (int x = 0; x < grid_w; x++) {
                    int v = canvas[y * grid_w + x];
                    int r = v & 0x3F;
                    int g = v & 0x3F;
                    int b = v & 0x3F;
                    unsigned char rgb[3] = { (unsigned char)(r*4), (unsigned char)(g*4), (unsigned char)(b*4) };
                    fwrite(rgb, 1, 3, fout);
                }
            }
            fclose(fout);
            printf("输出 PPM: %s\n", ppm_path);
        }

        /* 打印像素值统计 */
        int non_zero = 0;
        int max_v = 0;
        for (int i = 0; i < grid_w * grid_h; i++) {
            if (canvas[i]) non_zero++;
            if (canvas[i] > max_v) max_v = canvas[i];
        }
        printf("像素统计: %d/%d 非零, 最大值 %d\n", non_zero, grid_w * grid_h, max_v);
    }

    free(canvas);
    free(dat);
    return ret;
}
