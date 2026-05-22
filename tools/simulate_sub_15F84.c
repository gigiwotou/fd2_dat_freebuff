#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

typedef unsigned char u8;

/* 模拟sub_15F84的控制码处理，提取纯字符序列 */
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
    
    printf("=== 模拟sub_15F84处理流程提取字符 ===\n\n");
    printf("资源0: 偏移=0x%x, 大小=%zu\n\n", rs0, r0_size);
    
    int16_t* r0_words = (int16_t*)(fdtxt + rs0);
    
    /* 测试索引514-520和550-556（对应场景0-6） */
    printf("=== 使用sub_15F84公式提取索引514-520（场景0-6的名称） ===\n\n");
    
    for (int idx = 514; idx <= 520; idx++) {
        size_t pos = (size_t)(idx * 2);
        if (pos + 2 > r0_size) {
            printf("[%3d] 超出范围\n", idx);
            continue;
        }
        
        /* sub_15F84公式: v15 = (int16*)(*(int16*)(arg0 + 2*arg4) + arg0) */
        int16_t offset_val;
        memcpy(&offset_val, fdtxt + rs0 + pos, 2);
        
        if (offset_val < 0 || (size_t)offset_val >= r0_size) {
            printf("[%3d] 值=%d (无效偏移)\n", idx, offset_val);
            continue;
        }
        
        int16_t* txt = (int16_t*)(fdtxt + rs0 + offset_val);
        
        printf("[%3d] 偏移=%d -> 原始: ", idx, offset_val);
        for (int j = 0; j < 20 && txt[j] != -1; j++) {
            printf("%d ", txt[j]);
        }
        printf("\n");
        
        /* 模拟sub_15F84处理：提取纯字符 */
        printf("       处理后的字符序列: ");
        int char_count = 0;
        for (int j = 0; j < 50 && txt[j] != -1; j++) {
            int16_t w = txt[j];
            
            /* 控制码处理 */
            if (w == -1) break;  /* 文本结束 */
            else if (w == -2) { printf("[换行]"); continue; }
            else if (w == -3) { printf("[换行2]"); j++; continue; }  /* 跳过下一个参数 */
            else if (w == -4 || w == -5) { printf("[递归]"); continue; }
            else if (w == -6) { printf("[数字]"); continue; }
            else if (w == -17 || w == -18) { printf("[对话框%d]", w); j += 2; continue; }  /* 跳过2个参数 */
            else if (w == -19 || w == -20) { printf("[场景对话框%d]", w); j++; continue; }  /* 跳过1个参数 */
            else if (w < 0) { printf("[控制%d]", w); continue; }
            
            /* 普通字符 */
            if (w >= 0 && w < 2000) {
                printf("%d ", w);
                char_count++;
            }
        }
        printf("(%d个字符)\n\n", char_count);
    }
    
    printf("\n=== 使用sub_15F84公式提取索引550-556（子场景名称） ===\n\n");
    
    for (int idx = 550; idx <= 556; idx++) {
        size_t pos = (size_t)(idx * 2);
        if (pos + 2 > r0_size) {
            printf("[%3d] 超出范围\n", idx);
            continue;
        }
        
        int16_t offset_val;
        memcpy(&offset_val, fdtxt + rs0 + pos, 2);
        
        if (offset_val < 0 || (size_t)offset_val >= r0_size) {
            printf("[%3d] 值=%d (无效偏移)\n", idx, offset_val);
            continue;
        }
        
        int16_t* txt = (int16_t*)(fdtxt + rs0 + offset_val);
        
        printf("[%3d] 偏移=%d -> ", idx, offset_val);
        for (int j = 0; j < 20 && txt[j] != -1; j++) {
            printf("%d ", txt[j]);
        }
        printf("\n");
    }
    
    free(fdtxt);
    return 0;
}
