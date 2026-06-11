/**
 * FD2 DAT文件加载器 - 统一管理
 *
 * 基于IDA Pro sub_111BA汇编代码1:1还原
 *
 * DAT文件格式:
 *   字节 0-5: 魔数 "LLLLLL" (6字节)
 *   字节 6-9: 资源数量 (32位小端)
 *   字节 10+:  偏移表 (每资源4字节)
 *   偏移表后: 资源数据(连续存储)
 */

#ifndef FD2_DAT_LOADER_H
#define FD2_DAT_LOADER_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef uint8_t  byte;
typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint32_t dword;

/* DAT文件魔数长度 */
#define FD2_DAT_MAGIC_LEN 6
#define FD2_DAT_MAGIC_STR "LLLLLL"
#ifndef FD2_PALETTE_BYTES
#define FD2_PALETTE_BYTES 768
#endif

/* ============================================================================
 * 文件级操作
 * ============================================================================ */

/**
 * fd2_dat_loader_load_file - 加载整个文件到内存
 *
 * @param path    文件路径
 * @param out_size 输出文件大小
 * @return 加载的数据(需free), NULL失败
 */
u8* fd2_dat_loader_load_file(const char* path, u32* out_size);

/**
 * fd2_dat_loader_load_resource - 加载DAT文件中指定资源 (IDA sub_111BA)
 *
 * @param filename     DAT文件路径
 * @param prev_buf     旧资源指针(可NULL,如果非空则自动free)
 * @param resource_idx 资源索引
 * @param out_size     输出资源大小
 * @return 加载的资源数据(需free), NULL失败
 */
u8* fd2_dat_loader_load_resource(const char* filename, byte* prev_buf,
                                  int resource_idx, dword* out_size);

/**
 * fd2_dat_loader_load_palette - 从DAT文件加载调色板(资源0或7)
 *
 * @param filename  DAT文件路径
 * @param palette   输出调色板(768字节)
 * @return 0成功, -1失败
 */
int fd2_dat_loader_load_palette(const char* filename, byte palette[768]);

/* ============================================================================
 * 内存级操作
 * ============================================================================ */

/**
 * fd2_dat_loader_parse_entries - 解析DAT文件偏移表
 *
 * @param data         DAT文件数据
 * @param data_size    数据大小
 * @param out_offsets  输出偏移表(需free,NULL表示使用格式2)
 * @param out_count    输出资源数量
 * @return 0成功, -1失败
 */
int fd2_dat_loader_parse_entries(const u8* data, u32 data_size,
                                  u32** out_offsets, int* out_count);

/**
 * fd2_dat_loader_parse_entries_format2 - 解析格式2 DAT(无count,偏移表从byte 6)
 *
 * 用于FDFIELD.DAT, FDSHAP.DAT, FDOTHER.DAT
 * 偏移表从byte 6开始,连续读取直到偏移越界
 *
 * @param data         DAT文件数据
 * @param data_size    数据大小
 * @param max_count    最大资源数
 * @param out_offsets  输出偏移表(需free)
 * @param out_count    输出实际资源数
 * @return 0成功, -1失败
 */
int fd2_dat_loader_parse_entries_format2(const u8* data, u32 data_size,
                                          int max_count,
                                          u32** out_offsets, int* out_count);

/**
 * fd2_dat_loader_get_resource - 从已加载的DAT数据中获取资源
 *
 * @param data      DAT文件数据
 * @param data_size 数据大小
 * @param offsets   偏移表
 * @param count     资源数量
 * @param index     资源索引
 * @param out_size  输出资源大小
 * @return 资源数据指针, NULL失败
 */
const u8* fd2_dat_loader_get_resource(const u8* data, u32 data_size,
                                       const u32* offsets, int count,
                                       int index, u32* out_size);

/* ============================================================================
 * 辅助函数
 * ============================================================================ */

/**
 * fd2_dat_loader_get_dimensions - 从资源数据获取图像尺寸
 *
 * @param data   资源数据(含4字节头: width[2] + height[2])
 * @param width  输出宽度
 * @param height 输出高度
 */
void fd2_dat_loader_get_dimensions(const byte* data, int* width, int* height);

/**
 * fd2_dat_loader_get_resource_count - 获取DAT文件资源数量
 *
 * @param data      DAT文件数据
 * @param data_size 数据大小(至少10字节)
 * @return 资源数量, -1失败
 */
int fd2_dat_loader_get_resource_count(const u8* data, u32 data_size);

#ifdef __cplusplus
}
#endif

#endif /* FD2_DAT_LOADER_H */
