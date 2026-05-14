#ifndef FD2_GLOBALS_H
#define FD2_GLOBALS_H

/*
 * FD2 全局变量映射
 * 基于原游戏 (FD2.EXE) 的IDA反汇编代码1:1实现
 * 所有全局变量对应原游戏数据段地址
 */

#include "fd2_types.h"
#include <SDL2/SDL.h>

/* 类型别名 */
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int8_t s8;
typedef int16_t s16;
typedef int32_t s32;

/* ========================================================================
 * 场景控制变量 (原游戏 0x53xxx 区域)
 * ======================================================================== */

/* 当前场景ID (0x51E4A) */
extern int g_n17;

/* 当前子场景ID (0x53C03) */
extern int g_n16_1;

/* 动画帧计数器 (0x53C04) */
extern int g_n64;

/* 场景标志变量 (0x51AAC附近) */
extern int g_n6_5;

/* 屏幕滚动位置 (0x53AA9) - 低32位 */
extern int g_qword_53AA9;

/* 屏幕滚动位置 (0x53AB1) - 低32位 */
extern int g_qword_53AB1;

/* 场景状态标志 (0x53C07) - 0=主循环, 1=初始化, 2=场景交互 */
extern int g_n2_0;

/* 开场场景结束标志 (0x53C06) */
extern int g_n6_6;

/* 菜单选择索引 (0x53F4A) - 范围 0-5 */
extern int g_n5;

/* 动画帧计数器 (0x53F52) - 范围 0-3 */
extern int g_n3_4;

/* 按键扫描码 (0x53A8D) */
extern int g_n3;

/* 按键扫描码 (sub_11AA8返回值) */
extern int g_n44;

/* 游戏进度变量 (0x53BF3) */
extern int g_n999_0;

/* 特殊事件索引 */
extern int g_n255;

/* 当前选择项 */
extern int g_n6_2;

/* 32字节缓冲区 */
extern void* g_n8_0;

/* 场景备份缓冲区 */
extern void* g_n8_1;

/* 2560字节场景数据缓冲区 */
extern void* g_n8_3;

/* 后备缓冲区 (64KB) */
extern void* g_n655360_0;

/* 格式转换缓冲区 (456字节/行) */
extern void* g_n655360_1;

/* ========================================================================
 * 场景标志变量 (原游戏 0x51xxx, 0x52xxx 区域)
 * ======================================================================== */

/* 场景激活标志 (0x51AAC) - 0=非激活, 1=激活 */
extern int g_byte_51AAC;

/* 场景音乐ID映射表 (0x51E63) - 30个场景 */
extern char g_byte_51E63[30];

/* 特殊场景标志 (0x523E7) - 30个场景 */
extern char g_byte_523E7[30];

/* 光标Y坐标表 (0x52375) - 场景*菜单索引映射 */
extern unsigned char g_byte_52375[180];  /* 30场景 * 6菜单项 */

/* 光标X坐标表 (0x52363) - 场景*菜单索引映射 */
extern unsigned char g_byte_52363[180];  /* 30场景 * 6菜单项 */

/* ========================================================================
 * 资源指针变量 (原游戏数据段)
 * ======================================================================== */

/* FDOTHER.DAT数据指针数组 */
extern void* g_FDOTHER_DAT__2;   /* 索引31 */
extern void* g_FDOTHER_DAT__3;   /* 索引1 */
extern void* g_FDOTHER_DAT__4;   /* 索引2 */
extern void* g_FDOTHER_DAT__5;   /* 索引3 */
extern void* g_FDOTHER_DAT__6;   /* 索引4 */
extern void* g_FDOTHER_DAT__7;   /* 索引5 */
extern void* g_FDOTHER_DAT__8;   /* 索引6 */
extern void* g_FDOTHER_DAT__11;  /* 索引11 */
extern void* g_FDOTHER_DAT__12;  /* 索引12 */
extern void* g_FDOTHER_DAT__13;  /* 索引13 */

/* FDTXT.DAT文本数据 */
extern void* g_FDTXT_DAT__0;

/* 图形数据 */
extern void* g_FDSHAP_DAT;
extern void* g_FDFIELD_DAT__0;   /* 字段数据0 */
extern void* g_FDFIELD_DAT__1;   /* 字段数据1 */
extern void* g_FDICON_DAT;

/* 场景图形数据指针 */
extern int g_dword_53F56;

/* 其他数据段变量 */
extern void* g_dword_53A61;        /* 0x53A61 */
extern int g_dword_53BDF;        /* 0x53BDF */
extern int g_dword_53AE9;        /* 0x53AE9 */
extern int g_n4_1;               /* n4_1 */
extern int g_n6_0;               /* n6_0 */
extern int g_byte_51A42;         /* 0x51A42 */

/* 存档状态变量 (对应sub_10010) */
extern int g_n999;               /* 0x53C02 */
extern int g_n10;                /* 0x53C09 */
extern int g_n2;                 /* 0x53C0A */
extern int g_n127;               /* 0x53C0E */
extern int g_qword_53AA9_lo;     /* 0x53AA9 低字节 */
extern int g_qword_53AA9_hi;     /* 0x53AA9 高字节 */
extern int g_qword_53AB1_lo;     /* 0x53AB1 低字节 */
extern int g_qword_53AB1_hi;     /* 0x53AB1 高字节 */
extern int g_byte_53AF9;         /* 0x53AF9 */
extern int g_byte_51AAB;         /* 0x51AAB */
extern int g_byte_51E62;         /* 0x51E62 */

/* 资源加载大小 (0x53BFF) - sub_111BA返回值 */
extern u32 g_dword_53BFF;

/* 场景数据指针 (对应sub_10010) */
extern void* g_dword_53A51;        /* FDFIELD.DAT 3*n17 */
extern void* g_dword_53A59;        /* FDFIELD.DAT 3*n17+2 */
extern void* g_dword_53A69;        /* FDSHAP.DAT 2*n6_0+1 */

/* 音频句柄 */
extern int g_dword_53ED8;
extern int g_dword_53ED0;
extern int g_dword_53EDC;
extern int g_dword_53EE4;
extern int g_dword_53EE8;

/* 音频标志 */
extern int g_byte_53EF1;

/* 资源加载大小 (0x53BFF) - sub_111BA返回值 */
extern u32 g_dword_53BFF;

/* ========================================================================
 * BIOS定时器
 * ======================================================================== */

/* BIOS定时器滴答计数器 (原游戏 MEMORY[0x46C]) */
extern u16 g_bios_tick_base;
extern u16 g_bios_tick_current;

/* ========================================================================
 * 初始化函数
 * ======================================================================== */

/* SDL退出标志 - 用于X按钮关闭 */
extern int g_sdl_quit_requested;

/* ========================================================================
 * 调色板全局变量
 * ======================================================================== */

extern u8 g_palette_6bit[768];
extern int g_palette_loaded;
extern u8* g_current_palette_data;

/* 请求退出 (设置全局标志) */
void fd2_request_quit(void);

/* 初始化全局变量 */
void fd2_globals_init(void);

/* 清理所有全局变量 */
void fd2_globals_shutdown(void);

#endif /* FD2_GLOBALS_H */
