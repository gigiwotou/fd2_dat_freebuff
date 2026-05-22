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
    
    printf("Resource 0: offset=0x%x, size=%u\n", r0_start, r0_size);
    printf("First 50 bytes (hex): ");
    for (int i = 0; i < 50 && i < (int)r0_size; i++) {
        printf("%02x ", r0_data[i]);
    }
    printf("\n");
    
    /* 检查偏移表 */
    int16_t declared_count;
    memcpy(&declared_count, r0_data, 2);
    printf("Declared count: %d\n", declared_count);
    
    /* 检查是否是嵌套DAT */
    if (r0_size >= 10 && memcmp(r0_data, "LLLLLL", 6) == 0) {
        dword nc;
        memcpy(&nc, r0_data + 6, 4);
        printf("*** Resource 0 is a NESTED DAT with %u resources! ***\n", nc);
        
        /* 显示嵌套DAT的偏移表 */
        printf("Nested offset table:\n");
        for (int i = 0; i < (int)nc && i < 10; i++) {
            dword noff;
            memcpy(&noff, r0_data + 10 + i * 4, 4);
            printf("  [%d] offset=0x%x\n", i, noff);
        }
    } else {
        /* 普通FDTXT资源 - 分析偏移表 */
        printf("\nOffset table (first 30 entries):\n");
        for (int i = 0; i < 30 && (2 + i*2 + 2) < r0_size; i++) {
            int16_t off;
            memcpy(&off, r0_data + 2 + i * 2, 2);
            printf("  [%d] offset=%d", i, off);
            
            /* 如果偏移有效，显示前几个字 */
            if (off >= 0 && off < 100 && (2 + off * 2 + 2) < r0_size) {
                int16_t first_word;
                memcpy(&first_word, r0_data + 2 + off * 2, 2);
                printf(" -> first word=%d", first_word);
            }
            printf("\n");
        }
        
        /* 检查索引514在资源0中的位置 */
        int offset_514_pos = 2 + 514 * 2;
        printf("\nChecking position 2+514*2 = %d (0x%x):\n", offset_514_pos, offset_514_pos);
        if (offset_514_pos + 2 < r0_size) {
            int16_t val_at_514;
            memcpy(&val_at_514, r0_data + offset_514_pos, 2);
            printf("  Value at this position: %d (0x%x)\n", val_at_514, val_at_514);
            
            /* 如果这是一个偏移，检查指向的内容 */
            if (val_at_514 >= 0 && val_at_514 < 200 && (2 + val_at_514 * 2 + 2) < r0_size) {
                int16_t* txt = (int16_t*)(r0_data + 2 + val_at_514 * 2);
                printf("  Text content: ");
                for (int j = 0; j < 30 && txt[j] != -1; j++) {
                    printf("%d ", txt[j]);
                }
                printf("\n");
            }
        } else {
            printf("  Position out of range!\n");
        }
    }
    
    free(fdtxt);
    return 0;
}
