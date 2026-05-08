#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

int main() {
    const char* paths[] = {"FDOTHER.DAT", "bin/FDOTHER.DAT", "../bin/FDOTHER.DAT"};
    FILE* fp = NULL;
    
    for (int i = 0; i < 3; i++) {
        fp = fopen(paths[i], "rb");
        if (fp) {
            printf("Opened: %s\n", paths[i]);
            break;
        }
    }
    
    if (!fp) {
        printf("Cannot open FDOTHER.DAT\n");
        return 1;
    }
    
    /* 读取索引76的偏移 */
    uint32_t offsets[2];
    fseek(fp, 4 * 76 + 6, SEEK_SET);
    fread(offsets, 1, 8, fp);
    
    uint32_t size = offsets[1] - offsets[0];
    printf("Index 76: start=%u, end=%u, size=%u\n", offsets[0], offsets[1], size);
    
    /* 读取全部数据 */
    uint8_t* data = (uint8_t*)malloc(size);
    fseek(fp, offsets[0], SEEK_SET);
    fread(data, 1, size, fp);
    
    /* 检查前100字节 */
    printf("\nFirst 100 bytes:\n");
    for (int i = 0; i < 100; i++) {
        printf("%3d ", data[i]);
        if ((i + 1) % 16 == 0) printf("\n");
    }
    printf("\n");
    
    /* 检查末尾768字节 */
    printf("\nLast 768 bytes (possible palette):\n");
    uint8_t* palette = data + size - 768;
    for (int i = 0; i < 16; i++) {
        printf("Color %d: R=%d G=%d B=%d\n", i, palette[i*3], palette[i*3+1], palette[i*3+2]);
    }
    
    /* 检查偏移10000开始的768字节 */
    printf("\nBytes at offset 10000:\n");
    for (int i = 0; i < 16; i++) {
        int off = 10000 + i * 3;
        if (off + 2 < size)
            printf("Color %d: R=%d G=%d B=%d\n", i, data[off], data[off+1], data[off+2]);
    }
    
    /* 检查是否有明显的调色板模式（6-bit值应在0-63范围） */
    printf("\nSearching for 6-bit palette pattern (values 0-63):\n");
    for (int off = 0; off < size - 768; off += 100) {
        int all_valid = 1;
        for (int j = 0; j < 48; j++) { /* 检查前16个颜色 */
            if (data[off + j] > 63) {
                all_valid = 0;
                break;
            }
        }
        if (all_valid) {
            printf("Possible palette at offset %d:\n", off);
            for (int i = 0; i < 8; i++) {
                printf("  Color %d: R=%d G=%d B=%d\n", i, data[off+i*3], data[off+i*3+1], data[off+i*3+2]);
            }
            break;
        }
    }
    
    free(data);
    fclose(fp);
    return 0;
}
