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
    
    uint32_t rs13;
    memcpy(&rs13, fdother + 10 + 13*4, 4);
    uint32_t rs14;
    memcpy(&rs14, fdother + 10 + 14*4, 4);
    uint32_t r13_size = rs14 - rs13;
    
    printf("Resource 13: offset=0x%x, size=%u\n\n", rs13, r13_size);
    
    /* The offset table starts at position 8, 2-byte entries */
    /* Position 66-70 contain: 0xbecd, 0xbf01 */
    /* These are offsets into the resource */
    
    printf("=== Offset table entries around position 70 ===\n");
    for (int i = 30; i < 35; i++) {
        uint16_t off;
        memcpy(&off, fdother + rs13 + 8 + i*2, 2);
        uint16_t next_off;
        if (i + 1 < 35)
            memcpy(&next_off, fdother + rs13 + 8 + (i+1)*2, 2);
        else
            next_off = (uint16_t)r13_size;
        
        uint32_t entry_size = next_off - off;
        printf("Entry %d (pos %d): offset=%5u (0x%04x), size=%u\n", 
               i, 8+i*2, off, off, entry_size);
    }
    
    /* Entry 31 at position 70 has offset 0xBF01 (48897) */
    /* Let's check the image data at this offset */
    uint16_t offset_31;
    memcpy(&offset_31, fdother + rs13 + 70, 2);
    printf("\nEntry 31 offset: %u (0x%04x)\n", offset_31, offset_31);
    
    /* Check data at this offset */
    uint8_t* img_data = fdother + rs13 + offset_31;
    uint16_t w = img_data[0] | (img_data[1] << 8);
    uint16_t h = img_data[2] | (img_data[3] << 8);
    uint32_t avail = r13_size - offset_31 - 4;
    
    printf("\nImage data at offset %u:\n", offset_31);
    printf("  Width: %u, Height: %u\n", w, h);
    printf("  Available: %u bytes\n", avail);
    printf("  Needed: %u bytes (%ux%u)\n", w * h, w, h);
    
    /* Let's check the previous entry (entry 30 at position 68) */
    printf("\n=== Checking entry 30 (previous) ===\n");
    uint16_t offset_30;
    memcpy(&offset_30, fdother + rs13 + 68, 2);
    printf("Entry 30 offset: %u (0x%04x)\n", offset_30, offset_30);
    
    uint8_t* prev_data = fdother + rs13 + offset_30;
    uint16_t pw = prev_data[0] | (prev_data[1] << 8);
    uint16_t ph = prev_data[2] | (prev_data[3] << 8);
    printf("  Previous image: %dx%d\n", pw, ph);
    
    /* Check entry 15 which has large offset 0xbf01 */
    printf("\n=== Entry 15 (pos 38) has offset 0xBF01 ===\n");
    uint16_t offset_15;
    memcpy(&offset_15, fdother + rs13 + 38, 2);
    printf("Entry 15 offset: %u (0x%04x)\n", offset_15, offset_15);
    
    free(fdother);
    return 0;
}
