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
    
    /* 获取资源0的数据 */
    dword r0_start, r0_end;
    memcpy(&r0_start, fdtxt + 10 + 0 * 4, 4);
    memcpy(&r0_end, fdtxt + 10 + 1 * 4, 4);
    printf("\nResource 0: offset 0x%x - 0x%x, size=%u\n", r0_start, r0_end, r0_end - r0_start);
    
    u8* r0_data = fdtxt + r0_start;
    dword r0_size = r0_end - r0_start;
    
    /* 读取子文本数量 */
    int16_t sc;
    memcpy(&sc, r0_data, 2);
    printf("Declared sub-text count: %d\n", sc);
    
    /* 检查偏移表实际有多少条目 */
    printf("\nOffset table entries:\n");
    printf("Checking if index 514 exists in resource 0:\n");
    
    /* 索引514对应的偏移表位置：2 + 514*2 = 1030 */
    if (1030 + 2 <= r0_size) {
        int16_t offset_val;
        memcpy(&offset_val, r0_data + 2 + 514 * 2, 2);
        printf("  Offset table[514] = %d\n", offset_val);
        
        if (offset_val >= 0 && offset_val * 2 + 2 < r0_size) {
            int16_t* txt_ptr = (int16_t*)(r0_data + 2 + offset_val * 2);
            printf("  Text at index 514: ");
            for (int j = 0; j < 30 && txt_ptr[j] != -1; j++) {
                printf("%d ", txt_ptr[j]);
            }
            printf("\n");
        }
    } else {
        printf("  Index 514 offset out of range! (need %d bytes, have %u)\n", 1030 + 2, r0_size);
    }
    
    /* 检查资源0实际包含多少有效的偏移表条目 */
    int valid_entries = 0;
    for (int i = 0; i < 1000 && (2 + (i+1)*2) < r0_size; i++) {
        int16_t off;
        memcpy(&off, r0_data + 2 + i * 2, 2);
        if (off >= 0 && off * 2 + 2 < r0_size) {
            /* 检查这个位置是否有合理的文本数据 */
            int16_t first_word;
            memcpy(&first_word, r0_data + 2 + off * 2, 2);
            if (first_word >= 0 || first_word == -1 || first_word == -2) {
                valid_entries = i + 1;
            }
        }
    }
    printf("\nActual valid offset entries in resource 0: %d\n", valid_entries);
    
    /* 显示资源0的原始数据前100字节 */
    printf("\nResource 0 first 100 bytes (hex):\n");
    for (int i = 0; i < 100 && i < (int)r0_size; i++) {
        printf("%02x ", r0_data[i]);
        if ((i + 1) % 16 == 0) printf("\n");
    }
    printf("\n");
    
    free(fdtxt);
    return 0;
}
