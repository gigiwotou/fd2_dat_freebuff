#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

int main() {
    FILE* fp = fopen("game/FDOTHER.DAT", "rb");
    if (!fp) { printf("Cannot open FDOTHER.DAT\n"); return 1; }
    
    fseek(fp, 0, SEEK_END);
    size_t fsize = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    
    uint8_t* fdother = (uint8_t*)malloc(fsize);
    fread(fdother, 1, fsize, fp);
    fclose(fp);
    
    printf("FDOTHER.DAT size: %zu\n\n", fsize);
    
    /* 资源数量 */
    uint32_t count;
    memcpy(&count, fdother + 6, 4);
    printf("Resource count: %u\n\n", count);
    
    /* 分析索引13的完整结构 */
    printf("=== 详细分析 Resource 13 ===\n\n");
    uint32_t rs13;
    memcpy(&rs13, fdother + 10 + 13*4, 4);
    printf("Resource 13 offset: 0x%x\n", rs13);
    
    uint32_t rs14;
    if (14 < count)
        memcpy(&rs14, fdother + 10 + 14*4, 4);
    else
        rs14 = (uint32_t)fsize;
    
    uint32_t r13_size = rs14 - rs13;
    printf("Resource 13 size: %u bytes\n\n", r13_size);
    
    /* 资源13的前4字节是 "LMI1" - 可能是嵌套DAT的magic */
    printf("Resource 13 header: %c%c%c%c\n", 
           fdother[rs13], fdother[rs13+1], fdother[rs13+2], fdother[rs13+3]);
    
    /* 跳过4字节magic，接下来的可能是子资源数量 */
    uint32_t sub_count;
    memcpy(&sub_count, fdother + rs13 + 4, 4);
    printf("Sub-resource count: %u\n\n", sub_count);
    
    /* 偏移表从位置8开始，每项4字节 */
    printf("=== 资源13的偏移表 ===\n");
    for (int i = 0; i < 50 && i < (int)sub_count; i++) {
        uint32_t off;
        memcpy(&off, fdother + rs13 + 8 + i*4, 4);
        
        uint32_t next_off;
        if (i + 1 < (int)sub_count) {
            memcpy(&next_off, fdother + rs13 + 8 + (i+1)*4, 4);
        } else {
            next_off = r13_size;
        }
        
        uint32_t sub_size = next_off - off;
        printf("  [%2d] offset=0x%06x, size=%u\n", i, off, sub_size);
    }
    
    /* 特别检查偏移70处的值 */
    printf("\n=== 检查偏移70处的子资源 ===\n");
    if (r13_size >= 74) {
        uint32_t sub_offset;
        memcpy(&sub_offset, fdother + rs13 + 70, 4);
        printf("Offset at position 70: 0x%x (%u)\n\n", sub_offset, sub_offset);
        
        if (sub_offset < r13_size) {
            uint16_t width = fdother[rs13 + sub_offset] | (fdother[rs13 + sub_offset + 1] << 8);
            uint16_t height = fdother[rs13 + sub_offset + 2] | (fdother[rs13 + sub_offset + 3] << 8);
            printf("Image dimensions: %dx%d\n", width, height);
            printf("Expected size: %u bytes\n", width * height);
            
            uint32_t available = r13_size - sub_offset - 4;
            printf("Available data: %u bytes\n", available);
            
            if (available >= width * height) {
                printf("✓ 数据完整，可以直接使用\n");
            } else {
                printf("✗ 数据不足，可能需要从其他位置获取\n");
            }
        }
    }
    
    free(fdother);
    return 0;
}
