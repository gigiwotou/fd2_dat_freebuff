#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

typedef unsigned char u8;
typedef unsigned int dword;

int main() {
    FILE* fp = fopen("game/FDTXT.DAT", "rb");
    if (!fp) { printf("Cannot open FDTXT.DAT\n"); return 1; }
    
    fseek(fp, 0, SEEK_END);
    size_t fsize = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    
    u8* fdtxt = (u8*)malloc(fsize);
    fread(fdtxt, 1, fsize, fp);
    fclose(fp);
    
    printf("FDTXT.DAT size: %zu\n\n", fsize);
    
    /* 获取资源0的原始数据 */
    dword r0_off;
    dword r1_off;
    memcpy(&r0_off, fdtxt + 10, 4);
    memcpy(&r1_off, fdtxt + 14, 4);
    dword r0_size = r1_off - r0_off;
    
    printf("Resource 0: file_offset=0x%x, size=%u bytes\n\n", r0_off, r0_size);
    
    u8* r0 = fdtxt + r0_off;
    
    /* 显示资源0的前100字节 */
    printf("Resource 0 first 100 bytes:\n");
    for (int i = 0; i < 100 && i < (int)r0_size; i++) {
        if (i % 16 == 0) printf("\n  %04x: ", i);
        printf("%02x ", r0[i]);
    }
    printf("\n");
    
    /* 检查前2字节 */
    int16_t declared_count;
    memcpy(&declared_count, r0, 2);
    printf("\nDeclared count (first 2 bytes): %d\n", declared_count);
    
    /* 分析偏移表 */
    /* 如果declared_count=24，偏移表应该有24个int16 */
    /* 位置: 2 + i*2, i=0..23 */
    printf("\nOffset table (first %d entries):\n", declared_count);
    int16_t* offsets = (int16_t*)(r0 + 2);
    for (int i = 0; i < declared_count && (2 + (i+1)*2) <= r0_size; i++) {
        printf("  [%2d] offset=%4d (0x%04x)\n", i, offsets[i], offsets[i]);
    }
    
    /* 检查偏移表结束后是什么 */
    int offset_table_end = 2 + declared_count * 2;
    printf("\nOffset table ends at position: %d\n", offset_table_end);
    printf("Bytes after offset table:\n");
    for (int i = offset_table_end; i < offset_table_end + 50 && i < (int)r0_size; i++) {
        if (i % 16 == 0) printf("\n  %04x: ", i);
        printf("%02x ", r0[i]);
    }
    printf("\n");
    
    /* 扫描整个资源0，查找子文本的实际数量 */
    printf("\n=== Scanning for actual sub-text count ===\n");
    int max_sub_idx = 0;
    for (int i = 0; i < declared_count; i++) {
        if (offsets[i] > max_sub_idx) {
            max_sub_idx = offsets[i];
        }
    }
    printf("Max offset value in table: %d\n", max_sub_idx);
    
    /* 检查是否有嵌套的DAT */
    printf("\n=== Checking for nested DAT ===\n");
    if (r0_size >= 10 && memcmp(r0, "LLLLLL", 6) == 0) {
        printf("FOUND: Nested DAT at resource 0 start!\n");
        dword nc;
        memcpy(&nc, r0 + 6, 4);
        printf("Nested count: %u\n", nc);
    } else {
        printf("No nested DAT at resource 0 start\n");
    }
    
    free(fdtxt);
    return 0;
}
