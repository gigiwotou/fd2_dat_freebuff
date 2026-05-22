#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

typedef unsigned char u8;

/* 完全模拟sub_15F84的控制码处理，只输出实际渲染的字符 */
int main() {
    FILE* fp = fopen("game/FDTXT.DAT", "rb");
    if (!fp) { printf("Cannot open FDTXT.DAT\n"); return 1; }
    
    fseek(fp, 0, SEEK_END);
    size_t fsize = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    
    u8* fdtxt = (u8*)malloc(fsize);
    fread(fdtxt, 1, fsize, fp);
    fclose(fp);
    
    unsigned int rs0;
    memcpy(&rs0, fdtxt + 10 + 0*4, 4);
    unsigned int rs1;
    memcpy(&rs1, fdtxt + 10 + 1*4, 4);
    size_t r0_size = rs1 - rs0;
    
    printf("=== 完全模拟sub_15F84提取渲染字符 ===\n\n");
    printf("资源0: 偏移=0x%x, 大小=%zu\n\n", rs0, r0_size);
    
    /* 测试索引514-520（场景0-6的名称） */
    printf("索引514-520 (场景0-6名称):\n\n");
    
    for (int idx = 514; idx <= 520; idx++) {
        size_t pos = (size_t)(idx * 2);
        if (pos + 2 > r0_size) continue;
        
        int16_t offset_val;
        memcpy(&offset_val, fdtxt + rs0 + pos, 2);
        
        if (offset_val < 0 || (size_t)offset_val >= r0_size) continue;
        
        int16_t* txt = (int16_t*)(fdtxt + rs0 + offset_val);
        
        printf("[%3d] 字符序列: ", idx);
        
        /* 完全模拟sub_15F84控制码处理 */
        int char_count = 0;
        for (int j = 0; j < 100 && txt[j] != -1; j++) {
            int16_t w = txt[j];
            
            if (w == -1) break;
            else if (w == -2) continue;  /* 换行 */
            else if (w == -3) { j++; continue; }  /* 换行+参数 */
            else if (w == -4 || w == -5) continue;  /* 递归 */
            else if (w == -6) continue;  /* 数字 */
            else if (w == -17 || w == -18) { j += 2; continue; }  /* 对话框+2参数 */
            else if (w == -19 || w == -20) { j++; continue; }  /* 场景对话框+1参数 */
            else if (w < 0) continue;  /* 其他控制码 */
            
            /* 普通字符 - 字体索引 */
            if (w >= 0 && w < 1824) {
                printf("%d ", w);
                char_count++;
            }
        }
        printf("(%d字)\n", char_count);
    }
    
    printf("\n\n索引550-556 (子场景名称):\n\n");
    
    for (int idx = 550; idx <= 556; idx++) {
        size_t pos = (size_t)(idx * 2);
        if (pos + 2 > r0_size) continue;
        
        int16_t offset_val;
        memcpy(&offset_val, fdtxt + rs0 + pos, 2);
        
        if (offset_val < 0 || (size_t)offset_val >= r0_size) continue;
        
        int16_t* txt = (int16_t*)(fdtxt + rs0 + offset_val);
        
        printf("[%3d] 字符序列: ", idx);
        
        int char_count = 0;
        for (int j = 0; j < 100 && txt[j] != -1; j++) {
            int16_t w = txt[j];
            
            if (w == -1) break;
            else if (w == -2) continue;
            else if (w == -3) { j++; continue; }
            else if (w == -4 || w == -5) continue;
            else if (w == -6) continue;
            else if (w == -17 || w == -18) { j += 2; continue; }
            else if (w == -19 || w == -20) { j++; continue; }
            else if (w < 0) continue;
            
            if (w >= 0 && w < 1824) {
                printf("%d ", w);
                char_count++;
            }
        }
        printf("(%d字)\n", char_count);
    }
    
    free(fdtxt);
    return 0;
}
