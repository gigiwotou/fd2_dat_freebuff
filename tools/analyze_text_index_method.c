#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

typedef unsigned char u8;

int main() {
    FILE* fp = fopen("game/FDTXT.DAT", "rb");
    if (!fp) { printf("Cannot open FDTXT.DAT\n"); return 1; }
    
    fseek(fp, 0, SEEK_END);
    size_t fsize = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    
    u8* fdtxt = (u8*)malloc(fsize);
    fread(fdtxt, 1, fsize, fp);
    fclose(fp);
    
    /* 加载资源0 */
    unsigned int rs0;
    memcpy(&rs0, fdtxt + 10 + 0*4, 4);
    unsigned int rs1;
    memcpy(&rs1, fdtxt + 10 + 1*4, 4);
    size_t r0_size = rs1 - rs0;
    
    printf("=== 重新理解sub_15F84文本索引机制 ===\n\n");
    printf("资源0大小: %zu 字节 (%zu 字)\n", r0_size, r0_size/2);
    
    int16_t* r0_words = (int16_t*)(fdtxt + rs0);
    
    /* 偏移表在位置2-49（24项，对应索引0-23） */
    printf("\n=== 偏移表结构 ===\n");
    printf("位置0: 子文本数量 = %d\n", r0_words[0]);
    printf("位置1: 可能是填充或特殊值 = %d\n", r0_words[1]);
    printf("位置2-25: 偏移表(24项)\n");
    
    for (int i = 2; i < 26; i++) {
        printf("  [%d] %d\n", i-2, r0_words[i]);
    }
    
    /* 关键假设：偏移表之后是文本数据区 */
    printf("\n=== 测试不同索引方法 ===\n\n");
    
    /* 方法1：假设资源0只有24个子文本（0-23），之后的索引无效 */
    printf("方法1: 标准偏移表访问(0-23)\n");
    for (int i = 0; i < 24; i++) {
        int16_t off = r0_words[i + 2];
        if (off >= 0 && (size_t)off < r0_size) {
            int16_t* txt = (int16_t*)(fdtxt + rs0 + off);
            /* 检查是否是合理的文本 */
            int valid = 1;
            if (txt[0] < -20 || txt[0] > 2000) valid = 0;
            if (valid) {
                printf("  [%2d] 偏移=%4d -> ", i, off);
                for (int j = 0; j < 10 && txt[j] != -1; j++) {
                    printf("%d ", txt[j]);
                }
                printf("\n");
            }
        }
    }
    
    /* 方法2：检查资源0是否被当作连续的文本数据存储 */
    printf("\n方法2: 检查资源0的文本数据区（位置26之后）\n");
    printf("查找纯文本序列（不含控制码）\n\n");
    
    /* 从位置26开始扫描 */
    for (size_t i = 26; i < r0_size/2 - 10; i++) {
        int16_t first = r0_words[i];
        /* 如果第一个字是合理的BIG5字符 */
        if (first > 100 && first < 2000) {
            /* 检查接下来10个字是否都是合理字符 */
            int all_valid = 1;
            int len = 0;
            for (int j = 0; j < 15; j++) {
                if ((size_t)(i + j) >= r0_size/2) break;
                int16_t w = r0_words[i + j];
                if (w == -1) { len = j; break; }
                if (w < 30 || w > 2000) { all_valid = 0; break; }
                len = j + 1;
            }
            
            /* 如果是2-10个字的纯文本序列 */
            if (all_valid && len >= 2 && len <= 10) {
                printf("  位置%zu (字%zu), 长度%d: ", i, i, len);
                for (int j = 0; j < len; j++) {
                    printf("%d ", r0_words[i + j]);
                }
                printf("\n");
            }
        }
    }
    
    free(fdtxt);
    return 0;
}
