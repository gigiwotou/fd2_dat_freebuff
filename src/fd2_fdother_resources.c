/**
 * FDOTHER.DAT 资源加载和解析实现
 * 严格按照MCP汇编代码实现
 * 
 * 根据sub_111BA函数逻辑：
 * - 索引表从偏移6开始，每项4字节（1个dword = 资源起始偏移）
 * - 资源大小 = offsets[index+1] - offsets[index]
 * - fseek: 4 * index + 6, 然后读取8字节（当前索引偏移 + 下一个索引偏移）
 */

#include "fd2_fdother_resources.h"
#include "fd2_dat.h"
#include "fd2_rle.h"
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
    dword* offsets;      /* 每个索引4字节，存储资源起始偏移 */
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
    
    // 根据sub_111BA: 索引表从偏移6开始，每项4字节
    dword max_resources = 0;
    dword table_offset = 6;
    
    while (table_offset + 4 <= (dword)file_size) {
        dword res_offset = *(dword*)(data + table_offset);
        // 检查偏移是否有效
        if (res_offset == 0 || res_offset > (dword)file_size) {
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
    
    // 存储每个资源的起始偏移
    dword* offsets = (dword*)malloc((max_resources + 1) * sizeof(dword));
    if (!offsets) {
        free(data);
        printf("Error: Out of memory for offset table\n");
        return -1;
    }
    
    for (dword i = 0; i < max_resources; i++) {
        // 读取起始偏移（每个索引4字节）
        offsets[i] = *(dword*)(data + 6 + i * 4);
    }
    // 最后一个资源的结束偏移（文件末尾）
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

int fdother_get_resource_count(void) {
    if (!g_fdother.loaded) {
        return 0;
    }
    return (int)g_fdother.resource_count;
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
    
    /* 根据Python测试验证，tile格式固定为：
     * [width:2][height:2][window_offset:1][rle_data...]
     * RLE数据总是从offset 5开始
     */
    out_tile->header_size = 5;
    out_tile->palette_window = data[4];  // 单字节调色板窗口偏移
    out_tile->rle_data = data + 5;
    out_tile->rle_size = size - 5;
    
    return 0;
}

/* ========================================================================
 * 多图标TILE解析 (索引1)
 * ======================================================================== */

int fdother_parse_multi_tile(const byte* data, dword size, fdother_multi_tile_t* out_multi) {
    if (!data || !out_multi || size < 10) {
        return -1;
    }
    
    /* 索引1格式分析（根据实际数据）：
     * [0-1]: width=312 (总宽度，所有图标排成一行)
     * [2-3]: height=0 (未使用)
     * [4]: palette_window=28
     * [5]: padding=3
     * [6+]: 4字节相对偏移表
     * 
     * 每个图标是24x24，使用sub_4E22A编码
     */
    
    out_multi->width = 24;   // 固定24x24图标
    out_multi->height = 24;
    out_multi->palette_window = data[4];
    out_multi->data = data;
    out_multi->size = size;
    
    // 从偏移6开始解析4字节偏移表
    dword offset_table_start = 6;
    dword* offsets = NULL;
    dword count = 0;
    dword pos = offset_table_start;
    
    // 第一次遍历：计算偏移数量
    while (pos + 4 <= size) {
        dword off = data[pos] | (data[pos + 1] << 8) | 
                   (data[pos + 2] << 16) | (data[pos + 3] << 24);
        
        if (off == 0 || off > size) {
            break;
        }
        
        count++;
        pos += 4;
        
        if (count > 200) {
            break;
        }
    }
    
    if (count == 0) {
        return -1;
    }
    
    // 分配并复制偏移表
    offsets = (dword*)malloc(count * sizeof(dword));
    if (!offsets) {
        return -1;
    }
    
    pos = offset_table_start;
    for (dword i = 0; i < count; i++) {
        offsets[i] = data[pos] | (data[pos + 1] << 8) | 
                    (data[pos + 2] << 16) | (data[pos + 3] << 24);
        pos += 4;
    }
    
    out_multi->icon_count = (word)count;
    out_multi->icon_offsets = offsets;
    
    return 0;
}

int fdother_multi_tile_get_icon(const fdother_multi_tile_t* multi, int icon_index,
                                 const byte** out_rle_data, dword* out_rle_size) {
    if (!multi || icon_index < 0 || icon_index >= multi->icon_count) {
        return -1;
    }
    
    dword start = multi->icon_offsets[icon_index];
    dword end = (icon_index + 1 < multi->icon_count) ? 
                multi->icon_offsets[icon_index + 1] : multi->size;
    
    if (start >= multi->size || end > multi->size) {
        return -1;
    }
    
    if (out_rle_data) *out_rle_data = multi->data + start;
    if (out_rle_size) *out_rle_size = end - start;
    
    return 0;
}

void fdother_multi_tile_free(fdother_multi_tile_t* multi) {
    if (multi && multi->icon_offsets) {
        free(multi->icon_offsets);
        multi->icon_offsets = NULL;
        multi->icon_count = 0;
    }
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
    
    /* 计算tile尺寸：通过前两个tile的偏移差 */
    if (out_lmi1->tile_count >= 2) {
        dword first_offset = data[6] | (data[7] << 8) | (data[8] << 16) | (data[9] << 24);
        dword second_offset = data[10] | (data[11] << 8) | (data[12] << 16) | (data[13] << 24);
        dword tile_size = second_offset - first_offset;
        
        /* 寻找最接近正方形的宽高组合 (优先16的倍数) */
        int best_w = 16;
        int best_h = tile_size / 16;
        int best_diff = abs(16 - tile_size / 16);
        
        for (int w = 1; w <= 64; w++) {
            if (tile_size % w == 0) {
                int h = tile_size / w;
                if (w <= 64 && h <= 64) {
                    int diff = abs(w - h);
                    /* 优先选择接近正方形且宽高比例合理的 */
                    if (diff < best_diff || (diff == best_diff && w % 16 == 0)) {
                        best_w = w;
                        best_h = h;
                        best_diff = diff;
                    }
                }
            }
        }
        
        out_lmi1->tile_width = best_w;
        out_lmi1->tile_height = best_h;
    } else {
        /* 默认16x16 */
        out_lmi1->tile_width = 16;
        out_lmi1->tile_height = 16;
    }
    
    return 0;
}

int fdother_lmi1_get_tile(const fdother_lmi1_t* lmi1, int tile_index,
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
    
    /* LMI1 tile没有宽高头，直接是RLE数据 */
    if (out_rle_data) *out_rle_data = data + tile_offset;
    
    if (out_rle_size) {
        dword next_offset_addr = 6 + (tile_index + 1) * 4;
        if (next_offset_addr + 4 <= data_size) {
            dword next_tile_offset = data[next_offset_addr] |
                                   (data[next_offset_addr + 1] << 8) |
                                   (data[next_offset_addr + 2] << 16) |
                                   (data[next_offset_addr + 3] << 24);
            *out_rle_size = next_tile_offset - tile_offset;
        } else {
            *out_rle_size = data_size - tile_offset;
        }
    }
    
    return 0;
}

/* ------------------------------------------------------------------
 * 基于sub_4ED0B (0x4ED0B) 反汇编代码的正确LMI1 tile解码
 * 
 * 汇编逻辑:
 *   void sub_4ED0B(char *dst, unsigned __int16 *arg4, int arg8):
 *     count = *arg4           // 2字节width(每行字节数)
 *     src = arg4 + 2          // src指向height之后
 *     v6 = arg4[1]            // 2字节height(行数)
 *     do {
 *       rep movsb             // 逐字节memcpy一行count字节
 *       src += count
 *       dst += arg8           // 跳到下一行(pitch)
 *       v6--
 *     } while (v6)
 * 
 * LMI1 tile结构 (汇编实测):
 *   [0:2] = width (每行字节数)
 *   [2:2] = height (行数)
 *   [4:width*height] = 原始像素数据 (无RLE压缩)
 * ------------------------------------------------------------------ */

int fdother_lmi1_decode_tile(const fdother_lmi1_t* lmi1, int tile_index,
                             byte* out_pixels, int out_pitch) {
    if (!lmi1 || !out_pixels || tile_index < 0 || tile_index >= lmi1->tile_count) {
        return -1;
    }
    
    const byte* data = lmi1->data;
    dword data_size = lmi1->size;
    
    /* 读取tile偏移 */
    dword offset_addr = 6 + tile_index * 4;
    if (offset_addr + 4 > data_size) {
        return -1;
    }
    
    dword tile_offset = data[offset_addr] |
                       (data[offset_addr + 1] << 8) |
                       (data[offset_addr + 2] << 16) |
                       (data[offset_addr + 3] << 24);
    
    if (tile_offset >= data_size) {
        return -1;
    }
    
    /* 获取tile大小 */
    dword tile_size;
    dword next_offset_addr = 6 + (tile_index + 1) * 4;
    if (next_offset_addr + 4 <= data_size) {
        dword next_tile_offset = data[next_offset_addr] |
                                (data[next_offset_addr + 1] << 8) |
                                (data[next_offset_addr + 2] << 16) |
                                (data[next_offset_addr + 3] << 24);
        tile_size = next_tile_offset - tile_offset;
    } else {
        tile_size = data_size - tile_offset;
    }
    
    /* 自动检测格式: 类型A(4字节头)或类型B(无头, 16x16)
     *
     * 索引5的138个tile分析:
     *   - 所有tile都有4字节头[w:2][h:2]
     *   - size == 4+w*h: 未压缩, 用 sub_4ED4F (透明色过滤)
     *   - size < 4+w*h:  RLE压缩, 用 sub_4EBFF+sub_4EC66 (RLE+透明色过滤)
     *   - size > 4+w*h:  填充, 用 sub_4ED4F
     *   - tile_size == 256:  特殊固定16x16 (无头)
     */
    word width, height;
    const byte* src;

    if (tile_offset + 4 <= data_size) {
        word w = data[tile_offset]     | (data[tile_offset + 1] << 8);
        word h = data[tile_offset + 2] | (data[tile_offset + 3] << 8);
        if (w > 0 && w <= 1024 && h > 0 && h <= 1024) {
            /* 有4字节头 - 使用LMI1 tile解码(自动检测RLE/未压缩) */
            int out_w = 0, out_h = 0;
            int ret = fd2_rle_lmi1_decode_tile_auto(
                data + tile_offset, (int)tile_size,
                out_pixels, &out_w, &out_h, out_pitch);
            if (ret == 0) {
                width = (word)out_w;
                height = (word)out_h;
                return (int)width | ((int)height << 16);
            }
            /* 失败, 尝试回退到 sub_4ED0B memcpy */
            width = w;
            height = h;
            src = data + tile_offset + 4;
        } else if (tile_size == 256) {
            /* 类型B: 无头, 固定16x16 */
            width = 16;
            height = 16;
            src = data + tile_offset;
        } else {
            return -1;
        }
    } else if (tile_size == 256) {
        /* 类型B: 无头, 16x16 */
        width = 16;
        height = 16;
        src = data + tile_offset;
    } else {
        return -1;
    }

    /* 1:1 复现 sub_4ED0B 的逐行memcpy (回退方案) */
    byte* dst = out_pixels;
    for (int row = 0; row < height; row++) {
        /* 边界检查: 防止读取越界 */
        if ((dword)(src - data) + width > data_size) {
            return -1;
        }
        memcpy(dst, src, width);
        src += width;
        dst += out_pitch;
    }

    return (int)width | ((int)height << 16);  /* 高16位=h, 低16位=w */
}

/* 便捷函数: 获取tile的width和height */
int fdother_lmi1_get_tile_size(const fdother_lmi1_t* lmi1, int tile_index,
                               word* out_width, word* out_height) {
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
    
    /* 获取tile大小: 相邻偏移差 */
    dword tile_size;
    dword next_offset_addr = 6 + (tile_index + 1) * 4;
    if (next_offset_addr + 4 <= data_size) {
        dword next_tile_offset = data[next_offset_addr] |
                                (data[next_offset_addr + 1] << 8) |
                                (data[next_offset_addr + 2] << 16) |
                                (data[next_offset_addr + 3] << 24);
        tile_size = next_tile_offset - tile_offset;
    } else {
        tile_size = data_size - tile_offset;
    }
    
    /* 自动检测tile格式 (基于sub_4ED0B反汇编):
     *   类型A: 4字节头[w:2][h:2] + 原始数据, 总大小 = 4 + w*h
     *   类型B: 无头, 固定大小(如256字节对应16x16), 默认16x16
     */
    word w = data[tile_offset]     | (data[tile_offset + 1] << 8);
    word h = data[tile_offset + 2] | (data[tile_offset + 3] << 8);
    
    if (w > 0 && w <= 1024 && h > 0 && h <= 1024
        && (dword)(4 + (dword)w * (dword)h) == tile_size) {
        /* 类型A: 有4字节头 */
        if (out_width)  *out_width  = w;
        if (out_height) *out_height = h;
    } else if (tile_size == 256) {
        /* 类型B: 无头, 固定16x16 */
        if (out_width)  *out_width  = 16;
        if (out_height) *out_height = 16;
    } else if (out_width && out_height) {
        /* 未知格式, 用lmi1结构体的tile_width/height */
        *out_width  = lmi1->tile_width;
        *out_height = lmi1->tile_height;
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
    
    // 索引2的结构：前312字节是偏移表（78个dword偏移值）
    // 数据区从偏移312开始
    const dword offset_table_size = 312;  // 偏移表固定大小
    const dword offset_count = 78;        // 78个偏移值
    
    if (size < offset_table_size) {
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
