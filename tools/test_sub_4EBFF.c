#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

/* sub_4EBFF: Render pixel data block to screen buffer */
/* Based on MCP decompiled code analysis */
void sub_4EBFF(uint8_t* dst_buffer, uint8_t* src_data, int dst_pitch) {
    /* Parse width and height from source data header */
    uint16_t width = src_data[0] | (src_data[1] << 8);
    uint16_t height = src_data[2] | (src_data[3] << 8);
    
    /* Pixel data starts at offset 4 */
    uint8_t* pixel_data = src_data + 4;
    
    /* Render row by row */
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            dst_buffer[x] = *pixel_data++;
        }
        dst_buffer += dst_pitch;  /* Move to next row */
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
    printf("FDOTHER.DAT: %zu bytes, %u resources\n\n", fsize, count);
    
    /* Load resource 13 (background for Load UI) */
    uint32_t rs13;
    memcpy(&rs13, fdother + 10 + 13*4, 4);
    uint32_t rs14;
    memcpy(&rs14, fdother + 10 + 14*4, 4);
    uint32_t r13_size = rs14 - rs13;
    
    printf("Resource 13: offset=0x%x, size=%u\n\n", rs13, r13_size);
    
    /* Get offset at position 70 (pointer to background image) */
    uint32_t bg_offset;
    memcpy(&bg_offset, fdother + rs13 + 70, 4);
    printf("Background image offset: %u (0x%x)\n\n", bg_offset, bg_offset);
    
    /* Background image data */
    uint8_t* bg_data = fdother + rs13 + bg_offset;
    uint16_t bg_width = bg_data[0] | (bg_data[1] << 8);
    uint16_t bg_height = bg_data[2] | (bg_data[3] << 8);
    
    printf("Background: %dx%d pixels\n", bg_width, bg_height);
    printf("Expected size: %u bytes\n", bg_width * bg_height);
    printf("Available: %u bytes\n", r13_size - bg_offset - 4);
    
    /* Test rendering to screen buffer */
    uint8_t* screen = (uint8_t*)calloc(64000, 1);
    
    /* Render background at offset 35845 (as per MCP analysis) */
    sub_4EBFF(screen + 35845, bg_data, 320);
    
    /* Check some pixel values to verify rendering */
    printf("\nVerifying rendered pixels:\n");
    for (int y = 0; y < 5; y++) {
        int row_offset = 35845 + y * 320;
        printf("Row %d (offset %d): ", y, row_offset);
        for (int x = 0; x < 10; x++) {
            printf("%02x ", screen[row_offset + x]);
        }
        printf("...\n");
    }
    
    /* Save to file for inspection */
    FILE* out = fopen("output/test_load_bg.raw", "wb");
    fwrite(screen, 1, 64000, out);
    fclose(out);
    printf("\nSaved to output/test_load_bg.raw\n");
    
    free(screen);
    free(fdother);
    return 0;
}
