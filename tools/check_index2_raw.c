/* 检查索引2的原始数据
 * 目的: 探明索引2的实际格式, 验证子项数量和图片解析
 */
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

    int count = fdother_get_resource_count();
    printf("Total resources: %d\n\n", count);

    /* 索引2 资源 */
    dword size;
    const byte* data = fdother_get_resource(2, &size);
    if (!data) {
        printf("Cannot get index 2\n");
        return 1;
    }
    printf("Index 2: size=%u bytes\n\n", size);

    /* 输出前 64 字节 */
    printf("First 64 bytes:\n");
    for (int i = 0; i < 64 && i < (int)size; i++) {
        printf("%02x ", data[i]);
        if ((i + 1) % 16 == 0) printf("\n");
    }
    printf("\n\n");

    /* 输出前 8 个 dword 偏移值 (假设是偏移表) */
    printf("First 8 dwords (interpreted as offsets):\n");
    for (int i = 0; i < 8 && i * 4 + 3 < (int)size; i++) {
        dword off = data[i*4] | (data[i*4+1] << 8) | (data[i*4+2] << 16) | (data[i*4+3] << 24);
        printf("  [%d] = 0x%08x (%u)\n", i, off, off);
    }
    printf("\n");

    /* 尝试 78 个偏移 (当前硬编码) */
    printf("=== 假设 78 个偏移 (312字节表) ===\n");
    if (size >= 312) {
        for (int i = 0; i < 78; i++) {
            dword off = data[i*4] | (data[i*4+1] << 8) | (data[i*4+2] << 16) | (data[i*4+3] << 24);
            printf("  offset[%d] = %u\n", i, off);
        }
    }
    printf("\n");

    /* 假设偏移表较大(9420) - 检查头几个是否合理 */
    printf("=== 假设 9420 个偏移 (大表) ===\n");
    if (size >= 9420 * 4) {
        printf("Yes, size %u >= 9420*4 = 37680\n", size);
        for (int i = 0; i < 20; i++) {
            dword off = data[i*4] | (data[i*4+1] << 8) | (data[i*4+2] << 16) | (data[i*4+3] << 24);
            printf("  offset[%d] = %u\n", i, off);
        }
    } else {
        printf("No, size %u < 9420*4 = 37680\n", size);
    }
    printf("\n");

    /* 检查子资源头部 - 第一个子资源看起来像什么? */
    printf("=== 探查子资源区 ===\n");
    /* 假设偏移表大小未知, 我们从 data[0] 开始逐个尝试当子资源头 */
    for (int guess_table = 0; guess_table < 1024; guess_table += 4) {
        dword first_off = data[guess_table] | (data[guess_table+1] << 8) |
                         (data[guess_table+2] << 16) | (data[guess_table+3] << 24);
        /* 第一个子资源应指向一个合理的 tile 头 [w:2][h:2][window:1] */
        if (first_off < size - 5 && first_off > 0) {
            word w = data[first_off] | (data[first_off+1] << 8);
            word h = data[first_off+2] | (data[first_off+3] << 8);
            byte win = data[first_off+4];
            if (w > 0 && w <= 100 && h > 0 && h <= 100 && win < 256) {
                printf("  guess_table=%d: first_off=%u -> tile w=%d h=%d window=%d\n",
                       guess_table, first_off, w, h, win);
            }
        }
    }

    /* 显示 data[0] 开始的 tile 头 (假设没有偏移表) */
    printf("\n=== data[0] 开始的 tile 头 ===\n");
    for (int i = 0; i < 5; i++) {
        dword off = i * 4;
        if (off + 5 > size) break;
        word w = data[off] | (data[off+1] << 8);
        word h = data[off+2] | (data[off+3] << 8);
        byte win = data[off+4];
        printf("  [%d] w=%d h=%d window=%d (header bytes: %02x %02x %02x %02x %02x)\n",
               i, w, h, win, data[off], data[off+1], data[off+2], data[off+3], data[off+4]);
    }

    /* 尝试从data[0]开始, 4字节偏移, 偏移指向子资源 */
    /* 但索引2不是这个结构, 我们需要根据汇编确认 */
    /* 暂时输出整 312 字节的内容, 帮助分析 */
    printf("\n=== 整 320 字节 (作为有符号字节) ===\n");
    for (int i = 0; i < 320 && i < (int)size; i++) {
        printf("%3d ", (signed char)data[i]);
        if ((i + 1) % 16 == 0) printf("\n");
    }
    printf("\n");

    return 0;
}
