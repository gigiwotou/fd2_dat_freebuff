#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

/* sub_4EBFF: Render image to screen buffer */
void sub_4EBFF(uint8_t* dst, uint8_t* src, int pitch) {
    uint16_t w = src[0] | (src[1] << 8);
    uint16_t h = src[2] | (src[3] << 8);
    uint8_t* p = src + 4;
    
    printf("[sub_4EBFF] Rendering %dx%d image\n", w, h);
    
    for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
            dst[x] = *p++;
        }
        dst += pitch;
    }
}

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
    
    printf("=== Exact byte-level analysis ===\n\n");
    printf("Resource 13: base=0x%x, size=%u\n", rs13, r13_size);
    
    /* Print bytes 65-80 to see the structure around position 70 */
    printf("\nBytes around position 70:\n");
    for (int i = 65; i < 80; i++) {
        printf("  [%3d] = 0x%02x\n", i, fdother[rs13 + i]);
    }
    
    /* Read as DWORD at position 70 */
    uint32_t dword70;
    memcpy(&dword70, fdother + rs13 + 70, 4);
    printf("\nDWORD at position 70 (little-endian): 0x%08x (%u)\n", dword70, dword70);
    
    /* Source pointer calculation: rs13 + dword70 */
    uint32_t src_offset = rs13 + dword70;
    printf("Source offset in file: 0x%x\n", src_offset);
    
    if (src_offset < fsize - 4) {
        uint8_t* img_data = fdother + src_offset;
        uint16_t w = img_data[0] | (img_data[1] << 8);
        uint16_t h = img_data[2] | (img_data[3] << 8);
        uint32_t avail = fsize - src_offset - 4;
        
        printf("\nImage data at 0x%x:\n", src_offset);
        printf("  Dimensions: %dx%d\n", w, h);
        printf("  Expected size: %u bytes\n", w * h);
        printf("  Available: %u bytes\n", avail);
        
        if (avail >= w * h) {
            printf("  ✓ Data is sufficient!\n");
            
            /* Show first few pixel values */
            printf("\n  First 16 pixel values:\n");
            for (int i = 0; i < 16; i++) {
                printf("    [%2d] = %3u (0x%02x)\n", i, img_data[4+i], img_data[4+i]);
            }
            
            /* Test render */
            uint8_t* screen = (uint8_t*)calloc(64000, 1);
            sub_4EBFF(screen + 35845, img_data, 320);
            
            /* Save for inspection */
            FILE* out = fopen("output/test_bg_final.raw", "wb");
            fwrite(screen, 1, 64000, out);
            fclose(out);
            printf("\n  Saved to output/test_bg_final.raw\n");
            
            free(screen);
        } else {
            printf("  ✗ Insufficient data by %u bytes\n", w * h - avail);
        }
    } else {
        printf("✗ Source offset out of file range!\n");
    }
    
    free(fdother);
    return 0;
}
