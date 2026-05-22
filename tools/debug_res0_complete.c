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
    
    /* 资源0 */
    dword r0_start, r0_end;
    memcpy(&r0_start, fdtxt + 10, 4);
    memcpy(&r0_end, fdtxt + 14, 4);
    u8* r0_data = fdtxt + r0_start;
    dword r0_size = r0_end - r0_start;
    
    printf("Resource 0: offset=0x%x, size=%u\n\n", r0_start, r0_size);
    
    /* 十六进制显示前200字节 */
    printf("Hex dump (first 200 bytes):\n");
    for (int i = 0; i < 200 && i < (int)r0_size; i++) {
        if (i % 16 == 0) printf("\n  %04x: ", i);
        printf("%02x ", r0_data[i]);
    }
    printf("\n");
    
    /* 检查前2字节 */
    int16_t count;
    memcpy(&count, r0_data, 2);
    printf("\nFirst 2 bytes as int16: %d\n", count);
    
    /* 如果count=24，显示前30个偏移表条目 */
    if (count > 0 && count < 100) {
        printf("\nOffset table (%d entries):\n", count);
        int16_t* offsets = (int16_t*)(r0_data + 2);
        for (int i = 0; i < count && (2 + i*2 + 2) < r0_size; i++) {
            printf("  [%2d] offset=%4d (0x%04x)\n", i, offsets[i], offsets[i]);
        }
    }
    
    /* 检查位置 2+514*2 = 1030 */
    int target_pos = 2 + 514 * 2;
    printf("\n=== Position %d (0x%x) - index 514 ===\n", target_pos, target_pos);
    
    if (target_pos + 2 <= r0_size) {
        int16_t val;
        memcpy(&val, r0_data + target_pos, 2);
        printf("Value: %d (0x%04x)\n", val, val);
        
        /* 尝试按字显示周围的值 */
        printf("\nValues around position 1030:\n");
        for (int i = -5; i <= 5; i++) {
            int pos = target_pos + i * 2;
            if (pos >= 0 && pos + 2 <= r0_size) {
                int16_t v;
                memcpy(&v, r0_data + pos, 2);
                printf("  pos %5d [%3d]: %5d (0x%04x)\n", pos, i, v, v);
            }
        }
    } else {
        printf("Out of range! Resource size=%u\n", r0_size);
    }
    
    /* 检查位置 2+550*2 = 1102 */
    int target_pos2 = 2 + 550 * 2;
    printf("\n=== Position %d (0x%x) - index 550 ===\n", target_pos2, target_pos2);
    
    if (target_pos2 + 2 <= r0_size) {
        int16_t val;
        memcpy(&val, r0_data + target_pos2, 2);
        printf("Value: %d (0x%04x)\n", val, val);
    } else {
        printf("Out of range!\n");
    }
    
    /* 扫描整个资源0，查找是否有嵌套DAT标记 */
    printf("\n=== Scanning for nested DAT markers ===\n");
    for (int i = 0; i < (int)r0_size - 6; i++) {
        if (memcmp(r0_data + i, "LLLLLL", 6) == 0) {
            printf("Found 'LLLLLL' at offset %d (0x%x)\n", i, i);
            if (i + 10 <= r0_size) {
                dword nc;
                memcpy(&nc, r0_data + i + 6, 4);
                printf("  Nested count: %u\n", nc);
            }
        }
    }
    
    free(fdtxt);
    return 0;
}
