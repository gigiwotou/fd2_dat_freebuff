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
    
    /* 资源0的数据 */
    dword r0_start, r0_end;
    memcpy(&r0_start, fdtxt + 10, 4);
    memcpy(&r0_end, fdtxt + 14, 4);
    u8* r0 = fdtxt + r0_start;
    dword r0_size = r0_end - r0_start;
    
    printf("Resource 0: file_offset=0x%x, size=%u\n\n", r0_start, r0_size);
    
    /* 检查资源0是否是嵌套的DAT */
    if (r0_size >= 10 && memcmp(r0, "LLLLLL", 6) == 0) {
        printf("*** Resource 0 is a NESTED DAT! ***\n");
        dword nc;
        memcpy(&nc, r0 + 6, 4);
        printf("Nested count: %u\n", nc);
    } else {
        printf("Resource 0 is NOT a nested DAT\n");
        printf("First 10 bytes: ");
        for (int i = 0; i < 10; i++) printf("%02x ", r0[i]);
        printf("\n");
    }
    
    /* 检查资源0前2字节的值 */
    int16_t first_2bytes;
    memcpy(&first_2bytes, r0, 2);
    printf("First 2 bytes as int16: %d\n", first_2bytes);
    
    /* 如果前2字节不是24，说明偏移表可能更大 */
    if (first_2bytes > 100) {
        printf("Resource 0 has %d sub-texts!\n", first_2bytes);
        
        /* 检查位置1030 (2+514*2) */
        int pos = 2 + 514 * 2;
        if (pos + 2 <= r0_size) {
            int16_t val;
            memcpy(&val, r0 + pos, 2);
            printf("\nIndex 514 offset value: %d\n", val);
            
            if (val >= 0 && val < 200 && 2 + val*2 + 2 <= r0_size) {
                int16_t* txt = (int16_t*)(r0 + 2 + val*2);
                printf("Text content: ");
                for (int j = 0; j < 30 && txt[j] != -1; j++) {
                    printf("%d ", txt[j]);
                }
                printf("\n");
            }
        }
    }
    
    /* 扫描资源0，查找所有可能的2字节值 */
    printf("\n=== Scanning resource 0 for structure ===\n");
    printf("Position 0-50 (hex):\n");
    for (int i = 0; i < 50 && i < (int)r0_size; i++) {
        if (i % 16 == 0) printf("\n  %04x: ", i);
        printf("%02x ", r0[i]);
    }
    printf("\n");
    
    /* 将资源0作为int16数组显示前50个字 */
    printf("\nResource 0 as int16 array (first 50 words):\n");
    int16_t* words = (int16_t*)r0;
    for (int i = 0; i < 50 && (i*2+2) < r0_size; i++) {
        printf("  [%2d] %5d (0x%04x)", i, words[i], words[i]);
        if (i % 3 == 2) printf("\n");
        else printf("  ");
    }
    printf("\n");
    
    free(fdtxt);
    return 0;
}
