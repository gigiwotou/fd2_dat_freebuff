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
            for (int k = 0; k < count && dst_idx < total_size; k++) {
                dst[dst_idx++] = v;
            }
        } else {
            dst[dst_idx++] = b;
        }
    }
    return 0;
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
