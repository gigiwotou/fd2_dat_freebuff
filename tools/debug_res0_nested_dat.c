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
    
    /* 资源0 */
    dword r0_start, r0_end;
    memcpy(&r0_start, fdtxt + 10, 4);
    memcpy(&r0_end, fdtxt + 14, 4);
    u8* r0 = fdtxt + r0_start;
    dword r0_size = r0_end - r0_start;
    
    printf("Resource 0: file_offset=0x%x, size=%u bytes\n\n", r0_start, r0_size);
    
    /* 关键：分析资源0的真实结构 */
    printf("=== Analyzing resource 0 structure ===\n\n");
    
    /* 1. 检查是否是嵌套DAT */
    if (r0_size >= 10 && memcmp(r0, "LLLLLL", 6) == 0) {
        printf("*** Resource 0 IS a nested DAT! ***\n");
        dword nc;
        memcpy(&nc, r0 + 6, 4);
        printf("Nested resource count: %u\n\n", nc);
        
        /* 显示嵌套DAT的偏移表 */
        printf("Nested offset table (first 20):\n");
        for (int i = 0; i < 20 && i < (int)nc; i++) {
            dword off;
            memcpy(&off, r0 + 10 + i*4, 4);
            printf("  [%d] 0x%x (%u)\n", i, off, off);
        }
        
        /* 在嵌套DAT中查找索引514 */
        printf("\n=== Looking for index 514 in nested DAT ===\n");
        if (514 < nc) {
            dword off;
            memcpy(&off, r0 + 10 + 514*4, 4);
            printf("Index 514 offset: %u (0x%x)\n", off, off);
            
            if (off < r0_size) {
                /* 读取该偏移处的内容 */
                int16_t sc;
                memcpy(&sc, r0 + off, 2);
                printf("Sub-text count: %d\n", sc);
                
                if (sc > 0 && sc < 100) {
                    int16_t* subs = (int16_t*)(r0 + off + 2);
                    printf("First sub-text: ");
                    if (off + 2 + subs[0]*2 + 2 < r0_size) {
                        int16_t* txt = (int16_t*)(r0 + off + 2 + subs[0]*2);
                        for (int j = 0; j < 20 && txt[j] != -1; j++) {
                            printf("%d ", txt[j]);
                        }
                        printf("\n");
                    }
                }
            }
        } else {
            printf("Index 514 out of nested DAT range (count=%u)\n", nc);
        }
    } else {
        printf("Resource 0 is NOT a nested DAT\n");
        printf("First 50 bytes: ");
        for (int i = 0; i < 50 && i < (int)r0_size; i++) {
            printf("%02x ", r0[i]);
        }
        printf("\n");
    }
    
    /* 2. 尝试将整个资源0作为int16数组分析 */
    printf("\n=== Resource 0 as int16 array ===\n");
    int16_t* words = (int16_t*)r0;
    int num_words = r0_size / 2;
    
    printf("Total words: %d\n", num_words);
    printf("\nFirst 30 words:\n");
    for (int i = 0; i < 30 && i < num_words; i++) {
        printf("  [%3d] %6d (0x%04x)", i, words[i], words[i]);
        if (i % 2 == 1) printf("\n");
        else printf("  ");
    }
    printf("\n");
    
    /* 查找所有看起来像偏移表的位置 */
    printf("\n=== Scanning for offset table patterns ===\n");
    printf("Checking if words[0-23] could be offset table:\n");
    int all_valid = 1;
    for (int i = 0; i < 24; i++) {
        int16_t off = words[i];
        if (off < 0 || off >= num_words) {
            all_valid = 0;
            printf("  [%d] %d - INVALID\n", i, off);
        } else {
            printf("  [%d] %d -> ", i, off);
            /* 检查该位置的内容 */
            int16_t first_word = words[off];
            if (first_word >= -20 && first_word < 2000) {
                printf("valid (first word=%d)\n", first_word);
            } else {
                printf("INVALID (first word=%d)\n", first_word);
            }
        }
    }
    
    if (all_valid) {
        printf("\n*** First 24 words form a valid offset table! ***\n");
    }
    
    free(fdtxt);
    return 0;
}
