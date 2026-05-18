#ifndef FD2_SAVE_LOAD_H
#define FD2_SAVE_LOAD_H

#include <stdint.h>

/* 类型定义 */
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;

/*
 * FD2.SAV存档系统 (原游戏 sub_10010, sub_25EBB)
 * 基于IDA反编译代码1:1实现
 *
 * FD2.SAV文件结构:
 * - 总大小: 22987字节
 * - [0-2210]: FDFIELD_DAT__1 战场布局数据 (2211字节)
 * - [2211-4770]: n8_3 场景数据 (2560字节)
 * - [4771-(4771+80*n6_0-1)]: 角色数据 (80字节/角色)
 * - [12451-12482]: n8_0 状态数据 (32字节)
 * - [12483]: n999 (1字节)
 * - [12484]: n6_0 角色数量 (1字节)
 * - [12485]: n17 当前场景索引 (1字节)
 * - [12486-12487]: qword_53AA9 屏幕滚动位置 (2字节)
 * - [12488-12489]: qword_53AB1 屏幕滚动位置 (2字节)
 * - [12490]: n10 (1字节)
 * - [12491]: n2 (1字节)
 * - [12492]: n16_1 子场景索引 (1字节)
 * - [12493-12496]: n999_0 游戏进度 (4字节)
 * - [12497]: byte_53AF9 (1字节)
 * - [12498]: byte_51AAB (1字节)
 * - [12499]: n127 音乐相关 (1字节)
 * - [12500]: byte_51E62 (1字节)
 * - [12501-22982]: 战场存档Slots (10482字节, 4个slot)
 * - [22983-22986]: 校验和 (4字节)
 *
 * 战场存档Slot结构 (每个2600字节, 从偏移12501开始):
 * - 偏移+0-2559: n8_3 场景数据 (2560字节)
 * - 偏移+2560: n17 场景索引 (1字节)
 * - 偏移+2561: n16_1 子场景索引 (1字节)
 * - 偏移+2562-2565: n999_0 游戏进度 (4字节)
 * - 偏移+2566: byte_51AAB (1字节)
 * - 偏移+2567: byte_53AF9 (1字节)
 * - 偏移+2568: n127 (1字节)
 * - 偏移+2569: byte_51E62 (1字节)
 * - 偏移+2570-2599: 填充 (30字节)
 */

/* 战场存档Slot结构 (对应sub_25EBB) */
typedef struct {
    u8 sceneData[2560];          /* +0 场景数据 */
    u8 n17;                      /* +2560 场景索引 */
    u8 n16_1;                    /* +2561 子场景索引 */
    u32 n999_0;                  /* +2562 游戏进度 */
    u8 byte_51AAB;               /* +2566 */
    u8 byte_53AF9;               /* +2567 */
    u8 n127;                     /* +2568 */
    u8 byte_51E62;               /* +2569 */
    u8 padding[30];              /* +2570-2599 */
} fd2_battle_sav_slot_t;

/* 角色数据结构 (80字节/角色) */
typedef struct {
    u8 data[80];                 /* 角色完整数据 */
} fd2_char_data_t;

/* 存档数据结构 (1:1 对应原游戏) */
typedef struct {
    u8 fieldData[2211];          /* +0 FDFIELD_DAT__1 战场布局数据 */
    u8 sceneData[2560];          /* +2211 n8_3 场景数据 */
    
    u8 charData[7680];           /* +4771 角色数据区 (80字节/角色, 最多96个) */
    u8 stateData[32];            /* +12451 n8_0 状态数据 */
    
    /* 存档状态变量 (从偏移12483) */
    u8 n999;                     /* +12483 游戏进度标志 */
    u8 n6_0;                     /* +12484 角色数量 */
    u8 n17;                      /* +12485 当前场景索引 */
    u8 qword_53AA9_lo;           /* +12486 屏幕滚动位置 */
    u8 qword_53AA9_hi;           /* +12487 */
    u8 qword_53AB1_lo;           /* +12488 屏幕滚动位置 */
    u8 qword_53AB1_hi;           /* +12489 */
    u8 n10;                      /* +12490 */
    u8 n2;                       /* +12491 */
    u8 n16_1;                    /* +12492 子场景索引 */
    u32 n999_0;                  /* +12493 游戏进度 (4字节) */
    u8 byte_53AF9;               /* +12497 */
    u8 byte_51AAB;               /* +12498 */
    u8 n127;                     /* +12499 音乐相关 */
    u8 byte_51E62;               /* +12500 */
    
    fd2_battle_sav_slot_t battleSlots[4];  /* +12501 战场存档Slots (4个, 每个2600字节) */
    
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
 * fd2_sav_encrypt: 加密存档数据 (对应 sub_4DF28，与解密相同)
 *
 * 参数:
 *   data: 存档数据
 *   size: 数据大小 (22987)
 */
void fd2_sav_encrypt(u8* data, int size);

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
 * fd2_sav_calculate_checksum: 计算存档校验和 (对应 sub_4DF09)
 *
 * 参数:
 *   data: 存档数据 (前22983字节)
 *   size: 数据大小 (22983)
 *
 * 返回值:
 *   计算的校验和
 */
u32 fd2_sav_calculate_checksum(const u8* data, int size);

/*
 * fd2_sav_apply: 应用存档数据到全局变量 (对应 sub_10010 后半部分)
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

/*
 * fd2_sav_save: 保存FD2.SAV存档文件
 *
 * 参数:
 *   filename: 存档文件路径
 *   sav:      存档数据结构
 *
 * 功能:
 *   - 从全局变量填充存档数据
 *   - 计算校验和
 *   - 加密数据
 *   - 写入文件
 *
 * 返回值:
 *   0=成功, -1=失败
 */
int fd2_sav_save(const char* filename, const fd2_sav_data_t* sav);

/*
 * fd2_sav_continue_load: Continue选项加载存档 (对应 sub_25EBB:0x25f42)
 *
 * IDA原始代码 (sub_25EBB:0x25f42):
 *   if ( v6 != 1 )  // Continue选项
 *   {
 *     sub_25977(v6, -1, 0);              // 停止音乐
 *     sub_10010();                        // 加载存档
 *     sub_25977(byte_51E63[n17], 0);     // 播放场景音乐
 *     return 0;
 *   }
 *
 * 参数:
 *   filename: 存档文件路径
 *   sav:      输出存档数据结构
 *
 * 返回值:
 *   0=成功, -1=失败
 */
int fd2_sav_continue_load(const char* filename, fd2_sav_data_t* sav);

/*
 * fd2_battle_sav_load: 加载战场存档Slot (对应 sub_25EBB:0x26019)
 *
 * 参数:
 *   slotData: slot原始数据指针 (偏移12587 + 2600*slotIndex)
 *   sav:      输出存档数据结构
 *
 * 返回值:
 *   0=成功, -1=失败 (slot未使用)
 */
int fd2_battle_sav_load(const u8* slotData, fd2_sav_data_t* sav);

#endif /* FD2_SAVE_LOAD_H */
