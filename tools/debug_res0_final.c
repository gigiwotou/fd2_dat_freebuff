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
    
    printf("FDTXT.DAT size: %zu\n\n", fsize);
    
    /* 资源0的数据 */
    dword r0_start, r0_end;
    memcpy(&r0_start, fdtxt + 10, 4);
    memcpy(&r0_end, fdtxt + 14, 4);
    u8* r0 = fdtxt + r0_start;
    dword r0_size = r0_end - r0_start;
    
    printf("Resource 0: file_offset=0x%x, size=%u bytes\n\n", r0_start, r0_size);
    
    /* 关键：资源0的前24个字（位置0-47）是偏移表 */
    printf("=== Resource 0 offset table (indices 0-23) ===\n");
    int16_t* offsets = (int16_t*)r0;
    
    for (int i = 0; i < 24; i++) {
        int16_t off = offsets[i];
        printf("  [%2d] offset=%4d (0x%04x)", i, off, off);
        
        if (off >= 0 && off < (int)r0_size) {
            int16_t* txt = (int16_t*)(r0 + off);
            printf(" -> ");
            int valid = 1;
            for (int j = 0; j < 10; j++) {
                if (txt[j] == -1) { printf("[-1]"); break; }
                else if (txt[j] < -20 || txt[j] > 2000) { printf("[%d]", txt[j]); valid = 0; break; }
                else printf("%d ", txt[j]);
            }
            if (valid) printf("(VALID)");
        }
        printf("\n");
    }
    
    /* 检查索引514 */
    printf("\n=== Index 514 analysis ===\n");
    printf("Position 2*514 = %d in resource 0\n", 2*514);
    
    if (2*514 < r0_size) {
        int16_t val;
        memcpy(&val, r0 + 2*514, 2);
        printf("Value at this position: %d (0x%04x)\n", val, val);
        
        /* 测试1: 如果val是字形索引 */
        printf("\nTest 1: val as character index\n");
        printf("  Character %d would be rendered directly\n", val);
        
        /* 测试2: 如果val是偏移 */
        printf("\nTest 2: val as offset\n");
        if (val >= 0 && val < (int)r0_size) {
            int16_t* txt = (int16_t*)(r0 + val);
            printf("  Text at arg0+%d: ", val);
            int valid = 1;
            for (int j = 0; j < 15; j++) {
                if (txt[j] == -1) { printf("[-1]"); break; }
                else if (txt[j] < -20 || txt[j] > 2000) { printf("[%d]", txt[j]); valid = 0; break; }
                else printf("%d ", txt[j]);
            }
            if (valid) printf("(VALID TEXT)");
            else printf("(INVALID - this is raw data, not an offset table)");
            printf("\n");
        }
    }
    
    /* 分析资源0的实际结构 */
    printf("\n=== Resource 0 structure analysis ===\n");
    printf("Position 0-1: %d (declared count?)\n", offsets[0]);
    printf("Position 2-47: 23 offset table entries (indices 1-23)\n");
    printf("Position 48+: text data area\n\n");
    
    /* 查找文本数据区域开始位置 */
    printf("Scanning for text data area start...\n");
    int text_start = -1;
    for (int i = 12; i < 50; i++) {
        int16_t val = offsets[i];
        /* 如果值在合理的字形索引范围内 */
        if (val >= 100 && val <= 2000) {
            if (text_start < 0) text_start = i;
        }
    }
    printf("Text data likely starts at word index %d (byte offset %d)\n", 
           text_start, text_start * 2);
    
    /* 验证：位置48开始是文本数据（字形索引） */
    printf("\nResource 0 words 24-35 (text data area):\n");
    for (int i = 24; i < 36 && (i*2+2) < r0_size; i++) {
        printf("  [%2d] %4d", i, offsets[i]);
        if (i % 3 == 2) printf("\n");
        else printf("  ");
    }
    printf("\n");
    
    free(fdtxt);
    return 0;
}
