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
    printf("Magic: %.*s\n", 6, fdtxt);
    
    dword count;
    memcpy(&count, fdtxt + 6, 4);
    printf("Resource count: %u\n", count);
    
    /* 检查文件级别偏移表 - 每个条目4字节 */
    /* 偏移表从位置10开始 */
    printf("\nFile-level offset table:\n");
    printf("Checking if file has >= 560 entries (for index 514+scene_idx):\n");
    
    /* 检查索引514的位置：10 + 514*4 = 2066 */
    int pos_514 = 10 + 514 * 4;
    printf("\nIndex 514 at file position: %d (0x%x)\n", pos_514, pos_514);
    
    if (pos_514 + 4 <= fsize) {
        dword val;
        memcpy(&val, fdtxt + pos_514, 4);
        printf("Value at index 514: %u (0x%x)\n", val, val);
        
        /* 如果这是一个有效的文件偏移 */
        if (val < fsize) {
            printf("This is a valid file offset!\n");
            /* 读取该位置的前2字节（子文本数量） */
            int16_t sc;
            memcpy(&sc, fdtxt + val, 2);
            printf("Sub-text count at this resource: %d\n", sc);
            
            /* 显示前10个子文本 */
            if (sc > 0 && sc < 1000) {
                int16_t* offsets = (int16_t*)(fdtxt + val + 2);
                printf("First 10 sub-texts:\n");
                for (int i = 0; i < 10 && i < sc && (val + 2 + (i+1)*2) < fsize; i++) {
                    printf("  [%d] offset=%d", i, offsets[i]);
                    if (offsets[i] >= 0 && val + 2 + offsets[i]*2 + 2 < fsize) {
                        int16_t first_word;
                        memcpy(&first_word, fdtxt + val + 2 + offsets[i]*2, 2);
                        printf(" -> first word=%d", first_word);
                    }
                    printf("\n");
                }
            }
        }
    } else {
        printf("Out of file range!\n");
    }
    
    /* 检查索引550的位置：10 + 550*4 = 2210 */
    int pos_550 = 10 + 550 * 4;
    printf("\nIndex 550 at file position: %d (0x%x)\n", pos_550, pos_550);
    
    if (pos_550 + 4 <= fsize) {
        dword val;
        memcpy(&val, fdtxt + pos_550, 4);
        printf("Value at index 550: %u (0x%x)\n", val, val);
        
        if (val < fsize) {
            int16_t sc;
            memcpy(&sc, fdtxt + val, 2);
            printf("Sub-text count at this resource: %d\n", sc);
        }
    }
    
    /* 检查总共有多少个文件级别条目 */
    printf("\n=== File offset table entries count ===\n");
    int valid_entries = 0;
    for (int i = 0; i < 1000; i++) {
        int pos = 10 + i * 4;
        if (pos + 4 > fsize) break;
        
        dword off;
        memcpy(&off, fdtxt + pos, 4);
        if (off < fsize) {
            valid_entries = i + 1;
        }
    }
    printf("Valid file-level entries: %d\n", valid_entries);
    
    free(fdtxt);
    return 0;
}
