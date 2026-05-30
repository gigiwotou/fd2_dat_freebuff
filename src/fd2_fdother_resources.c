/**
 * FDOTHER.DAT 资源加载和解析实现
 * 严格按照MCP汇编代码实现，从索引0开始逐一解析所有资源
 * 
 * 根据sub_111BA函数逻辑：
 * - 索引表从偏移6开始，每项4字节
 * - 资源大小 = offsets[index+1] - offsets[index]
 */

#include "fd2_fdother_resources.h"
#include "fd2_dat.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ========================================================================
 * FDOTHER.DAT 全局数据结构
 * ======================================================================== */

typedef struct {
    byte* data;          
    dword file_size;     
    dword resource_count; 
    dword* offsets;      
    bool loaded;         
} fdother_global_t;

static fdother_global_t g_fdother = {0};

/* ========================================================================
 * FDOTHER.DAT 文件加载
 * ======================================================================== */

int fdother_load(const char* filepath) {
    if (g_fdother.loaded) {
        fdother_unload();
    }
    
    FILE* fp = fopen(filepath, "rb");
    if (!fp) {
        printf("Error: Cannot open FDOTHER.DAT: %s\n", filepath);
        return -1;
    }
    
    fseek(fp, 0, SEEK_END);
    long file_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    
    byte* data = (byte*)malloc(file_size);
    if (!data) {
        fclose(fp);
        printf("Error: Out of memory for FDOTHER.DAT (%ld bytes)\n", file_size);
        return -1;
    }
    
    if (fread(data, 1, file_size, fp) != file_size) {
        free(data);
        fclose(fp);
        printf("Error: Failed to read FDOTHER.DAT\n");
        return -1;
    }
    fclose(fp);
    
    if (file_size < 6 || memcmp(data, "LLLLLL", 6) != 0) {
        free(data);
        printf("Error: Invalid FDOTHER.DAT magic\n");
        return -1;
    }
    
    dword max_resources = 0;
    dword table_offset = 6;
    
    while (table_offset + 4 <= (dword)file_size) {
        dword res_offset = *(dword*)(data + table_offset);
        if (res_offset > (dword)file_size || res_offset == 0) {
            break;
        }
        max_resources++;
        table_offset += 4;
    }
    
    if (max_resources == 0) {
        free(data);
        printf("Error: No resources found in FDOTHER.DAT\n");
        return -1;
    }
    
    dword* offsets = (dword*)malloc((max_resources + 1) * sizeof(dword));
    if (!offsets) {
        free(data);
        printf("Error: Out of memory for offset table\n");
        return -1;
    }
    
    for (dword i = 0; i < max_resources; i++) {
        offsets[i] = *(dword*)(data + 6 + i * 4);
    }
    offsets[max_resources] = (dword)file_size;
    
    g_fdother.data = data;
    g_fdother.file_size = (dword)file_size;
    g_fdother.resource_count = max_resources;
    g_fdother.offsets = offsets;
    g_fdother.loaded = true;
    
    printf("FDOTHER.DAT loaded: %u resources, %u bytes\n", max_resources, g_fdother.file_size);
    return 0;
}

void fdother_unload(void) {
    if (g_fdother.data) {
        free(g_fdother.data);
        g_fdother.data = NULL;
    }
    if (g_fdother.offsets) {
        free(g_fdother.offsets);
        g_fdother.offsets = NULL;
    }
    g_fdother.file_size = 0;
    g_fdother.resource_count = 0;
    g_fdother.loaded = false;
}

const byte* fdother_get_resource(int index, dword* out_size) {
    if (!g_fdother.loaded || index < 0 || index >= (int)g_fdother.resource_count) {
        if (out_size) *out_size = 0;
        return NULL;
    }
    
    dword start = g_fdother.offsets[index];
    dword end = g_fdother.offsets[index + 1];
    dword size = end - start;
    
    if (out_size) *out_size = size;
    return g_fdother.data + start;
}

/* ========================================================================
 * 资源类型识别
 * ======================================================================== */

fdother_res_type_t fdother_get_resource_type(const byte* data, dword size) {
    if (!data || size < 4) {
        return FDOTHER_RES_TYPE_RAW;
    }
    
    if (size == 768) {
        return FDOTHER_RES_TYPE_PALETTE;
    }
    
    if (memcmp(data, "LMI1", 4) == 0) {
        return FDOTHER_RES_TYPE_LMI1;
    }
    
    if (size >= 6 && memcmp(data, "LLLLLL", 6) == 0) {
        return FDOTHER_RES_TYPE_NESTED_DAT;
    }
    
    if (size >= 4) {
        word w = data[0] | (data[1] << 8);
        word h = data[2] | (data[3] << 8);
        if (w > 0 && w <= 640 && h > 0 && h <= 480) {
            return FDOTHER_RES_TYPE_TILE;
        }
    }
    
    return FDOTHER_RES_TYPE_RAW;
}

/* ========================================================================
 * 调色板解析
 * ======================================================================== */

int fdother_parse_palette(const byte* data, dword size, fdother_palette_t* out_palette) {
    if (!data || !out_palette || size != 768) {
        return -1;
    }
    
    memcpy(out_palette->colors, data, 768);
    return 0;
}

void fdother_palette_to_rgb24(const fdother_palette_t* pal, byte* out_rgb24) {
    if (!pal || !out_rgb24) return;
    
    for (int i = 0; i < 256; i++) {
        byte r = pal->colors[i * 3];
        byte g = pal->colors[i * 3 + 1];
        byte b = pal->colors[i * 3 + 2];
        
        out_rgb24[i * 3] = fdother_color_6bit_to_8bit(r);
        out_rgb24[i * 3 + 1] = fdother_color_6bit_to_8bit(g);
        out_rgb24[i * 3 + 2] = fdother_color_6bit_to_8bit(b);
    }
}

void fdother_palette_to_rgb32(const fdother_palette_t* pal, dword* out_rgb32) {
    if (!pal || !out_rgb32) return;
    
    for (int i = 0; i < 256; i++) {
        byte r = pal->colors[i * 3];
        byte g = pal->colors[i * 3 + 1];
        byte b = pal->colors[i * 3 + 2];
        
        out_rgb32[i] = (fdother_color_6bit_to_8bit(r) << 0) |
                       (fdother_color_6bit_to_8bit(g) << 8) |
                       (fdother_color_6bit_to_8bit(b) << 16) |
                       (0xFF << 24);
    }
}

/* ========================================================================
 * Tile图像解析
 * ======================================================================== */

int fdother_parse_tile(const byte* data, dword size, fdother_tile_t* out_tile) {
    if (!data || !out_tile || size < 5) {
        return -1;
    }
    
    word w = data[0] | (data[1] << 8);
    word h = data[2] | (data[3] << 8);
    
    if (w == 0 || w > 640 || h == 0 || h > 480) {
        return -1;
    }
    
    out_tile->width = w;
    out_tile->height = h;
    
    // 自动检测头格式：字节5=0使用5字节头，字节5!=0使用8字节头
    if (size >= 8 && data[5] != 0) {
        // 8字节头格式
        out_tile->header_size = 8;
        out_tile->palette_window = data[4] | (data[5] << 8);
        out_tile->rle_data = data + 8;
        out_tile->rle_size = size - 8;
    } else {
        // 5字节头格式
        out_tile->header_size = 5;
        out_tile->palette_window = data[4];
        out_tile->rle_data = data + 5;
        out_tile->rle_size = size - 5;
    }
    
    return 0;
}

int fdother_decode_tile(const fdother_tile_t* tile, byte* dst) {
    if (!tile || !dst || !tile->rle_data) {
        return -1;
    }
    
    int result = fd_decompress_rle(
        tile->rle_data,
        (int)tile->rle_size,
        dst,
        tile->width,
        tile->height,
        tile->palette_window
    );
    
    return result;
}

/* ========================================================================
 * LMI1 Tile集解析
 * ======================================================================== */

int fdother_parse_lmi1(const byte* data, dword size, fdother_lmi1_t* out_lmi1) {
    if (!data || !out_lmi1 || size < 6) {
        return -1;
    }
    
    if (memcmp(data, "LMI1", 4) != 0) {
        return -1;
    }
    
    out_lmi1->magic[0] = data[0];
    out_lmi1->magic[1] = data[1];
    out_lmi1->magic[2] = data[2];
    out_lmi1->magic[3] = data[3];
    out_lmi1->tile_count = data[4] | (data[5] << 8);
    out_lmi1->data = data;
    out_lmi1->size = size;
    
    return 0;
}

int fdother_lmi1_get_tile(const fdother_lmi1_t* lmi1, int tile_index,
                          word* out_width, word* out_height,
                          const byte** out_rle_data, dword* out_rle_size) {
    if (!lmi1 || tile_index < 0 || tile_index >= lmi1->tile_count) {
        return -1;
    }
    
    const byte* data = lmi1->data;
    dword data_size = lmi1->size;
    
    dword offset_addr = 6 + tile_index * 4;
    if (offset_addr + 4 > data_size) {
        return -1;
    }
    
    dword tile_offset = data[offset_addr] |
                      (data[offset_addr + 1] << 8) |
                      (data[offset_addr + 2] << 16) |
                      (data[offset_addr + 3] << 24);
    
    if (tile_offset + 4 > data_size) {
        return -1;
    }
    
    word w = data[tile_offset] | (data[tile_offset + 1] << 8);
    word h = data[tile_offset + 2] | (data[tile_offset + 3] << 8);
    
    if (out_width) *out_width = w;
    if (out_height) *out_height = h;
    if (out_rle_data) *out_rle_data = data + tile_offset + 4;
    
    if (out_rle_size) {
        dword next_offset_addr = 6 + (tile_index + 1) * 4;
        if (next_offset_addr + 4 <= data_size) {
            dword next_tile_offset = data[next_offset_addr] |
                                   (data[next_offset_addr + 1] << 8) |
                                   (data[next_offset_addr + 2] << 16) |
                                   (data[next_offset_addr + 3] << 24);
            *out_rle_size = next_tile_offset - tile_offset - 4;
        } else {
            *out_rle_size = data_size - tile_offset - 4;
        }
    }
    
    return 0;
}

/* ========================================================================
 * 嵌套DAT解析
 * ======================================================================== */

int fdother_parse_nested_dat(const byte* data, dword size, fdother_nested_dat_t* out_nested) {
    if (!data || !out_nested || size < 10) {
        return -1;
    }
    
    if (memcmp(data, "LLLLLL", 6) != 0) {
        return -1;
    }
    
    out_nested->magic[0] = data[0];
    out_nested->magic[1] = data[1];
    out_nested->magic[2] = data[2];
    out_nested->magic[3] = data[3];
    out_nested->magic[4] = data[4];
    out_nested->magic[5] = data[5];
    out_nested->resource_count = data[6] | (data[7] << 8) |
                                 (data[8] << 16) | (data[9] << 24);
    out_nested->data = data;
    out_nested->size = size;
    
    return 0;
}

const byte* fdother_nested_get_resource(const fdother_nested_dat_t* nested,
                                        int resource_index, dword* out_size) {
    if (!nested || resource_index < 0 || resource_index >= (int)nested->resource_count) {
        if (out_size) *out_size = 0;
        return NULL;
    }
    
    const byte* data = nested->data;
    dword data_size = nested->size;
    dword count = nested->resource_count;
    
    dword table_start = 10;
    
    dword offset_addr = table_start + resource_index * 4;
    if (offset_addr + 4 > data_size) {
        if (out_size) *out_size = 0;
        return NULL;
    }
    
    dword res_offset = data[offset_addr] |
                     (data[offset_addr + 1] << 8) |
                     (data[offset_addr + 2] << 16) |
                     (data[offset_addr + 3] << 24);
    
    dword next_offset;
    if (resource_index + 1 < (int)count) {
        dword next_addr = table_start + (resource_index + 1) * 4;
        if (next_addr + 4 <= data_size) {
            next_offset = data[next_addr] |
                         (data[next_addr + 1] << 8) |
                         (data[next_addr + 2] << 16) |
                         (data[next_addr + 3] << 24);
        } else {
            next_offset = data_size;
        }
    } else {
        next_offset = data_size;
    }
    
    dword res_size = next_offset - res_offset;
    
    if (out_size) *out_size = res_size;
    return data + res_offset;
}

/* ========================================================================
 * 便捷函数：直接通过索引获取资源
 * ======================================================================== */

int fdother_get_palette(int palette_index, fdother_palette_t* out_palette) {
    dword size;
    const byte* data = fdother_get_resource(palette_index, &size);
    if (!data) return -1;
    return fdother_parse_palette(data, size, out_palette);
}

int fdother_get_tile(int tile_index, fdother_tile_t* out_tile) {
    dword size;
    const byte* data = fdother_get_resource(tile_index, &size);
    if (!data) return -1;
    return fdother_parse_tile(data, size, out_tile);
}

int fdother_get_lmi1(int lmi1_index, fdother_lmi1_t* out_lmi1) {
    dword size;
    const byte* data = fdother_get_resource(lmi1_index, &size);
    if (!data) return -1;
    return fdother_parse_lmi1(data, size, out_lmi1);
}

int fdother_get_nested_dat(int nested_index, fdother_nested_dat_t* out_nested) {
    dword size;
    const byte* data = fdother_get_resource(nested_index, &size);
    if (!data) return -1;
    return fdother_parse_nested_dat(data, size, out_nested);
}

/* ========================================================================
 * 索引2偏移表解析
 * ======================================================================== */

int fdother_parse_offset_table(int index, fdother_offset_table_t* out_table) {
    if (!out_table || index != 2) {
        return -1;
    }
    
    dword size;
    const byte* data = fdother_get_resource(index, &size);
    if (!data || size < 8) {
        return -1;
    }
    
    // 解析偏移表
    dword offset_count = size / 4;
    
    // 验证是否为有效的偏移表
    // 第一个偏移应该指向偏移表之后
    dword first_offset = data[0] | (data[1] << 8) | (data[2] << 16) | (data[3] << 24);
    if (first_offset < offset_count * 4) {
        return -1;
    }
    
    out_table->offset_count = offset_count;
    out_table->data = data;
    out_table->size = size;
    
    // 分配并复制偏移表
    out_table->offsets = (dword*)malloc(offset_count * sizeof(dword));
    if (!out_table->offsets) {
        return -1;
    }
    
    for (dword i = 0; i < offset_count; i++) {
        dword addr = i * 4;
        if (addr + 4 > size) break;
        out_table->offsets[i] = data[addr] | (data[addr + 1] << 8) | 
                               (data[addr + 2] << 16) | (data[addr + 3] << 24);
    }
    
    return 0;
}

const byte* fdother_offset_table_get_resource(const fdother_offset_table_t* table,
                                               int resource_index, dword* out_size) {
    if (!table || resource_index < 0 || resource_index >= (int)table->offset_count - 1) {
        if (out_size) *out_size = 0;
        return NULL;
    }
    
    dword start = table->offsets[resource_index];
    dword end = table->offsets[resource_index + 1];
    dword size = end - start;
    
    if (start >= table->size || end > table->size) {
        if (out_size) *out_size = 0;
        return NULL;
    }
    
    if (out_size) *out_size = size;
    return table->data + start;
}

void fdother_offset_table_free(fdother_offset_table_t* table) {
    if (table && table->offsets) {
        free(table->offsets);
        table->offsets = NULL;
        table->offset_count = 0;
        table->data = NULL;
        table->size = 0;
    }
}
