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
    
    /* 分析资源30（92个子文本） */
    printf("=== Detailed analysis of Resource 30 ===\n");
    dword rs30;
    memcpy(&rs30, fdtxt + 10 + 30*4, 4);
    printf("Resource 30 offset: 0x%x\n", rs30);
    
    int16_t sc30;
    memcpy(&sc30, fdtxt + rs30, 2);
    printf("Sub-text count: %d\n\n", sc30);
    
    if (sc30 > 0 && sc30 < 200) {
        printf("All sub-texts:\n");
        for (int j = 0; j < sc30; j++) {
            int16_t off;
            memcpy(&off, fdtxt + rs30 + 2 + j*2, 2);
            printf("  [%3d] offset=%4d -> ", j, off);
            
            if (off >= 0 && rs30 + 2 + off*2 + 2 < fsize) {
                int16_t* txt = (int16_t*)(fdtxt + rs30 + 2 + off*2);
                /* 打印前20个字 */
                for (int k = 0; k < 20 && txt[k] != -1; k++) {
                    printf("%d ", txt[k]);
                }
                if (txt[20] != -1) printf("...");
                printf("\n");
            } else {
                printf("(out of range)\n");
            }
        }
    }
    
    /* 也检查资源0的子文本514指向的内容 */
    printf("\n=== What does Resource 0 index 514 point to? ===\n");
    dword rs0;
    memcpy(&rs0, fdtxt + 10 + 0*4, 4);
    printf("Resource 0 offset: 0x%x\n", rs0);
    
    size_t r0_size = 0;
    dword rs1;
    memcpy(&rs1, fdtxt + 10 + 1*4, 4);
    r0_size = rs1 - rs0;
    printf("Resource 0 size: %zu\n", r0_size);
    
    int16_t sc0;
    memcpy(&sc0, fdtxt + rs0, 2);
    printf("Sub-text count: %d\n", sc0);
    
    /* 检查索引514 */
    size_t pos = 2 * 514;
    printf("\nChecking index 514 (pos=%zu):\n", pos);
    if (pos + 2 <= r0_size) {
        int16_t val;
        memcpy(&val, fdtxt + rs0 + pos, 2);
        printf("  Value at index 514: %d (0x%x)\n", val, val);
        
        if (val >= 0 && (size_t)val < r0_size) {
            int16_t* txt = (int16_t*)(fdtxt + rs0 + val);
            printf("  Text content: ");
            for (int k = 0; k < 30 && txt[k] != -1; k++) {
                printf("%d ", txt[k]);
            }
            printf("\n");
        }
    }
    
    /* 检查资源0的所有索引，找到指向文本数据的位置 */
    printf("\n=== Scanning Resource 0 for index 514 equivalent ===\n");
    printf("Looking for texts that might be level names...\n\n");
    
    /* 资源0的偏移表只有24项(0-23)，之后的内容是文本数据 */
    /* 直接扫描文本数据区域，寻找可能的关卡名称模式 */
    int16_t* r0_data = (int16_t*)(fdtxt + rs0 + 2);  /* 跳过子文本数量 */
    size_t r0_data_size = r0_size - 2;
    
    /* 打印偏移表之后的文本数据 */
    printf("Text data after offset table (first 500 words):\n");
    for (size_t i = 0; i < 500 && i*2 < r0_data_size; i++) {
        if (i % 20 == 0) printf("\n[%4zu] ", i);
        printf("%5d ", r0_data[i]);
    }
    printf("\n");
    
    free(fdtxt);
    return 0;
}
