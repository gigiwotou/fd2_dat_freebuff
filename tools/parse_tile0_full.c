/* 
 * parse_tile0_full.c - 完整解析资源0的偏移表
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
    
    uint32_t s0, e0;
    memcpy(&s0, dat + 10 + 0 * 4, 4);
    memcpy(&e0, dat + 10 + 1 * 4, 4);
    
    uint8_t* res0 = dat + s0;
    uint32_t r0sz = e0 - s0;
    
    printf("Resource 0 size: %u bytes\n", r0sz);
    
    /* 打印前64字节hex */
    printf("\nFirst 64 bytes:\n");
    for (int i = 0; i < 64 && i < r0sz; i++) {
        printf("%02X ", res0[i]);
        if ((i + 1) % 16 == 0) printf("\n");
    }
    printf("\n");
    
    /* 解析偏移表 - 从byte 4开始，每4字节一个偏移 */
    printf("\nTile offsets (starting at byte 4):\n");
    int tile_count = 0;
    for (int i = 0; i < 100; i++) {
        uint32_t off;
        int pos = 4 + i * 4;
        if (pos + 4 > r0sz) break;
        memcpy(&off, res0 + pos, 4);
        if (off == 0 || off >= r0sz) {
            printf("  Tile %d: offset=%u (END at byte %d)\n", i, off, pos);
            break;
        }
        printf("  Tile %d: offset=%u (byte %d)\n", i, off, pos);
        tile_count = i + 1;
    }
    
    printf("\nTotal tiles found: %d\n", tile_count);
    
    /* 打印前几个tile的头部 */
    for (int i = 0; i < tile_count && i < 20; i++) {
        uint32_t off;
        memcpy(&off, res0 + 4 + i * 4, 4);
        if (off + 4 <= r0sz) {
            int16_t w, h;
            memcpy(&w, res0 + off, 2);
            memcpy(&h, res0 + off + 2, 2);
            printf("  Tile %d at byte %u: w=%d h=%d\n", i, off, w, h);
        }
    }
    
    free(dat);
    return 0;
}
