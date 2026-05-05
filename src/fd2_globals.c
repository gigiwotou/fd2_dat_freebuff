#include "fd2_globals.h"
#include <stdlib.h>
#include <string.h>

/* ========================================================================
 * 场景控制变量 (原游戏 0x53xxx 区域)
 * ======================================================================== */

int g_n17 = 0;          /* 0x53C03 - 当前场景索引 (0-29) */
int g_n16_1 = 0;        /* 0x53BFB - 子场景索引 (0-9) */
int g_n2_0 = 0;         /* 0x53C07 - 场景状态 (0=主循环, 1=初始化, 2=场景交互) */
int g_n64 = 0;          /* 0x53C04 - 动画帧计数器 */
int g_n6_5 = 0;         /* 0x51xxx - 场景标志变量 */
int g_qword_53AA9 = 0;  /* 0x53AA9 - 屏幕滚动位置 */
int g_qword_53AB1 = 0;  /* 0x53AB1 - 屏幕滚动位置 */
int g_n5 = 0;           /* 0x53F4A - 菜单选择索引 (0-5) */
int g_n3_4 = 0;         /* 0x53F52 - 动画帧计数器 (0-3) */
int g_n3 = 0;           /* 0x53A8D - 按键扫描码 */
int g_n44 = 0;          /* sub_11AA8返回值 */
int g_n999_0 = 0;       /* 0x53BF3 - 游戏进度 */
int g_n255 = 255;       /* 特殊事件索引 (默认255) */
int g_n6_2 = -1;        /* 当前选择项 (默认-1) */

void* g_n8_0 = NULL;    /* 32字节缓冲区 */
void* g_n8_1 = NULL;    /* 场景备份缓冲区 */
void* g_n8_3 = NULL;    /* 2560字节场景数据缓冲区 */

void* g_n655360_0 = NULL;  /* 后备缓冲区 (64KB) */
void* g_n655360_1 = NULL;  /* 格式转换缓冲区 (456字节/行) */

/* ========================================================================
 * 场景标志变量 (原游戏 0x51xxx, 0x52xxx 区域)
 * ======================================================================== */

int g_byte_51AAC = 0;           /* 0x51AAC - 场景激活标志 */
char g_byte_51E63[30] = {0};    /* 0x51E63 - 场景音乐ID映射表 */
char g_byte_523E7[30] = {0};    /* 0x523E7 - 特殊场景标志 */

unsigned char g_byte_52375[180] = {0};  /* 0x52375 - 光标Y坐标表 (30场景*6菜单项) */
unsigned char g_byte_52363[180] = {0};  /* 0x52363 - 光标X坐标表 (30场景*6菜单项) */

/* ========================================================================
 * 资源指针变量 (原游戏数据段)
 * ======================================================================== */

/* FDOTHER.DAT */
void* g_FDOTHER_DAT__2 = NULL;   /* 索引31 */
void* g_FDOTHER_DAT__3 = NULL;   /* 索引1 */
void* g_FDOTHER_DAT__4 = NULL;   /* 索引2 */
void* g_FDOTHER_DAT__5 = NULL;   /* 索引3 */
void* g_FDOTHER_DAT__6 = NULL;   /* 索引4 */
void* g_FDOTHER_DAT__7 = NULL;   /* 索引5 */
void* g_FDOTHER_DAT__8 = NULL;   /* 索引6 */
void* g_FDOTHER_DAT__11 = NULL;  /* 索引11 */
void* g_FDOTHER_DAT__12 = NULL;  /* 索引12 */
void* g_FDOTHER_DAT__13 = NULL;  /* 索引13 */

/* FDTXT.DAT */
void* g_FDTXT_DAT__0 = NULL;

/* 图形数据 */
void* g_FDSHAP_DAT = NULL;
void* g_FDFIELD_DAT__0 = NULL;
void* g_FDFIELD_DAT__1 = NULL;
void* g_FDICON_DAT = NULL;

/* 其他数据段变量 */
int g_dword_53F56 = 0;
void* g_dword_53A61 = NULL;
int g_dword_53BDF = 0;
int g_dword_53AE9 = 0;
int g_n4_1 = 0;
int g_n6_0 = 0;
int g_byte_51A42 = 0;
void* g_dword_53A45 = NULL;
void* g_dword_53A55 = NULL;
void* g_dword_53F5A = NULL;
void* g_dword_53F66 = NULL;
int g_dword_53BFB = 0;
int g_dword_53BF7 = 0;
int g_dword_53A51 = 0;
int g_dword_53EEC = 0;
int g_dword_53EC8 = 0;
int g_n3_3 = 0;
void* g_n7 = NULL;

/* 存档状态变量 (对应sub_10010) */
int g_n999 = 0;              /* 0x53C02 */
int g_n10 = 0;               /* 0x53C09 */
int g_n2 = 0;                /* 0x53C0A */
int g_n127 = 0;              /* 0x53C0E */
int g_qword_53AA9_lo = 0;    /* 0x53AA9 低字节 */
int g_qword_53AA9_hi = 0;    /* 0x53AA9 高字节 */
int g_qword_53AB1_lo = 0;    /* 0x53AB1 低字节 */
int g_qword_53AB1_hi = 0;    /* 0x53AB1 高字节 */
int g_byte_53AF9 = 0;        /* 0x53AF9 */
int g_byte_51AAB = 0;        /* 0x51AAB */
int g_byte_51E62 = 0;        /* 0x51E62 */

int g_dword_53ED8 = 0;
int g_dword_53ED0 = 0;
int g_dword_53EDC = 0;
int g_dword_53EE4 = 0;
int g_dword_53EE8 = 0;

int g_byte_53EF1 = 0;

u32 g_dword_53BFF = 0;

/* ========================================================================
 * BIOS定时器
 * ======================================================================== */

u16 g_bios_tick_base = 0;
u16 g_bios_tick_current = 0;

/* SDL退出标志 */
int g_sdl_quit_requested = 0;

void fd2_request_quit(void) {
    g_sdl_quit_requested = 1;
}

/* ========================================================================
 * 初始化/清理函数
 * ======================================================================== */

void fd2_globals_init(void) {
    g_n17 = 0;
    g_n16_1 = 0;
    g_n2_0 = 0;
    g_n5 = 0;
    g_n3_4 = 0;
    g_n3 = 0;
    g_n44 = 0;
    g_n999_0 = 0;
    g_n255 = 255;
    g_n6_2 = -1;

    g_n8_0 = NULL;
    g_n8_1 = NULL;
    g_n8_3 = NULL;

    /* 分配后备缓冲区 (64KB) - 对应原游戏 n655360_0 */
    if (!g_n655360_0) {
        g_n655360_0 = calloc(1, FD2_SCREEN_SIZE);
    }

    /* 分配格式转换缓冲区 (456字节/行 * 200行) - 对应原游戏 n655360_1 */
    if (!g_n655360_1) {
        g_n655360_1 = calloc(1, FD2_STRIDE_WIDE * FD2_SCREEN_H);
    }

    /* 分配2560字节场景数据缓冲区 - 对应原游戏 n8_3 */
    if (!g_n8_3) {
        g_n8_3 = calloc(1, 2560);
    }

    g_byte_51AAC = 0;
    memset(g_byte_51E63, 0, sizeof(g_byte_51E63));
    memset(g_byte_523E7, 0, sizeof(g_byte_523E7));
    memset(g_byte_52375, 0, sizeof(g_byte_52375));
    memset(g_byte_52363, 0, sizeof(g_byte_52363));

    g_FDOTHER_DAT__2 = NULL;
    g_FDOTHER_DAT__3 = NULL;
    g_FDOTHER_DAT__4 = NULL;
    g_FDOTHER_DAT__5 = NULL;
    g_FDOTHER_DAT__6 = NULL;
    g_FDOTHER_DAT__7 = NULL;
    g_FDOTHER_DAT__8 = NULL;
    g_FDOTHER_DAT__12 = NULL;
    g_FDOTHER_DAT__13 = NULL;

    g_FDTXT_DAT__0 = NULL;
    g_FDSHAP_DAT = NULL;
    g_FDFIELD_DAT__1 = NULL;
    g_FDICON_DAT = NULL;

    g_dword_53F56 = 0;
    g_dword_53ED8 = 0;
    g_dword_53ED0 = 0;
    g_dword_53EDC = 0;
    g_dword_53EE4 = 0;
    g_dword_53EE8 = 0;
    g_byte_53EF1 = 0;
    g_dword_53BFF = 0;

    g_n999 = 0;
    g_n10 = 0;
    g_n2 = 0;
    g_n127 = 0;
    g_qword_53AA9_lo = 0;
    g_qword_53AA9_hi = 0;
    g_qword_53AB1_lo = 0;
    g_qword_53AB1_hi = 0;
    g_byte_53AF9 = 0;
    g_byte_51AAB = 0;
    g_byte_51E62 = 0;

    g_bios_tick_base = 0;
    g_bios_tick_current = 0;
}

void fd2_globals_shutdown(void) {
    /* 释放缓冲区 */
    if (g_n8_0) { free(g_n8_0); g_n8_0 = NULL; }
    if (g_n8_1) { free(g_n8_1); g_n8_1 = NULL; }
    if (g_n8_3) { free(g_n8_3); g_n8_3 = NULL; }
    if (g_n655360_0) { free(g_n655360_0); g_n655360_0 = NULL; }
    if (g_n655360_1) { free(g_n655360_1); g_n655360_1 = NULL; }

    /* 释放资源指针 */
    if (g_FDOTHER_DAT__2) { free(g_FDOTHER_DAT__2); g_FDOTHER_DAT__2 = NULL; }
    if (g_FDOTHER_DAT__3) { free(g_FDOTHER_DAT__3); g_FDOTHER_DAT__3 = NULL; }
    if (g_FDOTHER_DAT__4) { free(g_FDOTHER_DAT__4); g_FDOTHER_DAT__4 = NULL; }
    if (g_FDOTHER_DAT__5) { free(g_FDOTHER_DAT__5); g_FDOTHER_DAT__5 = NULL; }
    if (g_FDOTHER_DAT__6) { free(g_FDOTHER_DAT__6); g_FDOTHER_DAT__6 = NULL; }
    if (g_FDOTHER_DAT__7) { free(g_FDOTHER_DAT__7); g_FDOTHER_DAT__7 = NULL; }
    if (g_FDOTHER_DAT__8) { free(g_FDOTHER_DAT__8); g_FDOTHER_DAT__8 = NULL; }
    if (g_FDOTHER_DAT__12) { free(g_FDOTHER_DAT__12); g_FDOTHER_DAT__12 = NULL; }
    if (g_FDOTHER_DAT__13) { free(g_FDOTHER_DAT__13); g_FDOTHER_DAT__13 = NULL; }

    if (g_FDTXT_DAT__0) { free(g_FDTXT_DAT__0); g_FDTXT_DAT__0 = NULL; }
    if (g_FDSHAP_DAT) { free(g_FDSHAP_DAT); g_FDSHAP_DAT = NULL; }
    if (g_FDFIELD_DAT__1) { free(g_FDFIELD_DAT__1); g_FDFIELD_DAT__1 = NULL; }
    if (g_FDICON_DAT) { free(g_FDICON_DAT); g_FDICON_DAT = NULL; }

    fd2_globals_init();
}
