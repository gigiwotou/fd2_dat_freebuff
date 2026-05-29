/* 
 * parse_fdother.c - 解析FDOTHER.DAT查找对话框UI资源
 * 编译: gcc tools/parse_fdother.c -o tools/parse_fdother.exe
 * 运行: tools\parse_fdother.exe game\FDOTHER.DAT
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

/* BMP头 */
#pragma pack(push, 1)
typedef struct {
    uint16_t sig; uint32_t fsize; uint16_t r1, r2; uint32_t offset;
    uint32_t hsize; int32_t w, h; uint16_t planes, bpp;
    uint32_t comp, isize; int32_t xr, yr; uint32_t colors, important;
} BMPH;
#pragma pack(pop)

typedef struct { uint8_t b, g, r, a; } RGBA;

static void save_bmp_8bit(const char* path, uint8_t* px, int w, int h) {
    FILE* f = fopen(path, "wb");
    if (!f) return;
    
    int row = w, pad = (4 - (row % 4)) % 4, rowsz = row + pad;
    int isz = rowsz * h, psz = 256 * 4, fsz = sizeof(BMPH) + psz + isz;
    
    BMPH hdr = {0};
    hdr.sig = 0x4D42; hdr.fsize = fsz; hdr.offset = sizeof(BMPH) + psz;
    hdr.hsize = 40; hdr.w = w; hdr.h = h; hdr.planes = 1; hdr.bpp = 8; hdr.isize = isz;
    
    fwrite(&hdr, 1, sizeof(BMPH), f);
    
    RGBA pal[256];
    memset(pal, 0, sizeof(pal));
    for (int i = 0; i < 256; i++) {
        pal[i].r = pal[i].g = pal[i].b = (uint8_t)i;
    }
    fwrite(pal, 1, sizeof(pal), f);
    
    for (int y = h - 1; y >= 0; y--) {
        fwrite(px + y * w, 1, row, f);
        if (pad) { uint8_t z[3] = {0}; fwrite(z, 1, pad, f); }
    }
    fclose(f);
}

static void save_bmp_32bit(const char* path, uint32_t* px, int w, int h) {
    FILE* f = fopen(path, "wb");
    if (!f) return;
    
    int row_bytes = w * 4;
    int pad = (4 - (row_bytes % 4)) % 4;
    int rowsz = row_bytes + pad;
    int isz = rowsz * h;
    int psz = 0;
    int fsz = sizeof(BMPH) + psz + isz;
    
    BMPH hdr = {0};
    hdr.sig = 0x4D42; hdr.fsize = fsz; hdr.offset = sizeof(BMPH) + psz;
    hdr.hsize = 40; hdr.w = w; hdr.h = h; hdr.planes = 1; hdr.bpp = 32; 
    hdr.comp = 0; hdr.isize = isz;
    
    fwrite(&hdr, 1, sizeof(BMPH), f);
    
    uint8_t* row_buf = (uint8_t*)malloc(rowsz);
    for (int y = h - 1; y >= 0; y--) {
        memcpy(row_buf, (uint8_t*)(px + y * w), row_bytes);
        if (pad) memset(row_buf + row_bytes, 0, pad);
        fwrite(row_buf, 1, rowsz, f);
    }
    free(row_buf);
    fclose(f);
}

/* RLE解压缩 - 格式A: 0xC0+ 重复, 0x80+ 原始, <0x80 单字节 */
static int rle_decode_a(const uint8_t* src, int src_len, uint8_t* dst, int dst_len) {
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

/* RLE解压缩 - 格式B: 简单的字节对 (count, value) */
static int rle_decode_b(const uint8_t* src, int src_len, uint8_t* dst, int dst_len) {
    int si = 0, di = 0;
    while (si + 1 < src_len && di < dst_len) {
        uint8_t count = src[si++];
        uint8_t value = src[si++];
        for (int i = 0; i < count && di < dst_len; i++)
            dst[di++] = value;
    }
    return di;
}

/* 尝试解析图像资源 - 返回解码后的像素数据 */
typedef struct {
    int w, h;
    uint8_t* pixels_8bit;
    uint32_t* pixels_32bit;
    int is_32bit;
} ParsedImage;

/* 打印资源头部的hex dump */
static void dump_hex(const uint8_t* data, int len) {
    for (int i = 0; i < len; i++) {
        printf("%02X ", data[i]);
        if ((i + 1) % 16 == 0) printf("\n");
    }
    printf("\n");
}

static int try_parse_image(const uint8_t* res, uint32_t sz, ParsedImage* img) {
    if (sz < 20) return -1;
    
    /* 打印头部信息用于调试 */
    printf("       Header bytes: ");
    dump_hex(res, 32);
    
    /* 尝试不同的头部格式 */
    
    /* 格式1: [4B unknown][4B f0][4B f1][4B f2][2B w][2B h][data...] */
    int16_t w1, h1;
    memcpy(&w1, res + 16, 2);
    memcpy(&h1, res + 18, 2);
    
    /* 格式2: [4B w][4B h][data...] */
    int32_t w2, h2;
    memcpy(&w2, res + 0, 4);
    memcpy(&h2, res + 4, 4);
    
    /* 格式3: [2B w][2B h][data...] */
    int16_t w3, h3;
    memcpy(&w3, res + 0, 2);
    memcpy(&h3, res + 2, 2);
    
    printf("       Format1: w=%d h=%d, Format2: w=%d h=%d, Format3: w=%d h=%d\n", 
           w1, h1, w2, h2, w3, h3);
    
    /* 检查哪种格式合理 */
    int valid_format = -1;
    int pw = 0, ph = 0;
    
    if (w1 > 0 && w1 <= 2048 && h1 > 0 && h1 <= 2048) {
        valid_format = 1;
        pw = w1; ph = h1;
        printf("       Using format 1\n");
    } else if (w2 > 0 && w2 <= 2048 && h2 > 0 && h2 <= 2048) {
        valid_format = 2;
        pw = w2; ph = h2;
        printf("       Using format 2\n");
    } else if (w3 > 0 && w3 <= 2048 && h3 > 0 && h3 <= 2048) {
        valid_format = 3;
        pw = w3; ph = h3;
        printf("       Using format 3\n");
    }
    
    if (valid_format == -1) {
        printf("       No valid format found\n");
        return -1;
    }
    
    int pixel_count = pw * ph;
    if (pixel_count <= 0 || pixel_count > 10000000) {
        printf("       Invalid pixel count: %d\n", pixel_count);
        return -1;
    }
    
    /* 计算数据起始位置 */
    uint32_t data_start = 0;
    if (valid_format == 1) data_start = 20;
    else if (valid_format == 2) data_start = 8;
    else if (valid_format == 3) data_start = 4;
    
    if (data_start >= sz) {
        printf("       Data start beyond resource end\n");
        return -1;
    }
    
    uint32_t data_sz = sz - data_start;
    printf("       Data: start=%u, size=%u, pixels_needed=%d\n", data_start, data_sz, pixel_count);
    
    /* 分配8bit像素缓冲区 */
    uint8_t* pixels = (uint8_t*)calloc(pixel_count, 1);
    if (!pixels) return -1;
    
    /* 尝试RLE解码 */
    int decoded = rle_decode_a(res + data_start, data_sz, pixels, pixel_count);
    printf("       RLE-A decoded: %d bytes\n", decoded);
    
    if (decoded < pixel_count) {
        /* 尝试其他解码方式 */
        printf("       RLE-A failed, trying RLE-B...\n");
        decoded = rle_decode_b(res + data_start, data_sz, pixels, pixel_count);
        printf("       RLE-B decoded: %d bytes\n", decoded);
    }
    
    if (decoded < pixel_count) {
        printf("       Still not enough data, padding with zeros\n");
        /* 数据不足但填充 */
    }
    
    img->w = pw;
    img->h = ph;
    img->pixels_8bit = pixels;
    img->is_32bit = 0;
    
    return 0;
}

/* 查找特定尺寸的资源 */
static int find_dialog_resource(const uint8_t* dat, size_t fsize, int target_w, int target_h) {
    uint32_t count;
    memcpy(&count, dat + 6, 4);
    printf("Resource count: %d\n\n", count);
    
    for (uint32_t i = 0; i < count - 1; i++) {
        uint32_t so, eo;
        memcpy(&so, dat + 10 + i * 4, 4);
        memcpy(&eo, dat + 10 + (i + 1) * 4, 4);
        
        if (so >= fsize || eo > fsize || eo <= so) continue;
        uint32_t rsz = eo - so;
        const uint8_t* res = dat + so;
        
        printf("=== Resource %d: offset=%u, size=%u ===\n", i, so, rsz);
        
        ParsedImage img = {0};
        if (try_parse_image(res, rsz, &img) == 0) {
            printf("   SUCCESS: %dx%d\n", img.w, img.h);
            
            char path[256];
            snprintf(path, sizeof(path), "output/resource_%04d_%dx%d.bmp", i, img.w, img.h);
            save_bmp_8bit(path, img.pixels_8bit, img.w, img.h);
            printf("   Saved to: %s\n", path);
            
            /* 检查是否匹配目标尺寸 */
            if (img.w == target_w && img.h == target_h) {
                printf("   *** MATCHES TARGET SIZE %dx%d ***\n", target_w, target_h);
                free(img.pixels_8bit);
                return i;
            }
            
            /* 保存接近目标尺寸的资源 */
            if (img.w >= 200 && img.w <= 400 && img.h >= 50 && img.h <= 150) {
                snprintf(path, sizeof(path), "output/dialog_candidate_%04d_%dx%d.bmp", i, img.w, img.h);
                save_bmp_8bit(path, img.pixels_8bit, img.w, img.h);
                printf("   Saved as dialog candidate\n");
            }
            
            free(img.pixels_8bit);
        } else {
            printf("   Failed to parse\n");
        }
        printf("\n");
    }
    
    return -1;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        printf("Usage: %s <FDOTHER.DAT>\n", argv[0]);
        return 1;
    }
    
    size_t fsize;
    uint8_t* dat = load_file(argv[1], &fsize);
    if (!dat) { printf("Cannot load file\n"); return 1; }
    
    printf("=== FDOTHER.DAT Parser ===\n");
    printf("File size: %zu bytes\n\n", fsize);
    
    /* 首先打印文件头部 */
    printf("File header (first 64 bytes):\n");
    for (size_t i = 0; i < 64 && i < fsize; i++) {
        printf("%02X ", dat[i]);
        if ((i + 1) % 16 == 0) printf("\n");
    }
    printf("\n\n");
    
    /* 查找310x86的对话框背景 */
    printf("=== Searching for 310x86 dialog background ===\n\n");
    int found = find_dialog_resource(dat, fsize, 310, 86);
    
    if (found >= 0) {
        printf("\n*** Found dialog background at resource %d ***\n", found);
    } else {
        printf("\n*** Dialog background 310x86 not found ***\n");
        printf("Searching for similar sizes...\n\n");
    }
    
    free(dat);
    return 0;
}
