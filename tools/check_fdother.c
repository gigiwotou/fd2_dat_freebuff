#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

int main() {
    FILE* fp = fopen("D:/workspace/fd2_dat_freebuff/bin/FDOTHER.DAT", "rb");
    if (!fp) {
        printf("Cannot open FDOTHER.DAT\n");
        return 1;
    }
    
    /* 读取前200字节 */
    uint8_t header[200];
    fread(header, 1, 200, fp);
    fclose(fp);
    
    printf("FDOTHER.DAT header (first 200 bytes):\n");
    for (int i = 0; i < 200; i++) {
        if (i % 16 == 0) printf("\n%04X: ", i);
        printf("%02X ", header[i]);
    }
    printf("\n\n");
    
    /* 解析偏移表 */
    printf("Offset table analysis:\n");
    printf("Header bytes 0-5: ");
    for (int i = 0; i < 6; i++) {
        printf("%02X ", header[i]);
    }
    printf("\n");
    
    uint16_t header_val = *(uint16_t*)(header + 0);
    uint32_t offset_table_start = *(uint32_t*)(header + 2);
    
    printf("Header value (2 bytes): %u (0x%X)\n", header_val, header_val);
    printf("Offset table start (4 bytes): %u (0x%X)\n", offset_table_start, offset_table_start);
    
    /* 尝试从不同位置读取偏移表 */
    printf("\nOffsets from position 6:\n");
    for (int i = 0; i <= 20; i++) {
        uint32_t offset = *(uint32_t*)(header + 6 + 4*i);
        printf("  [%2d] offset = %u (0x%X)\n", i, offset, offset);
    }
    
    /* 验证索引1、20、3、5的资源数据 */
    printf("\nResource data verification:\n");
    
    /* 索引1 */
    uint32_t off1 = *(uint32_t*)(header + 6 + 4*1);
    printf("\nIndex 1: offset=%u\n", off1);
    if (off1 < 200) {
        printf("  Data at offset: ");
        for (int i = 0; i < 8; i++) {
            printf("%02X ", header[off1 + i]);
        }
        printf("\n");
        int w = header[off1 + 0] | (header[off1 + 1] << 8);
        int h = header[off1 + 2] | (header[off1 + 3] << 8);
        printf("  Dimensions: %dx%d\n", w, h);
    }
    
    /* 索引20 */
    uint32_t off20 = *(uint32_t*)(header + 6 + 4*20);
    printf("\nIndex 20: offset=%u\n", off20);
    if (off20 < 200) {
        printf("  Data at offset: ");
        for (int i = 0; i < 8; i++) {
            printf("%02X ", header[off20 + i]);
        }
        printf("\n");
        int w = header[off20 + 0] | (header[off20 + 1] << 8);
        int h = header[off20 + 2] | (header[off20 + 3] << 8);
        printf("  Dimensions: %dx%d\n", w, h);
    }
    
    return 0;
}
