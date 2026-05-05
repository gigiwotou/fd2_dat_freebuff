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
