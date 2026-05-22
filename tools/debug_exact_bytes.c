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
    
    printf("=== Detailed byte analysis at position 70 ===\n\n");
    printf("Resource 13 offset: 0x%x, size: %u\n", rs13, r13_size);
    printf("File size: 0x%x (%zu)\n\n", (uint32_t)fsize, fsize);
    
    /* Print exact bytes at position 70 */
    printf("Bytes at position 68-75:\n");
    for (int i = 68; i < 76; i++) {
        printf("  pos[%d] = 0x%02x\n", i, fdother[rs13 + i]);
    }
    printf("\n");
    
    /* 16-bit interpretation */
    uint16_t val16;
    memcpy(&val16, fdother + rs13 + 70, 2);
    printf("16-bit value at pos 70: %u (0x%04x)\n", val16, val16);
    
    /* 32-bit interpretation */
    uint32_t val32;
    memcpy(&val32, fdother + rs13 + 70, 4);
    printf("32-bit value at pos 70: %u (0x%08x)\n\n", val32, val32);
    
    /* The MCP code says: *(dword_53F66 + 70) is a DWORD */
    /* So it should read 4 bytes at position 70 */
    /* dword_53F66 + 70 = resource_13_base + 70 */
    /* *(dword_53F66 + 70) = DWORD at that position */
    
    /* If val32 = 0xBF01 (which is 48897), then: */
    /* source = rs13 + 48897 = 0x5a571 + 0xBF01 = 0x66472 */
    
    uint32_t src_ptr = rs13 + val32;
    printf("Source pointer: 0x%x + 0x%x = 0x%x\n", rs13, val32, src_ptr);
    printf("File size: 0x%x\n", (uint32_t)fsize);
    
    if (src_ptr < fsize) {
        uint16_t w = fdother[src_ptr] | (fdother[src_ptr + 1] << 8);
        uint16_t h = fdother[src_ptr + 2] | (fdother[src_ptr + 3] << 8);
        uint32_t avail = fsize - src_ptr - 4;
        
        printf("\nAt source pointer 0x%x:\n", src_ptr);
        printf("  Width: %d, Height: %d\n", w, h);
        printf("  Available: %u bytes\n", avail);
        printf("  Needed: %u bytes (%dx%d)\n", w * h, w, h);
        
        if (avail < w * h) {
            printf("\n  ✗ INSUFFICIENT DATA!\n");
            printf("  Available: %u, Needed: %u\n", avail, w * h);
            printf("  Missing: %u bytes\n", w * h - avail);
        }
    }
    
    /* Let's also check if there's a different interpretation */
    /* Maybe position 70 contains an index, not an offset */
    printf("\n=== Alternative: position 70 as index ===\n");
    printf("If val32 (%u) is an index into offset table...\n", val32);
    printf("But offset table starts at position 8 with 2-byte entries\n");
    printf("Index %u would be at position %u\n", val32, 8 + val32 * 2);
    printf("This is way out of range (%u bytes)\n\n", 8 + val32 * 2);
    
    free(fdother);
    return 0;
}
