#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

/* sub_4EBFF: 渲染像素数据到屏幕缓冲区 */
void sub_4EBFF(uint8_t* dst, uint8_t* src, int pitch) {
    uint16_t w = src[0] | (src[1] << 8);
    uint16_t h = src[2] | (src[3] << 8);
    uint8_t* p = src + 4;
    
    printf("sub_4EBFF: rendering %dx%d image\n", w, h);
    
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
    
    printf("=== Following MCP formula exactly ===\n\n");
    printf("dword_53F66 = resource 13 data pointer = offset 0x%x\n", rs13);
    printf("Resource 13 size: %u bytes\n\n", r13_size);
    
    /* MCP公式: sub_4EBFF(dst, *(dword_53F66 + 70) + dword_53F66, 320) */
    uint32_t dword_at_70;
    memcpy(&dword_at_70, fdother + rs13 + 70, 4);
    
    printf("*(dword_53F66 + 70) = 0x%08x (%u)\n", dword_at_70, dword_at_70);
    printf("dword_53F66 + *(dword_53F66 + 70) = 0x%x + 0x%x = 0x%x\n",
           rs13, dword_at_70, rs13 + dword_at_70);
    
    /* 这个值会超过资源13的范围，因为它是文件内的绝对偏移 */
    uint32_t bg_ptr_offset = rs13 + dword_at_70;
    printf("\nBackground pointer in FDOTHER.DAT: offset 0x%x\n", bg_ptr_offset);
    printf("File size: 0x%x (%u bytes)\n", (uint32_t)fsize, (uint32_t)fsize);
    
    if (bg_ptr_offset < fsize) {
        uint8_t* bg_data = fdother + bg_ptr_offset;
        uint16_t w = bg_data[0] | (bg_data[1] << 8);
        uint16_t h = bg_data[2] | (bg_data[3] << 8);
        uint32_t avail = fsize - bg_ptr_offset - 4;
        uint32_t needed = w * h;
        
        printf("\nBackground image at offset 0x%x:\n", bg_ptr_offset);
        printf("  Dimensions: %dx%d\n", w, h);
        printf("  Available: %u bytes\n", avail);
        printf("  Needed: %u bytes\n", needed);
        
        if (avail >= needed) {
            printf("  ✓ VALID: Can render background!\n\n");
            
            /* 渲染到屏幕缓冲区偏移35845处 */
            uint8_t* screen = (uint8_t*)calloc(64000, 1);
            sub_4EBFF(screen + 35845, bg_data, 320);
            
            /* 验证渲染结果 */
            printf("Rendered pixels (offset 35845):\n");
            for (int y = 0; y < 3; y++) {
                int row = 35845 + y * 320;
                printf("  Row %d: ", y);
                for (int x = 0; x < 10; x++) {
                    printf("%02x ", screen[row + x]);
                }
                printf("...\n");
            }
            
            /* 保存原始数据 */
            FILE* out = fopen("output/load_bg_raw.bin", "wb");
            fwrite(screen, 1, 64000, out);
            fclose(out);
            printf("\nSaved background to output/load_bg_raw.bin\n");
            
            free(screen);
        } else {
            printf("  ✗ INSUFFICIENT DATA\n");
        }
    } else {
        printf("✗ Background pointer out of file range!\n");
    }
    
    free(fdother);
    return 0;
}
