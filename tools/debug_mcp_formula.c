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
    
    printf("Resource 13: offset=0x%x, size=%u\n\n", rs13, r13_size);
    
    /* 根据MCP反编译: sub_29BCB中
     * sub_4EBFF(n30 + 35845, *(dword_53F66 + 70) + dword_53F66, 320)
     * 
     * dword_53F66 = 资源13指针
     * *(dword_53F66 + 70) = 位置70的DWORD值
     * 源指针 = 资源13基址 + 位置70的DWORD值
     */
    
    uint32_t dword_at_70;
    memcpy(&dword_at_70, fdother + rs13 + 70, 4);
    printf("DWORD at position 70: %u (0x%08x)\n", dword_at_70, dword_at_70);
    
    uint8_t* source_ptr = fdother + rs13 + dword_at_70;
    uint32_t source_offset = (uint32_t)(source_ptr - fdother);
    printf("Source pointer offset in FDOTHER.DAT: 0x%x\n", source_offset);
    
    /* 检查源数据 */
    if (source_offset < fsize) {
        uint16_t w = source_ptr[0] | (source_ptr[1] << 8);
        uint16_t h = source_ptr[2] | (source_ptr[3] << 8);
        uint32_t avail = fsize - source_offset - 4;
        uint32_t needed = w * h;
        
        printf("\nSource data analysis:\n");
        printf("  Dimensions: %dx%d\n", w, h);
        printf("  Available: %u bytes (to end of file)\n", avail);
        printf("  Needed: %u bytes\n", needed);
        
        if (avail >= needed) {
            printf("  ✓ Sufficient data!\n");
            
            /* 输出前几个像素值验证 */
            printf("\n  First 20 pixel values:\n");
            for (int i = 0; i < 20; i++) {
                printf("    [%2d] = %u (0x%02x)\n", i, source_ptr[4+i], source_ptr[4+i]);
            }
        } else {
            printf("  ✗ Insufficient data\n");
            printf("  Available: %u, Needed: %u\n", avail, needed);
        }
    } else {
        printf("Source offset out of file range!\n");
    }
    
    free(fdother);
    return 0;
}
