#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

/* sub_4EBFF: 渲染像素数据到屏幕缓冲区 */
/* 根据MCP反编译代码1:1实现 */
void sub_4EBFF(uint8_t* dst, uint8_t* src, int pitch) {
    uint16_t w = src[0] | (src[1] << 8);
    uint16_t h = src[2] | (src[3] << 8);
    uint8_t* p = src + 4;
    
    printf("sub_4EBFF: %dx%d pixels, rendering to pitch=%d\n", w, h, pitch);
    
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
    
    /* 偏移表从位置8开始，2字节每项 */
    printf("=== Offset table (2-byte entries, position 8+) ===\n");
    printf("Checking entry at position 70 (entry %d)\n\n", (70 - 8) / 2);
    
    /* 打印位置60-80的字节 */
    printf("Bytes at position 60-80:\n");
    for (int i = 60; i < 80; i++) {
        printf("  pos[%d] = 0x%02x\n", i, fdother[rs13 + i]);
    }
    printf("\n");
    
    /* 16-bit值在位置70 */
    uint16_t pos70;
    memcpy(&pos70, fdother + rs13 + 70, 2);
    printf("16-bit value at position 70: %u (0x%04x)\n\n", pos70, pos70);
    
    if (pos70 < r13_size) {
        uint8_t* img_data = fdother + rs13 + pos70;
        uint16_t w = img_data[0] | (img_data[1] << 8);
        uint16_t h = img_data[2] | (img_data[3] << 8);
        uint32_t avail = r13_size - pos70 - 4;
        uint32_t needed = w * h;
        
        printf("Image at offset %u:\n", pos70);
        printf("  Dimensions: %dx%d\n", w, h);
        printf("  Available: %u bytes\n", avail);
        printf("  Needed: %u bytes\n", needed);
        printf("  Ratio: %.1f%%\n", (float)avail / needed * 100);
        
        if (avail < needed) {
            printf("\n  WARNING: Insufficient data!\n");
            printf("  Checking if data wraps around or uses different encoding...\n\n");
            
            /* 检查偏移表其他条目 */
            printf("Other offset table entries:\n");
            for (int i = 0; i < 10; i++) {
                uint16_t off;
                memcpy(&off, fdother + rs13 + 8 + i*2, 2);
                printf("  Entry %d (pos %d): %u (0x%04x)\n", i, 8+i*2, off, off);
            }
        }
    }
    
    free(fdother);
    return 0;
}
