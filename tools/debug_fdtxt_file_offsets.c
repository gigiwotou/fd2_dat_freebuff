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
    printf("Declared resource count: %u\n", count);
    
    /* 分析文件级别偏移表 */
    printf("\n=== File-level offset table (4-byte entries) ===\n");
    printf("Checking entries near index 514:\n");
    
    /* 偏移表从位置10开始，每个条目4字节 */
    /* 检查索引0, 1, 513, 514, 515, 549, 550 */
    int indices[] = {0, 1, 513, 514, 515, 549, 550};
    
    for (int t = 0; t < 7; t++) {
        int idx = indices[t];
        int pos = 10 + idx * 4;
        
        if (pos + 4 <= fsize) {
            dword val;
            memcpy(&val, fdtxt + pos, 4);
            printf("  Index %3d at pos %5d (0x%04x): value=%u (0x%x)", idx, pos, pos, val, val);
            
            if (val < fsize && val > 0) {
                printf(" -> points to valid location");
                /* 读取该位置的内容 */
                int16_t sc;
                memcpy(&sc, fdtxt + val, 2);
                if (sc > 0 && sc < 2000) {
                    printf(", sub-count=%d", sc);
                }
            }
            printf("\n");
        } else {
            printf("  Index %3d: OUT OF RANGE\n", idx);
        }
    }
    
    /* 计算实际有多少个有效的文件级别条目 */
    printf("\n=== Counting valid file-level entries ===\n");
    int max_valid = 0;
    for (int i = 0; i < 2000; i++) {
        int pos = 10 + i * 4;
        if (pos + 4 > fsize) {
            printf("Stopped at index %d (file end)\n", i);
            break;
        }
        
        dword val;
        memcpy(&val, fdtxt + pos, 4);
        if (val > 0 && val < fsize) {
            max_valid = i + 1;
        } else if (i > 100) {
            /* 连续遇到无效值，停止 */
            printf("Stopped at index %d (invalid offset)\n", i);
            break;
        }
    }
    printf("Max valid file-level entries: %d\n", max_valid);
    
    /* 显示索引514指向的资源内容 */
    int pos_514 = 10 + 514 * 4;
    if (pos_514 + 4 <= fsize) {
        dword val;
        memcpy(&val, fdtxt + pos_514, 4);
        
        if (val < fsize) {
            printf("\n=== Resource at index 514 (offset 0x%x) ===\n", val);
            int16_t sc;
            memcpy(&sc, fdtxt + val, 2);
            printf("Sub-text count: %d\n", sc);
            
            if (sc > 0 && sc < 100) {
                int16_t* offsets = (int16_t*)(fdtxt + val + 2);
                printf("First 5 sub-texts:\n");
                for (int i = 0; i < 5 && i < sc && (val + 2 + (i+1)*2) < fsize; i++) {
                    printf("  [%d] offset=%d", i, offsets[i]);
                    if (offsets[i] >= 0 && val + 2 + offsets[i]*2 + 2 < fsize) {
                        int16_t first_word;
                        memcpy(&first_word, fdtxt + val + 2 + offsets[i]*2, 2);
                        printf(" -> words: %d", first_word);
                        if (first_word >= 0 && val + 2 + offsets[i]*2 + 4 < fsize) {
                            int16_t second_word;
                            memcpy(&second_word, fdtxt + val + 2 + offsets[i]*2 + 2, 2);
                            printf(", %d", second_word);
                        }
                    }
                    printf("\n");
                }
            }
        }
    }
    
    free(fdtxt);
    return 0;
}
