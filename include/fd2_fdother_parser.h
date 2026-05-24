/* 
 * 通用FDOTHER.DAT资源解析器 - 基于MCP汇编分析
 * 严格按照原游戏逻辑实现，不进行任何猜测
 */

#ifndef FD2_FDOTHER_PARSER_H
#define FD2_FDOTHER_PARSER_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// FDOTHER.DAT结构定义
typedef struct {
    unsigned char* data;      // 资源数据
    unsigned int size;        // 数据大小
    unsigned short width;     // 宽度（仅对tile数据有效）
    unsigned short height;    // 高度（仅对tile数据有效）
    unsigned char type;       // 资源类型
} fd2_resource_t;

typedef struct {
    char magic[6];           // 文件魔数 "LLLLLL"
    unsigned int count;      // 资源总数
    unsigned int* offsets;   // 偏移表
    FILE* file;              // 文件句柄
} fd2_fdother_t;

// 资源类型定义
#define FD2_RES_TYPE_RAW      0  // 原始数据
#define FD2_RES_TYPE_LMI1     1  // LMI1 tile集
#define FD2_RES_TYPE_LLLL     2  // LLLL 嵌套资源
#define FD2_RES_TYPE_PALETTE  3  // 调色板

// 初始化FDOTHER解析器
static fd2_fdother_t* fd2_fdother_init(const char* filepath) {
    fd2_fdother_t* fdother = (fd2_fdother_t*)calloc(1, sizeof(fd2_fdother_t));
    if (!fdother) return NULL;
    
    fdother->file = fopen(filepath, "rb");
    if (!fdother->file) {
        free(fdother);
        return NULL;
    }
    
    // 读取头部
    if (fread(fdother->magic, 1, 6, fdother->file) != 6 ||
        memcmp(fdother->magic, "LLLLLL", 6) != 0) {
        fclose(fdother->file);
        free(fdother);
        return NULL;
    }
    
    if (fread(&fdother->count, 4, 1, fdother->file) != 1) {
        fclose(fdother->file);
        free(fdother);
        return NULL;
    }
    
    fdother->offsets = (unsigned int*)malloc(fdother->count * sizeof(unsigned int));
    if (!fdother->offsets) {
        fclose(fdother->file);
        free(fdother);
        return NULL;
    }
    
    if (fread(fdother->offsets, 4, fdother->count, fdother->file) != fdother->count) {
        free(fdother->offsets);
        fclose(fdother->file);
        free(fdother);
        return NULL;
    }
    
    return fdother;
}

// 释放FDOTHER解析器
static void fd2_fdother_free(fd2_fdother_t* fdother) {
    if (fdother) {
        if (fdother->offsets) free(fdother->offsets);
        if (fdother->file) fclose(fdother->file);
        free(fdother);
    }
}

// 获取指定索引的资源数据
static fd2_resource_t* fd2_fdother_get_resource(fd2_fdother_t* fdother, int index) {
    if (!fdother || index < 0 || index >= fdother->count) {
        return NULL;
    }
    
    unsigned int start = fdother->offsets[index];
    unsigned int end = (index + 1 < fdother->count) ? fdother->offsets[index + 1] : 0;
    
    // 获取文件大小以确定最后一个资源的结束位置
    if (end == 0) {
        fseek(fdother->file, 0, SEEK_END);
        end = ftell(fdother->file);
    }
    
    unsigned int size = end - start;
    
    fd2_resource_t* res = (fd2_resource_t*)calloc(1, sizeof(fd2_resource_t));
    if (!res) return NULL;
    
    res->data = (unsigned char*)malloc(size);
    if (!res->data) {
        free(res);
        return NULL;
    }
    
    fseek(fdother->file, start, SEEK_SET);
    if (fread(res->data, 1, size, fdother->file) != size) {
        free(res->data);
        free(res);
        return NULL;
    }
    
    res->size = size;
    res->type = FD2_RES_TYPE_RAW;
    
    return res;
}

// 识别资源类型
static unsigned char fd2_fdother_identify_type(fd2_resource_t* res) {
    if (!res || res->size < 4) return FD2_RES_TYPE_RAW;
    
    if (memcmp(res->data, "LMI1", 4) == 0) {
        return FD2_RES_TYPE_LMI1;
    } else if (memcmp(res->data, "LLLL", 4) == 0) {
        return FD2_RES_TYPE_LLLL;
    }
    
    // 检查是否可能是调色板（768字节，每3字节为一个RGB值）
    if (res->size == 768) {
        return FD2_RES_TYPE_PALETTE;
    }
    
    return FD2_RES_TYPE_RAW;
}

// 解析LMI1格式的tile集
typedef struct {
    unsigned short tile_count;
    unsigned int* tile_offsets;  // 相对于tileset_data的偏移
    fd2_resource_t** tiles;      // 解析后的tile数组
    const unsigned char* tileset_data;  // tileset的原始数据
} fd2_lmi1_tileset_t;

static fd2_lmi1_tileset_t* fd2_lmi1_parse_tileset(const fd2_resource_t* res) {
    if (!res || res->type != FD2_RES_TYPE_LMI1 || res->size < 6) {
        return NULL;
    }
    
    const unsigned char* data = res->data;
    
    // 读取tile数量 (字节4-5)
    unsigned short tile_count = data[4] | (data[5] << 8);
    if (tile_count == 0 || tile_count > 1000) {  // 防止错误解析
        return NULL;
    }
    
    fd2_lmi1_tileset_t* tileset = (fd2_lmi1_tileset_t*)calloc(1, sizeof(fd2_lmi1_tileset_t));
    if (!tileset) return NULL;
    
    tileset->tile_count = tile_count;
    tileset->tile_offsets = (unsigned int*)malloc(tile_count * sizeof(unsigned int));
    tileset->tiles = (fd2_resource_t**)malloc(tile_count * sizeof(fd2_resource_t*));
    tileset->tileset_data = data;
    
    if (!tileset->tile_offsets || !tileset->tiles) {
        free(tileset->tile_offsets);
        free(tileset->tiles);
        free(tileset);
        return NULL;
    }
    
    // 初始化
    memset(tileset->tiles, 0, tile_count * sizeof(fd2_resource_t*));
    
    // 解析每个tile的偏移
    for (int i = 0; i < tile_count; i++) {
        unsigned int offset_addr = 6 + i * 4;
        if (offset_addr + 4 > res->size) break;
        
        unsigned int tile_offset = data[offset_addr] | 
                                  (data[offset_addr + 1] << 8) |
                                  (data[offset_addr + 2] << 16) |
                                  (data[offset_addr + 3] << 24);
        
        tileset->tile_offsets[i] = tile_offset;
        
        // 创建tile资源对象（指向原始数据中的特定位置）
        if (tile_offset + 4 <= res->size) {
            unsigned short width = data[tile_offset] | (data[tile_offset + 1] << 8);
            unsigned short height = data[tile_offset + 2] | (data[tile_offset + 3] << 8);
            
            if (width > 0 && height > 0 && width <= 320 && height <= 200) {
                fd2_resource_t* tile = (fd2_resource_t*)calloc(1, sizeof(fd2_resource_t));
                if (tile) {
                    tile->width = width;
                    tile->height = height;
                    tile->size = width * height;
                    tile->type = FD2_RES_TYPE_LMI1;
                    // 注意：对于tile，我们存储指向像素数据的指针（跳过宽高信息）
                    tile->data = (unsigned char*)&data[tile_offset + 4];
                    tileset->tiles[i] = tile;
                }
            }
        }
    }
    
    return tileset;
}

// 释放LMI1 tileset
static void fd2_lmi1_free_tileset(fd2_lmi1_tileset_t* tileset) {
    if (tileset) {
        // 注意：不释放tile->data，因为它指向原始tileset_data
        if (tileset->tiles) {
            for (int i = 0; i < tileset->tile_count; i++) {
                if (tileset->tiles[i]) {
                    // 不free tile->data，因为它指向原始数据
                    tileset->tiles[i]->data = NULL;
                    free(tileset->tiles[i]);
                }
            }
            free(tileset->tiles);
        }
        free(tileset->tile_offsets);
        free(tileset);
    }
}

// 获取LMI1 tileset中的特定tile
static fd2_resource_t* fd2_lmi1_get_tile(fd2_lmi1_tileset_t* tileset, int tile_index) {
    if (!tileset || tile_index < 0 || tile_index >= tileset->tile_count) {
        return NULL;
    }
    
    return tileset->tiles[tile_index];
}

#endif // FD2_FDOTHER_PARSER_H