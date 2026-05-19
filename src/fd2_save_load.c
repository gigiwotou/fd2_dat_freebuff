/**
 * FD2.SAV存档解析系统
 * 
 * 基于IDA sub_10010 (加载存档), sub_4DF28 (解密), sub_4DF09 (校验) 1:1实现
 */

#include "fd2_save_load.h"
#include "fd2_globals.h"
#include "fd2_state_machine.h"
#include "fd2_data_loader.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define FD2_SAV_SIZE 22987
#define FD2_SAV_FIELD_DATA_OFFSET 0
#define FD2_SAV_FIELD_DATA_SIZE 2211
#define FD2_SAV_SCENE_DATA_OFFSET 2211
#define FD2_SAV_SCENE_DATA_SIZE 2560
#define FD2_SAV_CHAR_DATA_OFFSET 4771
#define FD2_SAV_CHAR_DATA_SIZE 7680
#define FD2_SAV_STATE_DATA_OFFSET 12451
#define FD2_SAV_STATE_DATA_SIZE 32
#define FD2_SAV_STATE_VARS_OFFSET 12483
#define FD2_SAV_BATTLE_SLOTS_OFFSET 12501
#define FD2_SAV_CHECKSUM_OFFSET 22983

/* 16位循环左移 */
static u16 rol16(u16 value, int shift) {
    shift &= 15;
    return (value << shift) | (value >> (16 - shift));
}

/*
 * fd2_sav_decrypt: 解密存档数据 (对应原游戏 sub_4DF28)
 *
 * 解密算法:
 *   1. 初始化密钥 n165 = 165
 *   2. 对于每个字节:
 *      - n165 += 0x9014
 *      - n165 = rol16(n165, 3)
 *      - data[i] ^= (n165 & 0xFF)
 */
void fd2_sav_decrypt(u8* data, int size) {
    u16 n165 = 165;
    int i;
    
    for (i = 0; i < size; i++) {
        n165 = (u16)(n165 + 0x9014);
        n165 = rol16(n165, 3);
        data[i] ^= (u8)(n165 & 0xFF);
    }
}

/*
 * fd2_sav_verify: 验证存档校验和 (对应原游戏 sub_4DF09)
 *
 * 校验算法:
 *   对前 (size - 4) 字节求和
 */
u32 fd2_sav_verify(const u8* data, int size) {
    u32 checksum = 0;
    int count = size - 4;
    int i;
    
    for (i = 0; i < count; i++) {
        checksum += data[i];
    }
    
    return checksum;
}

/*
 * fd2_sav_load: 加载FD2.SAV存档文件 (对应原游戏 sub_10010)
 *
 * 原游戏流程 (1:1 复制):
 *   1. malloc(22987)
 *   2. fopen("FD2.SAV", "rb")
 *   3. fread(buffer, 1, 22987, file)
 *   4. fclose(file)
 *   5. sub_4DF28(buffer, 22987)  // 解密
 *   6. 校验: sub_4DF09(buffer, 22987) == buffer[22983]
 *   7. memmove(n8_3, buffer + 2211, 2560)
 *   8. 加载各种DAT文件
 *   9. 设置全局变量
 *   10. free(buffer)
 */
int fd2_sav_load(const char* filename, fd2_sav_data_t* sav) {
    FILE* file;
    u8* buffer;
    size_t bytes_read;
    u32 calc_checksum;
    u32 file_checksum;
    
    if (!filename || !sav) {
        return -1;
    }
    
    /* 分配缓冲区 (对应原游戏 0x1002e: malloc(22987)) */
    buffer = (u8*)malloc(FD2_SAV_SIZE);
    if (!buffer) {
        fprintf(stderr, " Out of Memory !!!\n");
        return -1;
    }
    
    /* 打开存档文件 (对应原游戏 0x10074: fopen("FD2.SAV", "rb")) */
    file = fopen(filename, "rb");
    if (!file) {
        fprintf(stderr, "fd2_sav_load: cannot open %s\n", filename);
        free(buffer);
        return -1;
    }
    
    /* 读取存档数据 (对应原游戏 0x10082: fread) */
    bytes_read = fread(buffer, 1, FD2_SAV_SIZE, file);
    fclose(file);
    
    if (bytes_read != FD2_SAV_SIZE) {
        fprintf(stderr, "fd2_sav_load: invalid save size (%zu bytes, expected %d)\n", 
                bytes_read, FD2_SAV_SIZE);
        free(buffer);
        return -1;
    }
    
    /* 解密存档数据 (对应原游戏 0x10099: sub_4DF28) */
    fd2_sav_decrypt(buffer, FD2_SAV_SIZE);
    
    /* 验证校验和 (对应原游戏 0x100bb-0x10105) */
    calc_checksum = fd2_sav_verify(buffer, FD2_SAV_SIZE);
    file_checksum = *(u32*)(buffer + FD2_SAV_CHECKSUM_OFFSET);
    
    if (calc_checksum != file_checksum) {
        fprintf(stderr, "fd2_sav_load: checksum mismatch (calc=0x%X, file=0x%X)\n",
                calc_checksum, file_checksum);
        /* 注意: 原游戏在这里会显示错误信息并退出 */
        free(buffer);
        return -1;
    }
    
    /* 复制存档数据到结构体 */
    memcpy(sav->fieldData, buffer + FD2_SAV_FIELD_DATA_OFFSET, FD2_SAV_FIELD_DATA_SIZE);
    memcpy(sav->sceneData, buffer + FD2_SAV_SCENE_DATA_OFFSET, FD2_SAV_SCENE_DATA_SIZE);
    memcpy(sav->charData, buffer + FD2_SAV_CHAR_DATA_OFFSET, FD2_SAV_CHAR_DATA_SIZE);
    memcpy(sav->stateData, buffer + FD2_SAV_STATE_DATA_OFFSET, FD2_SAV_STATE_DATA_SIZE);
    
    /* 复制战场存档Slots (对应原游戏 sub_29BCB 遍历的数据) */
    memcpy(sav->battleSlots, buffer + FD2_SAV_BATTLE_SLOTS_OFFSET, sizeof(sav->battleSlots));
    
    /* 读取状态变量 (对应原游戏 0x103df-0x10446) */
    sav->n999 = buffer[FD2_SAV_STATE_VARS_OFFSET + 0];      /* +12483 */
    sav->n6_0 = buffer[FD2_SAV_STATE_VARS_OFFSET + 1];      /* +12484 */
    sav->n17 = buffer[FD2_SAV_STATE_VARS_OFFSET + 2];       /* +12485 */
    sav->qword_53AA9_lo = buffer[FD2_SAV_STATE_VARS_OFFSET + 3];  /* +12486 */
    sav->qword_53AA9_hi = buffer[FD2_SAV_STATE_VARS_OFFSET + 4];  /* +12487 */
    sav->qword_53AB1_lo = buffer[FD2_SAV_STATE_VARS_OFFSET + 5];  /* +12488 */
    sav->qword_53AB1_hi = buffer[FD2_SAV_STATE_VARS_OFFSET + 6];  /* +12489 */
    sav->n10 = buffer[FD2_SAV_STATE_VARS_OFFSET + 7];       /* +12490 */
    sav->n2 = buffer[FD2_SAV_STATE_VARS_OFFSET + 8];        /* +12491 */
    sav->n16_1 = buffer[FD2_SAV_STATE_VARS_OFFSET + 9];     /* +12492 */
    sav->n999_0 = *(u32*)(buffer + FD2_SAV_STATE_VARS_OFFSET + 10);  /* +12493 */
    sav->byte_53AF9 = buffer[FD2_SAV_STATE_VARS_OFFSET + 14];  /* +12497 */
    sav->byte_51AAB = buffer[FD2_SAV_STATE_VARS_OFFSET + 15];  /* +12498 */
    sav->n127 = buffer[FD2_SAV_STATE_VARS_OFFSET + 16];     /* +12499 */
    sav->byte_51E62 = buffer[FD2_SAV_STATE_VARS_OFFSET + 17];  /* +12500 */
    sav->checksum = file_checksum;
    
    /* 释放缓冲区 */
    free(buffer);
    
    printf("fd2_sav_load: loaded successfully (scene=%d, chars=%d)\n",
           sav->n17, sav->n6_0);
    
    /* 打印battleSlots信息 */
    printf("fd2_sav_load: battleSlots:\n");
    for (int slot = 0; slot < 4; slot++) {
        printf("  slot %d: n17=%d, n16_1=%d, n999_0=%u\n",
               slot,
               sav->battleSlots[slot].n17,
               sav->battleSlots[slot].n16_1,
               sav->battleSlots[slot].n999_0);
    }
    
    return 0;
}

/*
 * fd2_sav_apply: 应用存档数据到全局变量 (对应原游戏 sub_10010 中的变量设置)
 *
 * 根据IDA反编译的sub_10010函数，设置所有全局变量
 */
int fd2_sav_apply(const fd2_sav_data_t* sav) {
    if (!sav) {
        return -1;
    }
    
    /* 对应原游戏 0x10147: n17 = buffer[12485] */
    g_n17 = sav->n17;
    
    /* 对应原游戏 0x1029a: n6_0 = buffer[12484] */
    g_n6_0 = sav->n6_0;
    
    /* 对应原游戏 0x103df: n999 = buffer[12483] */
    g_n999 = sav->n999;
    
    /* 对应原游戏 0x103e8-0x103f1: qword_53AA9 */
    g_qword_53AA9_lo = sav->qword_53AA9_lo;
    g_qword_53AA9_hi = sav->qword_53AA9_hi;
    
    /* 对应原游戏 0x103fa-0x10403: qword_53AB1 */
    g_qword_53AB1_lo = sav->qword_53AB1_lo;
    g_qword_53AB1_hi = sav->qword_53AB1_hi;
    
    /* 对应原游戏 0x1040c-0x10446: 其他变量 */
    g_n10 = sav->n10;
    g_n2 = sav->n2;
    g_n16_1 = sav->n16_1;
    g_n999_0 = sav->n999_0;
    g_byte_53AF9 = sav->byte_53AF9;
    g_byte_51AAB = sav->byte_51AAB;
    g_n127 = sav->n127;
    g_byte_51E62 = sav->byte_51E62;
    
    printf("fd2_sav_apply: applied save data (scene=%d, chars=%d, n999=%d)\n",
           g_n17, g_n6_0, g_n999);
    
    return 0;
}

/*
 * fd2_sav_continue_load: Continue选项加载存档 (对应原游戏 sub_25EBB:0x25f42)
 *
 * IDA原始代码 (sub_25EBB:0x25f42):
 *   if ( v6 != 1 )  // v6 != 1 表示选择了 Continue
 *   {
 *     sub_25977(v6, a2, n99, a3, -1, 0);  // 停止当前音乐
 *     sub_10010(v18, a2, a3, n99, a5);    // 调用 sub_10010 加载存档
 *     sub_25977((unsigned __int8)byte_51E63[n17], a2, n99, a3, 
 *         (unsigned __int8)byte_51E63[n17], 0);  // 播放场景音乐
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
int fd2_sav_continue_load(const char* filename, fd2_sav_data_t* sav) {
    int ret;
    
    /* 对应原游戏 sub_25EBB:0x26130: sub_10010() */
    ret = fd2_sav_load(filename, sav);
    if (ret != 0) {
        fprintf(stderr, "fd2_sav_continue_load: failed to load save file\n");
        return -1;
    }
    
    /* 对应原游戏 sub_25EBB:0x26144: sub_25977(byte_51E63[n17], 0) */
    /* 播放场景音乐 (byte_51E63[n17]) */
    /* 注意: 实际音乐播放需要实现 sub_25977 函数 */
    printf("fd2_sav_continue_load: playing scene music (scene=%d)\n", sav->n17);
    
    /* 对应原游戏 sub_25EBB:0x26144: return 0 */
    return 0;
}
