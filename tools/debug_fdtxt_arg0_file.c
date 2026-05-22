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
    
    /* 假设arg0是整个文件指针 */
    /* 公式: v15 = (int16*)(*(int16*)(arg0 + 2*arg4) + arg0) */
    
    printf("=== If arg0 = entire FDTXT.DAT file ===\n\n");
    
    /* 测试索引514 */
    int idx = 514;
    size_t pos = 2 * idx;  /* arg0 + 2*514 */
    printf("Index %d: position = %zu (0x%zx)\n", idx, pos, pos);
    
    if (pos + 2 <= fsize) {
        int16_t val;
        memcpy(&val, fdtxt + pos, 2);
        printf("Value at position %zu: %d (0x%04x)\n", pos, val, val);
        
        if (val >= 0 && (size_t)val < fsize) {
            int16_t* txt = (int16_t*)(fdtxt + val);
            printf("Text at arg0+%d: ", val);
            for (int j = 0; j < 20 && txt[j] != -1; j++) {
                printf("%d ", txt[j]);
            }
            printf("\n");
        }
    }
    
    /* 测试索引515 */
    idx = 515;
    pos = 2 * idx;
    printf("\nIndex %d: position = %zu\n", idx, pos);
    
    if (pos + 2 <= fsize) {
        int16_t val;
        memcpy(&val, fdtxt + pos, 2);
        printf("Value: %d (0x%04x)\n", val, val);
        
        if (val >= 0 && (size_t)val < fsize) {
            int16_t* txt = (int16_t*)(fdtxt + val);
            printf("Text: ");
            for (int j = 0; j < 15 && txt[j] != -1; j++) {
                printf("%d ", txt[j]);
            }
            printf("\n");
        }
    }
    
    /* 测试场景索引162 (514+162=676) */
    idx = 514 + 162;
    pos = 2 * idx;
    printf("\nIndex %d (514+162): position = %zu\n", idx, pos);
    
    if (pos + 2 <= fsize) {
        int16_t val;
        memcpy(&val, fdtxt + pos, 2);
        printf("Value: %d (0x%04x)\n", val, val);
        
        if (val >= 0 && (size_t)val < fsize) {
            int16_t* txt = (int16_t*)(fdtxt + val);
            printf("Text: ");
            for (int j = 0; j < 15 && txt[j] != -1; j++) {
                printf("%d ", txt[j]);
            }
            printf("\n");
        }
    }
    
    /* 显示位置1024-1050的十六进制 */
    printf("\nFile bytes 1024-1050:\n");
    for (int i = 1024; i < 1060 && i < (int)fsize; i++) {
        if (i % 16 == 0) printf("  %04x: ", i);
        printf("%02x ", fdtxt[i]);
    }
    printf("\n");
    
    /* 检查文件级别偏移表（从位置10开始） */
    printf("\n=== File-level offset table (pos 10+, 4-byte entries) ===\n");
    dword count;
    memcpy(&count, fdtxt + 6, 4);
    printf("Resource count: %u\n", count);
    
    /* 检查索引514在文件偏移表中的值 */
    /* 文件偏移表: 位置10 + 514*4 = 2066 */
    int file_off_pos = 10 + 514 * 4;
    printf("\nFile offset table index 514: position %d\n", file_off_pos);
    if (file_off_pos + 4 <= fsize) {
        dword val;
        memcpy(&val, fdtxt + file_off_pos, 4);
        printf("Value: %u (0x%x)\n", val, val);
    }
    
    free(fdtxt);
    return 0;
}
