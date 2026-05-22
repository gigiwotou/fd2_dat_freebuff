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
    u8* r0 = fdtxt + r0_start;
    dword r0_size = r0_end - r0_start;
    
    printf("Resource 0: file_offset=0x%x, size=%u\n\n", r0_start, r0_size);
    
    /* 声明的子文本数量 */
    int16_t declared_count;
    memcpy(&declared_count, r0, 2);
    printf("Declared count (first 2 bytes): %d\n", declared_count);
    
    /* 关键：检查资源0在位置 2+514*2 = 1030 处的值 */
    int pos = 2 + 514 * 2;  /* = 1030 */
    printf("\n=== Checking position 1030 (0x406) in resource 0 ===\n");
    printf("Position in resource: %d\n", pos);
    printf("Position in file: %u (0x%x)\n", r0_start + pos, r0_start + pos);
    
    if (pos + 2 <= r0_size) {
        int16_t val;
        memcpy(&val, r0 + pos, 2);
        printf("Value at this position: %d (0x%04x)\n", val, val);
        
        /* 如果这是一个有效的偏移值 */
        if (val >= 0 && val < 200 && 2 + val*2 + 2 <= r0_size) {
            int16_t* txt = (int16_t*)(r0 + 2 + val*2);
            printf("Text content: ");
            for (int j = 0; j < 30 && txt[j] != -1; j++) {
                printf("%d ", txt[j]);
            }
            printf("\n");
        } else {
            printf("Not a valid offset (>= 0 && < 200)\n");
        }
    } else {
        printf("Position out of range!\n");
    }
    
    /* 分析资源0的真实结构 */
    printf("\n=== Analyzing resource 0 structure ===\n");
    
    /* 前2字节后的偏移表 */
    int16_t* offsets = (int16_t*)(r0 + 2);
    
    /* 扫描偏移表，找到实际的偏移表结束位置 */
    int offset_table_size = 0;
    for (int i = 0; i < 200 && (2 + (i+1)*2) <= r0_size; i++) {
        int16_t off = offsets[i];
        /* 检查这个偏移是否指向合理的位置 */
        if (off >= 0 && off < 200) {
            /* 检查该位置是否有合理的文本数据 */
            if (2 + off*2 + 2 <= r0_size) {
                int16_t first_word;
                memcpy(&first_word, r0 + 2 + off*2, 2);
                if (first_word >= -20 && first_word < 2000) {
                    offset_table_size = i + 1;
                }
            }
        } else {
            /* 遇到非偏移值，可能是文本数据开始了 */
            break;
        }
    }
    
    printf("Actual offset table size: %d entries (%d bytes)\n", 
           offset_table_size, offset_table_size * 2);
    printf("Offset table ends at position: %d\n", 2 + offset_table_size * 2);
    
    /* 显示偏移表前10个条目 */
    printf("\nFirst 10 offset table entries:\n");
    for (int i = 0; i < 10 && i < offset_table_size; i++) {
        printf("  [%d] offset=%d\n", i, offsets[i]);
    }
    
    /* 显示位置1030周围的数据 */
    printf("\n=== Data around position 1030 ===\n");
    for (int i = -5; i <= 5; i++) {
        int p = pos + i * 2;
        if (p >= 0 && p + 2 <= r0_size) {
            int16_t v;
            memcpy(&v, r0 + p, 2);
            printf("  pos %4d: %5d (0x%04x)\n", p, v, v);
        }
    }
    
    /* 十六进制显示位置1020-1040 */
    printf("\nHex dump around position 1030:\n");
    for (int i = 1020; i <= 1045 && i < (int)r0_size; i++) {
        if (i % 16 == 0) printf("\n  %04x: ", i);
        printf("%02x ", r0[i]);
    }
    printf("\n");
    
    free(fdtxt);
    return 0;
}
