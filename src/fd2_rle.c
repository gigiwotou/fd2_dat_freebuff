/* fd2_rle.c - 统一管理所有RLE解码函数
 *
 * 基于 IDA Pro MCP 反汇编游戏二进制分析得出:
 *
 * ===== 4E000-4EFFF 范围 (8个RLE解码器, 4种模式) =====
 *
 *   sub_4E016 (0x4E016, 0x8C) - 24x24 RLE + 调色板查找(argC)
 *   sub_4E0A2 (0x4E0A2, 0x85) - 24x24 RLE + 调色板查找(argC, 不同变量名)
 *   sub_4E127 (0x4E127, 0x7F) - 24x24 RLE + 单色填充(n456=颜色)
 *   sub_4E1A6 (0x4E1A6, 0x84) - 24x24 RLE + 像素=(src&7)+24
 *   sub_4E22A (0x4E22A, 0x72) - 24x24 普通RLE (无调色板)
 *   sub_4E29C (0x4E29C, 0x74) - 24x24 RLE + 透明色=73(0x49)
 *   sub_4E8D3 (0x4E8D3, 0xBA) - BG.DAT RLE + 调色板查找(a6)
 *   sub_4E98D (0x4E98D, 0x1BB) - 通用RLE(3分支value_1)
 *
 * ===== 36E00-36FFF 范围 (3个RLE解码器, 2种模式) =====
 *
 *   sub_36E65 (0x36E65, 0x42) - 调色板RLE(768字节) - 2种模式RLE/RAW
 *   sub_36F24 (0x36F24, 0x45) - 帧数据RLE(64000字节) - 2种模式RLE/RAW
 *   sub_36F82 (0x36F82, 0x2A) - 像素填充RLE(变长) - 2种模式RLE/RAW
 *
 * ===== 公共RLE控制字节格式 (4E范围) =====
 *
 *   控制字节 (8-bit):
 *     bit7=0, bit6=0: FILL    count = (b & 0x3F) + 1, 用像素值填充
 *     bit7=0, bit6=1: ALT     间隔写入(只写偶数索引)
 *     bit7=1, bit6=0: COPY    count = (b & 0x3F) + 1, 从源复制count字节
 *     bit7=1, bit6=1: SKIP    count = (b & 0x3F) + 1, 跳过count像素
 *
 * ===== 公共RLE控制字节格式 (36范围) =====
 *
 *   控制字节 (8-bit):
 *     if (b & 0xC0) == 0xC0: RLE    count = b & 0x3F, 重复下一个字节count次
 *     else:                   RAW     直接拷贝1字节
 */

#include "../include/fd2_rle.h"
#include <string.h>

/* ========================================================================
 *  fd2_decode_fdother_resource (makeShapBMP 算法)
 * ======================================================================== */
int fd2_decode_fdother_resource(byte* src, int src_size, byte* dst, int width, int height) {
    if (src_size < 4) return -1;
    int w = src[0] | (src[1] << 8);
    int h = src[2] | (src[3] << 8);
    if (src_size <= 4) return -1;
    byte* compressed = src + 4;
    int comp_size = src_size - 4;
    int expected = width * height;
    (void)w; (void)h;

    int num4 = 0;
    int num3 = comp_size - 1;
    int num7 = 0;
    int num8 = 0;
    int num9 = 0;
    byte b = 0;
    int num10 = 0;
    int num11 = 0;
    int pixel_idx = 0;

    while (num4 <= num3 && pixel_idx < expected) {
        int flag = num8 != 0;
        if (!flag) {
            num7 = 0; num8 = 0; num9 = 0;
            if (num4 < comp_size) {
                b = compressed[num4];
                if (b >= 192) {
                    num7 = b - 192 + 1;
                } else if (b >= 128) {
                    num8 = b - 128 + 1;
                } else if (b >= 64) {
                    num9 = b - 64;
                    num8 = 1;
                } else {
                    num8 = 1;
                    num9 = b;
                }
            }
            num10 += num7;
            if (num10 >= width) {
                num10 = 0;
                num11 += 1;
            }
        } else {
            int num12 = num9;
            int num13 = 0;
            while (num13 <= num12) {
                if (b >= 64 && b < 128) {
                    num10 += 1;
                    num4++;
                }
                if (num4 < comp_size) {
                    byte index = compressed[num4];
                    if (num10 >= 0 && num10 < width && num11 >= 0 && num11 < height) {
                        if (pixel_idx < expected) {
                            dst[pixel_idx] = index;
                            pixel_idx++;
                        }
                    }
                }
                num10 += 1;
                if (num10 >= width) {
                    num10 = 0;
                    num11 += 1;
                }
                num13++;
            }
            num8--;
        }
        num4++;
        if (num11 >= height) break;
    }
    return 0;
}

/* ========================================================================
 *  sub_4E22A - 24x24 精灵RLE (4种模式, 无调色板)
 *  IDA Pro MCP反汇编: 0x4E22A, size 0x72
 * ======================================================================== */
int fd2_rle_sub_4E22A(const byte* src, int src_size, byte* dst, int width, int height, int pitch) {
    if (!src || !dst || width <= 0 || height <= 0 || src_size <= 0) return -1;
    if (width < 24 || height < 24) return -1;

    int src_idx = 0;
    byte* row = dst;

    for (int y = 0; y < 24; y++) {
        byte* col = row;
        int remaining = 24;
        while (remaining > 0) {
            if (src_idx >= src_size) return -1;
            byte ctrl = src[src_idx++];
            int count = ((ctrl * 4) & 0xFF) >> 2;
            count = count + 1;

            byte top2 = ctrl & 0xC0;
            if (top2 == 0x00) {
                /* FILL: 读1字节, memset count次 */
                if (src_idx >= src_size) return -1;
                byte v = src[src_idx++];
                memset(col, v, count);
                col += count;
                remaining -= count;
            } else if (top2 == 0x40) {
                /* ALT: 间隔写入(读1字节, 写1个跳1个) */
                if (src_idx >= src_size) return -1;
                byte v = src[src_idx++];
                remaining -= count + count;
                for (int k = 0; k < count; k++) {
                    col[0] = v;
                    col += 2;
                }
            } else if (top2 == 0x80) {
                /* COPY: 从源复制count字节 */
                if (src_idx + count > src_size) return -1;
                memcpy(col, src + src_idx, count);
                src_idx += count;
                col += count;
                remaining -= count;
            } else {
                /* SKIP: 跳过count像素 */
                col += count;
                remaining -= count;
            }
        }
        row += pitch;
    }
    return 0;
}

/* ========================================================================
 *  sub_4E016 - 24x24 RLE + 调色板查找表
 *  IDA Pro MCP反汇编: 0x4E016, size 0x8C
 *  参数:
 *    src    - 压缩数据
 *    dst    - 目标缓冲区(24x24)
 *    arg8   - 目标步长(pitch)
 *    argC   - 调色板查找表基地址(256字节, 用于 src_byte -> 实际像素)
 * ======================================================================== */
int fd2_rle_sub_4E016(const byte* src, int src_size, byte* dst, int width, int height, int arg8, const byte* argC) {
    if (!src || !dst || !argC || width <= 0 || height <= 0 || src_size <= 0) return -1;
    if (width < 24 || height < 24) return -1;

    int src_idx = 0;
    byte* row = dst;

    for (int y = 0; y < 24; y++) {
        byte* col = row;
        int remaining = 24;
        while (remaining > 0) {
            if (src_idx >= src_size) return -1;
            byte ctrl = src[src_idx++];
            int count = ((ctrl * 4) & 0xFF) >> 2;
            count = count + 1;

            byte top2 = ctrl & 0xC0;
            if (top2 == 0x00) {
                /* FILL + 调色板查找 */
                if (src_idx >= src_size) return -1;
                byte v = argC[src[src_idx++]];
                memset(col, v, count);
                col += count;
                remaining -= count;
            } else if (top2 == 0x40) {
                /* ALT + 调色板查找 */
                if (src_idx >= src_size) return -1;
                byte v = argC[src[src_idx++]];
                remaining -= count + count;
                for (int k = 0; k < count; k++) {
                    col[0] = v;
                    col += 2;
                }
            } else if (top2 == 0x80) {
                /* COPY + 调色板查找(逐字节) */
                for (int k = 0; k < count; k++) {
                    if (src_idx >= src_size) return -1;
                    col[k] = argC[src[src_idx++]];
                }
                col += count;
                remaining -= count;
            } else {
                /* SKIP */
                col += count;
                remaining -= count;
            }
        }
        row += arg8;
    }
    return 0;
}

/* ========================================================================
 *  sub_4E0A2 - 24x24 RLE + 调色板查找 (与sub_4E016类似, 参数顺序不同)
 *  IDA Pro MCP反汇编: 0x4E0A2, size 0x85
 * ======================================================================== */
int fd2_rle_sub_4E0A2(const byte* src, int src_size, byte* dst, int width, int height, int arg8, const byte* argC) {
    /* 实际与sub_4E016相同逻辑, 只是编译器变量名不同 */
    return fd2_rle_sub_4E016(src, src_size, dst, width, height, arg8, argC);
}

/* ========================================================================
 *  sub_4E127 - 24x24 RLE + 单色填充(n456 = 颜色值)
 *  IDA Pro MCP反汇编: 0x4E127, size 0x7F
 *  所有FILL/COPY/ALT操作都使用固定颜色 n456
 * ======================================================================== */
int fd2_rle_sub_4E127(const byte* src, int src_size, byte* dst, int width, int height, int arg8, byte n456) {
    if (!src || !dst || width <= 0 || height <= 0 || src_size <= 0) return -1;
    if (width < 24 || height < 24) return -1;

    int src_idx = 0;
    byte* row = dst;

    for (int y = 0; y < 24; y++) {
        byte* col = row;
        int remaining = 24;
        while (remaining > 0) {
            if (src_idx >= src_size) return -1;
            byte ctrl = src[src_idx++];
            int count = ((ctrl * 4) & 0xFF) >> 2;
            count = count + 1;

            byte top2 = ctrl & 0xC0;
            if (top2 == 0x00) {
                /* FILL: 跳过1字节(不读), 用 n456 填充 */
                src_idx++;
                memset(col, n456, count);
                col += count;
                remaining -= count;
            } else if (top2 == 0x40) {
                /* ALT: 跳过1字节, 用 n456 */
                src_idx++;
                remaining -= count + count;
                for (int k = 0; k < count; k++) {
                    col[0] = n456;
                    col += 2;
                }
            } else if (top2 == 0x80) {
                /* COPY: 跳过count字节, 用 n456 填充 */
                src_idx += count;
                memset(col, n456, count);
                col += count;
                remaining -= count;
            } else {
                /* SKIP */
                col += count;
                remaining -= count;
            }
        }
        row += arg8;
    }
    return 0;
}

/* ========================================================================
 *  sub_4E1A6 - 24x24 RLE + 像素值范围限制 ((src & 7) + 24)
 *  IDA Pro MCP反汇编: 0x4E1A6, size 0x84
 *  实际像素 = (源字节 & 7) + 24, 限制在 24-31 范围
 * ======================================================================== */
int fd2_rle_sub_4E1A6(const byte* src, int src_size, byte* dst, int width, int height, int arg8) {
    if (!src || !dst || width <= 0 || height <= 0 || src_size <= 0) return -1;
    if (width < 24 || height < 24) return -1;

    int src_idx = 0;
    byte* row = dst;

    for (int y = 0; y < 24; y++) {
        byte* col = row;
        int remaining = 24;
        while (remaining > 0) {
            if (src_idx >= src_size) return -1;
            byte ctrl = src[src_idx++];
            int count = ((ctrl * 4) & 0xFF) >> 2;
            count = count + 1;

            byte top2 = ctrl & 0xC0;
            if (top2 == 0x00) {
                /* FILL: 读1字节, 像素 = (v & 7) + 24 */
                if (src_idx >= src_size) return -1;
                byte v = (src[src_idx++] & 7) + 24;
                memset(col, v, count);
                col += count;
                remaining -= count;
            } else if (top2 == 0x40) {
                /* ALT: 像素 = (v & 7) + 24 */
                if (src_idx >= src_size) return -1;
                byte v = (src[src_idx++] & 7) + 24;
                remaining -= count + count;
                for (int k = 0; k < count; k++) {
                    col[0] = v;
                    col += 2;
                }
            } else if (top2 == 0x80) {
                /* COPY: 每像素 = (v & 7) + 24 */
                for (int k = 0; k < count; k++) {
                    if (src_idx >= src_size) return -1;
                    col[k] = (src[src_idx++] & 7) + 24;
                }
                col += count;
                remaining -= count;
            } else {
                /* SKIP */
                col += count;
                remaining -= count;
            }
        }
        row += arg8;
    }
    return 0;
}

/* ========================================================================
 *  sub_4E29C - 24x24 RLE + 特殊透明色(73=0x49)
 *  IDA Pro MCP反汇编: 0x4E29C, size 0x74
 *  0x80模式(bit7=1,bit6=0): 不是copy, 是用 0x49(73) 填充
 * ======================================================================== */
int fd2_rle_sub_4E29C(const byte* src, int src_size, byte* dst, int width, int height, int arg8) {
    if (!src || !dst || width <= 0 || height <= 0 || src_size <= 0) return -1;
    if (width < 24 || height < 24) return -1;

    int src_idx = 0;
    byte* row = dst;

    for (int y = 0; y < 24; y++) {
        byte* col = row;
        int remaining = 24;
        while (remaining > 0) {
            if (src_idx >= src_size) return -1;
            byte ctrl = src[src_idx++];
            int count = ((ctrl * 4) & 0xFF) >> 2;
            count = count + 1;

            byte top2 = ctrl & 0xC0;
            if (top2 == 0x00) {
                /* FILL: 读1字节并填充 */
                if (src_idx >= src_size) return -1;
                byte v = src[src_idx++];
                memset(col, v, count);
                col += count;
                remaining -= count;
            } else if (top2 == 0x40) {
                /* ALT: 读1字节, 间隔写入 */
                if (src_idx >= src_size) return -1;
                byte v = src[src_idx++];
                remaining -= count + count;
                for (int k = 0; k < count; k++) {
                    col[0] = v;
                    col += 2;
                }
            } else if (top2 == 0x80) {
                /* 特殊: 用 0x49(73) 填充(透明色) */
                memset(col, 0x49, count);
                col += count;
                remaining -= count;
            } else {
                /* SKIP: 跳过count像素 */
                col += count;
                remaining -= count;
            }
        }
        row += arg8;
    }
    return 0;
}

/* ========================================================================
 *  sub_4E8D3 - BG.DAT RLE + 调色板查找(无SKIP模式)
 *  IDA Pro MCP反汇编: 0x4E8D3, size 0xBA
 *  参数:
 *    src    - 包含[w:2][h:2]头的压缩数据
 *    dst    - 目标缓冲区
 *    arg0   - 目标x坐标(行内起始位置)
 *    arg8   - 目标y坐标(行起始位置)
 *    n320   - 目标步长(pitch)
 *    a6     - 调色板查找表基地址
 * ======================================================================== */
int fd2_rle_sub_4E8D3(const byte* src, int src_size, byte* dst, int arg0, int arg8, int n320, int width, int height, const byte* a6) {
    if (!src || !dst || !a6 || src_size < 4) return -1;
    if (width <= 0 || height <= 0) return -1;

    /* 读取头 [w:2][h:2] */
    int w = src[0] | (src[1] << 8);
    int h = src[2] | (src[3] << 8);
    (void)w; (void)h;
    int src_idx = 4;
    byte* row = dst + n320 * arg8 + arg0;
    int remaining_height = height;

    for (int y = 0; y < height; y++) {
        byte* col = row;
        int remaining = width;
        while (remaining > 0) {
            if (src_idx >= src_size) return -1;
            byte ctrl = src[src_idx++];
            int count = ((ctrl * 4) & 0xFF) >> 2;
            count = count + 1;

            byte top2 = ctrl & 0xC0;
            if (top2 == 0x00) {
                /* FILL + 调色板查找 */
                if (src_idx >= src_size) return -1;
                byte v = a6[src[src_idx++]];
                memset(col, v, count);
                col += count;
                remaining -= count;
            } else if (top2 == 0x40) {
                /* ALT + 调色板查找 */
                if (src_idx >= src_size) return -1;
                byte v = a6[src[src_idx++]];
                remaining -= count + count;
                for (int k = 0; k < count; k++) {
                    col[0] = v;
                    col += 2;
                }
            } else if (top2 == 0x80) {
                /* COPY + 调色板查找(逐字节) */
                for (int k = 0; k < count; k++) {
                    if (src_idx >= src_size) return -1;
                    col[k] = a6[src[src_idx++]];
                }
                col += count;
                remaining -= count;
            } else {
                /* bit7=1,bit6=1: 跳过count像素(无调色板) */
                col += count;
                remaining -= count;
            }
        }
        row += n320;
        (void)remaining_height;
    }
    return 0;
}

/* ========================================================================
 *  sub_4E98D - 通用RLE解码器 (3分支value_1)
 *  IDA Pro MCP反汇编: 0x4E98D, size 0x1BB
 *  参数:
 *    src     - 包含[w:2][h:2]头的压缩数据
 *    src_size - 源数据大小
 *    dst     - 目标缓冲区
 *    width   - 图像宽度
 *    height  - 图像高度
 *    value_1 - 模式控制:
 *                -1: 直接复制像素
 *                > 0xFF: 调色板映射 (value_1 + ((value_1>>8 + pixel) & 7))
 *                <= 0xFF: 固定值填充
 * ======================================================================== */
int fd2_rle_sub_4E98D(const byte* src, int src_size, byte* dst, int width, int height, int value_1) {
    if (!src || !dst || src_size < 4 || width <= 0 || height <= 0) return -1;

    int w = src[0] | (src[1] << 8);
    int h = src[2] | (src[3] << 8);
    (void)w; (void)h;
    int src_idx = 4;
    byte* row = dst;
    int dst_size = width * height;

    for (int y = 0; y < height; y++) {
        byte* col = row;
        int remaining = width;
        while (remaining > 0) {
            if (src_idx >= src_size) return -1;
            byte ctrl = src[src_idx++];
            int count = ((ctrl * 4) & 0xFF) >> 2;
            count = count + 1;

            byte top2 = ctrl & 0xC0;
            byte pixel;

            if (top2 == 0x00) {
                /* FILL */
                if (src_idx >= src_size) return -1;
                byte v = src[src_idx++];
                if (value_1 == -1) pixel = v;
                else if (value_1 > 0xFF) pixel = (value_1 + (((value_1 >> 8) + v) & 7)) & 0xFF;
                else pixel = value_1 & 0xFF;
                memset(col, pixel, count);
                col += count;
                remaining -= count;
            } else if (top2 == 0x40) {
                /* ALT */
                if (src_idx >= src_size) return -1;
                byte v = src[src_idx++];
                if (value_1 == -1) pixel = v;
                else if (value_1 > 0xFF) pixel = (value_1 + (((value_1 >> 8) + v) & 7)) & 0xFF;
                else pixel = value_1 & 0xFF;
                remaining -= count + count;
                for (int k = 0; k < count; k++) {
                    col[0] = pixel;
                    col += 2;
                }
            } else if (top2 == 0x80) {
                /* COPY(逐像素处理) */
                for (int k = 0; k < count; k++) {
                    if (src_idx >= src_size) return -1;
                    byte v = src[src_idx++];
                    if (value_1 == -1) pixel = v;
                    else if (value_1 > 0xFF) pixel = (value_1 + (((value_1 >> 8) + v) & 7)) & 0xFF;
                    else pixel = value_1 & 0xFF;
                    col[k] = pixel;
                }
                col += count;
                remaining -= count;
            } else {
                /* SKIP */
                col += count;
                remaining -= count;
            }
        }
        row += width;
        (void)dst_size;
    }
    return 0;
}

/* ========================================================================
 *  fd2_rle_sub_4E98D_no_header - 通用RLE解码器(无4字节头版本)
 *  IDA Pro MCP反汇编: 0x4E98D, size 0x1BB (去掉头部读取)
 *  用于 fd2_dat.c 中旧 fd_decompress_rle 调用方,数据不含[w:2][h:2]头
 *
 *  RLE控制字节 b:
 *    bit7=0, bit6=0 (b<0x40):     FILL     count=b+1,           写count个v到dst
 *    bit7=0, bit6=1 (0x40<=b<0x80): FILL2   count=(b&0x3F)+1,   隔一个写count个v(consume 2*count)
 *    bit7=1, bit6=0 (0x80<=b<0xC0): COPY   count=(b&0x3F)+1,   复制count个src字节
 *    bit7=1, bit6=1 (b>=0xC0):      SKIP   count=(b&0x3F)+1,   跳过count像素
 *
 *  参数:
 *    src     - 压缩数据(无头)
 *    src_size - 源数据大小
 *    dst     - 目标缓冲区
 *    width   - 图像宽度
 *    height  - 图像高度
 *    value_1 - 模式控制:
 *                -1: 直接复制像素
 *                > 0xFF: 调色板映射 (value_1 + ((value_1>>8 + pixel) & 7))
 *                <= 0xFF: 固定值填充
 * ======================================================================== */
int fd2_rle_sub_4E98D_no_header(const byte* src, int src_size, byte* dst, int width, int height, int value_1) {
    if (!src || !dst || src_size <= 0 || width <= 0 || height <= 0) return -1;

    int src_idx = 0;
    byte* row = dst;

    for (int y = 0; y < height; y++) {
        byte* col = row;
        int remaining = width;
        while (remaining > 0) {
            /* 源数据耗尽: 视为剩余像素全部为0(透明/背景).
             * 这种情况出现在索引2的"空"子资源(全0 RLE数据)
             * 和全 0 子资源中, 视为合法解码完成. */
            if (src_idx >= src_size) {
                return 0;
            }
            byte ctrl = src[src_idx++];
            byte top2 = ctrl & 0xC0;
            int count;

            if (top2 == 0x00) {
                /* FILL: count = ctrl + 1 */
                count = ctrl + 1;
                if (src_idx >= src_size) return 0;  /* 源数据耗尽, 视为全0完成 */
                byte v = src[src_idx++];
                byte pixel;
                if (value_1 == -1) pixel = v;
                else if (value_1 > 0xFF) pixel = (value_1 + (((value_1 >> 8) + v) & 7)) & 0xFF;
                else pixel = value_1 & 0xFF;
                memset(col, pixel, count);
                col += count;
                remaining -= count;
            } else if (top2 == 0x40) {
                /* FILL2: count = (ctrl & 0x3F) + 1, 隔一个写 (consume 2*count) */
                count = (ctrl & 0x3F) + 1;
                if (src_idx >= src_size) return 0;  /* 源数据耗尽, 视为全0完成 */
                byte v = src[src_idx++];
                byte pixel;
                if (value_1 == -1) pixel = v;
                else if (value_1 > 0xFF) pixel = (value_1 + (((value_1 >> 8) + v) & 7)) & 0xFF;
                else pixel = value_1 & 0xFF;
                /* 写入 col[1], col[3], col[5], ... 共 count 个 */
                for (int k = 0; k < count; k++) {
                    if (1 + k * 2 < remaining) {
                        col[1 + k * 2] = pixel;
                    }
                }
                col += count * 2;
                remaining -= count * 2;
            } else if (top2 == 0x80) {
                /* COPY: count = (ctrl & 0x3F) + 1 */
                count = (ctrl & 0x3F) + 1;
                for (int k = 0; k < count; k++) {
                    if (src_idx >= src_size) return 0;  /* 源数据耗尽, 视为全0完成 */
                    byte v = src[src_idx++];
                    byte pixel;
                    if (value_1 == -1) pixel = v;
                    else if (value_1 > 0xFF) pixel = (value_1 + (((value_1 >> 8) + v) & 7)) & 0xFF;
                    else pixel = value_1 & 0xFF;
                    if (k < remaining) col[k] = pixel;
                }
                col += count;
                remaining -= count;
            } else {
                /* SKIP: count = (ctrl & 0x3F) + 1 */
                count = (ctrl & 0x3F) + 1;
                col += count;
                remaining -= count;
            }
        }
        row += width;
    }
    return 0;
}

/* ========================================================================
 *  36xxx 范围 RLE 解码器 (2种模式: RLE/RAW)
 *
 *  控制字节 (8-bit):
 *    if (b & 0xC0) == 0xC0: RLE    count = b & 0x3F, 重复下一字节 count次
 *    else:                   RAW     直接拷贝 1 字节
 * ======================================================================== */

/* sub_36E65 - 调色板RLE (768字节, 256色×3通道)
 *  IDA Pro MCP反汇编: 0x36E65, size 0x42
 */
int fd2_rle_sub_36E65(const byte* src, int src_size, byte* dst) {
    if (!src || !dst || src_size <= 0) return -1;
    int total = 768;
    int src_idx = 0;
    int dst_idx = 0;

    while (dst_idx < total) {
        if (src_idx >= src_size) return -1;
        byte b = src[src_idx++];
        if ((b & 0xC0) == 0xC0) {
            /* RLE模式 */
            if (src_idx >= src_size) return -1;
            byte v = src[src_idx++];
            int count = b & 0x3F;
            for (int k = 0; k < count && dst_idx < total; k++) {
                dst[dst_idx++] = v;
            }
        } else {
            /* RAW模式 */
            dst[dst_idx++] = b;
        }
    }
    return 0;
}

/* sub_36F24 - 帧数据RLE (64000字节)
 *  IDA Pro MCP反汇编: 0x36F24, size 0x45
 *  与sub_36E65结构相同, 仅目标大小不同
 *
 *  兼容性: count=0 时按 64 处理(游戏中常见trick, 与旧 rle_decompress 一致)
 */
int fd2_rle_sub_36F24(const byte* src, int src_size, byte* dst, int total_size) {
    if (!src || !dst || src_size <= 0 || total_size <= 0) return -1;
    int src_idx = 0;
    int dst_idx = 0;

    while (dst_idx < total_size) {
        if (src_idx >= src_size) return -1;
        byte b = src[src_idx++];
        if ((b & 0xC0) == 0xC0) {
            if (src_idx >= src_size) return -1;
            byte v = src[src_idx++];
            int count = b & 0x3F;
            if (count == 0) count = 64;  /* 兼容旧实现: 0当作64 */
            for (int k = 0; k < count && dst_idx < total_size; k++) {
                dst[dst_idx++] = v;
            }
        } else {
            dst[dst_idx++] = b;
        }
    }
    return 0;
}

/* ========================================================================
 *  LMI1 Tile 解码函数 (FDOTHER.DAT 索引5)
 *
 *  LMI1 Tile 格式: 4字节头 [w:2][h:2] + 像素数据
 *  - 透明色 = 0 (0字节表示透明像素, 不写入目标缓冲区)
 *  - 非0字节 = 像素索引
 *
 *  两种编码方式:
 *  A. 未压缩 (sub_4ED4F @ 0x4ED4F, size 0x2A):
 *     直接 w*h 字节, 0=透明, 非0=像素
 *
 *  B. RLE压缩 (sub_4EBFF @ 0x4EBFF, size 0x32 + sub_4EC66 @ 0x4EC66, size 0x16):
 *     RLE控制字节 (基于 sub_4EC66 状态机):
 *       - 0xC0 以下: RAW, 1个像素
 *       - 0xC0+count (0xC1-0xFF): RLE, count=al-0xC0个相同像素
 *     状态寄存器: ah = 待输出计数(初值0,每次输出后减1,0时再读)
 *     输出值: al
 *     0=透明色 (不写入)
 * ======================================================================== */

/* sub_4ED4F - LMI1 tile 未压缩解码 (透明色过滤)
 *  头: [w:2][h:2]
 *  数据: w*h 字节 (0=透明,非0=像素)
 */
int fd2_rle_lmi1_decode_tile(const byte* src, int src_size, byte* dst, int* out_w, int* out_h) {
    if (!src || !dst || src_size < 4) return -1;
    int w = src[0] | (src[1] << 8);
    int h = src[2] | (src[3] << 8);
    if (w <= 0 || h <= 0 || w > 1024 || h > 1024) return -1;
    if (src_size < 4 + w * h) return -1;
    const byte* s = src + 4;
    for (int i = 0; i < w * h; i++) {
        byte v = s[i];
        if (v) dst[i] = v;  /* 0=透明,跳过 */
    }
    if (out_w) *out_w = w;
    if (out_h) *out_h = h;
    return 0;
}

/* sub_4EBFF + sub_4EC66 - LMI1 tile RLE压缩解码 (透明色过滤)
 *  头: [w:2][h:2]
 *  数据: RLE压缩的 w*h 像素
 *  RLE格式 (基于 sub_4EC66 状态机):
 *    - 状态ah=0时,读1字节al:
 *      - al <= 0xC0: RAW,输出al (1像素)
 *      - al > 0xC0:  RLE,ah=al-0xC1,再读1字节al作为重复值,输出al
 *    - 状态ah>0时,直接输出上次的al,ah--
 *  0=透明色,不写入
 */
int fd2_rle_lmi1_decode_tile_rle(const byte* src, int src_size, byte* dst, int* out_w, int* out_h) {
    if (!src || !dst || src_size < 4) return -1;
    int w = src[0] | (src[1] << 8);
    int h = src[2] | (src[3] << 8);
    if (w <= 0 || h <= 0 || w > 1024 || h > 1024) return -1;
    const byte* s = src + 4;
    int data_size = src_size - 4;
    if (data_size <= 0) return -1;

    /* 状态机: ah = 待输出计数(初值0, 触发新读), al = 当前值 */
    int ah = 0;
    byte al = 0;
    int pos = 0;  /* 数据读取位置 */

    for (int i = 0; i < w * h; i++) {
        if (ah == 0) {
            /* 读新控制/数据字节 */
            if (pos >= data_size) return -1;
            al = s[pos++];
            if (al > 0xC0) {
                /* RLE模式: ah = al - 0xC1 (修正:汇编 sub ah, 0xC1h) */
                ah = (al - 0xC1) & 0xFF;
                if (pos >= data_size) return -1;
                al = s[pos++];
            }
            /* RAW模式: ah=0, al=像素值 */
        } else {
            ah--;  /* 输出前递减 */
        }
        if (al) dst[i] = al;  /* 0=透明,跳过 */
    }
    /* 严格检查: RLE 模式必须完整消耗 data_size, 否则不是 RLE 编码 */
    if (pos != data_size) return -1;
    if (out_w) *out_w = w;
    if (out_h) *out_h = h;
    return 0;
}

/* LMI1 tile 4E 范围 RLE 解码 (透明色过滤)
 *  4E 范围 RLE 协议 (4 模式: FILL/ALT/COPY/SKIP):
 *    - 控制字节 c: count = ((4*c) & 0xFF) >> 2 + 1
 *    - top2 = 0x00: FILL  count 像素, 值 = 下一字节
 *    - top2 = 0x40: ALT   count 对 (写 count 像素+跳 count 像素)
 *    - top2 = 0x80: COPY  count 字节, 复制
 *    - top2 = 0xC0: SKIP  count 像素
 *  0=透明色,不写入
 *  对应 IDA Pro MCP sub_4E98D 风格的 4E 范围 RLE
 */
int fd2_rle_lmi1_decode_tile_4e(const byte* src, int src_size, byte* dst, int* out_w, int* out_h) {
    if (!src || !dst || src_size < 4) return -1;
    int w = src[0] | (src[1] << 8);
    int h = src[2] | (src[3] << 8);
    if (w <= 0 || h <= 0 || w > 1024 || h > 1024) return -1;
    const byte* s = src + 4;
    int data_size = src_size - 4;
    if (data_size <= 0) return -1;

    int pos = 0;
    int total = w * h;
    int out = 0;
    /* 目标缓冲区需先初始化为0 (透明) */
    memset(dst, 0, total);

    while (out < total && pos < data_size) {
        byte c = s[pos++];
        byte top2 = c & 0xC0;
        int count = (((4 * c) & 0xFF) >> 2) + 1;

        if (top2 == 0x00) {
            /* FILL: 读 1 字节值, 写 count 像素 */
            if (pos >= data_size) return -1;
            byte v = s[pos++];
            if (v) {
                for (int k = 0; k < count && out < total; k++) {
                    dst[out++] = v;
                }
            } else {
                out += count;
            }
        } else if (top2 == 0x40) {
            /* ALT: 读 1 字节值, 间隔写 count 像素 (中间跳 count 透明) */
            if (pos >= data_size) return -1;
            byte v = s[pos++];
            for (int k = 0; k < count && out < total; k++) {
                if (v) dst[out] = v;
                out += 2;
            }
        } else if (top2 == 0x80) {
            /* COPY: 复制 count 字节 */
            for (int k = 0; k < count && out < total; k++) {
                if (pos >= data_size) return -1;
                byte v = s[pos++];
                if (v) dst[out] = v;
                out++;
            }
        } else {
            /* SKIP: 跳过 count 像素 (透明) */
            out += count;
        }
    }
    if (out != total) return -1;
    /* 严格检查: 4E 范围 RLE 必须完整消耗 data_size, 否则不是 RLE 编码.
     * 否则未压缩数据(如 0x63 0xbd ...)会"误判成功": 0x63 控制字节被当作
     * FILL count=36 + 0xbd 像素, 2 条指令就填满 48 像素, 错误地"成功" */
    if (pos != data_size) return -1;
    if (out_w) *out_w = w;
    if (out_h) *out_h = h;
    return 0;
}

/* LMI1 tile 自动检测解码 (未压缩/RLE/4E-RLE)
 *  关键: 不能用 size 与 4+w*h 的大小关系来判断格式!
 *  因为某些 RLE 编码的 size 可能 >= expected (例如小数字图 4e RLE 编码).
 *  必须先尝试 RLE 解码 (sub_4EBFF+sub_4EC66, 然后 4E), 验证完整消耗 data_size 才算成功.
 *  最后才回退到未压缩解码 (sub_4ED4F).
 *  @param out_pixels 目标缓冲区 (至少 w*h 字节, 已初始化为0)
 *  @param pitch      目标步长 (供未来扩展, 当前未使用)
 *  @return 0 成功, -1 失败
 */
int fd2_rle_lmi1_decode_tile_auto(const byte* src, int src_size, byte* dst,
                                   int* out_w, int* out_h, int pitch) {
    if (!src || !dst || src_size < 4) return -1;
    (void)pitch;
    int w = src[0] | (src[1] << 8);
    int h = src[2] | (src[3] << 8);
    if (w <= 0 || h <= 0 || w > 1024 || h > 1024) return -1;
    int expected_size = 4 + w * h;
    if (expected_size <= 0) return -1;

    int ret;

    /* 1. 优先尝试 sub_4EBFF+sub_4EC66 RLE (状态机编码, 0=透明像素也消耗1字节)
     *    严格检查 pos==data_size, 失败才回退 */
    ret = fd2_rle_lmi1_decode_tile_rle(src, src_size, dst, out_w, out_h);
    if (ret == 0) return 0;

    /* 2. 尝试 4E 范围 RLE (sub_4E98D 风格, SKIP跳过0=透明) */
    ret = fd2_rle_lmi1_decode_tile_4e(src, src_size, dst, out_w, out_h);
    if (ret == 0) return 0;

    /* 3. 回退: 未压缩 (sub_4ED4F) - 仅当 src_size 足够时 */
    if (src_size >= expected_size) {
        return fd2_rle_lmi1_decode_tile(src, expected_size, dst, out_w, out_h);
    }
    return -1;
}

/* sub_36F82 - 像素填充RLE (变长, 用于BG像素)
 *  IDA Pro MCP反汇编: 0x36F82, size 0x2A
 *  输入格式: [count:2] 重复count次以下结构:
 *    [offset:2] [rle_len:1] [data:rle_len字节]
 *  rle_len字节的解码: 同样使用 RLE/RAW 模式
 */
int fd2_rle_sub_36F82(const byte* src, int src_size, byte* dst) {
    if (!src || !dst || src_size < 2) return -1;
    int src_idx = 0;

    /* 第一个字是重复次数 */
    int repeat = src[src_idx] | (src[src_idx + 1] << 8);
    src_idx += 2;

    for (int r = 0; r < repeat; r++) {
        if (src_idx + 3 > src_size) return -1;
        /* 读偏移(2字节, 相对dst) */
        int offset = src[src_idx] | (src[src_idx + 1] << 8);
        src_idx += 2;
        /* 读RLE数据长度(1字节) */
        int rle_len = src[src_idx++];

        if (src_idx + rle_len > src_size) return -1;

        /* 解码RLE到 dst + offset */
        byte* target = dst + offset;
        int rle_src_idx = src_idx;
        int rle_end = rle_src_idx + rle_len;
        int target_idx = 0;

        while (rle_src_idx < rle_end) {
            byte b = src[rle_src_idx++];
            if ((b & 0xC0) == 0xC0) {
                if (rle_src_idx >= rle_end) return -1;
                byte v = src[rle_src_idx++];
                int count = b & 0x3F;
                for (int k = 0; k < count; k++) {
                    target[target_idx++] = v;
                }
            } else {
                target[target_idx++] = b;
            }
        }
        src_idx += rle_len;
    }
    return 0;
}

/* ========================================================================
 *  fd2_decode_bg_resource (BG.DAT 战斗背景图像)
 *  使用 sub_4E98D 解码(任意尺寸, value_1=-1)
 * ======================================================================== */
int fd2_decode_bg_resource(byte* src, int length, byte* palette, byte* dst, int stride) {
    (void)palette; (void)stride;
    if (!src || !dst || length < 4) return -1;
    int w = src[0] | (src[1] << 8);
    int h = src[2] | (src[3] << 8);
    return fd2_rle_sub_4E98D(src, length, dst, w, h, -1);
}
