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
    
    uint32_t count;
    memcpy(&count, fdother + 6, 4);
    printf("Total resource count: %u\n\n", count);
    
    /* 分析索引13 */
    uint32_t rs13;
    memcpy(&rs13, fdother + 10 + 13*4, 4);
    uint32_t rs14;
    if (14 < count)
        memcpy(&rs14, fdother + 10 + 14*4, 4);
    else
        rs14 = (uint32_t)fsize;
    
    uint32_t r13_size = rs14 - rs13;
    printf("Resource 13 offset: 0x%x, size: %u\n\n", rs13, r13_size);
    
    /* 资源13可能是嵌套的DAT文件 */
    printf("=== Checking if Resource 13 is a nested DAT ===\n");
    
    /* 检查"LMI1"是否是DAT的变体magic */
    printf("Header bytes: ");
    for (int i = 0; i < 10; i++) {
        printf("%02x ", fdother[rs13 + i]);
    }
    printf("\n\n");
    
    /* 假设从位置4开始是标准的DAT结构 */
    printf("Checking from position 4:\n");
    printf("  Magic at +4: %c%c%c%c%c%c\n",
           fdother[rs13 + 4], fdother[rs13 + 5], fdother[rs13 + 6],
           fdother[rs13 + 7], fdother[rs13 + 8], fdother[rs13 + 9]);
    
    uint32_t nested_count;
    memcpy(&nested_count, fdother + rs13 + 10, 4);
    printf("  Nested resource count: %u\n\n", nested_count);
    
    if (nested_count > 0 && nested_count < 1000) {
        printf("=== Nested offset table ===\n");
        for (int i = 0; i < (int)nested_count && i < 50; i++) {
            uint32_t off;
            memcpy(&off, fdother + rs13 + 14 + i*4, 4);
            
            uint32_t next_off;
            if (i + 1 < (int)nested_count) {
                memcpy(&next_off, fdother + rs13 + 14 + (i+1)*4, 4);
            } else {
                next_off = r13_size;
            }
            
            uint32_t sub_size = next_off - off;
            printf("  [%2d] offset=%6u (0x%06x), size=%u\n", i, off, off, sub_size);
        }
    }
    
    /* 检查偏移70处的值在嵌套DAT中的位置 */
    printf("\n=== Offset at position 70 in Resource 13 ===\n");
    uint32_t offset_at_70;
    memcpy(&offset_at_70, fdother + rs13 + 70, 4);
    printf("Value at offset 70: %u (0x%x)\n", offset_at_70, offset_at_70);
    
    if (offset_at_70 < r13_size) {
        uint16_t width = fdother[rs13 + offset_at_70] | (fdother[rs13 + offset_at_70 + 1] << 8);
        uint16_t height = fdother[rs13 + offset_at_70 + 2] | (fdother[rs13 + offset_at_70 + 3] << 8);
        printf("Image at this offset: %dx%d\n", width, height);
        printf("Expected pixel data size: %u bytes\n", width * height);
        printf("Available data from this offset: %u bytes\n", r13_size - offset_at_70 - 4);
    }
    
    free(fdother);
    return 0;
}
