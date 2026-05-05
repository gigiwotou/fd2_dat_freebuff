#ifndef FD2_RENDER_PIPELINE_H
#define FD2_RENDER_PIPELINE_H

#include "fd2_types.h"
#include "fd2_state_machine.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================
 * FD2 绘制管线函数 (1:1 对应原游戏IDA反汇编)
 * 
 * 原游戏绘制函数:
 * - sub_4EBFF(): 正向位块传输 (0x4EBFF)
 * - sub_4EC31(): 反向位块传输 (0x4EC31)
 * - sub_4EC66(): 获取下一个像素值 (0x4EC66)
 * - sub_4ED7A(): 字符/精灵渲染 (0x4ED7A)
 * - sub_11D40(): VGA调色板设置 (0x11D40)
 * - sub_15F84(): 文本/UI渲染引擎 (0x15F84)
 * - sub_19953(): 场景渲染管线 (0x19953)
 * - sub_2670E(): 场景特效 (0x2670E)
 * - sub_4ED34(): 颜色叠加 (0x4ED34)
 * - sub_11EB0(): 区域更新 (0x11EB0)
 * - sub_11EEE(): 区域复制 (0x11EEE)
 * - sub_4E381(): 刷新/清理 (0x4E381)
 * ======================================================================== */

/* ---- sub_4EBFF: 正向位块传输 ---- */

/*
 * 从左到右绘制图像 (标准BitBlt)
 * 对应原游戏 sub_4EBFF (地址: 0x4EBFF)
 * 
 * 原游戏逻辑:
 *   width = source[0];
 *   height = source[1];
 *   do {
 *     rowStart = dest;
 *     x = width;
 *     do {
 *       pixel = sub_4EC66();  // 获取下一个像素
 *       *dest++ = pixel;
 *       --x;
 *     } while (x);
 *     dest = &rowStart[lineSpan];
 *     --height;
 *   } while (height);
 *
 * 参数:
 *   dest     - 目标缓冲区地址 (屏幕缓冲区偏移)
 *   source   - 源图像数据 [宽, 高, 像素数据...]
 *   lineSpan - 目标行跨度 (通常320或456)
 */
void fd2_blit_forward(u8* dest, const u8* source, int lineSpan);

/* ---- sub_4EC31: 反向位块传输 ---- */

/*
 * 从右到左绘制图像 (镜像效果)
 * 对应原游戏 sub_4EC31 (地址: 0x4EC31)
 * 
 * 原游戏逻辑与sub_4EBFF相同,但:
 *   *dest-- = pixel;  // 从右到左写入 (镜像)
 *
 * 参数:
 *   dest     - 目标缓冲区地址 (指向行末)
 *   source   - 源图像数据 [宽, 高, 像素数据...]
 *   lineSpan - 目标行跨度 (通常320或456)
 */
void fd2_blit_reverse(u8* dest, const u8* source, int lineSpan);

/* ---- sub_4ED7A: 字符/精灵渲染 ---- */

/*
 * 从FDOTHER.DAT加载字形数据并渲染16x16字符
 * 对应原游戏 sub_4ED7A (地址: 0x4ED7A)
 * 
 * 原游戏逻辑:
 *   1. 如果arg18!=0, 先填充背景 (每行16字节, 16行)
 *   2. 从FDOTHER.DAT读取字符数据 (32字节/字符 = 16行x2字节)
 *   3. 逐行扫描, 每行16位, 逐位检查
 *   4. 位=1: 使用前景色, 位=0: 使用背景色
 *   5. 字符数据16位需要字节交换
 *
 * 参数:
 *   fdother_dat  - FDOTHER.DAT字体数据指针
 *   char_index   - 字符索引 (0-255)
 *   screen_buf   - 屏幕缓冲区指针
 *   screen_offset - 屏幕缓冲区偏移
 *   lineSpan     - 行跨度 (argC, 通常320)
 *   fg_color     - 前景色 (arg10, 通常205)
 *   bg_color     - 背景色 (arg14, 通常76)
 *   flags        - 标志 (arg18, 非零则填充背景)
 */
void fd2_render_char_glyph(const u8* fdother_dat, int char_index,
                           u8* screen_buf, int screen_offset,
                           int lineSpan, u8 fg_color, u8 bg_color, int flags);

/* ---- sub_11D40: VGA调色板设置 ---- */

/*
 * 通过VGA DAC端口设置调色板颜色
 * 对应原游戏 sub_11D40 (地址: 0x11D40)
 * 
 * 原游戏逻辑:
 *   while (startColor <= endColor) {
 *     outp(968, startColor);  // DAC写地址寄存器
 *     red   = FDOTHER[3*startColor] - colorOffset;
 *     green = FDOTHER[3*startColor+1] - colorOffset;
 *     blue  = FDOTHER[3*startColor+2] - colorOffset;
 *     if (red < 0) red = 0;
 *     if (green < 0) green = 0;
 *     if (blue < 0) blue = 0;
 *     outp(969, red);
 *     outp(969, green);
 *     outp(969, blue);
 *     ++startColor;
 *   }
 *
 * 参数:
 *   fdother_data - FDOTHER.DAT调色板数据 (768字节RGB)
 *   start_color  - 起始颜色索引 (0-255)
 *   end_color    - 结束颜色索引 (0-255)
 *   color_offset - 颜色偏移量 (用于淡入淡出)
 *   render       - 渲染器 (用于设置SDL调色板)
 */
void fd2_set_palette_vga(const u8* fdother_data, int start_color,
                         int end_color, int color_offset,
                         fd2_render_t* render);

/* ---- sub_15F84: 文本/UI渲染引擎 ---- */

/*
 * 解析文本数据格式并渲染到屏幕
 * 对应原游戏 sub_15F84 (地址: 0x15F84, 大小0x564)
 * 
 * 特殊标记值:
 *   -1  - 文本结束
 *   -2  - 换行
 *   -3  - 字体切换
 *   -4  - 递归调用 (索引410)
 *   -5  - 递归调用 (索引513)
 *   -6  - 数字显示 (格式化n999_1)
 *   -17 - 加载图片1 (偏移1832)
 *   -18 - 加载图片2 (偏移36887)
 *   -19/-20 - 动态图片加载
 *   其他  - 字符索引
 *
 * 参数:
 *   scene_data   - 场景数据指针 (a1)
 *   text_base    - FDTXT.DAT文本基址
 *   data_index   - 文本数据索引
 *   screen_offset - 屏幕偏移 (初始658255)
 *   lineSpan     - 行跨度 (argC, 320)
 *   fg_color     - 前景色 (205)
 *   bg_color     - 背景色 (76)
 *   flags        - 标志 (74)
 *   refresh_flag - 刷新标志 (19)
 *   arg1C        - 行级计数器乘数
 *   render       - 渲染器
 */
void fd2_render_text_ui(const u8* scene_data, const u8* text_base,
                        int data_index, int screen_offset,
                        int lineSpan, u8 fg_color, u8 bg_color,
                        int flags, int refresh_flag, int arg1C,
                        fd2_render_t* render);

/* ---- sub_19953: 场景渲染管线 ---- */

/*
 * 场景主渲染循环,包含动画和输入处理
 * 对应原游戏 sub_19953 (地址: 0x19953, 大小0x4A4)
 * 
 * 渲染流程:
 *   1. 备份后备缓冲区 (memmove)
 *   2. 格式转换 (320->456字节/行)
 *   3. 多层叠加效果 (4层)
 *   4. 主循环: 等待vsync, 更新动画, 重新渲染
 *   5. 处理键盘输入
 *
 * 参数:
 *   sm - 状态机
 * 返回:
 *   退出时的按键结果
 */
int fd2_scene_render_pipeline(fd2_state_machine_t* sm);

/* ---- sub_4E381: 屏幕刷新/清理 ---- */

/*
 * 刷新屏幕显示
 * 对应原游戏 sub_4E381
 */
void fd2_screen_refresh(fd2_state_machine_t* sm);

/* ---- sub_4ED34: 颜色叠加 ---- */

/*
 * 叠加颜色层到屏幕缓冲区
 * 对应原游戏 sub_4ED34
 */
void fd2_overlay_color_layer(u8* screen_buf, const u8* color_data, int lineSpan);

/* ---- sub_11EB0: 区域更新 ---- */

/*
 * 复制多个区域行
 * 对应原游戏 sub_11EB0
 */
void fd2_region_update(u8* dst, int dst_stride,
                       const u8* src, int src_stride,
                       int copy_size, int num_lines);

/* ---- sub_11EEE: 区域复制 ---- */

/*
 * 复制屏幕区域 (带 stride)
 * 对应原游戏 sub_11EEE
 */
void fd2_region_copy(u8* dst, int dst_stride,
                     const u8* src, int src_stride,
                     int width, int height);

#ifdef __cplusplus
}
#endif

#endif /* FD2_RENDER_PIPELINE_H */
