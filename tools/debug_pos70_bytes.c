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
    
    uint32_t count;
    memcpy(&count, fdother + 6, 4);
    uint32_t rs13;
    memcpy(&rs13, fdother + 10 + 13*4, 4);
    uint32_t rs14;
    memcpy(&rs14, fdother + 10 + 14*4, 4);
    uint32_t r13_size = rs14 - rs13;
    
    printf("=== Exact byte analysis of Resource 13 ===\n\n");
    printf("Resource 13: base=0x%x, size=%u\n\n", rs13, r13_size);
    
    /* Check position 70 byte by byte */
    printf("=== Position 70 byte-by-byte ===\n");
    for (int i = 68; i < 76; i++) {
        printf("  pos[%d] = 0x%02x (%d)\n", i, fdother[rs13 + i], fdother[rs13 + i]);
    }
    printf("\n");
    
    /* Interpret as 16-bit value */
    uint16_t val16;
    memcpy(&val16, fdother + rs13 + 70, 2);
    printf("16-bit value at pos 70: %u (0x%04x)\n", val16, val16);
    
    /* Interpret as 32-bit value */
    uint32_t val32;
    memcpy(&val32, fdother + rs13 + 70, 4);
    printf("32-bit value at pos 70: %u (0x%08x)\n\n", val32, val32);
    
    /* Now let's trace through the offset table */
    printf("=== Offset table analysis ===\n");
    printf("Header: %c%c%c%c\n", fdother[rs13], fdother[rs13+1], fdother[rs13+2], fdother[rs13+3]);
    
    uint32_t sub_count;
    memcpy(&sub_count, fdother + rs13 + 4, 4);
    printf("Sub-count at pos 4: %u\n\n", sub_count);
    
    /* Print first 30 offset table entries */
    printf("Offset table (pos 8+):\n");
    for (int i = 0; i < 30; i++) {
        uint16_t off;
        memcpy(&off, fdother + rs13 + 8 + i*2, 2);
        printf("  [%2d] pos=%3d: 0x%04x (%u)\n", i, 8+i*2, off, off);
    }
    
    printf("\n=== Where is position 70 in the offset table? ===\n");
    printf("Position 70 is offset table entry %d\n", (70 - 8) / 2);
    printf("This is entry %d in the table\n", (70 - 8) / 2);
    
    /* The offset at position 70 should point to actual data */
    if (val16 < r13_size) {
        printf("\nOffset %u is VALID (< %u)\n", val16, r13_size);
        printf("Data at offset %u:\n", val16);
        
        for (int i = 0; i < 20 && (val16 + i) < r13_size; i++) {
            if (i % 16 == 0) printf("  %04x: ", val16 + i);
            printf("%02x ", fdother[rs13 + val16 + i]);
            if (i % 16 == 15) printf("\n");
        }
        printf("\n\n");
        
        /* Check dimensions at this offset */
        uint16_t w = fdother[rs13 + val16] | (fdother[rs13 + val16 + 1] << 8);
        uint16_t h = fdother[rs13 + val16 + 2] | (fdother[rs13 + val16 + 3] << 8);
        printf("Dimensions: %dx%d\n", w, h);
        printf("Available data: %u bytes\n", r13_size - val16 - 4);
        printf("Required for image: %u bytes\n", w * h);
    }
    
    free(fdother);
    return 0;
}
