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
    u8* r0_data = fdtxt + r0_start;
    dword r0_size = r0_end - r0_start;
    
    printf("Resource 0: offset=0x%x, size=%u bytes\n\n", r0_start, r0_size);
    
    /* 显示前100字节 */
    printf("First 100 bytes (hex dump):\n");
    for (int i = 0; i < 100 && i < (int)r0_size; i++) {
        if (i % 16 == 0) printf("\n  %04x: ", i);
        printf("%02x ", r0_data[i]);
    }
    printf("\n");
    
    /* 前2字节是子文本数量 */
    int16_t count;
    memcpy(&count, r0_data, 2);
    printf("\nDeclared sub-text count: %d\n", count);
    
    /* 分析偏移表 */
    printf("\nOffset table analysis:\n");
    int16_t* offsets = (int16_t*)(r0_data + 2);
    
    /* 找到实际使用的偏移表条目数量 */
    int actual_entries = 0;
    for (int i = 0; i < count && (i+1)*2 + 2 < r0_size; i++) {
        int16_t off = offsets[i];
        if (off >= 0 && off < 200) {
            /* 检查偏移指向的位置是否有合理的文本 */
            if (2 + off * 2 < r0_size) {
                int16_t first_word;
                memcpy(&first_word, r0_data + 2 + off * 2, 2);
                if (first_word >= -20 && first_word < 2000) {
                    actual_entries = i + 1;
                }
            }
        }
    }
    printf("Actual valid offset entries: %d\n", actual_entries);
    
    /* 显示前10个子文本的内容 */
    printf("\nFirst 10 sub-texts content:\n");
    for (int i = 0; i < 10 && i < actual_entries; i++) {
        int16_t off = offsets[i];
        printf("  [%d] offset=%d, content: ", i, off);
        int16_t* txt = (int16_t*)(r0_data + 2 + off * 2);
        for (int j = 0; j < 20 && txt[j] != -1; j++) {
            printf("%d ", txt[j]);
        }
        printf("\n");
    }
    
    /* 关键：检查位置 2+514*2 = 1030 处的值 */
    int pos_514 = 2 + 514 * 2;
    printf("\n=== Checking position %d (0x%x) ===\n", pos_514, pos_514);
    
    if (pos_514 + 2 <= r0_size) {
        int16_t val;
        memcpy(&val, r0_data + pos_514, 2);
        printf("Value at position: %d (0x%04x)\n", val, val);
        
        /* 如果这是一个有效的偏移 */
        if (val >= 0 && val < 200 && 2 + val * 2 < r0_size) {
            int16_t* txt = (int16_t*)(r0_data + 2 + val * 2);
            printf("If this is an offset, text content: ");
            for (int j = 0; j < 30 && txt[j] != -1; j++) {
                printf("%d ", txt[j]);
            }
            printf("\n");
        }
    } else {
        printf("Position out of range (resource size=%u)\n", r0_size);
    }
    
    /* 检查位置 2+550*2 = 1102 */
    int pos_550 = 2 + 550 * 2;
    printf("\n=== Checking position %d (0x%x) ===\n", pos_550, pos_550);
    
    if (pos_550 + 2 <= r0_size) {
        int16_t val;
        memcpy(&val, r0_data + pos_550, 2);
        printf("Value at position: %d (0x%04x)\n", val, val);
        
        if (val >= 0 && val < 200 && 2 + val * 2 < r0_size) {
            int16_t* txt = (int16_t*)(r0_data + 2 + val * 2);
            printf("If this is an offset, text content: ");
            for (int j = 0; j < 30 && txt[j] != -1; j++) {
                printf("%d ", txt[j]);
            }
            printf("\n");
        }
    } else {
        printf("Position out of range (resource size=%u)\n", r0_size);
    }
    
    free(fdtxt);
    return 0;
}
