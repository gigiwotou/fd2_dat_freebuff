/* analyze_res12.c - 分析资源12的子项特征，找出汉字资源 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/fd2_types.h"

#pragma pack(push, 1)
typedef struct {
    int start;
    int size;
} FdotherEntry;
#pragma pack(pop)

int main(int argc, char* argv[]) {
    const char* dat_path = (argc >= 2) ? argv[1] : "d:/workspace/fd2ida/FD2/FDOTHER.DAT";
    int res_idx = 12;

    FILE* fp = fopen(dat_path, "rb");
    if (!fp) { fprintf(stderr, "无法打开: %s\n", dat_path); return 1; }
    fseek(fp, 0, SEEK_END);
    long dat_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    unsigned char* dat = (unsigned char*)malloc(dat_size);
    fread(dat, 1, dat_size, fp);
    fclose(fp);

    if (dat_size < 6 || memcmp(dat, "LLLLLL", 6) != 0) {
        fprintf(stderr, "魔数错误\n");
        free(dat);
        return 1;
    }

    /* 4 字节偏移表 */
    FdotherEntry* entries = (FdotherEntry*)(dat + 6);
    int start = entries[res_idx].start;
    int size = entries[res_idx].size;
    printf("资源12: start=0x%x, size=0x%x (%d 字节)\n", start, size, size);

    const unsigned char* res = dat + start;
    dword declared_count = res[6] | (res[7] << 8) | (res[8] << 16) | (res[9] << 24);
    printf("声明子资源数: %u (0x%x)\n", declared_count, declared_count);

    /* 扫描所有有效子项 */
    printf("\n=== 子项扫描 ===\n");
    printf("idx | offset  | w  x  h   | 内容预览\n");
    printf("----+---------+-----------+----------\n");

    int valid_count = 0;
    for (int i = 0; i < 256; i++) {
        dword off_pos = 6 + i * 4;
        if (off_pos + 4 > (dword)size) break;
        dword sub_off = res[off_pos] | (res[off_pos+1] << 8) |
                        (res[off_pos+2] << 16) | (res[off_pos+3] << 24);
        if (sub_off >= (dword)size) break;

        const unsigned char* sub = res + sub_off;
        dword sub_size = size - sub_off;

        if (sub_size < 4) {
            printf("[%3d] 0x%04x  | (头不足4字节)\n", i, sub_off);
            break;
        }

        int w = sub[0] | (sub[1] << 8);
        int h = sub[2] | (sub[3] << 8);

        /* 探测RLE数据特征 */
        const unsigned char* rle = sub + 4;
        int rle_size = sub_size - 4;

        /* 计算非零字节占比 */
        int non_zero = 0;
        for (int k = 0; k < rle_size && k < 32; k++) {
            if (rle[k] != 0) non_zero++;
        }
        float non_zero_ratio = (rle_size > 0) ? (float)non_zero / (rle_size < 32 ? rle_size : 32) : 0;

        /* 像素总数 */
        long pixels = (long)w * (long)h;

        printf("[%3d] 0x%04x  | %3d x %3d | RLE=%d 像素=%ld 占比=%.2f  头4: %02x %02x %02x %02x\n",
               i, sub_off, w, h, rle_size, pixels, non_zero_ratio,
               sub[0], sub[1], sub[2], sub[3]);

        valid_count++;
    }
    printf("\n有效子项总数: %d\n", valid_count);

    /* 找出看起来是汉字的子项 (小尺寸, 高密度非零) */
    printf("\n=== 可能的汉字子项 (尺寸 <= 32, 适合16x16字符位图) ===\n");
    for (int i = 0; i < valid_count; i++) {
        dword off_pos = 6 + i * 4;
        if (off_pos + 4 > (dword)size) break;
        dword sub_off = res[off_pos] | (res[off_pos+1] << 8) |
                        (res[off_pos+2] << 16) | (res[off_pos+3] << 24);
        if (sub_off >= (dword)size) break;

        const unsigned char* sub = res + sub_off;
        dword sub_size = size - sub_off;
        if (sub_size < 4) continue;

        int w = sub[0] | (sub[1] << 8);
        int h = sub[2] | (sub[3] << 8);

        if (w >= 1 && w <= 32 && h >= 1 && h <= 32) {
            const unsigned char* rle = sub + 4;
            int rle_size = sub_size - 4;
            int non_zero = 0;
            for (int k = 0; k < rle_size; k++) {
                if (rle[k] != 0) non_zero++;
            }
            float ratio = (float)non_zero / rle_size;
            if (ratio > 0.3f) {
                printf("  子项[%3d] %dx%d  RLE=%d  非零比=%.2f\n",
                       i, w, h, rle_size, ratio);
            }
        }
    }

    free(dat);
    return 0;
}
