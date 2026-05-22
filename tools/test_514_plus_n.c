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
    
    printf("资源0: 偏移=0x%x, 大小=%zu\n\n", rs0, r0_size);
    
    int16_t* r0_words = (int16_t*)(fdtxt + rs0);
    
    /* 按sub_15F84公式检查索引514-560 */
    printf("=== 使用sub_15F84公式检查索引514-560 ===\n");
    printf("公式: v15 = (int16*)(*(int16*)(arg0 + 2*arg4) + arg0)\n\n");
    
    for (int idx = 514; idx <= 560; idx++) {
        size_t pos = (size_t)(idx * 2);
        if (pos + 2 > r0_size) {
            printf("[%3d] 位置%zu 超出范围\n", idx, pos);
            continue;
        }
        
        /* 读取该位置的值 */
        int16_t offset_val;
        memcpy(&offset_val, fdtxt + rs0 + pos, 2);
        
        printf("[%3d] 值=%5d (0x%04x)", idx, offset_val, offset_val);
        
        /* 如果offset_val是正数且在范围内，指向文本数据 */
        if (offset_val >= 0 && (size_t)offset_val < r0_size) {
            int16_t* txt = (int16_t*)(fdtxt + rs0 + offset_val);
            
            /* 打印文本内容直到-1或15个字 */
            printf(" -> 文本: ");
            int valid = 1;
            for (int j = 0; j < 15 && (size_t)(offset_val + j*2) < r0_size; j++) {
                if (txt[j] == -1) { printf("[-1]"); break; }
                else if (txt[j] < -20 || txt[j] > 2000) { 
                    printf("[%d]", txt[j]); 
                    valid = 0; 
                    break; 
                }
                else printf("%d ", txt[j]);
            }
            if (valid) printf("(可能有效)");
        } else {
            printf(" (无效偏移)");
        }
        printf("\n");
    }
    
    free(fdtxt);
    return 0;
}
