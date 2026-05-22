#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

typedef unsigned char u8;
typedef unsigned int dword;

int main() {
    FILE* fp = fopen("game/FDOTHER.DAT", "rb");
    if (!fp) { printf("Cannot open FDOTHER.DAT\n"); return 1; }
    
    fseek(fp, 0, SEEK_END);
    size_t fsize = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    
    u8* fdother = (u8*)malloc(fsize);
    fread(fdother, 1, fsize, fp);
    fclose(fp);
    
    printf("FDOTHER.DAT size: %zu\n\n", fsize);
    
    /* 检查文件头 */
    printf("File header: ");
    for (int i = 0; i < 6; i++) {
        printf("%c", fdother[i]);
    }
    printf("\n\n");
    
    /* 资源数量 */
    dword count;
    memcpy(&count, fdother + 6, 4);
    printf("Resource count: %u\n\n", count);
    
    /* 分析索引13 */
    printf("=== Analyzing Resource 13 (用于Load界面背景) ===\n");
    dword rs13;
    memcpy(&rs13, fdother + 10 + 13*4, 4);
    printf("Resource 13 offset: 0x%x\n", rs13);
    
    dword rs14;
    if (14 < count)
        memcpy(&rs14, fdother + 10 + 14*4, 4);
    else
        rs14 = (dword)fsize;
    
    dword r13_size = rs14 - rs13;
    printf("Resource 13 size: %u bytes\n\n", r13_size);
    
    /* 索引13可能是嵌套DAT结构或包含多个子资源 */
    printf("Resource 13 content analysis:\n");
    printf("First 200 bytes (hex):\n");
    for (int i = 0; i < 200 && i < (int)r13_size; i++) {
        if (i % 16 == 0) printf("  %04x: ", i);
        printf("%02x ", fdother[rs13 + i]);
        if (i % 16 == 15) printf("\n");
    }
    printf("\n\n");
    
    /* 偏移70处的值 */
    if (r13_size >= 74) {
        dword sub_offset;
        memcpy(&sub_offset, fdother + rs13 + 70, 4);
        printf("Offset at position 70: 0x%x (%u)\n", sub_offset, sub_offset);
        
        if (sub_offset < r13_size) {
            printf("Sub-resource at offset 70+0x%x:\n", sub_offset);
            
            /* 检查是否是图像数据 (前4字节可能是宽高) */
            if (r13_size >= sub_offset + 4) {
                unsigned short width = fdother[rs13 + sub_offset] | (fdother[rs13 + sub_offset + 1] << 8);
                unsigned short height = fdother[rs13 + sub_offset + 2] | (fdother[rs13 + sub_offset + 3] << 8);
                printf("  Possible dimensions: %dx%d\n", width, height);
                printf("  Sub-resource size available: %u bytes\n", r13_size - sub_offset);
                
                if (width > 0 && width <= 320 && height > 0 && height <= 200) {
                    printf("  -> This looks like a valid background image!\n");
                    printf("  Expected size for %dx%d: %u bytes\n", width, height, width * height);
                }
            }
        }
    }
    
    /* 也检查索引11作为对比 */
    printf("\n=== Resource 11 (当前使用的背景) ===\n");
    dword rs11;
    memcpy(&rs11, fdother + 10 + 11*4, 4);
    dword rs12;
    if (12 < count)
        memcpy(&rs12, fdother + 10 + 12*4, 4);
    else
        rs12 = (dword)fsize;
    
    printf("Resource 11 offset: 0x%x, size: %u\n", rs11, rs12 - rs11);
    
    if (rs12 - rs11 >= 4) {
        unsigned short w = fdother[rs11] | (fdother[rs11 + 1] << 8);
        unsigned short h = fdother[rs11 + 2] | (fdother[rs11 + 3] << 8);
        printf("Dimensions: %dx%d\n", w, h);
    }
    
    free(fdother);
    return 0;
}
