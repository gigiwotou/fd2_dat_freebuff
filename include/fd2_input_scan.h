#ifndef FD2_INPUT_SCAN_H
#define FD2_INPUT_SCAN_H

#include "fd2_types.h"
#include <SDL2/SDL.h>

/*
 * 输入扫描码系统
 * 基于原游戏 (FD2.EXE) 的IDA反汇编代码1:1实现
 * 
 * 原游戏核心函数:
 * - sub_11AA8() 0x11AA8 - BIOS中断读取按键
 * - sub_117E7() 0x117E7 - 复杂输入处理
 */

/*
 * sub_11AA8: BIOS中断读取按键 (原游戏 0x11AA8, 0xA0字节)
 *
 * 原游戏行为 (1:1 复制):
 *   1. while (!sub_10620()) { sub_4E31C(); }  // 等待按键
 *   2. HIBYTE(n3) = 16;
 *   3. int386(22, &n3, &n3);                 // BIOS键盘中断
 *   4. if (HIBYTE(n3) == 224 || HIBYTE(n3) == 82) HIBYTE(n3) = 28;
 *   5. if (HIBYTE(n3) == 83) HIBYTE(n3) = 1;
 *   6. return HIBYTE(n3);
 *
 * 返回值:
 *   按键扫描码
 */
int fd2_input_get_scan_code(void);

/* SDL按键码到原游戏扫描码映射 */
typedef struct {
    SDL_Scancode sdl_key;
    int original_scan_code;
} fd2_key_mapping_t;

extern const fd2_key_mapping_t fd2_key_map[];
extern const int fd2_key_map_size;

/*
 * sub_117E7: 复杂输入处理 (原游戏 0x117E7, 0x2C1字节)
 *
 * 原游戏签名:
 *   int __usercall sub_117E7@<eax>(int a1@<edx>, int n80_1@<ebx>, int a3@<esi>,
 *                                   __int32 a4@<eax>, int a5@<ecx>, unsigned __int8 *a6@<edi>)
 *
 * 功能:
 *   1. 获取按键扫描码 (sub_11AA8)
 *   2. 处理特殊按键 (1, 44, 76 - 场景对象导航)
 *   3. 处理Enter/Space (57, 28 - 确认)
 *   4. 处理Tab (34 - 子场景切换)
 *   5. 处理方向键 (H, P, K, M - 上下左右)
 *   6. 处理其他功能键
 *   7. 调用场景完成条件检查 (funcs_1197B[n17])
 */
int fd2_input_process_key(int key_code);

/* 按键扫描码常量 (原游戏BIOS扫描码) */
#define FD2_SCAN_ESC          1
#define FD2_SCAN_ENTER        28
#define FD2_SCAN_SPACE        57
#define FD2_SCAN_TAB          15
#define FD2_SCAN_INSERT       82
#define FD2_SCAN_DELETE       83
#define FD2_SCAN_UP           72
#define FD2_SCAN_DOWN         80
#define FD2_SCAN_LEFT         75
#define FD2_SCAN_RIGHT        77
#define FD2_SCAN_EXTEND       224
#define FD2_SCAN_SEMICOLON    39
#define FD2_SCAN_COMMA        51
#define FD2_SCAN_PERIOD       52
#define FD2_SCAN_SLASH        53

/* 辅助函数 */
int fd2_sdl_to_scan_code(SDL_Scancode sdl_key);
void fd2_input_init(void);
void fd2_input_shutdown(void);

#endif /* FD2_INPUT_SCAN_H */
