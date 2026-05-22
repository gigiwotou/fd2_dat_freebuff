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
    
    printf("FDTXT.DAT file size: %zu\n\n", fsize);
    
    /* 检查文件级别的4字节偏移表 */
    /* 从位置10开始，每个条目4字节 */
    dword count;
    memcpy(&count, fdtxt + 6, 4);
    printf("File resource count: %u\n\n", count);
    
    /* 测试文件级别的索引514 */
    /* 位置: 10 + 514*4 = 2066 */
    int pos_514 = 10 + 514 * 4;
    printf("=== File-level index 514 ===\n");
    printf("Position: %d (0x%x)\n", pos_514, pos_514);
    
    if (pos_514 + 4 <= fsize) {
        dword offset;
        memcpy(&offset, fdtxt + pos_514, 4);
        printf("Offset value: %u (0x%x)\n", offset, offset);
        
        if (offset < fsize) {
            printf("Points to valid location in file\n");
            
            /* 读取该位置的内容 - 假设是嵌套的FDTXT资源 */
            int16_t sc;
            memcpy(&sc, fdtxt + offset, 2);
            printf("Sub-text count at this location: %d\n", sc);
            
            if (sc > 0 && sc < 100) {
                printf("First 5 sub-texts:\n");
                int16_t* subs = (int16_t*)(fdtxt + offset + 2);
                for (int i = 0; i < 5 && i < sc; i++) {
                    int sub_off = subs[i];
                    printf("  [%d] offset=%d -> ", i, sub_off);
                    
                    if (sub_off >= 0 && offset + 2 + sub_off*2 + 2 <= fsize) {
                        int16_t* txt = (int16_t*)(fdtxt + offset + 2 + sub_off*2);
                        for (int j = 0; j < 10 && txt[j] != -1; j++) {
                            printf("%d ", txt[j]);
                        }
                        printf("\n");
                    } else {
                        printf("(out of range)\n");
                    }
                }
            }
        }
    }
    
    /* 测试文件级别的索引550 */
    int pos_550 = 10 + 550 * 4;
    printf("\n=== File-level index 550 ===\n");
    printf("Position: %d (0x%x)\n", pos_550, pos_550);
    
    if (pos_550 + 4 <= fsize) {
        dword offset;
        memcpy(&offset, fdtxt + pos_550, 4);
        printf("Offset value: %u (0x%x)\n", offset, offset);
    }
    
    /* 扫描文件，查找有多少个有效的4字节偏移 */
    printf("\n=== Scanning file-level offset table ===\n");
    int valid_entries = 0;
    for (int i = 0; i < 2000; i++) {
        int pos = 10 + i * 4;
        if (pos + 4 > fsize) break;
        
        dword off;
        memcpy(&off, fdtxt + pos, 4);
        if (off > 0 && off < fsize) {
            valid_entries = i + 1;
        } else if (i > 100) {
            break;  /* 连续遇到无效值 */
        }
    }
    printf("Valid file-level entries: %d\n", valid_entries);
    
    /* 显示前20个文件级别偏移 */
    printf("\nFile-level offset table (first 20):\n");
    for (int i = 0; i < 20 && i < (int)count; i++) {
        dword off;
        memcpy(&off, fdtxt + 10 + i*4, 4);
        printf("  [%d] 0x%x (%u)\n", i, off, off);
    }
    
    free(fdtxt);
    return 0;
}
