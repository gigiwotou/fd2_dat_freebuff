/* test_decode_res12.c - 测试 fd2_rle_decompress 对资源12 NESTED_DAT 子资源的解码 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/fd2_types.h"
#include "../include/fd2_rle.h"
#include "../include/fd2_decoder.h"

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
    printf("资源 %d: start=0x%x, size=%d\n", res_idx, start, size);

    const unsigned char* res = dat + start;
    dword declared_count = res[6] | (res[7] << 8) | (res[8] << 16) | (res[9] << 24);
    printf("声明子资源数: %u\n", declared_count);

    /* 测试每个有效子项 */
    byte buf[64000];
    int valid_count = 0;
    for (int i = 0; i < 64; i++) {
        dword off_pos = 6 + i * 4;
        if (off_pos + 4 > size) break;
        dword sub_off = res[off_pos] | (res[off_pos+1] << 8) |
                        (res[off_pos+2] << 16) | (res[off_pos+3] << 24);
        if (sub_off >= size) break;
        valid_count++;
    }
    printf("有效子项数: %d\n", valid_count);

    printf("\n--- 解码所有子项 ---\n");
    for (int i = 0; i < valid_count; i++) {
        dword off_pos = 6 + i * 4;
        dword sub_off = res[off_pos] | (res[off_pos+1] << 8) |
                        (res[off_pos+2] << 16) | (res[off_pos+3] << 24);
        if (sub_off >= size) break;

        const unsigned char* sub_data = res + sub_off;
        dword sub_size = size - sub_off;
        if (sub_size < 4) continue;

        int w = sub_data[0] | (sub_data[1] << 8);
        int h = sub_data[2] | (sub_data[3] << 8);
        if (w <= 0 || h <= 0) continue;

        printf("  [%2d] %dx%-3d ", i, w, h);
        fflush(stdout);

        memset(buf, 0, w * h);
        int ret = fd2_rle_decompress(sub_data + 4, sub_size - 4,
                                      buf, 0, 0, w, w, h, -1);
        if (ret == 0) {
            int non_zero = 0;
            for (int j = 0; j < w*h; j++) if (buf[j]) non_zero++;
            printf("✓ ok, 非零像素=%d/%d\n", non_zero, w*h);
        } else {
            printf("❌ ret=%d\n", ret);
        }
    }

    free(dat);
    return 0;
}
