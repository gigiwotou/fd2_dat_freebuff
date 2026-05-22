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
    
    /* 分析资源0的结构 - 原游戏sub_29AB2使用的是资源0 */
    dword r0_start, r0_end;
    memcpy(&r0_start, fdtxt + 10, 4);
    memcpy(&r0_end, fdtxt + 14, 4);
    printf("\nResource 0: offset 0x%x - 0x%x, size=%u bytes\n", r0_start, r0_end, r0_end - r0_start);
    
    u8* r0_data = fdtxt + r0_start;
    dword r0_size = r0_end - r0_start;
    
    /* 资源0内部结构: 前2字节是子文本数量 */
    int16_t sc;
    memcpy(&sc, r0_data, 2);
    printf("Declared sub-text count: %d\n", sc);
    
    /* 检查子文本数量是否合理 */
    if (sc <= 0 || sc > 10000) {
        printf("WARNING: sub-text count %d is suspicious!\n", sc);
        /* 尝试扫描找到实际的文本数据开始位置 */
        printf("\nScanning for text patterns...\n");
        for (int i = 0; i < (int)r0_size && i < 2000; i++) {
            int16_t potential_count;
            memcpy(&potential_count, r0_data + i, 2);
            if (potential_count > 500 && potential_count < 1000) {
                printf("  Found potential count %d at offset %d (0x%x)\n", 
                       potential_count, i, i);
            }
        }
    } else {
        printf("Resource 0 has %d sub-texts\n", sc);
        
        /* 检查索引514是否存在 */
        if (sc > 514) {
            /* 获取索引514的偏移 */
            int16_t off_514;
            memcpy(&off_514, r0_data + 2 + 514 * 2, 2);
            printf("\nSub-text 514 offset: %d\n", off_514);
            
            if (off_514 >= 0 && off_514 < sc) {
                int16_t* txt = (int16_t*)(r0_data + 2 + off_514 * 2);
                printf("Text content: ");
                for (int j = 0; j < 40 && txt[j] != -1; j++) {
                    printf("%d ", txt[j]);
                }
                printf("\n");
            }
        } else {
            printf("Index 514 out of range (max=%d)\n", sc-1);
        }
    }
    
    /* 检查其他可能包含关卡名称的资源 */
    printf("\n\n=== Scanning all resources for stage names ===\n");
    dword count;
    memcpy(&count, fdtxt + 6, 4);
    
    for (int i = 0; i < (int)count && i < 146; i++) {
        dword rs, re;
        memcpy(&rs, fdtxt + 10 + i * 4, 4);
        if (i + 1 < (int)count)
            memcpy(&re, fdtxt + 10 + (i + 1) * 4, 4);
        else
            re = (dword)fsize;
        
        if (rs < fsize && (re - rs) > 1000) {
            int16_t local_sc;
            memcpy(&local_sc, fdtxt + rs, 2);
            
            /* 查找可能包含514+索引的资源 */
            if (local_sc > 560) {
                printf("Resource %d: size=%u, sub-count=%d *** POTENTIAL CANDIDATE ***\n",
                       i, re - rs, local_sc);
            }
        }
    }
    
    free(fdtxt);
    return 0;
}
