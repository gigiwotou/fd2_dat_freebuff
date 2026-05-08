#include <stdio.h>
#include <stdint.h>
#include <string.h>

int main() {
    const char* paths[] = {"FDOTHER.DAT", "bin/FDOTHER.DAT", "../bin/FDOTHER.DAT"};
    FILE* fp = NULL;
    
    for (int i = 0; i < 3; i++) {
        fp = fopen(paths[i], "rb");
        if (fp) {
            printf("Opened: %s\n", paths[i]);
            break;
        }
    }
    
    if (!fp) {
        printf("Cannot open FDOTHER.DAT\n");
        return 1;
    }
    
    fseek(fp, 0, SEEK_END);
    long file_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    
    printf("File size: %ld bytes\n", file_size);
    
    /* 读取前20字节 */
    uint8_t header[20];
    fread(header, 1, 20, fp);
    
    printf("\nFirst 20 bytes:\n");
    for (int i = 0; i < 20; i++) {
        printf("  [%d] = %d (0x%02X)\n", i, header[i], header[i]);
    }
    
    /* 检查字节6-9作为32位值 */
    uint32_t val_at_6;
    memcpy(&val_at_6, header + 6, 4);
    printf("\nValue at offset 6 (4 bytes): %u (0x%X)\n", val_at_6, val_at_6);
    
    /* 检查字节6+4*N处的偏移值 */
    printf("\nChecking offset table (4-byte entries from offset 6):\n");
    for (int i = 0; i <= 77; i++) {
        fseek(fp, 6 + 4 * i, SEEK_SET);
        uint32_t offset;
        fread(&offset, 1, 4, fp);
        if (i <= 5 || i >= 74) {
            printf("  Index %d at offset %d: start=%u\n", i, 6 + 4 * i, offset);
        }
    }
    
    /* 检查索引76和77的条目 */
    printf("\nIndex 76 entry (8 bytes at offset 6+76*4=%d):\n", 6 + 76 * 4);
    fseek(fp, 6 + 76 * 4, SEEK_SET);
    uint32_t e76[2];
    fread(e76, 1, 8, fp);
    printf("  start=%u, end=%u, size=%u\n", e76[0], e76[1], e76[1] - e76[0]);
    
    printf("\nIndex 77 entry:\n");
    fseek(fp, 6 + 77 * 4, SEEK_SET);
    uint32_t e77[2];
    fread(e77, 1, 8, fp);
    printf("  start=%u, end=%u, size=%u\n", e77[0], e77[1], e77[1] - e77[0]);
    
    /* 检查是否每个条目是8字节 */
    printf("\nChecking 8-byte entries from offset 6:\n");
    fseek(fp, 6 + 8 * 76, SEEK_SET);
    uint32_t e76_8[2];
    fread(e76_8, 1, 8, fp);
    printf("  8-byte mode Index 76: start=%u, end=%u, size=%u\n", e76_8[0], e76_8[1], e76_8[1] - e76_8[0]);
    
    fclose(fp);
    return 0;
}
