/* 检查索引2的完整结构 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../include/fd2_types.h"
#include "../include/fd2_fdother_resources.h"

int main(int argc, char** argv) {
    const char* path = "D:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT";
    if (argc > 1) path = argv[1];

    if (fdother_load(path) != 0) {
        printf("Cannot load FDOTHER.DAT\n");
        return 1;
    }

    dword size;
    const byte* data = fdother_get_resource(2, &size);
    printf("Index 2: size=%u bytes\n\n", size);

    /* 解析为偏移表 - 遍历 4 字节偏移, 验证 */
    /* 子资源 0-77: 每个都是 tile 头 [w:2][h:2][window:1] */
    printf("=== 假设 78 个偏移, 每个子资源 484 字节 (24x20 RLE) ===\n");
    for (int i = 0; i < 78; i++) {
        dword off = i * 4;
        dword offset_val = data[off] | (data[off+1] << 8) |
                          (data[off+2] << 16) | (data[off+3] << 24);
        dword next_off = (i+1 < 78) ? (data[(i+1)*4] | (data[(i+1)*4+1] << 8) |
                                       (data[(i+1)*4+2] << 16) | (data[(i+1)*4+3] << 24)) : size;
        dword sub_size = next_off - offset_val;
        if (offset_val + 5 > size) {
            printf("  [%d] offset=%u - 越界!\n", i, offset_val);
            break;
        }
        word w = data[offset_val] | (data[offset_val+1] << 8);
        word h = data[offset_val+2] | (data[offset_val+3] << 8);
        byte win = data[offset_val+4];
        printf("  [%d] offset=%u size=%u  tile w=%d h=%d win=%d\n",
               i, offset_val, sub_size, w, h, win);
    }
    printf("\n");

    /* 探查最后一个子资源: offset[77]=37196 后面是什么 */
    dword last_off = 37196;
    printf("=== data[%u] 开始的 tile 头 (子资源 77) ===\n", last_off);
    for (int i = 0; i < 6; i++) {
        dword off = last_off + i * 4;
        if (off + 5 > size) break;
        word w = data[off] | (data[off+1] << 8);
        word h = data[off+2] | (data[off+3] << 8);
        byte win = data[off+4];
        printf("  [%d] w=%d h=%d win=%d\n", i, w, h, win);
    }
    printf("\n");

    /* 探查 offset 偏移间距 */
    printf("=== 偏移表项之间的差值 ===\n");
    int last_w = 0, last_h = 0;
    for (int i = 0; i < 78; i++) {
        dword off = data[i*4] | (data[i*4+1] << 8) |
                   (data[i*4+2] << 16) | (data[i*4+3] << 24);
        dword next = (i+1 < 78) ? (data[(i+1)*4] | (data[(i+1)*4+1] << 8) |
                                   (data[(i+1)*4+2] << 16) | (data[(i+1)*4+3] << 24)) : size;
        int diff = next - off;
        if (i < 10 || i > 70) {
            printf("  [%d] off=%u next=%u diff=%d\n", i, off, next, diff);
        }
        if (diff != 484) {
            printf("    !!! 不等于 484 !!!\n");
        }
    }
    printf("\n");

    /* 探查 sub_4ED0B 风格: 子资源可能是 [w:2][h:2][像素数据] */
    /* 24x20 tile: 5 + 484 = 489 bytes */
    /* 但是偏移间距是 484, 不是 489 */
    /* 所以子资源不含tile头, 直接是 RLE 数据 */
    printf("=== 子资源 0 的前 32 字节 (假设直接是 RLE 数据) ===\n");
    for (int i = 0; i < 32; i++) {
        printf("%02x ", data[312 + i]);
        if ((i+1) % 16 == 0) printf("\n");
    }
    printf("\n\n");

    /* 偏移表 0-77 -> 每个子资源起始, 实际"长度" = 下一偏移-当前偏移 */
    /* 但 sub_4ED0B 是从头部读取 w, h, 然后逐行 memcpy width 字节 height 次 */
    /* 所以子资源可能是 [width:2][height:2][pixel_data: w*h] */
    /* 24*20 = 480, 头 4 字节, 总 484 字节 ✓ */
    /* 那么前 4 字节就是 18 00 14 00 (24, 20) */
    printf("=== 子资源 0 前 6 字节: 是否 [24:2][20:2][win:1]? ===\n");
    printf("data[312..317]: %02x %02x %02x %02x %02x %02x\n",
           data[312], data[313], data[314], data[315], data[316], data[317]);
    word sw = data[312] | (data[313] << 8);
    word sh = data[314] | (data[315] << 8);
    byte swin = data[316];
    printf("width=%d, height=%d, window=%d (期望 24/20/?)\n", sw, sh, swin);
    printf("\n");

    /* 子资源 1 头部 */
    printf("=== 子资源 1 前 6 字节 (offset=796) ===\n");
    printf("data[796..801]: %02x %02x %02x %02x %02x %02x\n",
           data[796], data[797], data[798], data[799], data[800], data[801]);
    sw = data[796] | (data[797] << 8);
    sh = data[798] | (data[799] << 8);
    swin = data[800];
    printf("width=%d, height=%d, window=%d\n", sw, sh, swin);
    printf("\n");

    /* 子资源 48 头部 (24x16 不同) */
    printf("=== 子资源 48 前 6 字节 (offset=23544) ===\n");
    printf("data[23544..23549]: %02x %02x %02x %02x %02x %02x\n",
           data[23544], data[23545], data[23546], data[23547], data[23548], data[23549]);
    sw = data[23544] | (data[23545] << 8);
    sh = data[23546] | (data[23547] << 8);
    swin = data[23548];
    printf("width=%d, height=%d, window=%d\n", sw, sh, swin);

    /* 假设每个子资源 = 4字节头 + width*height 字节原始数据 */
    /* 那么 "24*20=480, 4+480=484" 但 "24*16=384, 4+384=388" 不等于 484 */
    /* 所以子资源不是定长 484 字节 */
    /* 重新计算: 假设有 78 个偏移, 偏移间距由 sub_4ED0B 决定 */
    /* 但其实我的发现 "guess_table=192 -> first_off=23544 -> w=24 h=16"  */
    /*   23544 - 4*48 = 23352, 也就是 offset[48] - offset[47] = 23544 - 23060 = 484 */
    /*   但 w=24 h=16 -> 4 + 24*16 = 388 字节, 而 484 - 388 = 96 字节剩余 */
    /* 这说明子资源 48 不是 24x16 原始数据, 而是其他格式 */

    /* 实际上让我再仔细看: sub_4ED0B 是从 4 字节头读 w/h 然后逐行 */
    /* 但是有 RLE 压缩, 实际大小可能 < 4+w*h */
    /* 这里可能是 sub_4E22A 之类的 RLE 压缩 */

    /* 检查每个子资源的实际头信息 */
    printf("\n=== 所有 78 个子资源的头部 (基于 78 个偏移) ===\n");
    int same_size = 1;
    for (int i = 0; i < 78; i++) {
        dword off = i * 4;
        dword offset_val = data[off] | (data[off+1] << 8) |
                          (data[off+2] << 16) | (data[off+3] << 24);
        dword next_off = (i+1 < 78) ? (data[(i+1)*4] | (data[(i+1)*4+1] << 8) |
                                       (data[(i+1)*4+2] << 16) | (data[(i+1)*4+3] << 24)) : size;
        dword sub_size = next_off - offset_val;
        if (offset_val + 4 > size) break;
        word w = data[offset_val] | (data[offset_val+1] << 8);
        word h = data[offset_val+2] | (data[offset_val+3] << 8);
        if (w != 24 || h != 20) same_size = 0;
        if (i < 60 || i > 75) {
            printf("  [%2d] off=%5u size=%4u tile=%2dx%2d\n", i, offset_val, sub_size, w, h);
        }
    }
    if (same_size) {
        printf(">>> 全部 78 个子资源都是 24x20\n");
    } else {
        printf(">>> 子资源尺寸不一致, 偏移表硬编码为 78 不正确\n");
    }

    return 0;
}
