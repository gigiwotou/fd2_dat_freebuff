/* 
 * parse_resource98.c - 解析FDOTHER.DAT资源98，查看是否是调色板
 * 编译: gcc tools/parse_resource98.c -o tools/parse_resource98.exe
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

static uint8_t* load_file(const char* path, size_t* out_size) {
    FILE* f = fopen(path, "rb");
    if (!f) return NULL;
    fseek(f, 0, SEEK_END);
    size_t sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    uint8_t* buf = (uint8_t*)malloc(sz);
    if (buf) fread(buf, 1, sz, f);
    fclose(f);
    if (out_size) *out_size = sz;
    return buf;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        printf("Usage: %s <FDOTHER.DAT>\n", argv[0]);
        return 1;
    }
    
    size_t fsize;
    uint8_t* dat = load_file(argv[1], &fsize);
    if (!dat) { printf("Cannot load file\n"); return 1; }
    
    printf("File size: %zu bytes\n", fsize);
    
    uint32_t count;
    memcpy(&count, dat + 6, 4);
    printf("Resource count: %d\n\n", count);
    
    /* 查看资源98 */
    uint32_t s98, e98;
    memcpy(&s98, dat + 10 + 98 * 4, 4);
    memcpy(&e98, dat + 10 + 99 * 4, 4);
    printf("Resource 98: offset=%u, size=%u\n", s98, e98 - s98);
    
    /* 打印前100字节 */
    printf("First 100 bytes:\n");
    for (int i = 0; i < 100 && (s98 + i) < fsize; i++) {
        printf("%02X ", dat[s98 + i]);
        if ((i + 1) % 16 == 0) printf("\n");
    }
    printf("\n\n");
    
    /* 检查是否是768字节的调色板 */
    if (e98 - s98 == 768) {
        printf("Resource 98 is 768 bytes - likely a palette (256 colors * 3 bytes)\n");
        printf("Palette entries (first 10):\n");
        for (int i = 0; i < 10; i++) {
            uint8_t r = dat[s98 + i * 3];
            uint8_t g = dat[s98 + i * 3 + 1];
            uint8_t b = dat[s98 + i * 3 + 2];
            printf("  Color %d: R=%d G=%d B=%d\n", i, r, g, b);
        }
    }
    
    /* 查看资源99 */
    uint32_t s99, e99;
    memcpy(&s99, dat + 10 + 99 * 4, 4);
    memcpy(&e99, dat + 10 + 100 * 4, 4);
    printf("\nResource 99: offset=%u, size=%u\n", s99, e99 - s99);
    
    if (e99 - s99 == 768) {
        printf("Resource 99 is 768 bytes - likely a palette\n");
        printf("Palette entries (first 10):\n");
        for (int i = 0; i < 10; i++) {
            uint8_t r = dat[s99 + i * 3];
            uint8_t g = dat[s99 + i * 3 + 1];
            uint8_t b = dat[s99 + i * 3 + 2];
            printf("  Color %d: R=%d G=%d B=%d\n", i, r, g, b);
        }
    }
    
    free(dat);
    return 0;
}
