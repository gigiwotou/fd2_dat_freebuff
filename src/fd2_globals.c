#include "fd2_globals.h"
#include <stdlib.h>
#include <string.h>

/* ========================================================================
 * 场景控制变量 (原游戏 0x53xxx 区域)
 * ======================================================================== */

int g_n17 = 0;          /* 0x53C03 - 当前场景索引 (0-29) */
int g_n16_1 = 0;        /* 0x53BFB - 子场景索引 (0-9) */
int g_n2_0 = 0;         /* 0x53C07 - 场景状态 (0=主循环, 1=初始化, 2=场景交互) */
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

/* ========================================================================
 * 资源指针变量 (原游戏数据段)
 * ======================================================================== */

void* g_FDOTHER_DAT__2 = NULL;
void* g_FDOTHER_DAT__3 = NULL;
void* g_FDOTHER_DAT__4 = NULL;
void* g_FDOTHER_DAT__5 = NULL;
void* g_FDOTHER_DAT__6 = NULL;
void* g_FDOTHER_DAT__7 = NULL;
void* g_FDOTHER_DAT__8 = NULL;
void* g_FDOTHER_DAT__12 = NULL;
void* g_FDOTHER_DAT__13 = NULL;

void* g_FDTXT_DAT__0 = NULL;

void* g_FDSHAP_DAT = NULL;
void* g_FDFIELD_DAT__1 = NULL;
void* g_FDICON_DAT = NULL;

int g_dword_53F56 = 0;

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

    g_n655360_0 = NULL;
    g_n655360_1 = NULL;

    g_byte_51AAC = 0;
    memset(g_byte_51E63, 0, sizeof(g_byte_51E63));
    memset(g_byte_523E7, 0, sizeof(g_byte_523E7));

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
