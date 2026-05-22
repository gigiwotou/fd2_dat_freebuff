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
    
    printf("=== 分析 FDTXT.DAT 资源0 结构 ===\n\n");
    
    /* 加载资源0 */
    dword rs0;
    memcpy(&rs0, fdtxt + 10 + 0*4, 4);
    dword rs1;
    memcpy(&rs1, fdtxt + 10 + 1*4, 4);
    size_t r0_size = rs1 - rs0;
    
    printf("资源0: 偏移=0x%x, 大小=%zu\n\n", rs0, r0_size);
    
    /* 读取子文本数量 */
    int16_t sc0;
    memcpy(&sc0, fdtxt + rs0, 2);
    printf("子文本数量: %d\n", sc0);
    
    /* 偏移表从位置2开始，每项2字节 */
    printf("\n=== 偏移表 (24项，位置2-49) ===\n");
    for (int i = 0; i < sc0 && i < 24; i++) {
        int16_t off;
        memcpy(&off, fdtxt + rs0 + 2 + i*2, 2);
        printf("  [%2d] 偏移=%4d (0x%04x)\n", i, off, off);
    }
    
    /* 关键：检查从偏移48开始的后续数据 */
    printf("\n=== 偏移表之后的数据（位置24-50） ===\n");
    printf("这些数据可能被直接当作索引访问（如514）\n\n");
    
    int16_t* r0_words = (int16_t*)(fdtxt + rs0);
    
    /* 打印位置24-60的字 */
    for (int i = 24; i < 60; i++) {
        size_t pos = i * 2;
        if (pos + 2 <= r0_size) {
            int16_t val = r0_words[i];
            printf("  [%3d] 值=%5d (0x%04x)", i, val, val);
            
            /* 检查该值是否指向文本数据 */
            if (val >= 0 && (size_t)val < r0_size) {
                int16_t* txt = (int16_t*)(fdtxt + rs0 + val);
                if (txt[0] >= 0 && txt[0] < 2000 || txt[0] == -1 || txt[0] == -2) {
                    printf(" -> 文本: ");
                    for (int j = 0; j < 10 && txt[j] != -1; j++) {
                        printf("%d ", txt[j]);
                    }
                }
            }
            printf("\n");
        }
    }
    
    /* 关键测试：索引514对应的值 */
    printf("\n=== 测试索引514 ===\n");
    printf("索引514 位置 = %zu\n", 514 * 2);
    if (514 * 2 + 2 <= r0_size) {
        int16_t val = r0_words[514];
        printf("索引514 处的值 = %d (0x%04x)\n", val, val);
        
        /* 如果val是正的，它应该是文本数据的偏移 */
        if (val >= 0 && (size_t)val < r0_size) {
            int16_t* txt = (int16_t*)(fdtxt + rs0 + val);
            printf("指向的文本内容: ");
            for (int j = 0; j < 30 && txt[j] != -1; j++) {
                printf("%d ", txt[j]);
            }
            printf("\n");
        }
    }
    
    /* 扫描所有256以上的索引，看看哪些有合理的值 */
    printf("\n=== 扫描索引500-600 ===\n");
    for (int i = 500; i <= 600 && i < (int)(r0_size / 2); i++) {
        int16_t val = r0_words[i];
        if (val >= 0 && (size_t)val < r0_size) {
            int16_t* txt = (int16_t*)(fdtxt + rs0 + val);
            /* 检查是否是合理的文本开头 */
            if ((txt[0] >= 0 && txt[0] < 2000) || txt[0] == -1 || txt[0] == -2 || txt[0] == -18) {
                printf("  [%3d] 值=%4d -> ", i, val);
                for (int j = 0; j < 15 && txt[j] != -1; j++) {
                    printf("%d ", txt[j]);
                }
                printf("\n");
            }
        }
    }
    
    free(fdtxt);
    return 0;
}
