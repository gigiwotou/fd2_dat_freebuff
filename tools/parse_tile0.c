/* 
 * parse_tile0.c - 详细解析FDOTHER.DAT资源0 (tile资源)
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

/* RLE解压缩 */
static int rle_decode(const uint8_t* src, int src_len, uint8_t* dst, int dst_len) {
    int si = 0, di = 0;
    while (si < src_len && di < dst_len) {
        uint8_t cmd = src[si++];
        if (cmd >= 0xC0) {
            int count = cmd & 0x3F;
            if (count == 0) count = 64;
            if (si < src_len) {
                uint8_t val = src[si++];
                for (int i = 0; i < count && di < dst_len; i++)
                    dst[di++] = val;
            }
        } else if (cmd >= 0x80) {
            int count = cmd & 0x7F;
            if (count == 0) count = 128;
            for (int i = 0; i < count && di < dst_len && si < src_len; i++)
                dst[di++] = src[si++];
        } else {
            dst[di++] = cmd;
        }
    }
    return di;
}

typedef struct { uint8_t b, g, r, a; } RGBA;
#pragma pack(push, 1)
typedef struct {
    uint16_t sig; uint32_t fsize; uint16_t r1, r2; uint32_t offset;
    uint32_t hsize; int32_t w, h; uint16_t planes, bpp;
    uint32_t comp, isize; int32_t xr, yr; uint32_t colors, important;
} BMPH;
#pragma pack(pop)

static void save_bmp_8bit(const char* path, uint8_t* px, int w, int h, uint32_t* pal) {
    FILE* f = fopen(path, "wb");
    if (!f) return;
    
    int row = w, pad = (4 - (row % 4)) % 4, rowsz = row + pad;
    int isz = rowsz * h, psz = 256 * 4, fsz = sizeof(BMPH) + psz + isz;
    
    BMPH hdr = {0};
    hdr.sig = 0x4D42; hdr.fsize = fsz; hdr.offset = sizeof(BMPH) + psz;
    hdr.hsize = 40; hdr.w = w; hdr.h = h; hdr.planes = 1; hdr.bpp = 8; hdr.isize = isz;
    
    fwrite(&hdr, 1, sizeof(BMPH), f);
    
    RGBA palette[256];
    for (int i = 0; i < 256; i++) {
        palette[i].r = (pal[i] >> 16) & 0xFF;
        palette[i].g = (pal[i] >> 8) & 0xFF;
        palette[i].b = pal[i] & 0xFF;
        palette[i].a = 0;
    }
    fwrite(palette, 1, sizeof(palette), f);
    
    for (int y = h - 1; y >= 0; y--) {
        fwrite(px + y * w, 1, row, f);
        if (pad) { uint8_t z[3] = {0}; fwrite(z, 1, pad, f); }
    }
    fclose(f);
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
    
    /* 资源0 */
    uint32_t s0, e0;
    memcpy(&s0, dat + 10 + 0 * 4, 4);
    memcpy(&e0, dat + 10 + 1 * 4, 4);
    printf("Resource 0: offset=%u, size=%u\n", s0, e0 - s0);
    
    uint8_t* res0 = dat + s0;
    uint32_t r0sz = e0 - s0;
    
    /* 打印头部32字节 */
    printf("Header (first 32 bytes):\n");
    for (int i = 0; i < 32 && i < r0sz; i++) {
        printf("%02X ", res0[i]);
        if ((i + 1) % 16 == 0) printf("\n");
    }
    printf("\n\n");
    
    /* 解析格式: [2B w][2B h][4B f0][4B f1][4B f2][4B f3][data...] */
    int16_t w, h;
    memcpy(&w, res0, 2);
    memcpy(&h, res0 + 2, 2);
    printf("Width=%d, Height=%d\n", w, h);
    
    uint32_t foffs[4];
    memcpy(&foffs[0], res0 + 4, 4);
    memcpy(&foffs[1], res0 + 8, 4);
    memcpy(&foffs[2], res0 + 12, 4);
    memcpy(&foffs[3], res0 + 16, 4);
    printf("Frame offsets: f0=%u, f1=%u, f2=%u, f3=%u\n", foffs[0], foffs[1], foffs[2], foffs[3]);
    
    /* 计算每帧大小 */
    struct { int s, e; } frames[4];
    frames[0].s = 20; frames[0].e = foffs[0] < r0sz ? foffs[0] : r0sz;
    frames[1].s = foffs[0]; frames[1].e = foffs[1] < r0sz ? foffs[1] : r0sz;
    frames[2].s = foffs[1]; frames[2].e = foffs[2] < r0sz ? foffs[2] : r0sz;
    frames[3].s = foffs[2]; frames[3].e = foffs[3] < r0sz ? foffs[3] : r0sz;
    
    int px = w * h;
    printf("\nExpected pixels per tile: %d\n", px);
    
    /* 加载资源98调色板 */
    uint32_t s98, e98;
    memcpy(&s98, dat + 10 + 98 * 4, 4);
    memcpy(&e98, dat + 10 + 99 * 4, 4);
    printf("\nResource 98 (palette): offset=%u, size=%u\n", s98, e98 - s98);
    
    uint32_t palette[256] = {0};
    if (e98 - s98 == 768) {
        for (int i = 0; i < 256; i++) {
            uint8_t r6 = dat[s98 + i * 3] & 0x3F;
            uint8_t g6 = dat[s98 + i * 3 + 1] & 0x3F;
            uint8_t b6 = dat[s98 + i * 3 + 2] & 0x3F;
            palette[i] = (0xFFu << 24) | 
                         ((r6 << 2) | (r6 >> 4)) << 16 | 
                         ((g6 << 2) | (g6 >> 4)) << 8 | 
                         ((b6 << 2) | (b6 >> 4));
        }
    }
    
    /* 解压缩并保存每一帧 */
    uint8_t* buf = (uint8_t*)malloc(px);
    for (int i = 0; i < 4; i++) {
        int fsz = frames[i].e - frames[i].s;
        printf("\nFrame %d: offset=%d, size=%d\n", i, frames[i].s, fsz);
        
        if (fsz > 0) {
            memset(buf, 0, px);
            int decoded = rle_decode(res0 + frames[i].s, fsz, buf, px);
            printf("  Decoded: %d pixels\n", decoded);
            
            /* 打印第一行像素值 */
            printf("  First row pixels: ");
            for (int c = 0; c < w && c < 24; c++) {
                printf("%d ", buf[c]);
            }
            printf("\n");
            
            /* 保存BMP */
            char path[64];
            snprintf(path, sizeof(path), "output/tile_frame%d.bmp", i);
            save_bmp_8bit(path, buf, w, h, palette);
            printf("  Saved to %s\n", path);
        }
    }
    
    free(buf);
    free(dat);
    return 0;
}
