#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

typedef unsigned char u8;
typedef unsigned int dword;

int main() {
    FILE* fp = fopen("game/FDTXT.DAT", "rb");
    if (!fp) { printf("Cannot open FDTXT.DAT\n"); return 1; }
    
    fseek(fp, 0, SEEK_END);
    size_t fsize = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    
    u8* fdtxt = (u8*)malloc(fsize);
    fread(fdtxt, 1, fsize, fp);
    fclose(fp);
    
    printf("FDTXT.DAT size: %zu\n", fsize);
    printf("Magic: %.*s\n", 6, fdtxt);
    
    dword count;
    memcpy(&count, fdtxt + 6, 4);
    printf("Resource count: %u\n", count);
    
    /* 检查资源0的结构 */
    printf("\n=== Analyzing Resource 0 ===\n");
    dword r0_start, r0_end;
    memcpy(&r0_start, fdtxt + 10, 4);
    memcpy(&r0_end, fdtxt + 14, 4);
    printf("Resource 0: offset=0x%x, end=0x%x, size=%u\n", r0_start, r0_end, r0_end - r0_start);
    
    u8* r0 = fdtxt + r0_start;
    dword r0_size = r0_end - r0_start;
    
    /* 前2字节声明的子文本数量 */
    int16_t declared_count;
    memcpy(&declared_count, r0, 2);
    printf("Declared sub-text count: %d\n", declared_count);
    
    /* 检查是否是嵌套DAT */
    if (r0_size >= 10 && memcmp(r0, "LLLLLL", 6) == 0) {
        printf("*** Resource 0 is a nested DAT! ***\n");
        dword nc;
        memcpy(&nc, r0 + 6, 4);
        printf("Nested count: %u\n", nc);
    } else {
        /* 普通FDTXT资源，分析偏移表 */
        printf("\nOffset table at resource start:\n");
        printf("Position 2+514*2 = %d (0x%x)\n", 2 + 514*2, 2 + 514*2);
        
        if (2 + 514*2 + 2 <= r0_size) {
            int16_t offset_val;
            memcpy(&offset_val, r0 + 2 + 514*2, 2);
            printf("Index 514 offset: %d (0x%04x)\n", offset_val, offset_val);
            
            if (offset_val >= 0 && offset_val < 200 && 2 + offset_val*2 + 2 <= r0_size) {
                int16_t* txt = (int16_t*)(r0 + 2 + offset_val*2);
                printf("Text content: ");
                for (int j = 0; j < 30 && txt[j] != -1; j++) {
                    printf("%d ", txt[j]);
                }
                printf("\n");
            }
        } else {
            printf("Index 514 out of range in resource 0 (need %d bytes, have %u)\n", 
                   2 + 514*2 + 2, r0_size);
        }
    }
    
    /* 扫描整个文件，查找子文本数量接近514的资源 */
    printf("\n=== Searching for resources with ~514+ sub-texts ===\n");
    for (int i = 0; i < (int)count && i < 146; i++) {
        dword rs, re;
        memcpy(&rs, fdtxt + 10 + i*4, 4);
        if (i + 1 < (int)count)
            memcpy(&re, fdtxt + 10 + (i+1)*4, 4);
        else
            re = (dword)fsize;
        
        if (rs < fsize && (re - rs) >= 2) {
            int16_t sc;
            memcpy(&sc, fdtxt + rs, 2);
            if (sc >= 500 && sc < 1000) {
                printf("Resource %d: sub-count=%d, size=%u *** CANDIDATE ***\n", 
                       i, sc, re - rs);
            }
        }
    }
    
    /* 关键：检查位置 10+514*4 的文件偏移 */
    printf("\n=== Checking file-level offset at 10+514*4 ===\n");
    int file_pos = 10 + 514 * 4;
    if (file_pos + 4 <= fsize) {
        dword val;
        memcpy(&val, fdtxt + file_pos, 4);
        printf("Value at file position %d: %u (0x%x)\n", file_pos, val, val);
        
        if (val < fsize) {
            int16_t sc;
            memcpy(&sc, fdtxt + val, 2);
            printf("Resource at this offset: sub-count=%d\n", sc);
        }
    }
    
    free(fdtxt);
    return 0;
}
