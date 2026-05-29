/* 
 * parse_tile0_correct.c - 正确解析资源0的偏移表
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
    
    /* 解析头部: [2B w][2B h][offsets as 2B WORDs...] */
    int16_t w, h;
    memcpy(&w, res0, 2);
    memcpy(&h, res0 + 2, 2);
    printf("Width=%d, Height=%d\n", w, h);
    
    /* 偏移表从byte 4开始，每2字节一个WORD偏移 */
    printf("\nTile offsets (WORD, starting at byte 4):\n");
    int tile_count = 0;
    for (int i = 0; i < 100; i++) {
        int pos = 4 + i * 2;
        if (pos + 2 > r0sz) break;
        uint16_t off;
        memcpy(&off, res0 + pos, 2);
        if (off == 0 || off >= r0sz) {
            printf("  Tile %d: offset=%u (END at byte %d)\n", i, off, pos);
            break;
        }
        printf("  Tile %d: offset=%u (byte %d)\n", i, off, pos);
        tile_count = i + 1;
    }
    
    printf("\nTotal tiles found: %d\n", tile_count);
    
    /* 打印前几个tile的头部 */
    for (int i = 0; i < tile_count && i < 30; i++) {
        uint16_t off;
        memcpy(&off, res0 + 4 + i * 2, 2);
        if (off + 4 <= r0sz) {
            int16_t tw, th;
            memcpy(&tw, res0 + off, 2);
            memcpy(&th, res0 + off + 2, 2);
            printf("  Tile %d at byte %u: w=%d h=%d, pixel_data starts at %u\n", 
                   i, off, tw, th, off + 4);
        }
    }
    
    /* 计算每个tile的数据大小 */
    printf("\nTile data sizes:\n");
    int pixel_count = w * h;
    for (int i = 0; i < tile_count; i++) {
        uint16_t off, next_off;
        memcpy(&off, res0 + 4 + i * 2, 2);
        if (i + 1 < tile_count) {
            memcpy(&next_off, res0 + 4 + (i + 1) * 2, 2);
        } else {
            next_off = r0sz;
        }
        int tile_data_sz = next_off - off;
        printf("  Tile %d: data size = %d bytes (expected pixels = %d)\n", 
               i, tile_data_sz, pixel_count);
    }
    
    free(dat);
    return 0;
}
