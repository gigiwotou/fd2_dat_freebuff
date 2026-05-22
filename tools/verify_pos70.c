#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

/* sub_4EBFF: Render pixel data to screen buffer */
void sub_4EBFF(uint8_t* dst, uint8_t* src, int pitch) {
    uint16_t w = src[0] | (src[1] << 8);
    uint16_t h = src[2] | (src[3] << 8);
    uint8_t* p = src + 4;
    
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
    
    printf("Resource 13: offset=0x%x, size=%u\n\n", rs13, r13_size);
    
    /* Offset table at position 8, 2-byte entries */
    printf("=== Offset table (2-byte entries from position 8) ===\n");
    for (int i = 0; i < 60 && (8 + i*2) < r13_size; i++) {
        uint16_t off;
        memcpy(&off, fdother + rs13 + 8 + i*2, 2);
        
        uint16_t next_off;
        if (i + 1 < 60)
            memcpy(&next_off, fdother + rs13 + 8 + (i+1)*2, 2);
        else
            next_off = (uint16_t)r13_size;
        
        printf("  [%2d] pos=%3d: offset=%5u (0x%04x)\n", i, 8+i*2, off, off);
        
        /* Print entry 31 specially (position 70) */
        if (i == 31) {
            printf("       ^^^ This is at position 70!\n");
            
            /* Check data at this offset */
            if (off < r13_size) {
                uint16_t w = fdother[rs13 + off] | (fdother[rs13 + off + 1] << 8);
                uint16_t h = fdother[rs13 + off + 2] | (fdother[rs13 + off + 3] << 8);
                printf("       Image at offset %u: %dx%d\n", off, w, h);
                printf("       Available: %u bytes, Required: %u bytes\n",
                       r13_size - off - 4, w * h);
            }
        }
    }
    
    /* Now let's also check the offset at position 70 */
    printf("\n=== Value at position 70 ===\n");
    uint16_t pos70_val;
    memcpy(&pos70_val, fdother + rs13 + 70, 2);
    printf("16-bit value: %u (0x%04x)\n", pos70_val, pos70_val);
    
    if (pos70_val < r13_size) {
        /* This points to image data */
        uint8_t* img_data = fdother + rs13 + pos70_val;
        uint16_t w = img_data[0] | (img_data[1] << 8);
        uint16_t h = img_data[2] | (img_data[3] << 8);
        printf("Image dimensions: %dx%d\n", w, h);
        printf("Available data: %u bytes\n", r13_size - pos70_val - 4);
        
        if (r13_size - pos70_val - 4 >= w * h) {
            printf("✓ VALID: Sufficient data for rendering!\n");
            
            /* Test render to screen buffer */
            uint8_t* screen = (uint8_t*)calloc(64000, 1);
            sub_4EBFF(screen + 35845, img_data, 320);
            
            /* Verify some pixels */
            printf("\nRendered pixels at offset 35845:\n");
            for (int y = 0; y < 3; y++) {
                int row = 35845 + y * 320;
                printf("  Row %d: ", y);
                for (int x = 0; x < 10; x++) {
                    printf("%02x ", screen[row + x]);
                }
                printf("...\n");
            }
            
            /* Save for inspection */
            FILE* out = fopen("output/test_bg_render.raw", "wb");
            fwrite(screen, 1, 64000, out);
            fclose(out);
            printf("\nSaved to output/test_bg_render.raw\n");
            
            free(screen);
        } else {
            printf("✗ INVALID: Insufficient data\n");
        }
    }
    
    free(fdother);
    return 0;
}
