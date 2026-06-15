/**
 * 批量解码资源12所有28个子项到PPM文件
 * 1:1 复刻 sub_16886 + sub_4E98D 算法
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/fd2_types.h"
#include "../include/fd2_rle.h"
#include "../include/fd2_fdother_resources.h"

int main(int argc, char** argv) {
    const char* dat_path = (argc > 1) ? argv[1] : "../bin/FDOTHER.DAT";
    const char* out_dir = (argc > 2) ? argv[2] : ".";
    byte pal[768];
    /* 简单调色板: index 0=黑, 1=白, 16-31=灰阶, 32-255=任意 */
    memset(pal, 0, 768);
    for (int i = 0; i < 256; i++) {
        pal[i*3+0] = (i*37) & 0xFF;
        pal[i*3+1] = (i*67) & 0xFF;
        pal[i*3+2] = (i*97) & 0xFF;
    }
    pal[0]=0; pal[1]=0; pal[2]=0;
    pal[3]=255; pal[4]=255; pal[5]=255;

    /* 读取整个DAT */
    FILE* f = fopen(dat_path, "rb");
    if (!f) { fprintf(stderr, "无法打开 %s\n", dat_path); return 1; }
    fseek(f, 0, SEEK_END);
    long fsize = ftell(f);
    fseek(f, 0, SEEK_SET);
    byte* data = (byte*)malloc(fsize);
    fread(data, 1, fsize, f);
    fclose(f);

    /* 找到资源12的偏移和大小 */
    /* DAT文件结构: 先看resource_count */
    dword res_count;
    /* 简化: 直接从off_12=0x40b68, size_12=0x4d597-off_12 */
    dword off_12 = 0x40b68;
    dword size_12 = 0x4d597 - off_12;
    byte* res12 = data + off_12;

    /* 扫描子项数 */
    int valid_count = 0;
    dword offsets[64];
    for (int i = 0; i < 64; i++) {
        if ((dword)(6 + i * 4) + 4 > size_12) break;
        dword sub_offset = res12[6 + i*4] | (res12[6 + i*4+1] << 8) |
                           (res12[6 + i*4+2] << 16) | (res12[6 + i*4+3] << 24);
        if (sub_offset >= size_12) break;
        offsets[i] = sub_offset;
        valid_count++;
    }
    fprintf(stderr, "资源12有 %d 个子项\n", valid_count);

    /* 解码每个子项并输出原始像素数据 */
    /* 1:1 复刻游戏: 用 320x200 back buffer 作为 dst, fd2_rle_sub_4E98D
     * 内部按 320 行宽 (a6) 推进, 可能写 w*h 之外 (不影响实际显示).
     * 我们只提取 [0, w*h) 范围的像素.
     *
     * 关键修复: src 必须是 sub_data 起点 (含 4 字节头),
     * fd2_rle_sub_4E98D 内部会从 src[0..3] 读 w,h (1:1 复刻游戏汇编).
     * src_size 设为 size_12-sub_offset, 游戏汇编不检查 src 越界,
     * 直接读连续 res_data 内存. */
    static byte back_buffer[320*200];
    for (int idx = 0; idx < valid_count; idx++) {
        dword sub_offset = offsets[idx];
        byte* sub_data = res12 + sub_offset;
        if (size_12 - sub_offset < 4) continue;
        int w = sub_data[0] | (sub_data[1] << 8);
        int h = sub_data[2] | (sub_data[3] << 8);
        if (w <= 0 || h <= 0 || w * h > 64000) continue;
        memset(back_buffer, 0, sizeof(back_buffer));
        int ret = fd2_rle_sub_4E98D(sub_data, (int)(size_12 - sub_offset), back_buffer, w, h, -1);
        if (ret != 0) {
            fprintf(stderr, "  子项%d %dx%d 解码失败 ret=%d\n", idx, w, h, ret);
            continue;
        }
        /* 统计 [0, w*h) 范围唯一色 */
        int colors[256] = {0};
        for (int i = 0; i < w*h; i++) colors[back_buffer[i]]++;
        int n_uniq = 0;
        for (int i = 0; i < 256; i++) if (colors[i]) n_uniq++;
        fprintf(stderr, "  子项%d %dx%d 唯一色=%d OK\n", idx, w, h, n_uniq);
        (void)colors;

        /* 输出原始像素数据 (只取 w*h 范围) */
        char fname[256];
        snprintf(fname, sizeof(fname), "%s/res12_c_sub%d.bin", out_dir, idx);
        FILE* pf = fopen(fname, "wb");
        if (!pf) continue;
        fwrite(&w, 2, 1, pf);
        fwrite(&h, 2, 1, pf);
        fwrite(back_buffer, 1, w*h, pf);
        fclose(pf);
    }

    free(data);
    return 0;
}
