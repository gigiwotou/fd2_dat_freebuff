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
#include "fd2_state_machine.h"
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
 * 原游戏行为 (1:1 复制):
 *   1. if (a6) free(a6);                    // 释放旧数据
 *   2. _rb_ = fopen(a5, "rb");              // 打开文件
 *   3. fseek(_rb_, 4 * a7 + 6, 0);         // 定位到索引表
 *   4. 读取8字节 (start_offset, end_offset)
 *   5. dword_53BFF = end_offset - start_offset;  // 计算大小
 *   6. v10 = malloc(dword_53BFF);           // 分配内存
 *   7. fseek(_rb_, start_offset, 0);       // 定位到数据
 *   8. fread(v10, 1, dword_53BFF, _rb_);   // 读取数据
 *   9. fclose(_rb_);
 *   10. return v10;
 *
 * 参数:
 *   filename:    文件名 (如 "FDOTHER.DAT")
 *   oldData:     旧数据指针 (需要释放)
 *   index:       资源索引
 *
 * 返回值:
 *   指向加载的数据的指针
 *
 * 全局变量:
 *   g_dword_53BFF - 加载的数据大小
 */
void* fd2_dat_load_resource(const char* filename, void* oldData, int index);

/*
 * fd2_data_load_all: 加载所有初始资源 (对应原游戏 main() 0x25BF4 中的加载序列)
 * 
 * 加载顺序 (必须1:1按原游戏顺序):
 *   1. FDOTHER.DAT 索引31 -> FDOTHER_DAT__2
 *   2. FDOTHER.DAT 索引1  -> FDOTHER_DAT__3
 *   3. FDOTHER.DAT 索引2  -> FDOTHER_DAT__4
 *   4. FDOTHER.DAT 索引3  -> FDOTHER_DAT__5
 *   5. FDOTHER.DAT 索引4  -> FDOTHER_DAT__6
 *   6. FDOTHER.DAT 索引5  -> FDOTHER_DAT__7
 *   7. FDTXT.DAT   索引0  -> FDTXT_DAT__0
 *   8. FDOTHER.DAT 索引6  -> FDOTHER_DAT__8
 *   9. malloc(32)         -> n8_0
 *   10. malloc(65536)     -> n655360_0
 *   11. malloc(2560)      -> n8_3
 */
int fd2_data_load_all(fd2_state_machine_t* sm, const char* data_dir);

/* 辅助函数: 拼接数据目录路径 */
const char* fd2_get_data_path(const char* data_dir, const char* filename);

/*
 * sub_25977: 音乐切换函数 (原游戏 0x25977)
 *
 * 原游戏签名:
 *   void __fastcall sub_25977(__int32 a1, int a2, int a3, int a4, int n16, int arg4)
 *
 * 参数:
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
 *
 * 注意: 类型定义已在 fd2_state_machine.h 中声明，这里仅引用
 */

/* fd2_scene_check_fn 已在 fd2_state_machine.h 中定义 */

extern fd2_scene_check_fn funcs_1197B[30];

/* 初始化场景检查数组 */
void fd2_scene_check_init(void);

/* 默认检查函数 */
int scene_check_default(void);

/* 数据加载辅助函数 */
int fd2_data_init(void);
void fd2_data_shutdown(void);

#endif /* FD2_DATA_LOADER_H */
