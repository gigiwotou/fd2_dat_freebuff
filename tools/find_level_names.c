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
    
    /* 加载资源0 */
    dword rs0;
    memcpy(&rs0, fdtxt + 10 + 0*4, 4);
    dword rs1;
    memcpy(&rs1, fdtxt + 10 + 1*4, 4);
    size_t r0_size = rs1 - rs0;
    
    printf("资源0: 偏移=0x%x, 大小=%zu\n", rs0, r0_size);
    
    int16_t* r0_words = (int16_t*)(fdtxt + rs0);
    int16_t sc0;
    memcpy(&sc0, fdtxt + rs0, 2);
    printf("子文本数量: %d\n\n", sc0);
    
    /* 偏移表在位置2-49（24项） */
    printf("=== 偏移表位置2-49 ===\n");
    for (int i = 0; i < sc0; i++) {
        int16_t off;
        memcpy(&off, fdtxt + rs0 + 2 + i*2, 2);
        printf("  [%2d] %d\n", i, off);
    }
    
    /* 扫描文本数据区域，找看起来像关卡名称的短文本 */
    printf("\n=== 扫描文本数据区域寻找关卡名称 ===\n");
    printf("关卡名称应该是短文本(2-10个字)，包含中文字符(>1000)\n\n");
    
    int16_t* text_data = r0_words + 26;  /* 跳过偏移表区域 */
    size_t text_data_size = r0_size / 2 - 26;
    
    /* 找所有短文本（-1终止符在10个字以内） */
    int found = 0;
    for (size_t i = 0; i < text_data_size && found < 20; i++) {
        /* 检查是否是合理的文本开头 */
        int16_t first = text_data[i];
        if ((first > 100 && first < 2000) || first == -18 || first == -2) {
            /* 找终止符 */
            size_t len = 0;
            for (size_t j = i; j < text_data_size && j < i + 15; j++) {
                if (text_data[j] == -1) {
                    len = j - i;
                    break;
                }
            }
            
            /* 如果是短文本（2-10个字），打印出来 */
            if (len >= 2 && len <= 10) {
                printf("  偏移=%zu, 长度=%zu: ", i, len);
                for (size_t j = 0; j < len; j++) {
                    printf("%d ", text_data[i + j]);
                }
                printf("\n");
                found++;
                
                /* 跳到文本末尾 */
                i += len;
            }
        }
    }
    
    free(fdtxt);
    return 0;
}
