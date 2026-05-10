#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

int main() {
    FILE* fp = fopen("bin/FDOTHER.DAT", "rb");
    if (!fp) {
        printf("Cannot open FDOTHER.DAT\n");
        return 1;
    }
    
    /* 读取文件 */
    fseek(fp, 0, SEEK_END);
    long file_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    
    unsigned char* data = (unsigned char*)malloc(file_size);
    fread(data, 1, file_size, fp);
    fclose(fp);
    
    printf("FDOTHER.DAT file size: %ld bytes\n\n", file_size);
    
    /* 打印前100字节 */
    printf("First 100 bytes:\n");
    for (int i = 0; i < 100; i++) {
        if (i % 16 == 0) printf("%04X: ", i);
        printf("%02X ", data[i]);
        if (i % 16 == 15) printf("\n");
    }
    printf("\n");
    
    /* 打印头部结构 */
    uint16_t header_2bytes = *(uint16_t*)(data + 0);
    uint32_t offset_table_4bytes = *(uint32_t*)(data + 2);
    uint32_t offset_0 = *(uint32_t*)(data + 6);
    uint32_t offset_1 = *(uint32_t*)(data + 10);
    uint32_t offset_20 = *(uint32_t*)(data + 6 + 4*20);
    
    printf("Header analysis:\n");
    printf("  Bytes 0-1 (uint16): %u (0x%04X)\n", header_2bytes, header_2bytes);
    printf("  Bytes 2-5 (uint32): %u (0x%08X)\n", offset_table_4bytes, offset_table_4bytes);
    printf("\n");
    printf("Offset table (from position 6):\n");
    printf("  [0]  = %u (0x%08X)\n", offset_0, offset_0);
    printf("  [1]  = %u (0x%08X)\n", offset_1, offset_1);
    printf("  [20] = %u (0x%08X)\n", offset_20, offset_20);
    printf("\n");
    
    /* 验证索引20的资源数据 */
    printf("=== Index 20 verification ===\n");
    if (offset_20 < file_size) {
        unsigned char* res = data + offset_20;
        int16_t w = *(int16_t*)(res + 0);
        int16_t h = *(int16_t*)(res + 2);
        printf("  Offset: %u\n", offset_20);
        printf("  Width:  %d\n", w);
        printf("  Height: %d\n", h);
        printf("  First 16 bytes: ");
        for (int i = 0; i < 16; i++) {
            printf("%02X ", res[i]);
        }
        printf("\n\n");
    }
    
    /* 验证索引1的资源数据 */
    printf("=== Index 1 verification ===\n");
    if (offset_1 < file_size) {
        unsigned char* res = data + offset_1;
        int16_t w = *(int16_t*)(res + 0);
        int16_t h = *(int16_t*)(res + 2);
        printf("  Offset: %u\n", offset_1);
        printf("  Width:  %d\n", w);
        printf("  Height: %d\n", h);
        printf("  First 16 bytes: ");
        for (int i = 0; i < 16; i++) {
            printf("%02X ", res[i]);
        }
        printf("\n\n");
    }
    
    /* 打印索引0-25的偏移 */
    printf("=== Offset table [0-25] ===\n");
    for (int i = 0; i <= 25; i++) {
        uint32_t off = *(uint32_t*)(data + 6 + 4*i);
        printf("  [%2d] = %u (0x%08X)", i, off, off);
        
        /* 检查这个偏移指向的数据 */
        if (off < file_size) {
            int16_t w = *(int16_t*)(data + off + 0);
            int16_t h = *(int16_t*)(data + off + 2);
            if (w > 0 && w < 640 && h > 0 && h < 480) {
                printf(" -> VALID: %dx%d\n", w, h);
            } else {
                printf(" -> INVALID: %dx%d\n", w, h);
            }
        } else {
            printf(" -> OUT OF BOUNDS\n");
        }
    }
    
    free(data);
    return 0;
}
