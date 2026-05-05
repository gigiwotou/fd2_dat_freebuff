#ifndef FD2_SAVE_LOAD_H
#define FD2_SAVE_LOAD_H

#include <stdint.h>

/* 类型定义 */
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;

/*
 * FD2.SAV存档解析系统 (原游戏 sub_10010)
 * 基于IDA反编译代码1:1实现
 *
 * FD2.SAV文件结构:
 * - 总大小: 22987字节
 * - [0-2210]: 字段数据 (2211字节)
 * - [2211-4770]: 场景数据缓冲区 (2560字节)
 * - [4771-12450]: 角色数据 (7680字节)
 * - [12451-12482]: 状态数据 (32字节)
 * - [12483-12500]: 存档状态变量 (18字节)
 * - [12501-22982]: 其他数据
 * - [22983-22986]: 校验和 (4字节)
 */

/* 存档数据结构 (1:1 对应原游戏) */
typedef struct {
    u8 fieldData[2211];          /* 字段数据 */
    u8 sceneData[2560];          /* 场景数据缓冲区 (偏移2211) */
    u8 charData[7680];           /* 角色数据 (偏移4771) */
    u8 stateData[32];            /* 状态数据 (偏移12451) */
    
    /* 存档状态变量 (偏移12483) */
    u8 n999;                     /* +12483 */
    u8 n6_0;                     /* +12484 角色数量 */
    u8 n17;                      /* +12485 场景ID */
    u8 qword_53AA9_lo;           /* +12486 */
    u8 qword_53AA9_hi;           /* +12487 */
    u8 qword_53AB1_lo;           /* +12488 */
    u8 qword_53AB1_hi;           /* +12489 */
    u8 n10;                      /* +12490 */
    u8 n2;                       /* +12491 */
    u8 n16_1;                    /* +12492 */
    u32 n999_0;                  /* +12493 (4字节) */
    u8 byte_53AF9;               /* +12497 */
    u8 byte_51AAB;               /* +12498 */
    u8 n127;                     /* +12499 */
    u8 byte_51E62;               /* +12500 */
    
    u8 otherData[10483];         /* 其他数据 (12501-22982) */
    u32 checksum;                /* +22983 校验和 */
} fd2_sav_data_t;

/*
 * fd2_sav_load: 加载FD2.SAV存档文件 (对应 sub_10010)
 *
 * 参数:
 *   filename: 存档文件路径
 *   sav:      输出存档数据结构
 *
 * 返回值:
 *   0=成功, -1=失败
 */
int fd2_sav_load(const char* filename, fd2_sav_data_t* sav);

/*
 * fd2_sav_decrypt: 解密存档数据 (对应 sub_4DF28)
 *
 * 参数:
 *   data: 存档数据
 *   size: 数据大小 (22987)
 */
void fd2_sav_decrypt(u8* data, int size);

/*
 * fd2_sav_verify: 验证存档校验和 (对应 sub_4DF09)
 *
 * 参数:
 *   data: 存档数据
 *   size: 数据大小
 *
 * 返回值:
 *   计算的校验和
 */
u32 fd2_sav_verify(const u8* data, int size);

/*
 * fd2_sav_apply: 应用存档数据到全局变量
 *
 * 参数:
 *   sav: 存档数据结构
 *
 * 功能:
 *   - 设置场景ID (g_n17)
 *   - 设置角色数量 (g_n6_0)
 *   - 设置所有存档状态变量
 */
int fd2_sav_apply(const fd2_sav_data_t* sav);

#endif /* FD2_SAVE_LOAD_H */
