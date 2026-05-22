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
    
    /* Resource 13 */
    uint32_t count;
    memcpy(&count, fdother + 6, 4);
    uint32_t rs13;
    memcpy(&rs13, fdother + 10 + 13*4, 4);
    uint32_t rs14;
    memcpy(&rs14, fdother + 10 + 14*4, 4);
    uint32_t r13_size = rs14 - rs13;
    
    printf("Resource 13: offset=0x%x, size=%u\n\n", rs13, r13_size);
    
    /* Resource 13 starts with "LMI1" then appears to have nested structure */
    /* Check if it follows standard DAT format from offset 4 */
    printf("Header: %c%c%c%c\n", 
           fdother[rs13], fdother[rs13+1], fdother[rs13+2], fdother[rs13+3]);
    
    /* Skip 4-byte magic, check if offset 4 has resource count */
    uint32_t nested_count;
    memcpy(&nested_count, fdother + rs13 + 4, 4);
    printf("Potential nested count at offset 4: %u\n", nested_count);
    
    /* If not valid, try standard DAT from offset 0 */
    if (nested_count > 10000) {
        printf("Invalid count, trying different interpretation...\n");
        
        /* Maybe "LMI1" indicates a different format */
        /* Let's check offset 6 for count (standard DAT has count at offset 6) */
        memcpy(&nested_count, fdother + rs13 + 6, 4);
        printf("Count at offset 6: %u\n", nested_count);
    }
    
    /* Resource 13's actual content structure */
    printf("\n=== Raw hex dump of Resource 13 ===\n");
    for (int i = 0; i < 100 && i < (int)r13_size; i++) {
        if (i % 16 == 0) printf("%04x: ", i);
        printf("%02x ", fdother[rs13 + i]);
        if (i % 16 == 15) printf("\n");
    }
    printf("\n\n");
    
    /* The value at offset 70 is 0xbf01 (48897) */
    /* This should point to actual image data */
    uint32_t bg_offset;
    memcpy(&bg_offset, fdother + rs13 + 70, 4);
    printf("Background offset value: %u (0x%x)\n\n", bg_offset, bg_offset);
    
    /* Since bg_offset > r13_size, it's likely an offset within the nested structure */
    /* Or it could be interpreted differently */
    
    /* Let's check if there's image data starting from different positions */
    printf("=== Scanning for image data patterns ===\n");
    printf("Looking for 310x86 or similar dimensions...\n\n");
    
    for (int pos = 0; pos < (int)r13_size - 4; pos += 2) {
        uint16_t w = fdother[rs13 + pos] | (fdother[rs13 + pos + 1] << 8);
        uint16_t h = fdother[rs13 + pos + 2] | (fdother[rs13 + pos + 3] << 8);
        
        if (w > 50 && w < 400 && h > 20 && h < 250) {
            uint32_t expected = w * h;
            uint32_t available = r13_size - pos - 4;
            
            printf("  At offset %5d (0x%04x): %dx%d, expected %u bytes, available %u bytes\n",
                   pos, pos, w, h, expected, available);
            
            if (available >= expected) {
                printf("    ^^^ VALID candidate!\n");
            }
        }
    }
    
    free(fdother);
    return 0;
}
