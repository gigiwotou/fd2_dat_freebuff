#ifndef FD2_DATA_LOADER_H
#define FD2_DATA_LOADER_H

/*
 * FD2 数据加载系统
 * 基于原游戏 (FD2.EXE) 的IDA反汇编代码1:1实现
 * 
 * 原游戏核心函数:
 * - sub_111BA() 0x111BA - 资源加载
 * - sub_25977() 0x25977 - 音乐切换
 */

#include "fd2_types.h"
#include "fd2_globals.h"
#include <stdio.h>

/* 类型别名 */
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int8_t s8;
typedef int16_t s16;
typedef int32_t s32;

/* 数据文件类型 */
typedef enum {
    FD2_DAT_FDOTHER,    /* FDOTHER.DAT */
    FD2_DAT_FDTXT,      /* FDTXT.DAT */
    FD2_DAT_FDFIELD,    /* FDFIELD.DAT */
    FD2_DAT_FDSHAP,     /* FDSHAP.DAT */
    FD2_DAT_ANI,        /* ANI.DAT */
    FD2_DAT_FDICON,     /* FDICON.B24 */
    FD2_DAT_DATO,       /* DATO.DAT */
    FD2_DAT_FDMUS,      /* FDMUS.DAT */
    FD2_DAT_FD2SAV,     /* FD2.SAV */
    FD2_DAT_COUNT
} fd2_dat_file_t;

/*
 * sub_111BA: 资源加载函数 (原游戏 0x111BA)
 *
 * 原游戏签名:
 *   _BYTE *__fastcall sub_111BA(__int32 a1, int a2, int a3, int a4, int a5, int a6, int a7)
 *
 * 参数:
 *   a1-a4: 寄存器参数 (EAX, EDX, ECX, EBX)
 *   a5:    文件名 (字符串指针)
 *   a6:    旧数据指针 (需要释放)
 *   a7:    资源索引
 *
 * 返回值:
 *   指向加载的数据的指针
 *
 * 全局变量:
 *   dword_53BFF - 加载的数据大小
 *
 * 注意: 函数在fd2_decoder.c中已实现，这里只是引用
 */
/* fd2_dat_load_resource已在fd2_decoder.h中声明 */

/*
 * sub_25977: 音乐切换函数 (原游戏 0x25977)
 *
 * 原游戏签名:
 *   void __fastcall sub_25977(__int32 a1, int a2, int a3, int a4, int n16, int arg4)
 *
 * 参数:
 *   a1-a4: 寄存器参数
 *   n16:   音乐ID (-1=停止, 0+=播放)
 *   arg4:  额外参数
 */
void fd2_music_switch(int n16, int arg4);

/* 辅助函数 */
void fd2_music_stop(void);
void fd2_music_play(int musicId);
int fd2_music_get_scene_music_id(int sceneId);

/*
 * funcs_1197B: 场景完成条件检查函数数组 (原游戏 0x51B19)
 *
 * 原游戏签名:
 *   int (*funcs_1197B[30])(void)
 */

typedef int (*fd2_scene_check_fn)(void);

extern fd2_scene_check_fn funcs_1197B[30];

/* 初始化场景检查数组 */
void fd2_scene_check_init(void);

/* 默认检查函数 */
int scene_check_default(void);

/* 数据加载辅助函数 */
int fd2_data_init(void);
void fd2_data_shutdown(void);

#endif /* FD2_DATA_LOADER_H */
