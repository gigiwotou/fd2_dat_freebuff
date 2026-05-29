/*
 * parse_fdother_res0.c - 解析FDOTHER.DAT资源0的完整结构
 * 
 * 结构分析结果:
 * - 偏移0-1: Width = 24 (WORD)
 * - 偏移2-3: Height = 24 (WORD)
 * - 偏移4-42: 主偏移表 (20项，每项2字节WORD)
 * - 偏移20(Tile ID 1): 子偏移表 (指向Tile ID 6-13)
 * - 偏移86(Tile ID 2): RLE压缩的24x24 tile图像数据
 * - 偏移307(Tile ID 3): RLE压缩的24x24 tile图像数据
 * - 偏移558(Tile ID 4): RLE压缩的24x24 tile图像数据
 * - 偏移794(Tile ID 5): RLE压缩的24x24 tile图像数据
 * - 偏移940(Tile ID 6): RLE压缩的24x24 tile图像数据
 * - 偏移1079(Tile ID 7): RLE压缩的24x24 tile图像数据
 * - 偏移1310(Tile ID 8): RLE压缩的24x24 tile图像数据
 * - 偏移1444(Tile ID 9): RLE压缩的24x24 tile图像数据
 * - 偏移1575(Tile ID 10): RLE压缩的24x24 tile图像数据
 * - 偏移1707(Tile ID 11): RLE压缩的24x24 tile图像数据
 * 
 * RLE压缩格式:
 * - 0xC0-0xFF: 重复字节 (count = cmd & 0x3F, if 0 then 64)
 * - 0x80-0xBF: 原始字节 (count = cmd & 0x7F, if 0 then 128)
 * - 0x00-0x7F: 单字节
 * 
 * 编译: gcc -I. -o bin/parse_fdother_res0.exe tools/parse_fdother_res0.c
 * 运行: bin\parse_fdother_res0.exe game\FDOTHER.DAT
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

static void dump_hex(const uint8_t* data, size_t len, size_t base_offset) {
    for (size_t i = 0; i < len; i += 16) {
        printf("  %08X: ", (unsigned int)(base_offset + i));
        for (int j = 0; j < 16; j++) {
            if (i + j < len) {
                printf("%02X ", data[i + j]);
            } else {
                printf("   ");
            }
        }
        printf("  ");
        for (int j = 0; j < 16 && i + j < len; j++) {
            uint8_t c = data[i + j];
            printf("%c", (c >= 32 && c < 127) ? c : '.');
        }
        printf("\n");
    }
}

static uint8_t* load_file(const char* path, size_t* out_size) {
    FILE* f = fopen(path, "rb");
    if (!f) {
        fprintf(stderr, "错误: 无法打开文件 %s\n", path);
        return NULL;
    }
    fseek(f, 0, SEEK_END);
    size_t sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    uint8_t* buf = (uint8_t*)malloc(sz);
    if (buf) fread(buf, 1, sz, f);
    fclose(f);
    if (out_size) *out_size = sz;
    return buf;
}

static int rle_decode(const uint8_t* src, size_t src_len, uint8_t* dst, size_t dst_len) {
    size_t si = 0, di = 0;
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
    return (int)di;
}

static void save_bmp(const char* path, uint8_t* pixels, int w, int h, const uint8_t* palette) {
    FILE* f = fopen(path, "wb");
    if (!f) return;
    
    uint8_t bmp_header[14] = {0};
    bmp_header[0] = 'B'; bmp_header[1] = 'M';
    int row_bytes = w;
    int pad = (4 - (w % 4)) % 4;
    int row_size = w + pad;
    int pixel_data_size = row_size * h;
    int palette_size = 256 * 4;
    int file_size = 14 + 40 + palette_size + pixel_data_size;
    
    bmp_header[2] = file_size & 0xFF;
    bmp_header[3] = (file_size >> 8) & 0xFF;
    bmp_header[4] = (file_size >> 16) & 0xFF;
    bmp_header[5] = (file_size >> 24) & 0xFF;
    bmp_header[10] = 14 + 40 + palette_size;
    
    uint8_t info_header[40] = {0};
    info_header[0] = 40;
    info_header[4] = w & 0xFF; info_header[5] = (w >> 8) & 0xFF;
    info_header[6] = (w >> 16) & 0xFF; info_header[7] = (w >> 24) & 0xFF;
    info_header[8] = h & 0xFF; info_header[9] = (h >> 8) & 0xFF;
    info_header[10] = (h >> 16) & 0xFF; info_header[11] = (h >> 24) & 0xFF;
    info_header[12] = 1;
    info_header[14] = 8;
    info_header[20] = pixel_data_size & 0xFF;
    info_header[21] = (pixel_data_size >> 8) & 0xFF;
    info_header[22] = (pixel_data_size >> 16) & 0xFF;
    info_header[23] = (pixel_data_size >> 24) & 0xFF;
    
    fwrite(bmp_header, 1, 14, f);
    fwrite(info_header, 1, 40, f);
    
    if (palette) {
        for (int i = 0; i < 256; i++) {
            uint8_t b = palette[i * 3];
            uint8_t g = palette[i * 3 + 1];
            uint8_t r = palette[i * 3 + 2];
            uint8_t a = 0;
            fwrite(&b, 1, 1, f);
            fwrite(&g, 1, 1, f);
            fwrite(&r, 1, 1, f);
            fwrite(&a, 1, 1, f);
        }
    } else {
        for (int i = 0; i < 256; i++) {
            uint8_t rgb[4] = {(uint8_t)i, (uint8_t)i, (uint8_t)i, 0};
            fwrite(rgb, 1, 4, f);
        }
    }
    
    uint8_t* row_buf = (uint8_t*)malloc(row_size);
    for (int y = h - 1; y >= 0; y--) {
        memcpy(row_buf, pixels + y * w, w);
        memset(row_buf + w, 0, pad);
        fwrite(row_buf, 1, row_size, f);
    }
    free(row_buf);
    fclose(f);
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        printf("用法: %s <FDOTHER.DAT>\n", argv[0]);
        return 1;
    }
    
    size_t fsize;
    uint8_t* dat = load_file(argv[1], &fsize);
    if (!dat) return 1;
    
    printf("==========================================================\n");
    printf("FDOTHER.DAT 资源0 完整结构分析\n");
    printf("==========================================================\n");
    printf("文件大小: %zu 字节 (0x%08X)\n\n", fsize, (unsigned int)fsize);
    
    uint32_t res_count;
    memcpy(&res_count, dat + 6, 4);
    printf("资源总数: %u\n\n", res_count);
    
    if (res_count < 2) {
        printf("错误: 资源数量不足\n");
        free(dat);
        return 1;
    }
    
    uint32_t* offsets = (uint32_t*)malloc(res_count * sizeof(uint32_t));
    for (uint32_t i = 0; i < res_count; i++) {
        memcpy(&offsets[i], dat + 10 + i * 4, 4);
    }
    
    size_t res0_start = offsets[0];
    size_t res0_end = offsets[1];
    size_t res0_size = res0_end - res0_start;
    
    printf("资源0:\n");
    printf("  起始偏移: %zu (0x%08X)\n", res0_start, (unsigned int)res0_start);
    printf("  结束偏移: %zu (0x%08X)\n", res0_end, (unsigned int)res0_end);
    printf("  总大小: %zu 字节 (0x%08X)\n\n", res0_size, (unsigned int)res0_size);
    
    const uint8_t* res0 = dat + res0_start;
    
    /* ========== 1. 分析资源0头部 ========== */
    printf("=== 1. 资源0头部格式分析 ===\n\n");
    printf("资源0前32字节:\n");
    dump_hex(res0, res0_size > 32 ? 32 : res0_size, res0_start);
    
    uint16_t width, height;
    memcpy(&width, res0 + 0, 2);
    memcpy(&height, res0 + 2, 2);
    
    printf("\n头部解析:\n");
    printf("  偏移0-1: Width  = %u (0x%04X)\n", width, width);
    printf("  偏移2-3: Height = %u (0x%04X)\n", height, height);
    printf("  图像尺寸: %dx%d 像素\n", width, height);
    printf("  像素总数: %d\n\n", width * height);
    
    /* ========== 2. 分析主偏移表 ========== */
    printf("=== 2. 主偏移表分析 ===\n\n");
    printf("偏移表从偏移4开始，每项2字节(WORD)\n\n");
    printf("索引 | 表项位置 | 偏移值 | 说明\n");
    printf("-----|----------|--------|------\n");
    
    uint16_t main_offsets[30];
    int main_count = 0;
    
    for (int i = 0; i < 20; i++) {
        size_t pos = 4 + i * 2;
        if (pos + 2 > res0_size) break;
        
        uint16_t offset_val;
        memcpy(&offset_val, res0 + pos, 2);
        
        printf("  %2d  | 0x%04X   | 0x%04X(%5u) | %s\n", 
               i, (unsigned int)pos, offset_val, offset_val,
               (offset_val > 0 && offset_val < res0_size) ? "有效" : 
               (offset_val == 0) ? "空" : "无效");
        
        if (offset_val > 0 && offset_val < res0_size) {
            main_offsets[main_count++] = offset_val;
        }
    }
    
    printf("\n共找到 %d 个有效偏移\n", main_count);
    
    /* ========== 3. 分析Tile ID 1 (子偏移表) ========== */
    printf("\n=== 3. Tile ID 1 分析 (子偏移表) ===\n\n");
    
    uint16_t tile1_offset = main_offsets[0];
    printf("Tile ID 1起始偏移: %u (0x%04X)\n", tile1_offset, tile1_offset);
    printf("Tile ID 1数据前32字节:\n");
    dump_hex(res0 + tile1_offset, res0_size - tile1_offset > 32 ? 32 : res0_size - tile1_offset, 
             res0_start + tile1_offset);
    
    /* 检查是否是子偏移表 */
    printf("\n解析为WORD偏移表:\n");
    printf("索引 | 位置 | 偏移值 | 说明\n");
    printf("-----|------|--------|------\n");
    
    uint16_t sub_offsets[20];
    int sub_count = 0;
    
    for (int i = 0; i < 16; i++) {
        size_t pos = tile1_offset + i * 2;
        if (pos + 2 > res0_size) break;
        
        uint16_t val;
        memcpy(&val, res0 + pos, 2);
        
        printf("  %2d  | 0x%04X | 0x%04X(%5u) | %s\n", 
               i, (unsigned int)pos, val, val,
               (val > 0 && val < res0_size) ? "有效" : "无效");
        
        if (val > 0 && val < res0_size) {
            sub_offsets[sub_count++] = val;
        }
    }
    
    printf("\n子偏移表包含 %d 个有效偏移\n", sub_count);
    
    /* ========== 4. Tile ID 2-19 详细分析 ========== */
    printf("\n=== 4. Tile ID 2-19 详细分析 ===\n\n");
    
    typedef struct {
        int id;
        uint16_t offset;
        size_t size;
        int decoded;
        uint8_t* pixels;
    } TileInfo;
    
    TileInfo tiles[20];
    memset(tiles, 0, sizeof(tiles));
    
    for (int tile_id = 2; tile_id <= 19 && tile_id <= main_count; tile_id++) {
        uint16_t cur_offset = main_offsets[tile_id - 1];
        uint16_t next_offset = (tile_id < main_count) ? main_offsets[tile_id] : res0_size;
        size_t tile_size = next_offset - cur_offset;
        
        tiles[tile_id].id = tile_id;
        tiles[tile_id].offset = cur_offset;
        tiles[tile_id].size = tile_size;
        
        printf("Tile ID %d:\n", tile_id);
        printf("  偏移: %u (0x%04X)\n", cur_offset, cur_offset);
        printf("  大小: %zu 字节\n", tile_size);
        
        if (tile_size >= 8) {
            printf("  前8字节: ");
            for (int j = 0; j < 8; j++) {
                printf("%02X ", res0[cur_offset + j]);
            }
            printf("\n");
        }
        
        /* RLE解码 */
        size_t pixel_count = (size_t)width * height;
        uint8_t* pixels = (uint8_t*)calloc(pixel_count, 1);
        if (pixels) {
            int decoded = rle_decode(res0 + cur_offset, tile_size, pixels, pixel_count);
            tiles[tile_id].decoded = decoded;
            tiles[tile_id].pixels = pixels;
            
            printf("  RLE解码: %d / %zu 像素 (%.1f%%)\n", 
                   decoded, pixel_count,
                   (double)decoded / pixel_count * 100.0);
            
            /* 判断解码质量 */
            if (decoded == (int)pixel_count) {
                printf("  状态: 完全解码 ✓\n");
            } else if (decoded > (int)pixel_count * 0.5) {
                printf("  状态: 部分解码\n");
            } else {
                printf("  状态: 解码失败 ✗\n");
            }
        }
        printf("\n");
    }
    
    /* ========== 5. 保存Tile图像 ========== */
    printf("\n=== 5. 保存Tile图像 ===\n\n");
    printf("保存到 output/res0_tile_*.bmp\n\n");
    
    for (int tile_id = 2; tile_id <= 19 && tile_id <= main_count; tile_id++) {
        if (tiles[tile_id].pixels && tiles[tile_id].decoded > 0) {
            char path[256];
            snprintf(path, sizeof(path), "output/res0_tile_%02d_%dx%d.bmp", 
                     tile_id, width, height);
            save_bmp(path, tiles[tile_id].pixels, width, height, NULL);
            printf("  Tile %2d: 已保存 (解码 %d 像素)\n", 
                   tile_id, tiles[tile_id].decoded);
        }
    }
    
    /* ========== 6. 汇总表格 ========== */
    printf("\n=== 6. Tile ID 2-19 汇总 ===\n\n");
    printf("Tile ID | 偏移  | 大小 | 宽 | 高 | 解码率  | 状态\n");
    printf("--------|-------|------|----|----|---------|------\n");
    
    for (int tile_id = 2; tile_id <= 19 && tile_id <= main_count; tile_id++) {
        double rate = (double)tiles[tile_id].decoded / ((size_t)width * height) * 100.0;
        const char* status;
        if (rate >= 99.0) status = "完全";
        else if (rate >= 50.0) status = "良好";
        else if (rate >= 20.0) status = "部分";
        else status = "失败";
        
        printf("  %5d | 0x%04X | %4zu | %2d | %2d | %5.1f%% | %s\n",
               tile_id, tiles[tile_id].offset, tiles[tile_id].size,
               width, height, rate, status);
    }
    
    /* ========== 7. 结构总结 ========== */
    printf("\n=== 7. 资源0 完整结构总结 ===\n\n");
    printf("+-------------------------------------------------------+\n");
    printf("| 资源0 结构                                             |\n");
    printf("+-------------------------------------------------------+\n");
    printf("| 偏移0-1:  Width = %u                                    |\n", width);
    printf("| 偏移2-3:  Height = %u                                   |\n", height);
    printf("| 偏移4-42: 主偏移表 (20项，每项2字节WORD)                |\n");
    printf("| 偏移20:     Tile ID 1 (子偏移表，指向Tile 6-13)         |\n");
    printf("| 偏移86:     Tile ID 2 (RLE图像数据)                     |\n");
    printf("| 偏移307:    Tile ID 3 (RLE图像数据)                     |\n");
    printf("| 偏移558:    Tile ID 4 (RLE图像数据)                     |\n");
    printf("| 偏移794:    Tile ID 5 (RLE图像数据)                     |\n");
    printf("| 偏移940:    Tile ID 6 (RLE图像数据)                     |\n");
    printf("| 偏移1079:   Tile ID 7 (RLE图像数据)                     |\n");
    printf("| 偏移1310:   Tile ID 8 (RLE图像数据)                     |\n");
    printf("| 偏移1444:   Tile ID 9 (RLE图像数据)                     |\n");
    printf("| 偏移1575:   Tile ID 10 (RLE图像数据)                    |\n");
    printf("| 偏移1707:   Tile ID 11 (RLE图像数据)                    |\n");
    printf("+-------------------------------------------------------+\n\n");
    
    printf("关键发现:\n");
    printf("1. Tile尺寸: %dx%d 像素\n", width, height);
    printf("2. 偏移表类型: WORD (2字节)\n");
    printf("3. Tile ID 1是子偏移表，不是图像数据\n");
    printf("4. Tile ID 2-11是RLE压缩的图像数据\n");
    printf("5. 资源0前20字节不包含调色板，仅包含宽高和偏移表\n");
    printf("6. 调色板应该在资源0之前或其他资源中\n");
    
    /* 清理 */
    for (int i = 2; i <= 19; i++) {
        if (tiles[i].pixels) free(tiles[i].pixels);
    }
    free(offsets);
    free(dat);
    
    printf("\n==========================================================\n");
    printf("分析完成！\n");
    printf("==========================================================\n");
    
    return 0;
}