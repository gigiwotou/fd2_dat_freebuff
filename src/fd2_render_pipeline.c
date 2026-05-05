/**
 * FD2 绘制管线函数实现
 * 基于原游戏 (FD2.EXE) 的IDA反汇编代码1:1实现
 * 
 * 原游戏核心绘制函数:
 * - sub_4EBFF(): 正向位块传输 (0x4EBFF)
 * - sub_4EC31(): 反向位块传输 (0x4EC31)
 * - sub_4EC66(): 获取下一个像素值 (0x4EC66)
 * - sub_4ED7A(): 字符/精灵渲染 (0x4ED7A)
 * - sub_11D40(): VGA调色板设置 (0x11D40)
 * - sub_15F84(): 文本/UI渲染引擎 (0x15F84)
 * - sub_19953(): 场景渲染管线 (0x19953)
 * - sub_4ED34(): 颜色叠加 (0x4ED34)
 * - sub_11EB0(): 区域更新 (0x11EB0)
 */

#include "fd2_render_pipeline.h"
#include "fd2_globals.h"
#include "fd2_scenes.h"
#include "fd2_data_loader.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ========================================================================
 * sub_4EC66: 获取下一个像素值 (原游戏 0x4EC66)
 *
 * 原游戏逻辑:
 *   这是一个空函数 (nullsub), 实际像素值通过AL寄存器传递
 *   在sub_4EBFF/sub_4EC31中, 像素值从源数据读取后放在AL中
 *   然后调用sub_4EC66 (可能是为了预留钩子)
 *
 * 当前实现: 直接返回传入的像素值
 * ======================================================================== */
static inline u8 fd2_get_next_pixel(u8 pixel) {
    /* 原游戏: sub_4EC66是空函数, 直接返回AL */
    return pixel;
}

/* ========================================================================
 * sub_4EBFF: 正向位块传输 (原游戏 0x4EBFF)
 *
 * 原游戏逻辑 (1:1 复制):
 *   v4 = *a2;           // 宽度
 *   v5 = a2[1];         // 高度
 *   do {
 *     v8 = a1;          // 保存行首
 *     do {
 *       *a1++ = sub_4EC66(v7);
 *       --v4;
 *     } while (v4);
 *     a1 = &v8[a3];     // 下一行
 *     --v5;
 *   } while (v5);
 *
 * 源数据格式: [width:2][height:2][pixel_data...]
 * ======================================================================== */
void fd2_blit_forward(u8* dest, const u8* source, int lineSpan) {
    if (!dest || !source) return;

    /* 读取宽高 (小端序) */
    u16 width = *(const u16*)(source + 0);
    u16 height = *(const u16*)(source + 2);

    /* 像素数据从+4字节开始 */
    const u8* src_data = source + 4;

    u8* row_start;
    u16 y;
    for (y = 0; y < height; y++) {
        row_start = dest;

        u16 x;
        for (x = 0; x < width; x++) {
            u8 pixel = *src_data++;
            pixel = fd2_get_next_pixel(pixel);
            *dest++ = pixel;
        }

        /* 移动到下一行 */
        dest = row_start + lineSpan;
    }
}

/* ========================================================================
 * sub_4EC31: 反向位块传输 (原游戏 0x4EC31)
 *
 * 原游戏逻辑 (1:1 复制):
 *   与sub_4EBFF相同, 但:
 *   *dest-- = pixel;  // 从右到左写入 (镜像)
 *
 * 用于实现水平镜像效果
 * ======================================================================== */
void fd2_blit_reverse(u8* dest, const u8* source, int lineSpan) {
    if (!dest || !source) return;

    /* 读取宽高 (小端序) */
    u16 width = *(const u16*)(source + 0);
    u16 height = *(const u16*)(source + 2);

    /* 像素数据从+4字节开始 */
    const u8* src_data = source + 4;

    u8* row_start;
    u16 y;
    for (y = 0; y < height; y++) {
        row_start = dest;

        u16 x;
        for (x = 0; x < width; x++) {
            u8 pixel = *src_data++;
            pixel = fd2_get_next_pixel(pixel);
            *dest-- = pixel;  /* 从右到左 */
        }

        /* 移动到下一行 */
        dest = row_start + lineSpan;
    }
}

/* ========================================================================
 * sub_4ED7A: 字符/精灵渲染 (原游戏 0x4ED7A, 大小0xAB)
 *
 * 原游戏逻辑 (1:1 复制):
 *   1. FDOTHER_DAT__1 = fdotherData
 *   2. 如果flags非零, 先填充背景:
 *      for (i=0; i<16; i++) {
 *        memset32(screenPtr, fillColor, 4);
 *        screenPtr += lineSpan;
 *      }
 *   3. 如果charIndex != 10 (空格):
 *      glyphData = FDOTHER_DAT__1 + 32 * charIndex
 *      for (row=0; row<16; row++) {
 *        row = *glyphData++;
 *        row = 字节交换(row);  // HI/LO互换
 *        for (bit=0; bit<16; bit++) {
 *          carry = __CFSHL__(row, 1);  // 左移检查进位
 *          row *= 2;
 *          if (carry) {
 *            *screenPtr = arg10_1;           // 前景色
 *            screenPtr[lineSpan-1] = arg14_1; // 右边缘背景
 *            screenPtr[lineSpan] = arg14_1;   // 下一行背景
 *          }
 *          ++screenPtr;
 *        }
 *        screenPtr = linePtr + lineSpan;
 *      }
 *
 * 字符数据格式: 16行 x 2字节/行 = 32字节/字符
 * 每行16位, 位=1表示前景色, 位=0表示背景色
 * ======================================================================== */
void fd2_render_char_glyph(const u8* fdother_dat, int char_index,
                           u8* screen_buf, int screen_offset,
                           int lineSpan, u8 fg_color, u8 bg_color, int flags) {
    if (!fdother_dat || !screen_buf) return;

    /* 安全检查 */
    if (screen_offset < 0 || screen_offset >= FD2_SCREEN_SIZE) return;

    u8* screen_ptr = screen_buf + screen_offset;

    /* 阶段1: 如果flags非零, 先填充背景 (16行, 每行16字节) */
    if (flags) {
        u8* fill_ptr = screen_ptr;
        u8 height = 16;
        do {
            /* 边界检查 */
            int fill_offset = (int)(fill_ptr - screen_buf);
            if (fill_offset >= (FD2_SCREEN_SIZE - (int)lineSpan)) break;
            memset(fill_ptr, 0, 16);  /* 填充16字节背景 */
            fill_ptr += lineSpan;
            --height;
        } while (height);
    }

    /* 阶段2: 渲染字符 (如果不是空格, 原游戏中10是空格索引) */
    if (char_index != 10) {
        /* 从FDOTHER.DAT加载字形数据 */
        /* 每个字符32字节 = 16行 x 2字节 */
        const u16* glyph_data = (const u16*)(fdother_dat + 32 * char_index);

        u8* line_ptr = screen_ptr;
        u8 fg = fg_color;
        u8 bg = bg_color;
        u8 height = 16;

        do {
            /* 边界检查 */
            int line_offset = (int)(line_ptr - screen_buf);
            if (line_offset >= (FD2_SCREEN_SIZE - (int)(lineSpan * 2))) break;

            /* 读取一行字形数据 (16位) */
            u16 row = *glyph_data++;

            /* 字节交换 (原游戏: HIBYTE/LOBYTE互换) */
            row = ((row & 0xFF) << 8) | ((row >> 8) & 0xFF);

            u8* scan_ptr = line_ptr;
            u8 width = 16;

            do {
                /* 左移检查进位 (原游戏: __CFSHL__) */
                int carry = (row & 0x8000) ? 1 : 0;
                row <<= 1;

                if (carry) {
                    /* 位=1: 使用前景色 */
                    /* 边界检查 */
                    if ((size_t)(scan_ptr - screen_buf) < FD2_SCREEN_SIZE) {
                        *scan_ptr = fg;
                    }
                    /* 右边缘和下一行使用背景色 */
                    if ((size_t)(scan_ptr + lineSpan - 1 - screen_buf) < FD2_SCREEN_SIZE) {
                        *(scan_ptr + lineSpan - 1) = bg;
                    }
                    if ((size_t)(scan_ptr + lineSpan - screen_buf) < FD2_SCREEN_SIZE) {
                        *(scan_ptr + lineSpan) = bg;
                    }
                }
                ++scan_ptr;
                --width;
            } while (width);

            line_ptr += lineSpan;
            --height;
        } while (height);
    }
}

/* ========================================================================
 * sub_11D40: VGA调色板设置 (原游戏 0x11D40, 大小0xB2)
 *
 * 原游戏逻辑 (1:1 复制):
 *   while (startColor <= endColor) {
 *     outp(968, startColor);  // DAC写地址寄存器
 *     
 *     red = FDOTHER[3*startColor] - colorOffset;
 *     if (red < 0) red = 0;
 *     outp(969, red);
 *     
 *     green = FDOTHER[3*startColor+1] - colorOffset;
 *     if (green < 0) green = 0;
 *     outp(969, green);
 *     
 *     blue = FDOTHER[3*startColor+2] - colorOffset;
 *     if (blue < 0) blue = 0;
 *     outp(969, blue);
 *     
 *     ++startColor;
 *   }
 *
 * VGA DAC寄存器:
 *   端口968 (0x3C8): DAC写地址寄存器
 *   端口969 (0x3C9): DAC颜色数据寄存器 (RGB)
 *
 * 颜色格式: 每个分量6位 (0-63)
 * ======================================================================== */
void fd2_set_palette_vga(const u8* fdother_data, int start_color,
                         int end_color, int color_offset,
                         fd2_render_t* render) {
    if (!fdother_data || !render) return;

    u8 palette_8bit[FD2_PALETTE_BYTES];
    memcpy(palette_8bit, render->palette, FD2_PALETTE_BYTES);

    while (start_color <= end_color) {
        int idx = start_color * 3;

        /* 读取原始RGB并减去偏移 */
        int red = fdother_data[idx + 0] - color_offset;
        int green = fdother_data[idx + 1] - color_offset;
        int blue = fdother_data[idx + 2] - color_offset;

        /* 钳位到0 */
        if (red < 0) red = 0;
        if (green < 0) green = 0;
        if (blue < 0) blue = 0;

        /* 6位转8位 (扩展: val8 = (val6 << 2) | (val6 >> 4)) */
        palette_8bit[idx + 0] = (u8)((red << 2) | (red >> 4));
        palette_8bit[idx + 1] = (u8)((green << 2) | (green >> 4));
        palette_8bit[idx + 2] = (u8)((blue << 2) | (blue >> 4));

        ++start_color;
    }

    /* 更新SDL调色板 */
    fd2_render_set_palette_8bit(render, palette_8bit);
}

/* ========================================================================
 * sub_15F84: 文本/UI渲染引擎 (原游戏 0x15F84, 大小0x564)
 *
 * 原游戏逻辑 (简化版1:1复制):
 *   解析文本数据格式, 处理特殊标记并渲染
 *
 * 特殊标记值:
 *   -1  - 文本结束
 *   -2  - 换行 (行偏移增加)
 *   -3  - 字体切换
 *   -4  - 递归调用 (索引410)
 *   -5  - 递归调用 (索引513)
 *   -6  - 数字显示 (格式化n999_1)
 *   -17 - 加载图片1 (偏移1832)
 *   -18 - 加载图片2 (偏移36887)
 *   -19/-20 - 动态图片加载
 *   其他  - 字符索引 (渲染对应字符)
 *
 * 文本数据格式: 从FDTXT.DAT中读取索引表, 指向实际文本数据
 * 每个条目是int16_t, 指向文本数据在基址中的偏移
 * ======================================================================== */
void fd2_render_text_ui(const u8* scene_data, const u8* text_base,
                        int data_index, int screen_offset,
                        int lineSpan, u8 fg_color, u8 bg_color,
                        int flags, int refresh_flag, int arg1C,
                        fd2_render_t* render) {
    if (!text_base || !render) return;

    /* 获取文本数据指针 */
    /* 原游戏: textPtr = (int16*)(*(int16*)(textBase + 2*dataIndex) + textBase) */
    if (data_index < 0) return;

    /* 安全检查文本基址 */
    const u16* index_table = (const u16*)text_base;
    int text_data_offset = index_table[data_index];
    const s16* text_ptr = (const s16*)(text_base + text_data_offset);

    int n658255 = screen_offset;
    int line_level = 0;

    (void)scene_data;
    (void)arg1C;

    while (1) {
        /* 边界检查 */
        if (n658255 < 0 || n658255 >= FD2_SCREEN_SIZE) break;

        /* 获取当前字符/标记索引 */
        s16 char_idx = *text_ptr;

        /* 标记 -1: 文本结束 */
        if (char_idx == -1) {
            break;
        }

        /* 标记 -2: 换行 */
        if (char_idx == -2) {
            ++line_level;
            n658255 = line_level * arg1C * lineSpan + screen_offset;
            ++text_ptr;
            continue;
        }

        /* 标记 -3: 字体切换 */
        if (char_idx == -3) {
            ++line_level;
            n658255 = line_level * arg1C * lineSpan + screen_offset;
            ++text_ptr;
            continue;
        }

        /* 标记 -4: 递归调用 (索引410) */
        if (char_idx == -4) {
            /* 递归渲染文本索引410 */
            fd2_render_text_ui(scene_data, text_base, 410, n658255,
                              lineSpan, 205, 76, 74, 1, arg1C, render);
            ++text_ptr;
            continue;
        }

        /* 标记 -5: 递归调用 (索引513) */
        if (char_idx == -5) {
            /* 递归渲染文本索引513 */
            fd2_render_text_ui(scene_data, text_base, 513, n658255,
                              lineSpan, 205, 76, 74, 1, arg1C, render);
            ++text_ptr;
            continue;
        }

        /* 标记 -6: 数字显示 (显示n999_1的值) */
        if (char_idx == -6) {
            char buffer[16];
            int val = g_n999_0;
            snprintf(buffer, sizeof(buffer), "%d", val);
            int len = (int)strlen(buffer);

            int i;
            for (i = 0; i < len; i++) {
                int digit = buffer[i] - '0';
                if (digit >= 0 && digit <= 9) {
                    fd2_render_char_glyph(
                        g_FDOTHER_DAT__6, digit,
                        (u8*)g_n655360_0, n658255,
                        lineSpan, fg_color, bg_color, flags
                    );
                }
                n658255 += 16;
            }
            ++text_ptr;
            continue;
        }

        /* 标记 -17: 加载图片1 (偏移1832) - 简化版跳过 */
        if (char_idx == -17) {
            text_ptr += 2;  /* 跳过图片索引 */
            continue;
        }

        /* 标记 -18: 加载图片2 (偏移36887) - 简化版跳过 */
        if (char_idx == -18) {
            text_ptr += 2;
            continue;
        }

        /* 标记 -19/-20: 动态图片加载 - 简化版跳过 */
        if (char_idx == -19 || char_idx == -20) {
            text_ptr += 2;
            continue;
        }

        /* 默认: 渲染字符 */
        if (char_idx >= 0 && char_idx <= 255) {
            fd2_render_char_glyph(
                g_FDOTHER_DAT__6, char_idx,
                (u8*)g_n655360_0, n658255,
                lineSpan, fg_color, bg_color, flags
            );
        }

        n658255 += 16;  /* 字符宽度16像素 */
        ++text_ptr;

        /* 检查输入 (对应原游戏 sub_10620) */
        if (refresh_flag) {
            /* TODO: sub_164E8() - 刷新显示 */
        }
    }
}

/* ========================================================================
 * sub_4ED34: 颜色叠加 (原游戏 0x4ED34)
 *
 * 原游戏逻辑:
 *   将颜色数据叠加到屏幕缓冲区的特定位置
 *   用于场景多层叠加效果
 * ======================================================================== */
void fd2_overlay_color_layer(u8* screen_buf, const u8* color_data, int lineSpan) {
    if (!screen_buf || !color_data) return;

    /* 叠加256个颜色到屏幕 */
    int i;
    for (i = 0; i < 256; i++) {
        if ((size_t)(screen_buf + i - (u8*)g_n655360_0) < FD2_SCREEN_SIZE) {
            screen_buf[i] = color_data[i];
        }
    }
    (void)lineSpan;
}

/* ========================================================================
 * sub_11EB0: 区域更新 (原游戏 0x11EB0, 大小0x40)
 *
 * 原游戏逻辑 (1:1 复制):
 *   for (i = 0; i < a10; ++i) {
 *     memmove(a5, a7, a9);
 *     a5 += a6;
 *     a7 += a8;
 *   }
 *
 * 参数:
 *   dst       - 目标缓冲区
 *   dst_stride - 目标行跨度
 *   src       - 源缓冲区
 *   src_stride - 源行跨度
 *   copy_size - 每行拷贝字节数
 *   num_lines - 行数
 * ======================================================================== */
void fd2_region_update(u8* dst, int dst_stride,
                       const u8* src, int src_stride,
                       int copy_size, int num_lines) {
    if (!dst || !src) return;

    int i;
    for (i = 0; i < num_lines; i++) {
        memcpy(dst, src, copy_size);
        dst += dst_stride;
        src += src_stride;
    }
}

/* ========================================================================
 * sub_11EEE: 区域复制 (原游戏 0x11EEE)
 *
 * 原游戏逻辑:
 *   带stride的2D区域复制
 *   用于场景格式转换 (320->456字节/行)
 * ======================================================================== */
void fd2_region_copy(u8* dst, int dst_stride,
                     const u8* src, int src_stride,
                     int width, int height) {
    if (!dst || !src) return;

    int y;
    for (y = 0; y < height; y++) {
        memcpy(dst, src, width);
        dst += dst_stride;
        src += src_stride;
    }
}

/* ========================================================================
 * sub_4E381: 屏幕刷新/清理
 *
 * 原游戏逻辑:
 *   将后备缓冲区内容拷贝到渲染系统并显示
 * ======================================================================== */
void fd2_screen_refresh(fd2_state_machine_t* sm) {
    if (!sm || !g_n655360_0) return;

    /* 将后备缓冲区内容拷贝到渲染缓冲区 */
    u8* render_screen = sm->render.screen;
    memcpy(render_screen, g_n655360_0, FD2_SCREEN_SIZE);

    /* 显示 */
    fd2_render_present(&sm->render);
}

/* ========================================================================
 * sub_19953: 场景渲染管线 (原游戏 0x19953, 大小0x4A4)
 *
 * 原游戏逻辑 (1:1 复制):
 *   1. 备份后备缓冲: memmove(n655360_0, 655360, 64000)
 *   2. 格式转换: for(n200=0; n200<200; ++n200)
 *        memmove(456*(n200-4)+n655360+32900, &n655360_0[320*n200], 320)
 *   3. 如果FDFIELD_DAT__0 > 1, 进行额外处理
 *   4. 4层叠加效果循环
 *   5. 主循环:
 *      - 等待垂直同步 (sub_10620)
 *      - 更新动画帧 (每2个滴答)
 *      - 使用sub_4EBFF/sub_4EC31渲染动画
 *      - 处理键盘输入 (int386(22))
 *
 * 参数:
 *   sm - 状态机
 * 返回:
 *   退出时的按键结果
 * ======================================================================== */
int fd2_scene_render_pipeline(fd2_state_machine_t* sm) {
    if (!sm || !g_n655360_0 || !g_n655360_1) return 0;

    u8* backup_buf = (u8*)g_n655360_0;
    u8* convert_buf = (u8*)g_n655360_1;
    u8* screen_buf = sm->render.screen;

    /* 1. 备份后备缓冲到主缓冲 */
    memcpy(backup_buf, screen_buf, FD2_SCREEN_SIZE);

    /* 2. 格式转换 (320字节/行 -> 456字节/行) */
    /* 原游戏: memmove(456*(n200-4) + n655360 + 32900, &n655360_0[320*n200], 320) */
    int n200;
    for (n200 = 0; n200 < 200; n200++) {
        u8* dst = convert_buf + FD2_STRIDE_WIDE * (n200 - 4) + 32900;
        const u8* src = backup_buf + FD2_SCREEN_W * n200;

        /* 边界检查 */
        if (n200 >= 4 && dst < convert_buf + FD2_STRIDE_WIDE * FD2_SCREEN_H) {
            memcpy(dst, src, 320);
        }
    }

    /* 3. 如果场景模式>1, 进行额外处理 */
    if ((size_t)g_FDFIELD_DAT__0 > 1) {
        /* sub_1297D, sub_11EEE, sub_127A9 - 场景特效处理 */
        /* TODO: 实现这些特效函数 */
    }

    /* 4. 处理4层叠加效果 */
    int v21 = 0;
    int v22 = 0;
    int n4;
    for (n4 = 0; n4 < 4; n4++) {
        int n86 = 0;
        v21 -= 4;
        v22 += 4;

        /* 处理86行数据 */
        while (n86 < 86) {
            u8* dst = convert_buf + FD2_STRIDE_WIDE * (n86 + 108) + 32905;
            const u8* src = backup_buf + 320 * n86 + 35845;

            if (dst < convert_buf + FD2_STRIDE_WIDE * FD2_SCREEN_H) {
                memcpy(dst, src, 310);
            }
            ++n86;
        }

        /* 叠加2层颜色 */
        int n2;
        for (n2 = 0; n2 < 2; n2++) {
            /* sub_4ED34 - 颜色叠加 */
            /* TODO: 实现完整的颜色叠加 */
            (void)v21;
            (void)v22;
        }

        /* 混合处理 */
        fd2_region_update(
            convert_buf + 32904,
            456,
            convert_buf + 32904,
            456,
            312,
            192
        );
    }

    /* 5. 主渲染循环 */
    u8 v24 = 0;
    int v6 = 2;  /* 动画计时器初始值 */
    Uint32 last_tick = SDL_GetTicks();

    while (1) {
        /* 处理SDL事件 */
        SDL_Event event;
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_QUIT) {
                sm->running = 0;
                return 0;
            }
            if (event.type == SDL_KEYDOWN && !event.key.repeat) {
                int scan = event.key.keysym.scancode;
                if (scan == SDL_SCANCODE_ESCAPE || scan == SDL_SCANCODE_DELETE) {
                    g_n3_4 = 0;
                    return 0;
                }
                if (scan == SDL_SCANCODE_RETURN || scan == SDL_SCANCODE_SPACE) {
                    goto exit_loop;
                }
                if (scan == SDL_SCANCODE_LEFT) {
                    g_n4_1 = 0;
                }
                if (scan == SDL_SCANCODE_RIGHT) {
                    g_n4_1 = 1;
                }
            }
        }

        /* 检查定时器 (每2个滴答更新, 约110ms) */
        Uint32 current_tick = SDL_GetTicks();
        if (current_tick - last_tick >= 110) {
            last_tick = current_tick;

            /* 更新动画帧计数器 */
            g_n3_4++;
            if (g_n3_4 >= 4) g_n3_4 = 0;

            /* 更新场景渲染 */
            if ((size_t)g_FDFIELD_DAT__0 > 1) {
                /* sub_1297D, sub_11EEE, sub_127A9 */
            }

            /* 更新动画帧 */
            if (v24) {
                /* 使用sub_4EC31或sub_4EBFF渲染动画 */
                if (g_FDOTHER_DAT__12) {
                    u8 frame_data = *(u8*)g_FDOTHER_DAT__12;
                    const u8* img_src = (u8*)g_FDOTHER_DAT__12 + frame_data;

                    if ((size_t)g_FDFIELD_DAT__0) {
                        /* 反向渲染 */
                        if (g_n655360_0) {
                            u8* dst = backup_buf;  /* 简化: 渲染到备份缓冲 */
                            fd2_blit_reverse(dst, img_src, 320);
                        }
                    } else {
                        /* 正向渲染 */
                        if (g_n655360_0) {
                            u8* dst = backup_buf;
                            fd2_blit_forward(dst, img_src, 320);
                        }
                    }
                }

                v6 = 10;  /* 随机延迟 */
                v24 = 0;
            } else if (--v6 <= 0) {
                /* 切换动画帧 */
                if (g_FDOTHER_DAT__12) {
                    u32 frame_offset = *(u32*)((u8*)g_FDOTHER_DAT__12 + 12);
                    const u8* img_src = (u8*)g_FDOTHER_DAT__12 + frame_offset;

                    if ((size_t)g_FDFIELD_DAT__0) {
                        if (g_n655360_0) {
                            u8* dst = backup_buf;
                            fd2_blit_reverse(dst, img_src, 320);
                        }
                    } else {
                        if (g_n655360_0) {
                            u8* dst = backup_buf;
                            fd2_blit_forward(dst, img_src, 320);
                        }
                    }
                }
                v24 = 1;
            }

            /* 重新处理200行数据 */
            if ((size_t)g_FDFIELD_DAT__0 <= 1) {
                int n200_1;
                for (n200_1 = 0; n200_1 < 200; n200_1++) {
                    u8* dst = convert_buf + FD2_STRIDE_WIDE * (n200_1 - 4) + 32900;
                    const u8* src = backup_buf + FD2_SCREEN_W * n200_1;
                    if (n200_1 >= 4 && dst < convert_buf + FD2_STRIDE_WIDE * FD2_SCREEN_H) {
                        memcpy(dst, src, 320);
                    }
                }
            } else {
                int n86_1;
                for (n86_1 = 0; n86_1 < 86; n86_1++) {
                    u8* dst = convert_buf + FD2_STRIDE_WIDE * (n86_1 + 108) + 32905;
                    const u8* src = backup_buf + 320 * n86_1 + 35845;
                    if (dst < convert_buf + FD2_STRIDE_WIDE * FD2_SCREEN_H) {
                        memcpy(dst, src, 310);
                    }
                }
            }

            /* 叠加颜色层 */
            int n4_1;
            for (n4_1 = 0; n4_1 < 2; n4_1++) {
                /* sub_4ED34 - 颜色叠加 */
            }

            /* 混合处理 */
            fd2_region_update(
                convert_buf + 32904,
                456,
                convert_buf + 32904,
                456,
                312,
                192
            );

            /* 渲染到屏幕 */
            memcpy(screen_buf, backup_buf, FD2_SCREEN_SIZE);
            fd2_render_present(&sm->render);

            SDL_Delay(16);  /* ~60fps */
        }
    }

exit_loop:
    g_n3_4 = 0;
    return 0;
}
