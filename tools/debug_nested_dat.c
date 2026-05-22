#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

typedef unsigned char u8;
typedef unsigned int dword;

int main() {
    FILE* fp = fopen("game/FDOTHER.DAT", "rb");
    if (!fp) { printf("Cannot open FDOTHER.DAT\n"); return 1; }
    
    fseek(fp, 0, SEEK_END);
    size_t fsize = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    
    u8* data = (u8*)malloc(fsize);
    fread(data, 1, fsize, fp);
    fclose(fp);
    
    printf("FDOTHER.DAT size: %zu\n", fsize);
    
    /* 搜索所有嵌套DAT */
    printf("\nSearching for nested DAT files (magic='LLLLLL'):\n");
    int nested_count = 0;
    for (size_t i = 0; i < fsize - 10; i++) {
        if (memcmp(data + i, "LLLLLL", 6) == 0) {
            dword nc;
            memcpy(&nc, data + i + 6, 4);
            if (nc > 0 && nc < 1000) {
                printf("  Found at offset 0x%zx: nested DAT with %u resources\n", i, nc);
                nested_count++;
                
                /* 显示前5个资源的偏移 */
                printf("    First 5 resource offsets:");
                for (int j = 0; j < 5 && j < (int)nc; j++) {
                    dword roff;
                    memcpy(&roff, data + i + 10 + j * 4, 4);
                    printf(" [%d]=0x%x", j, roff);
                }
                printf("\n");
            }
        }
    }
    printf("Total nested DAT files found: %d\n", nested_count);
    
    /* 显示资源3的前50个字符图案 */
    printf("\n\n=== Resource 3 (font) character patterns ===\n");
    dword r3_start, r3_end;
    memcpy(&r3_start, data + 10 + 3 * 4, 4);
    memcpy(&r3_end, data + 10 + 4 * 4, 4);
    printf("Resource 3: offset 0x%x - 0x%x, size=%u, chars=%d\n", 
           r3_start, r3_end, r3_end - r3_start, (r3_end - r3_start) / 32);
    
    /* 显示字形0, 1, 514, 515的图案 */
    int indices[] = {0, 1, 2, 3, 514, 515, 516, 517};
    for (int idx_idx = 0; idx_idx < 8; idx_idx++) {
        int idx = indices[idx_idx];
        printf("\nCharacter %d:\n", idx);
        u8* cdata = data + r3_start + idx * 32;
        for (int row = 0; row < 16; row++) {
            uint16_t bits;
            memcpy(&bits, cdata + row * 2, 2);
            bits = ((bits & 0xFF) << 8) | ((bits >> 8) & 0xFF);
            for (int col = 0; col < 16; col++) {
                printf("%c", (bits & (1 << (15 - col))) ? '#' : '.');
            }
            printf("\n");
        }
    }
    
    /* 检查资源13（原游戏Load使用的资源） */
    printf("\n\n=== Resource 13 (used by Load) ===\n");
    dword r13_start, r13_end;
    memcpy(&r13_start, data + 10 + 13 * 4, 4);
    memcpy(&r13_end, data + 10 + 14 * 4, 4);
    printf("Resource 13: offset 0x%x - 0x%x, size=%u\n", r13_start, r13_end, r13_end - r13_start);
    printf("First 20 bytes: ");
    for (int i = 0; i < 20 && i < (int)(r13_end - r13_start); i++) {
        printf("%02x ", data[r13_start + i]);
    }
    printf("\n");
    
    /* 检查是否是嵌套DAT */
    if (r13_end - r13_start >= 10 && memcmp(data + r13_start, "LLLLLL", 6) == 0) {
        dword nc;
        memcpy(&nc, data + r13_start + 6, 4);
        printf("Resource 13 is nested DAT with %u resources\n", nc);
    }
    
    free(data);
    return 0;
}
