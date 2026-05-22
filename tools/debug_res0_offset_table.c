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
    
    printf("Resource 0: file_offset=0x%x, size=%u\n\n", r0_start, r0_size);
    
    /* 前2字节 */
    int16_t first_val;
    memcpy(&first_val, r0, 2);
    printf("Position 0-1: %d (0x%04x)\n\n", first_val, first_val);
    
    /* 按照公式 arg0 + 2*index 测试多个索引 */
    printf("Testing formula: *(arg0 + 2*index) gives offset, text at arg0+offset\n\n");
    
    int test_indices[] = {0, 1, 2, 10, 20, 23, 24, 25, 100, 514, 515, 549, 550, 676};
    int num_tests = sizeof(test_indices) / sizeof(test_indices[0]);
    
    for (int t = 0; t < num_tests; t++) {
        int idx = test_indices[t];
        size_t pos = 2 * idx;  /* arg0 + 2*idx */
        
        printf("=== Index %d ===\n", idx);
        printf("  Table position: %zu (0x%zx)\n", pos, pos);
        
        if (pos + 2 > r0_size) {
            printf("  OUT OF RANGE (resource size=%u)\n\n", r0_size);
            continue;
        }
        
        int16_t offset_val;
        memcpy(&offset_val, r0 + pos, 2);
        printf("  Offset value: %d (0x%04x)\n", offset_val, offset_val);
        
        if (offset_val < 0 || (size_t)offset_val >= r0_size) {
            printf("  INVALID OFFSET\n\n");
            continue;
        }
        
        /* 显示该偏移处的内容 */
        int16_t* txt = (int16_t*)(r0 + offset_val);
        printf("  Text at arg0+%d: ", offset_val);
        
        int valid = 1;
        for (int j = 0; j < 15; j++) {
            int16_t w = txt[j];
            if (w == -1) {
                printf("[-1]");
                break;
            } else if (w < -20 || w > 2000) {
                printf("[%d] ", w);
                if (j == 0) valid = 0;
            } else {
                printf("%d ", w);
            }
        }
        printf(valid ? "\n  -> VALID TEXT\n\n" : "\n  -> INVALID (garbage)\n\n");
    }
    
    /* 扫描资源0，找到所有看起来像有效偏移的位置 */
    printf("\n=== Scanning resource 0 for valid offset table entries ===\n");
    int valid_entries = 0;
    for (size_t i = 0; i < r0_size / 2; i++) {
        size_t pos = i * 2;
        int16_t val;
        memcpy(&val, r0 + pos, 2);
        
        /* 检查这个值是否是有效偏移 */
        if (val >= 0 && (size_t)val < r0_size) {
            /* 检查该偏移处的内容是否合理 */
            int16_t first_word;
            memcpy(&first_word, r0 + val, 2);
            if ((first_word >= 0 && first_word < 2000) || 
                first_word == -1 || first_word == -2 || 
                first_word == -3 || first_word == -18) {
                valid_entries = (int)i + 1;
            }
        }
    }
    printf("Valid offset table entries: %d (covers indices 0-%d)\n", 
           valid_entries, valid_entries - 1);
    
    free(fdtxt);
    return 0;
}
