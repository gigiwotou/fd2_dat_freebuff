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
    
    printf("FDTXT.DAT size: %zu\n\n", fsize);
    
    dword count;
    memcpy(&count, fdtxt + 6, 4);
    printf("Resource count: %u\n\n", count);
    
    /* 分析文件级别偏移表 */
    printf("=== File-level offset table (4-byte entries at pos 10) ===\n");
    printf("Checking all 33 valid entries:\n\n");
    
    int valid_count = 0;
    for (int i = 0; i < (int)count && i < 146; i++) {
        dword rs, re;
        memcpy(&rs, fdtxt + 10 + i*4, 4);
        if (i + 1 < (int)count)
            memcpy(&re, fdtxt + 10 + (i+1)*4, 4);
        else
            re = (dword)fsize;
        
        if (rs < fsize && rs > 0) {
            valid_count++;
            dword rsize = re - rs;
            
            /* 检查该资源是否是FDTXT格式（前2字节是子文本数量） */
            if (rsize >= 2) {
                int16_t sc;
                memcpy(&sc, fdtxt + rs, 2);
                
                printf("Resource %3d: offset=0x%05x, size=%5u, sub-count=%4d", 
                       i, rs, rsize, sc);
                
                /* 如果子文本数量合理，显示第一个子文本 */
                if (sc > 0 && sc < 1000 && rsize >= 4) {
                    int16_t first_off;
                    memcpy(&first_off, fdtxt + rs + 2, 2);
                    if (first_off >= 0 && rs + 2 + first_off*2 + 2 < fsize) {
                        int16_t* txt = (int16_t*)(fdtxt + rs + 2 + first_off*2);
                        printf(" -> first text: ");
                        for (int j = 0; j < 15 && txt[j] != -1; j++) {
                            printf("%d ", txt[j]);
                        }
                    }
                }
                printf("\n");
            }
        }
    }
    
    printf("\nTotal valid resources: %d\n", valid_count);
    
    /* 特别检查资源27-35（可能包含关卡名称） */
    printf("\n=== Detailed check of resources 27-35 ===\n");
    for (int i = 27; i <= 35 && i < (int)count; i++) {
        dword rs, re;
        memcpy(&rs, fdtxt + 10 + i*4, 4);
        if (i + 1 < (int)count)
            memcpy(&re, fdtxt + 10 + (i+1)*4, 4);
        else
            re = (dword)fsize;
        
        if (rs < fsize && rs > 0) {
            printf("\nResource %d (offset 0x%x, size %u):\n", i, rs, re-rs);
            int16_t sc;
            memcpy(&sc, fdtxt + rs, 2);
            printf("  Sub-text count: %d\n", sc);
            
            if (sc > 0 && sc < 200) {
                printf("  First 5 sub-texts:\n");
                for (int j = 0; j < 5 && j < sc; j++) {
                    int16_t off;
                    memcpy(&off, fdtxt + rs + 2 + j*2, 2);
                    printf("    [%d] offset=%d -> ", j, off);
                    if (off >= 0 && rs + 2 + off*2 + 2 < fsize) {
                        int16_t* txt = (int16_t*)(fdtxt + rs + 2 + off*2);
                        for (int k = 0; k < 10 && txt[k] != -1; k++) {
                            printf("%d ", txt[k]);
                        }
                        printf("\n");
                    } else {
                        printf("(out of range)\n");
                    }
                }
            }
        }
    }
    
    free(fdtxt);
    return 0;
}
