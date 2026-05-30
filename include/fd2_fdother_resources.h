/**
 * FDOTHER.DAT 资源完整定义
 * 基于MCP汇编代码分析，从索引0开始逐一解析
 * 
 * 文件格式：
 * - 魔数 "LLLLLL" (6字节)
 * - 索引表 (从偏移6开始，每项4字节，存储资源起始偏移)
 * - 资源大小 = offsets[index+1] - offsets[index]
 */

#ifndef FD2_FDOTHER_RESOURCES_H
#define FD2_FDOTHER_RESOURCES_H

#include "fd2_types.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================
 * 资源类型枚举
 * ======================================================================== */
typedef enum {
    FDOTHER_RES_TYPE_PALETTE = 0,    // 调色板 (768字节)
    FDOTHER_RES_TYPE_TILE,           // Tile图像 [w:2][h:2][palette_window:1][rle_data]
    FDOTHER_RES_TYPE_LMI1,           // LMI1 Tile集 "LMI1"[4] + tile_count[2] + offsets[]
    FDOTHER_RES_TYPE_NESTED_DAT,     // 嵌套DAT "LLLLLL"[6] + count[4] + offsets[]
    FDOTHER_RES_TYPE_RAW,            // 原始数据
} fdother_res_type_t;

/* ========================================================================
 * 调色板资源 (768字节 = 256色 × 3字节RGB)
 * ======================================================================== */
typedef struct {
    byte colors[768];  // 256色，每色3字节(R,G,B)，6位颜色值(0-63)
} fdother_palette_t;

/* 调色板资源索引 */
#define FDOTHER_PALETTE_0    0   // 主调色板
#define FDOTHER_PALETTE_8    8   // 调色板副本
#define FDOTHER_PALETTE_57   57  // 调色板副本
#define FDOTHER_PALETTE_76   76  // 标题画面调色板
#define FDOTHER_PALETTE_99   99  // 调色板副本
#define FDOTHER_PALETTE_101  101 // 调色板副本
#define FDOTHER_PALETTE_102  102 // 调色板副本

/* ========================================================================
 * Tile图像资源
 * 格式: [width:2][height:2][palette_window:1/2][rle_data]
 * 注意：存在两种头格式：
 *   - 5字节头：width(2) + height(2) + palette_window(1)，RLE从偏移5开始
 *   - 8字节头：width(2) + height(2) + palette_window(2) + extra(2)，RLE从偏移8开始
 * 区分方法：字节5=0使用5字节头，字节5!=0使用8字节头
 * ======================================================================== */
typedef struct {
    word width;              // 宽度 (2字节，小端序)
    word height;             // 高度 (2字节，小端序)
    word palette_window;    // 调色板窗口偏移 (1或2字节)
    byte header_size;       // 头大小 (5或8字节)
    const byte* rle_data;   // RLE压缩数据指针
    dword rle_size;         // RLE数据大小
} fdother_tile_t;

/* Tile资源 - 小图标和UI元素 */
#define FDOTHER_TILE_ICON_24X24    1   // 24x24 图标
#define FDOTHER_TILE_ICON_62X26    10  // 62x26 图标
#define FDOTHER_TILE_CHAR_16X16_A  18  // 16x16 字符A
#define FDOTHER_TILE_CHAR_30X30_A  19  // 30x30 字符A
#define FDOTHER_TILE_CHAR_16X16_B  20  // 16x16 字符B
#define FDOTHER_TILE_CHAR_30X30_B  21  // 30x30 字符B
#define FDOTHER_TILE_ICON_14X14_A  22  // 14x14 图标A
#define FDOTHER_TILE_ICON_14X14_B  23  // 14x14 图标B
#define FDOTHER_TILE_ICON_12X12_A  24  // 12x12 图标A
#define FDOTHER_TILE_ICON_12X12_B  25  // 12x12 图标B
#define FDOTHER_TILE_ICON_18X18_A  26  // 18x18 图标A (大量数据)
#define FDOTHER_TILE_ICON_18X18_B  27  // 18x18 图标B (大量数据)
#define FDOTHER_TILE_ICON_32X32_A  28  // 32x32 图标A
#define FDOTHER_TILE_ICON_32X32_B  30  // 32x32 图标B
#define FDOTHER_TILE_ICON_10X10_A  32  // 10x10 图标A
#define FDOTHER_TILE_ICON_10X10_B  33  // 10x10 图标B
#define FDOTHER_TILE_ICON_101X101  34  // 101x101 大图标
#define FDOTHER_TILE_ICON_5X5_A    37  // 5x5 图标A
#define FDOTHER_TILE_ICON_5X5_B    38  // 5x5 图标B
#define FDOTHER_TILE_ICON_33X33_A  39  // 33x33 图标A
#define FDOTHER_TILE_ICON_33X33_B  43  // 33x33 图标B
#define FDOTHER_TILE_312X192       42  // 312x192 大图像
#define FDOTHER_TILE_31X31         44  // 31x31 图像
#define FDOTHER_TILE_59X59         45  // 59x59 图像
#define FDOTHER_TILE_111X111       54  // 111x111 图像
#define FDOTHER_TILE_ICON_20X20    58  // 20x20 图标
#define FDOTHER_TILE_ICON_5X5_C    65  // 5x5 图标C (大量数据)
#define FDOTHER_TILE_ICON_14X14_C  66  // 14x14 图标C
#define FDOTHER_TILE_ICON_9X9_A    67  // 9x9 图标A
#define FDOTHER_TILE_ICON_9X9_B    68  // 9x9 图标B
#define FDOTHER_TILE_ICON_24X24_B  96  // 24x24 图标B
#define FDOTHER_TILE_155X30        98  // 155x30 长条图像

/* Tile资源 - 全屏图像 (320x200) */
#define FDOTHER_TILE_SCREEN_11    11  // 320x200 全屏图像A
#define FDOTHER_TILE_SCREEN_15    15  // 320x200 全屏图像B
#define FDOTHER_TILE_SCREEN_55    55  // 320x200 全屏图像C
#define FDOTHER_TILE_SCREEN_56    56  // 320x200 全屏图像D
#define FDOTHER_TILE_SCREEN_59    59  // 320x200 全屏图像E
#define FDOTHER_TILE_SCREEN_60    60  // 320x200 全屏图像F
#define FDOTHER_TILE_SCREEN_61    61  // 320x200 全屏图像G
#define FDOTHER_TILE_SCREEN_62    62  // 320x200 全屏图像H
#define FDOTHER_TILE_SCREEN_74    74  // 320x200 标题文字
#define FDOTHER_TILE_SCREEN_75    75  // 320x200 全屏图像I
#define FDOTHER_TILE_SCREEN_97    97  // 320x200 全屏图像J
#define FDOTHER_TILE_SCREEN_100   100 // 320x200 全屏图像K

/* Tile资源 - 菜单项图像 (320x147) */
#define FDOTHER_TILE_MENU_69      69  // 320x147 菜单项A
#define FDOTHER_TILE_MENU_70      70  // 320x147 菜单项B
#define FDOTHER_TILE_MENU_71      71  // 320x147 菜单项C
#define FDOTHER_TILE_MENU_72      72  // 320x147 菜单项D
#define FDOTHER_TILE_MENU_73      73  // 320x147 菜单项E

/* ========================================================================
 * LMI1 Tile集资源
 * 格式: "LMI1"[4] + tile_count[2] + tile_offsets[tile_count][4] + tile_data
 * ======================================================================== */
typedef struct {
    char magic[4];           // "LMI1"
    word tile_count;         // tile数量
    const byte* data;        // 原始数据指针
    dword size;              // 数据总大小
} fdother_lmi1_t;

/* LMI1 Tile集资源索引 */
#define FDOTHER_LMI1_3      3   // LMI1 (23个tile)
#define FDOTHER_LMI1_5      5   // LMI1 (138个tile)
#define FDOTHER_LMI1_6      6   // LMI1 (230个tile)
#define FDOTHER_LMI1_9      9   // LMI1 (12个tile)
#define FDOTHER_LMI1_13     13  // LMI1 (28个tile)
#define FDOTHER_LMI1_14     14  // LMI1 (32个tile)
#define FDOTHER_LMI1_29     29  // LMI1 (24个tile)

/* ========================================================================
 * 嵌套DAT资源
 * 格式: "LLLLLL"[6] + count[4] + offsets[count][4] + resource_data
 * ======================================================================== */
typedef struct {
    char magic[6];           // "LLLLLL"
    dword resource_count;    // 子资源数量
    const byte* data;        // 原始数据指针
    dword size;              // 数据总大小
} fdother_nested_dat_t;

/* 嵌套DAT资源索引 */
#define FDOTHER_NESTED_7    7   // 嵌套DAT (38个子资源)
#define FDOTHER_NESTED_12   12  // 嵌套DAT (122个子资源) - 重要
#define FDOTHER_NESTED_31   31  // 嵌套DAT (62个子资源)
#define FDOTHER_NESTED_63   63  // 嵌套DAT (130个子资源) - 重要
#define FDOTHER_NESTED_64   64  // 嵌套DAT (34个子资源)
#define FDOTHER_NESTED_77   77  // 嵌套DAT (26个子资源)
#define FDOTHER_NESTED_78   78  // 嵌套DAT (14个子资源)
#define FDOTHER_NESTED_80   80  // 嵌套DAT (74个子资源)
// 更多嵌套DAT: 48-53, 81-95

/* ========================================================================
 * RAW数据资源
 * ======================================================================== */
#define FDOTHER_RAW_2       2   // RAW数据 (37680字节) - 可能是字体数据
#define FDOTHER_RAW_4       4   // RAW数据 (58368字节) - 可能是字符位图

/* ========================================================================
 * 索引2偏移表结构
 * 格式: offsets[9420][4] + 9419个子资源
 * 每个子资源约480-484字节，第一个子资源是24x20 TILE图像
 * ======================================================================== */
typedef struct {
    dword offset_count;     // 偏移表数量 (9420)
    dword* offsets;         // 偏移表
    const byte* data;       // 原始数据指针
    dword size;             // 数据总大小
} fdother_offset_table_t;

/* ========================================================================
 * 资源加载和解析函数
 * ======================================================================== */

/* 加载和卸载FDOTHER.DAT文件 */
int fdother_load(const char* filepath);
void fdother_unload(void);

/* 获取原始资源数据 */
const byte* fdother_get_resource(int index, dword* out_size);

/* 获取资源类型 */
fdother_res_type_t fdother_get_resource_type(const byte* data, dword size);

/* 解析调色板 */
int fdother_parse_palette(const byte* data, dword size, fdother_palette_t* out_palette);

/* 解析Tile图像 */
int fdother_parse_tile(const byte* data, dword size, fdother_tile_t* out_tile);

/* 解析LMI1 Tile集 */
int fdother_parse_lmi1(const byte* data, dword size, fdother_lmi1_t* out_lmi1);

/* 获取LMI1中的特定tile */
int fdother_lmi1_get_tile(const fdother_lmi1_t* lmi1, int tile_index, 
                          word* out_width, word* out_height, 
                          const byte** out_rle_data, dword* out_rle_size);

/* 解析嵌套DAT */
int fdother_parse_nested_dat(const byte* data, dword size, fdother_nested_dat_t* out_nested);

/* 获取嵌套DAT中的特定子资源 */
const byte* fdother_nested_get_resource(const fdother_nested_dat_t* nested, 
                                        int resource_index, dword* out_size);

/* 将6位颜色值转换为8位 */
static inline byte fdother_color_6bit_to_8bit(byte c6) {
    return (c6 << 2) | (c6 >> 4);
}

/* 转换调色板为RGB24格式 */
void fdother_palette_to_rgb24(const fdother_palette_t* pal, byte* out_rgb24);

/* 转换调色板为RGB32格式 */
void fdother_palette_to_rgb32(const fdother_palette_t* pal, dword* out_rgb32);

/* 便捷函数：直接通过索引获取资源 */
int fdother_get_palette(int palette_index, fdother_palette_t* out_palette);
int fdother_get_tile(int tile_index, fdother_tile_t* out_tile);
int fdother_get_lmi1(int lmi1_index, fdother_lmi1_t* out_lmi1);
int fdother_get_nested_dat(int nested_index, fdother_nested_dat_t* out_nested);
int fdother_decode_tile(const fdother_tile_t* tile, byte* dst);

/* 解析索引2偏移表 */
int fdother_parse_offset_table(int index, fdother_offset_table_t* out_table);

/* 获取偏移表中的子资源 */
const byte* fdother_offset_table_get_resource(const fdother_offset_table_t* table,
                                               int resource_index, dword* out_size);

/* 释放偏移表 */
void fdother_offset_table_free(fdother_offset_table_t* table);

#ifdef __cplusplus
}
#endif

#endif /* FD2_FDOTHER_RESOURCES_H */
