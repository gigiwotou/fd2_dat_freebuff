/**
 * FD2 RLE Decoder - 统一RLE解码模块
 *
 * 基于IDA Pro汇编代码1:1还原
 * 包含以下IDA函数:
 *   - sub_4E98D: 通用RLE解码器
 *   - sub_4E22A: 24x24精灵RLE解码器
 *   - sub_36E65: AFM调色板RLE解码
 *   - sub_36F24: AFM帧数据RLE解码
 *   - sub_36F82: AFM像素填充RLE解码
 *
 * RLE格式说明:
 *   命令字节格式: [bit7][bit6][count:6]
 *   bit7=1, bit6=1: 跳过(透明) - 跳过count个像素
 *   bit7=1, bit6=0: 复制 - 从源复制count字节
 *   bit7=0, bit6=1: 交替填充 - 每隔一个位置写入
 *   bit7=0, bit6=0: 填充 - 用源字节值填充count个像素
 */

#ifndef FD2_RLE_H
#define FD2_RLE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ============================================================================
 * 类型定义
 * ============================================================================ */

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;

#define FD2_PALETTE_COLORS 256
#define FD2_PALETTE_BYTES   (FD2_PALETTE_COLORS * 3)

/* ============================================================================
 * sub_4E98D: 通用RLE解码器
 *
 * 适用于任意尺寸的图像数据解码
 * ============================================================================ */

/**
 * fd2_rle_decompress - 通用RLE解码 (IDA sub_4E98D)
 *
 * @param src       源数据指针
 * @param src_size  源数据大小
 * @param dst       目标缓冲区
 * @param width     图像宽度
 * @param height    图像高度
 * @return 0成功, -1失败
 */
int fd2_rle_decompress(const u8* src, u32 src_size,
                      u8* dst, int width, int height);

/**
 * fd2_rle_decompress_to_buffer - 带Stride的RLE解码
 *
 * @param res_data   资源数据(含4字节头)
 * @param res_size    资源大小
 * @param dst_buf     目标缓冲区
 * @param dst_y       Y偏移
 * @param stride      目标stride(行宽度)
 * @return 0成功, -1失败
 */
int fd2_rle_decompress_to_buffer(const u8* res_data, u32 res_size,
                                 u8* dst_buf, int dst_y, int stride);

/**
 * fd2_rle_decompress_from_resource - 从资源数据解码
 *
 * 自动解析4字节头(width,height)并分配解码缓冲区
 *
 * @param res_data    资源数据(含4字节头)
 * @param res_size     资源大小
 * @param out_pixels   输出像素数据(需free)
 * @param out_w        输出宽度
 * @param out_h        输出高度
 * @return 0成功, -1失败
 */
int fd2_rle_decompress_from_resource(const u8* res_data, u32 res_size,
                                     u8** out_pixels, int* out_w, int* out_h);

/* ============================================================================
 * sub_4E22A: 24x24精灵RLE解码器
 *
 * 固定24x24尺寸的精灵数据解码,用于战场角色图标、地形等
 * ============================================================================ */

/**
 * fd2_rle_blit_24x24 - 24x24精灵RLE解码 (IDA sub_4E22A)
 *
 * 解码24x24像素精灵到目标缓冲区
 *
 * @param src         源数据指针
 * @param dst         目标缓冲区
 * @param dst_stride  目标行跨度
 */
void fd2_rle_blit_24x24(const u8* src, u8* dst, int dst_stride);

/**
 * fd2_rle_blit_24x24_palette - 带调色板映射的24x24解码
 *
 * @param src          源数据指针
 * @param dst          目标缓冲区
 * @param dst_stride   目标行跨度
 * @param palette_map  调色板映射表(256字节)
 */
void fd2_rle_blit_24x24_palette(const u8* src, u8* dst, int dst_stride,
                                 const u8* palette_map);

/* ============================================================================
 * sub_4E98D变体: 地形/光标图像解码
 *
 * 用于地图地形、战场光标等特殊图像
 * ============================================================================ */

/**
 * fd2_rle_decode_terrain - 地形图像RLE解码
 *
 * @param src         源数据指针
 * @param dst         目标缓冲区
 * @param stride      目标行跨度
 */
void fd2_rle_decode_terrain(const u8* src, u8* dst, int stride);

/**
 * fd2_rle_decode_cursor - 光标图像RLE解码
 *
 * @param src         源数据指针
 * @param size        源数据大小
 * @param dst         目标缓冲区
 * @param dst_stride  目标行跨度
 * @return 0成功, -1失败
 */
int fd2_rle_decode_cursor(const u8* src, int size, u8* dst, int dst_stride);

/* ============================================================================
 * sub_36E65/sub_36F24: AFM调色板和帧数据RLE解码
 *
 * 用于ANI.DAT动画文件的调色板和帧数据
 * ============================================================================ */

/**
 * fd2_afm_rle_palette - AFM调色板RLE解码 (IDA sub_36E65)
 *
 * 解码768字节调色板数据
 *
 * @param data    源数据指针
 * @param palette 输出调色板缓冲区(768字节)
 * @return 消耗的字节数, -1失败
 */
int fd2_afm_rle_palette(const u8* data, u8* palette);

/**
 * fd2_afm_rle_frame - AFM帧数据RLE解码 (IDA sub_36F24)
 *
 * 解码64000字节帧数据
 *
 * @param data    源数据指针
 * @param frame   输出帧缓冲区(64000字节)
 * @param count   预期像素数
 * @return 消耗的字节数, -1失败
 */
int fd2_afm_rle_frame(const u8* data, u8* frame, int count);

/**
 * fd2_afm_rle_pixel_fill - AFM像素填充RLE解码 (IDA sub_36F82)
 *
 * 在特定偏移位置执行run-length填充
 *
 * @param data    源数据指针
 * @param count   填充次数
 * @param base    基础缓冲区指针
 * @param buf     工作缓冲区
 */
int fd2_afm_rle_pixel_fill(const u8* data, int count, u8* base, u8* buf);

/* ============================================================================
 * FDOTHER.DAT 专用解码器
 *
 * 用于字体、UI元素等特殊格式
 * ============================================================================ */

/**
 * fd2_rle_decode_shap - FDSHAP.DAT瓦片RLE解码
 *
 * 格式: [2B w][2B h][RLE pixel data]
 *
 * @param src         源数据(含4字节头)
 * @param src_size    源数据大小
 * @param dst         目标缓冲区
 * @param width       期望宽度
 * @param height      期望高度
 * @return 0成功, -1失败
 */
int fd2_rle_decode_shap(const u8* src, int src_size,
                        u8* dst, int width, int height);

/**
 * fd2_rle_decode_portrait - 头像RLE解码
 *
 * 用于DATO.DAT头像数据
 *
 * @param src         源数据(含4字节头)
 * @param src_size    源数据大小
 * @param dst         目标缓冲区
 * @param max_pixels  最大像素数
 * @return 解码像素数, -1失败
 */
int fd2_rle_decode_portrait(const u8* src, int src_size,
                             u8* dst, int max_pixels);

/* ============================================================================
 * 辅助函数
 * ============================================================================ */

/**
 * fd2_image_get_dimensions - 从资源数据获取图像尺寸
 *
 * @param data       数据指针
 * @param data_size  数据大小
 * @param out_w      输出宽度
 * @param out_h      输出高度
 * @return 0成功, -1失败
 */
int fd2_image_get_dimensions(const u8* data, u32 data_size,
                             int* out_w, int* out_h);

#ifdef __cplusplus
}
#endif

#endif /* FD2_RLE_H */
