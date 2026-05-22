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
    
    dword file_res_count;
    memcpy(&file_res_count, fdtxt + 6, 4);
    printf("File resource count: %u\n", file_res_count);
    
    /* 测试1: 如果sub_15F84传入的是整个文件指针 */
    printf("\n=== Test 1: File-level index (4-byte offset table at pos 10) ===\n");
    
    /* 索引514在文件偏移表中的位置: 10 + 514*4 = 2066 */
    int pos = 10 + 514 * 4;
    if (pos + 4 <= fsize) {
        dword offset;
        memcpy(&offset, fdtxt + pos, 4);
        printf("File index 514 -> offset: %u (0x%x)\n", offset, offset);
        
        if (offset < fsize) {
            /* 读取该偏移处的资源 */
            int16_t sc;
            memcpy(&sc, fdtxt + offset, 2);
            printf("  Resource sub-count: %d\n", sc);
            
            if (sc > 0 && sc < 100) {
                printf("  Sub-text 0: ");
                int16_t* subs = (int16_t*)(fdtxt + offset + 2);
                if (offset + 2 + subs[0]*2 + 2 < fsize) {
                    int16_t* txt = (int16_t*)(fdtxt + offset + 2 + subs[0]*2);
                    for (int j = 0; j < 20 && txt[j] != -1; j++) {
                        printf("%d ", txt[j]);
                    }
                    printf("\n");
                }
            }
        }
    }
    
    /* 测试2: 如果sub_15F84传入的是资源0的数据指针 */
    printf("\n=== Test 2: Resource 0 level index (2-byte offset table) ===\n");
    
    /* 资源0的偏移 */
    dword r0_off;
    memcpy(&r0_off, fdtxt + 10, 4);
    u8* r0_data = fdtxt + r0_off;
    dword r0_size = 0;
    if (file_res_count > 1) {
        dword r1_off;
        memcpy(&r1_off, fdtxt + 14, 4);
        r0_size = r1_off - r0_off;
    }
    
    printf("Resource 0 offset: 0x%x, size: %u\n", r0_off, r0_size);
    
    /* 资源0内部的2字节偏移表 */
    /* 索引514的位置: 2 + 514*2 = 1030 */
    pos = 2 + 514 * 2;
    if (pos + 2 <= r0_size) {
        int16_t offset;
        memcpy(&offset, r0_data + pos, 2);
        printf("Res0 index 514 -> offset: %d (0x%x)\n", offset, offset);
        
        if (offset >= 0 && offset < 200 && 2 + offset*2 + 2 <= r0_size) {
            int16_t* txt = (int16_t*)(r0_data + 2 + offset*2);
            printf("  Text content: ");
            for (int j = 0; j < 20 && txt[j] != -1; j++) {
                printf("%d ", txt[j]);
            }
            printf("\n");
        }
    } else {
        printf("Index 514 out of range in resource 0 (need %d bytes, have %u)\n", pos + 2, r0_size);
    }
    
    /* 测试3: 扫描文件偏移表，查找有多少个有效条目 */
    printf("\n=== Test 3: Counting valid file-level entries ===\n");
    int valid_count = 0;
    for (int i = 0; i < 2000; i++) {
        pos = 10 + i * 4;
        if (pos + 4 > fsize) break;
        
        dword off;
        memcpy(&off, fdtxt + pos, 4);
        if (off > 0 && off < fsize) {
            valid_count = i + 1;
        }
    }
    printf("Valid file-level entries: %d\n", valid_count);
    
    /* 测试4: 显示文件偏移表前20个条目 */
    printf("\nFile offset table (first 20):\n");
    for (int i = 0; i < 20 && i < (int)file_res_count; i++) {
        dword off;
        memcpy(&off, fdtxt + 10 + i*4, 4);
        printf("  [%d] 0x%x\n", i, off);
    }
    
    free(fdtxt);
    return 0;
}
