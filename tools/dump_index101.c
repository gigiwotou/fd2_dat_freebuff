#include <stdio.h>
#include <stdint.h>
#include <string.h>

int main() {
    FILE* fp = fopen("bin/FDOTHER.DAT", "rb");
    if (!fp) fp = fopen("FDOTHER.DAT", "rb");
    if (!fp) { printf("Cannot open FDOTHER.DAT\n"); return 1; }
    
    fseek(fp, 0, SEEK_END);
    long file_size = ftell(fp);
    
    printf("Checking index 101...\n");
    
    uint32_t e100[2], e101[2], e102[2];
    
    fseek(fp, 6 + 100 * 4, SEEK_SET);
    fread(e100, 1, 8, fp);
    
    fseek(fp, 6 + 101 * 4, SEEK_SET);
    fread(e101, 1, 8, fp);
    
    fseek(fp, 6 + 102 * 4, SEEK_SET);
    fread(e102, 1, 8, fp);
    
    printf("Index 100: start=%u, end=%u, size=%u\n", e100[0], e100[1], e100[1]-e100[0]);
    printf("Index 101: start=%u, end=%u, size=%u\n", e101[0], e101[1], e101[1]-e101[0]);
    printf("Index 102: start=%u, end=%u, size=%u\n", e102[0], e102[1], e102[1]-e102[0]);
    
    /* 读取索引101的前20字节 */
    uint8_t buf[100];
    fseek(fp, e101[0], SEEK_SET);
    fread(buf, 1, sizeof(buf), fp);
    
    printf("\nIndex 101 first 100 bytes:\n");
    for (int i = 0; i < 100; i++) {
        printf("%3d ", buf[i]);
        if ((i + 1) % 16 == 0) printf("\n");
    }
    printf("\n");
    
    /* 检查前768字节是否是调色板 */
    printf("\nFirst 16 colors (assuming 768-byte palette at start):\n");
    for (int i = 0; i < 16; i++) {
        printf("Color %d: R=%d G=%d B=%d\n", i, buf[i*3], buf[i*3+1], buf[i*3+2]);
    }
    
    /* 检查末尾768字节 */
    if (e101[1] - e101[0] > 768) {
        fseek(fp, e101[1] - 768, SEEK_SET);
        fread(buf, 1, 48, fp);
        printf("\nLast 16 colors (palette at end):\n");
        for (int i = 0; i < 16; i++) {
            printf("Color %d: R=%d G=%d B=%d\n", i, buf[i*3], buf[i*3+1], buf[i*3+2]);
        }
    }
    
    fclose(fp);
    return 0;
}
