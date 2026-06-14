/* test_res7_viewer_fix.c - 验证 viewer 资源 7 修复后的解析逻辑
 *
 * 这个测试模拟 viewer 中 NESTED_DAT 分支的修改后逻辑:
 * 1. 使用 fdother_nested_calculate_valid_count 计算有效子资源数
 * 2. 使用 fd2_rle_lmi1_decode_tile_auto 解码子资源
 *
 * 与 test_res7_lmi1.c 的区别: 模拟 viewer 的完整处理流程
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "fd2_types.h"
#include "fd2_fdother_resources.h"
#include "fd2_rle.h"

/* 模拟 viewer 中的辅助函数 (与 viewer 完全一致) */
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
    /* 末尾偏移 == size 是结束标记, 实际子资源数 = valid_count - 1 */
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

int main(int argc, char* argv[]) {
    const char* filepath = "game/FDOTHER.DAT";
    if (argc > 1) filepath = argv[1];

    int ret = fdother_load(filepath);
    if (ret != 0) {
        printf("Failed to load %s\n", filepath);
        return 1;
    }

    printf("=== Viewer Resource 7 Fix Verification ===\n\n");

    /* viewer 资源 7 */
    dword res_size;
    const byte* res_data = fdother_get_resource(7, &res_size);
    if (!res_data) {
        printf("Failed to get resource 7\n");
        return 1;
    }

    printf("[Problem 1] 子资源数量:\n");
    dword declared_count = (dword)(res_data[6] | (res_data[7] << 8) |
                                    (res_data[8] << 16) | (res_data[9] << 24));
    int valid_count = fdother_nested_calculate_valid_count(res_data, res_size, declared_count);
    printf("  字节 6-9 声明的子资源数: %d\n", declared_count);
    printf("  实际有效子资源数(修复后): %d\n", valid_count);
    printf("  -> g_max_sub_items = %d (修复后正确值)\n\n", valid_count);

    /* 显示所有有效子资源的分辨率 - 模拟 viewer 修复后的逻辑
     * (viewer 中直接用 valid_count + 偏移表计算, 不用 fdother_nested_get_resource) */
    printf("[Problem 2] 首张图片(及所有有效子资源)分辨率:\n");
    int all_ok = 1;
    byte buf[256 * 256];

    for (int i = 0; i < valid_count; i++) {
        dword offset_addr = 10 + i * 4;
        if (offset_addr + 4 > res_size) break;
        dword sub_offset = res_data[offset_addr] |
                          (res_data[offset_addr + 1] << 8) |
                          (res_data[offset_addr + 2] << 16) |
                          (res_data[offset_addr + 3] << 24);
        dword sub_end;
        if (i + 1 < valid_count) {
            dword next_addr = 10 + (i + 1) * 4;
            sub_end = res_data[next_addr] |
                     (res_data[next_addr + 1] << 8) |
                     (res_data[next_addr + 2] << 16) |
                     (res_data[next_addr + 3] << 24);
        } else {
            sub_end = res_size;
        }
        dword sub_size = sub_end - sub_offset;
        const byte* sub_data = res_data + sub_offset;

        /* 模拟 viewer 中修复后的解码: 用 fd2_rle_lmi1_decode_tile_auto */
        int out_w = 0, out_h = 0;
        int decode_ret = fd2_rle_lmi1_decode_tile_auto(
            sub_data, (int)sub_size, buf, &out_w, &out_h, 0);

        /* 4 字节头 w, h (预期) */
        word w_hdr = sub_data[0] | (sub_data[1] << 8);
        word h_hdr = sub_data[2] | (sub_data[3] << 8);

        const char* status = (decode_ret == 0 && out_w == w_hdr && out_h == h_hdr) ? "OK" : "FAIL";
        if (decode_ret != 0) all_ok = 0;

        printf("  Sub %d: size=%u, 头[w=%d, h=%d], 解码结果[%dx%d] %s\n",
               i, sub_size, w_hdr, h_hdr, out_w, out_h, status);
    }

    printf("\n=== 总结 ===\n");
    printf("子资源数: %d -> %d (修复后)\n", declared_count, valid_count);
    printf("首张图片(Sub 0): 应为 61x7 (4字节头 LMI1)\n");
    printf("所有有效子资源解码: %s\n", all_ok ? "成功" : "失败");

    return (all_ok && valid_count == 6) ? 0 : 1;
}
