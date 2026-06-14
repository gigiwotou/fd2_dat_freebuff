#ifndef FD2_RLE_H
#define FD2_RLE_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

typedef uint8_t byte;
typedef uint16_t word;

/* ========================================================================
 *  统一管理所有RLE解码函数
 *  基于 IDA Pro MCP 反汇编游戏二进制分析得出:
 *
 *  ===== 4E000-4EFFF 范围 (8个RLE解码器, 4种模式) =====
 *
 *    sub_4E016 (0x4E016, 0x8C) - 24x24 RLE + 调色板查找(argC)
 *    sub_4E0A2 (0x4E0A2, 0x85) - 24x24 RLE + 调色板查找(argC, 不同变量名)
 *    sub_4E127 (0x4E127, 0x7F) - 24x24 RLE + 单色填充(n456=颜色)
 *    sub_4E1A6 (0x4E1A6, 0x84) - 24x24 RLE + 像素=(src&7)+24
 *    sub_4E22A (0x4E22A, 0x72) - 24x24 普通RLE (无调色板)
 *    sub_4E29C (0x4E29C, 0x74) - 24x24 RLE + 透明色=73(0x49)
 *    sub_4E8D3 (0x4E8D3, 0xBA) - BG.DAT RLE + 调色板查找(a6)
 *    sub_4E98D (0x4E98D, 0x1BB) - 通用RLE(3分支value_1)
 *
 *  ===== 36E00-36FFF 范围 (3个RLE解码器, 2种模式) =====
 *
 *    sub_36E65 (0x36E65, 0x42) - 调色板RLE(768字节) - 2种模式RLE/RAW
 *    sub_36F24 (0x36F24, 0x45) - 帧数据RLE(64000字节) - 2种模式RLE/RAW
 *    sub_36F82 (0x36F82, 0x2A) - 像素填充RLE(变长) - 2种模式RLE/RAW
 *
 *  ===== 公共RLE控制字节格式 (4E范围) =====
 *
 *    控制字节 (8-bit):
 *      bit7=0, bit6=0: FILL    count = (b & 0x3F) + 1, 用像素值填充
 *      bit7=0, bit6=1: ALT     间隔写入(只写偶数索引)
 *      bit7=1, bit6=0: COPY    count = (b & 0x3F) + 1, 从源复制count字节
 *      bit7=1, bit6=1: SKIP    count = (b & 0x3F) + 1, 跳过count像素
 *
 *  ===== 公共RLE控制字节格式 (36范围) =====
 *
 *    控制字节 (8-bit):
 *      if (b & 0xC0) == 0xC0: RLE    count = b & 0x3F, 重复下一个字节count次
 *      else:                   RAW     直接拷贝1字节
 * ======================================================================== */

/**
 * Decompress FDOTHER.DAT resources using the makeShapBMP algorithm.
 *
 * @param src      Source compressed data (including 4-byte width/height header)
 * @param src_size Size of source data
 * @param dst      Destination buffer (must be width * height bytes)
 * @param width    Image width
 * @param height   Image height
 * @return 0 on success, -1 on error
 */
int fd2_decode_fdother_resource(byte* src, int src_size, byte* dst, int width, int height);

/**
 * Decompress BG.DAT battle background images.
 *
 * Algorithm matches IDA function sub_4E98D and base_parser.py makeBgBMP.
 *
 * @param src      Source data pointer (includes 4-byte width/height header)
 * @param length   Length of source data
 * @param palette  256-color palette (RGB format, 768 bytes)
 * @param dst      Destination buffer (for pixel indices, width * height bytes)
 * @param stride   Destination stride (line width in bytes)
 * @return 0 on success, -1 on error
 */
int fd2_decode_bg_resource(byte* src, int length, byte* palette, byte* dst, int stride);

/* ========================================================================
 *  4E范围 RLE 解码函数 (4种模式: FILL/ALT/COPY/SKIP)
 * ======================================================================== */

/**
 * sub_4E016 - 24x24 RLE + 调色板查找表
 * @param src     压缩数据
 * @param src_size 源大小
 * @param dst     目标缓冲区(至少24*pitch字节)
 * @param width   目标宽度(>=24)
 * @param height  目标高度(>=24)
 * @param arg8    目标步长(pitch)
 * @param argC    调色板查找表(256字节)
 * @return 0 成功, -1 失败
 */
int fd2_rle_sub_4E016(const byte* src, int src_size, byte* dst, int width, int height, int arg8, const byte* argC);

/**
 * sub_4E0A2 - 24x24 RLE + 调色板查找 (与sub_4E016相同)
 */
int fd2_rle_sub_4E0A2(const byte* src, int src_size, byte* dst, int width, int height, int arg8, const byte* argC);

/**
 * sub_4E127 - 24x24 RLE + 单色填充
 * @param n456    固定颜色值
 */
int fd2_rle_sub_4E127(const byte* src, int src_size, byte* dst, int width, int height, int arg8, byte n456);

/**
 * sub_4E1A6 - 24x24 RLE + 像素=(src&7)+24
 */
int fd2_rle_sub_4E1A6(const byte* src, int src_size, byte* dst, int width, int height, int arg8);

/**
 * sub_4E22A - 24x24 精灵RLE (4种模式, 无调色板)
 * @param pitch   目标步长
 */
int fd2_rle_sub_4E22A(const byte* src, int src_size, byte* dst, int width, int height, int pitch);

/**
 * sub_4E29C - 24x24 RLE + 特殊透明色(73=0x49)
 */
int fd2_rle_sub_4E29C(const byte* src, int src_size, byte* dst, int width, int height, int arg8);

/**
 * sub_4E8D3 - BG.DAT RLE + 调色板查找(无SKIP模式)
 * @param arg0    目标x坐标
 * @param arg8    目标y坐标
 * @param n320    目标步长(pitch)
 * @param a6      调色板查找表
 */
int fd2_rle_sub_4E8D3(const byte* src, int src_size, byte* dst, int arg0, int arg8, int n320, int width, int height, const byte* a6);

/**
 * sub_4E98D - 通用RLE解码器 (3分支value_1)
 * @param value_1 模式控制:
 *                  -1: 直接复制像素
 *                  > 0xFF: 调色板映射
 *                  <= 0xFF: 固定值填充
 */
int fd2_rle_sub_4E98D(const byte* src, int src_size, byte* dst, int width, int height, int value_1);

/**
 * sub_4E98D 无4字节头版本 - 通用RLE解码器
 * 数据格式: 直接从src[0]开始是控制字节(无[w:2][h:2]头部)
 * 用于旧 fd_decompress_rle 调用方
 */
int fd2_rle_sub_4E98D_no_header(const byte* src, int src_size, byte* dst, int width, int height, int value_1);

/**
 * sub_4EC66 (0x4EC66, size 0x16) - FDOTHER.DAT TILE 状态机RLE解码器
 *
 * 算法(基于汇编代码 1:1 复刻):
 *   状态机寄存器: ah = 待输出计数(初值0), al = 当前像素值
 *   数据格式: 4字节头[w:2][h:2] + RLE压缩的 w*h 像素
 *   RLE控制字节:
 *     - al <= 0xC0: RAW, 1个像素 (ah=0, al=像素值)
 *     - al >  0xC0: RLE, ah=al-0xC1 (再读1字节作为重复值), 输出ah+1次
 *   状态ah>0时: 直接输出上次的al, ah--
 *
 * 与 sub_4E22A/sub_4E98D 风格的 4模式RLE (FILL/ALT/COPY/SKIP) 不同,
 * sub_4EC66 是 2模式RLE (RAW/RLE), 简单但有效.
 *
 * 用于 FDOTHER.DAT 资源10 (62x26图标) 等所有 TILE 资源.
 *
 * @param src      源数据(包含4字节头[w:2][h:2])
 * @param src_size 源数据大小
 * @param dst      目标缓冲区(至少 width*height 字节)
 * @param width    图像宽度(从src[0..1]读取)
 * @param height   图像高度(从src[2..3]读取)
 * @return 0 成功, -1 失败
 */
int fd2_rle_sub_4EC66(const byte* src, int src_size, byte* dst, int width, int height);

/* ========================================================================
 *  36范围 RLE 解码函数 (2种模式: RLE/RAW)
 * ======================================================================== */

/**
 * sub_36E65 - 调色板RLE (768字节, 256色×3通道)
 */
int fd2_rle_sub_36E65(const byte* src, int src_size, byte* dst);

/**
 * sub_36F24 - 帧数据RLE (变长)
 * @param total_size 目标总大小
 */
int fd2_rle_sub_36F24(const byte* src, int src_size, byte* dst, int total_size);

/**
 * sub_36F82 - 像素填充RLE (变长, 用于BG像素)
 * 格式: [count:2] 重复count次: [offset:2] [rle_len:1] [data:rle_len字节]
 */
int fd2_rle_sub_36F82(const byte* src, int src_size, byte* dst);

/* ========================================================================
 *  LMI1 Tile 解码函数 (FDOTHER.DAT 索引5)
 *  LMI1 Tile 格式: 4字节头 [w:2][h:2] + 像素数据
 *  - 透明色 = 0 (不写入目标缓冲区)
 *  - 非0字节 = 像素索引
 * ======================================================================== */

/**
 * LMI1 tile 未压缩解码 (对应 IDA sub_4ED4F @ 0x4ED4F, size 0x2A)
 * 数据: 4字节头 + w*h字节 (0=透明, 非0=像素)
 */
int fd2_rle_lmi1_decode_tile(const byte* src, int src_size, byte* dst, int* out_w, int* out_h);

/**
 * LMI1 tile RLE压缩解码 (对应 IDA sub_4EBFF @ 0x4EBFF + sub_4EC66 @ 0x4EC66)
 * 数据: 4字节头 + RLE压缩的w*h像素
 * RLE格式 (基于 sub_4EC66 状态机):
 *   - 状态ah=0时,读1字节al:
 *     - al <= 0xC0: RAW,输出al (1像素)
 *     - al > 0xC0:  RLE,ah=al-0xC0,再读1字节al作为重复值,输出al
 *   - 状态ah>0时,直接输出上次的al,ah--
 */
int fd2_rle_lmi1_decode_tile_rle(const byte* src, int src_size, byte* dst, int* out_w, int* out_h);

/**
 * LMI1 tile 4E 范围 RLE 解码 (透明色过滤)
 * 4E 范围 RLE 协议 (4 模式: FILL/ALT/COPY/SKIP):
 *   - 控制字节 c: count = ((4*c) & 0xFF) >> 2 + 1
 *   - top2 = 0x00: FILL  count 像素, 值 = 下一字节
 *   - top2 = 0x40: ALT   count 对 (写 count 像素+跳 count 像素)
 *   - top2 = 0x80: COPY  count 字节, 复制
 *   - top2 = 0xC0: SKIP  count 像素
 * 0=透明色,不写入
 */
int fd2_rle_lmi1_decode_tile_4e(const byte* src, int src_size, byte* dst, int* out_w, int* out_h);

/**
 * LMI1 tile 自动检测解码 (未压缩/RLE/4E-RLE)
 * 自动根据 tile_size 与 4+w*h 的关系选择:
 *   - size >= 4+w*h: 未压缩 (sub_4ED4F)
 *   - size <  4+w*h: 先尝试RLE (sub_4EBFF+sub_4EC66), 失败后尝试4E-RLE (sub_4E98D风格)
 */
int fd2_rle_lmi1_decode_tile_auto(const byte* src, int src_size, byte* dst,
                                   int* out_w, int* out_h, int pitch);

/* ========================================================================
 *  5x5 字符位图解码 (FDOTHER.DAT 资源 19/21)
 *
 *  资源 19 头部格式 (基于实际数据 1:1 分析):
 *    [w:2] = 5  (5 列字符网格)
 *    [h:2] = 5  (5 行字符网格)
 *    [dword:4] = 0  (保留)
 *    [offset_table:5*dword] - 5 行 RLE 数据起点 (小端字节序)
 *    [rle_data] - 5 行字符 RLE 数据 (每行 5 个 16x16 字符, sub_4E22A 风格 4 模式 RLE)
 *
 *  sub_4E22A 风格 RLE 控制字节:
 *    count = ((ctrl * 4) & 0xFF) >> 2 + 1
 *    top2 = 0x00: FILL   读1字节值, 写 count 像素
 *    top2 = 0x40: ALT    读1字节值, 间隔写 count 像素 (col+=2)
 *    top2 = 0x80: COPY   复制 count 字节
 *    top2 = 0xC0: SKIP   跳过 count 像素
 *
 *  @param src         源数据(资源19字节流)
 *  @param src_size    源数据大小
 *  @param dst         目标缓冲区(至少 5*16*5*16 = 6400 字节)
 *  @param char_w      每字符宽度(默认 16)
 *  @param char_h      每字符高度(默认 16)
 *  @return 0 成功, -1 失败
 * ======================================================================== */
int fd2_rle_decode_char_grid_5x5(const byte* src, int src_size, byte* dst,
                                  int char_w, int char_h);

#ifdef __cplusplus
}
#endif

#endif
