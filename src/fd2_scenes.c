/*
 * FD2 场景生命周期实现
 * 对应原游戏 funcs_25E23[] 和 funcs_25E3A[] 函数指针数组
 * 
 * 原游戏数据:
 * - funcs_25E3A[0] = sub_3231B (主菜单场景初始化)
 * - funcs_25E3A[1-29] = sub_21206 (默认处理)
 * - funcs_25E23[0-29] = sub_22EF6 (默认处理)
 */

#include "fd2_scenes.h"
#include "fd2_opening_intro.h"
#include "fd2_resources.h"
#include "fd2_globals.h"
#include <stdlib.h>
#include <stdio.h>

/* ========================================================================
 * sub_4E809: 场景元数据读取 (原游戏 0x4E809, 大小 0x16)
 *
 * 原游戏逻辑 (1:1 复制):
 *   return &unk_6238D + 31 * (a1 - 1);
 *
 * unk_6238D 是场景元数据表基地址，每个场景元数据占31字节
 * ======================================================================== */
typedef struct fd2_scene_metadata {
    u8 field_0;       /* +0 */
    u8 field_1;       /* +1 */
    u16 field_2_3;    /* +2 */
    u16 field_4_5;    /* +4 */
    u8 field_6;       /* +6 */
    u8 field_7;       /* +7 */
    u8 field_8;       /* +8 */
    u16 field_9_A;    /* +9 */
    u16 field_B_C;    /* +11 */
    u16 field_D_E;    /* +13 */
    u8 field_F;       /* +15 */
    u8 field_10;      /* +16 */
    u8 field_11_1F[15]; /* +17 ~ +31 */
} fd2_scene_metadata_t;

/* 场景元数据表 (原游戏 unk_6238D, 约30个场景 * 31字节) */
static fd2_scene_metadata_t g_scene_metadata_table[32] = {0};

void* fd2_scene_get_metadata(int scene_id) {
    if (scene_id < 1 || scene_id > 32) return NULL;
    return (void*)&g_scene_metadata_table[scene_id - 1];
}

/* ========================================================================
 * sub_4E838: 图标元数据读取 (原游戏 0x4E838, 大小 0x15)
 *
 * 原游戏逻辑 (1:1 复制):
 *   return &unk_61DA1 + 24 * icon_id;
 *
 * unk_61DA1 是图标元数据表基地址，每个图标元数据占24字节
 * ======================================================================== */
typedef struct fd2_icon_metadata {
    u8 field_0;       /* +0 */
    u8 field_1;       /* +1 */
    u8 field_2;       /* +2 - 宽度? */
    u16 field_3_4;    /* +3 */
    u16 field_5_6;    /* +5 */
    u16 field_7_8;    /* +7 */
    u16 field_9_A;    /* +9 */
    u16 field_B_C;    /* +11 */
    u8 field_D;       /* +13 */
    u8 field_E;       /* +14 */
    u8 field_F;       /* +15 */
    u8 field_10_17[8]; /* +16 ~ +23 */
} fd2_icon_metadata_t;

/* 图标元数据表 (原游戏 unk_61DA1) */
static fd2_icon_metadata_t g_icon_metadata_table[64] = {0};

void* fd2_icon_get_metadata(int icon_id) {
    if (icon_id < 0 || icon_id >= 64) return NULL;
    return (void*)&g_icon_metadata_table[icon_id];
}

/* ========================================================================
 * sub_4E821: 图标属性读取 (原游戏 0x4E821, 大小 0x15)
 *
 * 原游戏逻辑 (1:1 复制):
 *   return &unk_620A1 + 11 * icon_id;
 *
 * unk_620A1 是图标属性表基地址，每个图标属性占11字节
 * ======================================================================== */
typedef struct fd2_icon_props {
    u8 field_0;       /* +0 */
    u8 field_1;       /* +1 */
    u8 field_2;       /* +2 */
    u8 field_3;       /* +3 */
    u8 field_4;       /* +4 */
    u16 field_5_6;    /* +5 */
    u16 field_7_8;    /* +7 */
    u8 field_9;       /* +9 */
    u8 field_A;       /* +10 */
} fd2_icon_props_t;

/* 图标属性表 (原游戏 unk_620A1) */
static fd2_icon_props_t g_icon_props_table[64] = {0};

void* fd2_icon_get_props(int icon_id) {
    if (icon_id < 0 || icon_id >= 64) return NULL;
    return (void*)&g_icon_props_table[icon_id];
}

/* ========================================================================
 * sub_112A5: 图标加载函数 (原游戏 0x112A5, 大小 0x1BA)
 *
 * 原游戏逻辑 (1:1 复制):
 *   1. v5 = 80 * n16_1 + n8_3;  // 目标缓冲区偏移
 *   2. v6 = sub_4E838(n0x44);   // 获取图标元数据
 *   3. v17 = sub_4E821(n0x44);  // 获取图标属性
 *   4. 从图标元数据读取各种字段
 *   5. 写入目标缓冲区80字节结构
 *   6. 调用sub_1145A(n16_1)     // 图标b24处理
 *   7. ++n16_1;
 * ======================================================================== */

int fd2_icon_load(int icon_id) {
    u8* target_buf;
    u8* icon_meta;
    u8* icon_props;
    u16 v15;
    u16 v11, v12, v13, v14, v16;
    int i;
    
    /* 1. 计算目标缓冲区偏移: v5 = 80 * n16_1 + n8_3 */
    if (!g_n8_3) return -1;
    target_buf = (u8*)g_n8_3 + 80 * g_n16_1;
    
    /* 2. 获取图标元数据 */
    icon_meta = (u8*)fd2_icon_get_metadata(icon_id);
    if (!icon_meta) return -1;
    
    /* 3. 获取图标属性 */
    icon_props = (u8*)fd2_icon_get_props(icon_id);
    if (!icon_props) return -1;
    
    /* 4. 从图标元数据读取字段 */
    v15 = icon_meta[2];                                    /* 宽度/高度? */
    v11 = *(u16*)(icon_meta + 3) + (v15 - 1) * icon_props[6];
    v16 = icon_props[8] * (v15 - 1) + *(u16*)(icon_meta + 5);
    v12 = *(u16*)(icon_meta + 9);
    v14 = *(u16*)(icon_meta + 11);
    v13 = *(u16*)(icon_meta + 13);
    
    /* 5. 写入目标缓冲区80字节结构 */
    target_buf[5] = 0;
    target_buf[6] = 2;
    target_buf[7] = (u8)icon_id;
    target_buf[8] = (u8)icon_id;
    target_buf[9] = 0;
    target_buf[10] = 64;
    target_buf[11] = icon_meta[12];
    target_buf[12] = 64;
    target_buf[13] = icon_meta[13];
    
    /* 写入4个特殊字段 (14-21字节) */
    for (i = 0; i < 4; i++) {
        u8 val = icon_meta[14 + i];
        if (val == 255)
            target_buf[14 + 2 * i] = 0x80;
        else
            target_buf[14 + 2 * i] = 0;
        target_buf[15 + 2 * i] = val;
    }
    
    target_buf[22] = 0x80;
    target_buf[24] = 0x80;
    
    /* memmove(v5 + 26, v6 + 8, 4) */
    memcpy(target_buf + 26, icon_meta + 8, 4);
    
    target_buf[30] = 0;
    target_buf[31] = icon_meta[0];
    target_buf[32] = icon_meta[1];
    target_buf[33] = v15;
    
    /* memset(v5 + 34, 0, 6) */
    memset(target_buf + 34, 0, 6);
    
    target_buf[49] = -1;
    
    /* 写入计算后的字段 */
    *(u16*)(target_buf + 55) = v15 * icon_props[0] + v12;
    *(u16*)(target_buf + 57) = v15 * icon_props[2] + v14;
    target_buf[59] = icon_meta[7];
    target_buf[60] = 0;
    *(u16*)(target_buf + 62) = v15 * icon_props[4] + v13;
    *(u16*)(target_buf + 64) = v11;
    *(u16*)(target_buf + 66) = v11;
    *(u16*)(target_buf + 68) = v16;
    *(u16*)(target_buf + 70) = v16;
    
    /* 7. ++n16_1 */
    ++g_n16_1;
    
    return 0;
}

/* ========================================================================
 * sub_4ED7A: 字符渲染函数 (原游戏 0x4ED7A, 大小 0xAB)
 *
 * 原游戏逻辑 (1:1 复制):
 *   1. 如果arg18!=0，先清空16行屏幕区域（每行填充4个32位值）
 *   2. 从FDOTHER.DAT字体表读取32字节字符数据
 *   3. 逐16行扫描字符
 *   4. 每行16位，逐位检查是否设置
 *   5. 如果位=1，写入颜色值到屏幕缓冲区
 *   6. 字符数据16位需要字节交换
 *
 * 参数:
 *   fdother_dat  - FDOTHER.DAT字体数据指针 (6字节头 + 32字节/字符)
 *   char_index   - 字符索引 (0-9数字字符)
 *   screen_buf   - 屏幕缓冲区指针
 *   screen_offset - 屏幕缓冲区偏移
 *   row_width    - 每行宽度 (通常是行宽argC)
 *   color1       - 前景色 (arg10)
 *   color2       - 背景色 (arg14)
 *   do_clear     - 是否先清除区域 (arg18)
 * ======================================================================== */
void fd2_render_char(void* fdother_dat, int char_index, void* screen_buf,
                     int screen_offset, int row_width, u8 color1, u8 color2, int do_clear) {
    u8* screen;
    u16* font_data;
    u16 char_bits;
    int row, bit;
    const int MAX_SCREEN_SIZE = 655360;  /* 缓冲区最大值 (640KB) */

    if (!fdother_dat || !screen_buf) return;

    /* 安全检查：确保偏移在缓冲区范围内 */
    if (screen_offset < 0 || screen_offset >= MAX_SCREEN_SIZE) return;

    screen = (u8*)screen_buf + screen_offset;

    /* 阶段1: 如果需要清除，先清空16行区域 */
    /* 原游戏: memset32(n655360_1, value, 4u) - 每行填充4个32位值 */
    if (do_clear) {
        u8* p = screen;
        for (int i = 0; i < 16; i++) {
            /* 边界检查 */
            if ((u8*)p - (u8*)screen_buf >= MAX_SCREEN_SIZE - row_width) break;
            memset(p, 0, row_width);
            p += row_width;
        }
    }

    /* 阶段2: 从FDOTHER.DAT字体表读取字符数据 */
    /* 每个字符32字节 (16位 * 2字节/行)，偏移 = 6(头) + 32 * char_index */
    font_data = (u16*)((u8*)fdother_dat + 6 + 32 * char_index);

    /* 阶段3: 逐行渲染字符 (16行) */
    u8* dst = screen;
    for (row = 0; row < 16; row++) {
        /* 边界检查：确保不会写入越界 */
        if ((u8*)dst - (u8*)screen_buf >= MAX_SCREEN_SIZE - row_width * 2) break;

        /* 读取16位字符数据并字节交换 */
        char_bits = *font_data++;
        char_bits = ((char_bits & 0xFF) << 8) | ((char_bits >> 8) & 0xFF);

        /* 阶段4: 逐位检查并渲染 - 使用左移和进位检查 */
        /* 原游戏: v21 = __CFSHL__(v18, 1); v18 *= 2; */
        u8* p = dst;
        u16 bits = char_bits;
        for (bit = 0; bit < 16; bit++) {
            /* 左移并检查进位 */
            int carry = (bits & 0x8000) ? 1 : 0;
            bits <<= 1;

            if (carry) {
                /* 位=1: 写入前景色+背景色对 */
                /* 边界检查 */
                if ((u8*)p - (u8*)screen_buf < MAX_SCREEN_SIZE) {
                    *p = color1;
                }
                if ((u8*)(p + row_width - 1) - (u8*)screen_buf < MAX_SCREEN_SIZE) {
                    *(p + row_width - 1) = color2;
                }
                if ((u8*)(p + row_width) - (u8*)screen_buf < MAX_SCREEN_SIZE) {
                    *(p + row_width) = color2;
                }
            }
            p++;
        }
        dst += row_width;
    }
}

/* ========================================================================
 * sub_15F84 简化版: 文本渲染函数
 *
 * 原游戏 sub_15F84 极其复杂（约700行），包含：
 * - FDTXT.DAT压缩文本解析
 * - 特殊标记处理 (-1~-20)
 * - sub_4ED7A字符渲染
 * - sub_11EEE屏幕区域复制
 * - 子画面控制
 * - DATO.DAT动态资源加载
 *
 * 当前实现简化版：直接使用fd2_render_char渲染字符串
 * ======================================================================== */
void fd2_render_text(void* fdother_dat, void* screen_buf,
                     int x, int y, const char* text,
                     u8 color1, u8 color2, int do_clear) {
    if (!fdother_dat || !screen_buf || !text) return;
    
    int row_width = 320;  /* 屏幕宽度 */
    int screen_offset = y * row_width + x;
    
    for (int i = 0; text[i] != '\0'; i++) {
        int char_index = text[i] - '0';  /* 假设是数字字符 */
        if (char_index >= 0 && char_index <= 9) {
            fd2_render_char(fdother_dat, char_index, screen_buf,
                           screen_offset, row_width, color1, color2, do_clear);
        }
        screen_offset += 16;  /* 每个字符宽16像素 */
    }
}

/* ========================================================================
 * sub_1366A 简化版: 场景动画/资源加载函数 (原游戏 0x1366A, 大小 ~0x340)
 *
 * 原游戏逻辑极其复杂，涉及：
 *   - sub_4EB48(): 获取场景动画数据
 *   - sub_32230(): 动画帧处理
 *   - sub_11CAC(): 渲染控制
 *   - sub_11D40(): 调色板设置
 *   - sub_17AA9(): 子画面渲染
 *   - sub_11EEE(): 屏幕区域复制
 *   - sub_127E0(): 精灵位置更新
 *   - sub_129EC(): 屏幕刷新
 *   - sub_11EB0(): 区域渲染
 *
 * 当前实现简化版：加载图标数据并初始化场景
 * ======================================================================== */
int fd2_scene_load_resources(int resource_id) {
    /* 原游戏: sub_4EB48(resource_id) 获取动画数据 */
    /* 简化实现：加载场景图标 */
    
    /* 原游戏: 循环处理每个动画帧 */
    /* 简化实现：暂时跳过复杂动画 */
    
    return 0;
}

/* ========================================================================
 * sub_4EBFF: 屏幕区域复制函数 (原游戏 0x4EBFF, 大小 0x2E)
 *
 * 原游戏逻辑 (1:1 复制):
 *   v4 = *a2;         // 宽度
 *   v5 = a2[1];       // 高度
 *   do {
 *     v8 = a1;
 *     do {
 *       sub_4EC66();  // nullsub，空函数
 *       *a1++ = v7;   // v7是al寄存器，实际是从某处读取的字节值
 *       --v4;
 *     } while (v4);
 *     a1 = &v8[a3];   // 移动到下一行
 *     --v5;
 *   } while (v5);
 *
 * 注意: sub_4EC66是空函数，v7的值来源需要看调用上下文
 * 实际上这个函数是从源缓冲区复制数据到目标缓冲区
 * ======================================================================== */
void fd2_copy_screen_region(u8* dst, s16* src, int row_width) {
     s16 width = src[0];
     s16 height = src[1];
     u8* src_data = (u8*)(src + 2);  /* 数据从src+4字节开始 */
     
     for (int y = 0; y < height; y++) {
         for (int x = 0; x < width; x++) {
             *dst++ = *src_data++;
         }
         dst += row_width - width;  /* 跳到下一行起始位置 */
     }
 }

/* ========================================================================
 * sub_11EB0: 屏幕区域更新函数 (原游戏 0x11EB0, 大小 0x40)
 *
 * 原游戏逻辑 (1:1 复制):
 *   for (i = 0; i < a10; ++i) {
 *     memmove(a5, a7, a9);
 *     a5 += a6;
 *     a7 += a8;
 *   }
 *
 * 参数:
 *   a1-a4: 保留参数
 *   a5: 目标缓冲区指针
 *   a6: 目标行宽
 *   a7: 源缓冲区指针
 *   a8: 源行宽
 *   a9: 每行拷贝字节数
 *   a10: 行数
 * ======================================================================== */
void fd2_screen_region_update(void* dst, int dst_stride,
                               const void* src, int src_stride,
                               int copy_size, int num_lines) {
    const u8* s = (const u8*)src;
    u8* d = (u8*)dst;
    
    for (int i = 0; i < num_lines; i++) {
        memcpy(d, s, copy_size);
        d += dst_stride;
        s += src_stride;
    }
}

/* ========================================================================
 * sub_4E22A: 光标图像复制函数 (原游戏 0x4E22A, 大小 0x6E)
 *
 * 原游戏逻辑 (1:1 复制):
 *   这是一个简单的图像解压/复制函数
 *   - 24行 x 24列的光标图像
 *   - 使用位流压缩格式
 *   - 每位表示操作类型：填充/拷贝/跳过
 *
 * 简化实现：直接拷贝24x24光标图像
 * ======================================================================== */
void fd2_copy_cursor_image(u8* dst, const u8* src, int row_width) {
    /* 简化实现：直接拷贝24x24区域 */
    for (int y = 0; y < 24; y++) {
        memcpy(dst, src, 24);
        dst += row_width;
        src += 24;
    }
}

/*
 * 场景0: 主菜单/标题场景初始化 (对应原游戏 sub_3231B)
 * 地址: 0x3231B, 大小: 0x65A (1626字节)
 */
static int g_scene0_initialized = 0;  /* 防止重复初始化 */

void scene_0_init(struct fd2_state_machine* sm) {
    if (!sm) return;
    
    /* 防止重复初始化 - 开场剧情只执行一次 */
    if (g_scene0_initialized) {
        printf("[SCENE0] Already initialized, skipping opening intro\n");
        return;
    }
    g_scene0_initialized = 1;
    
    /* 调用开场剧情函数 (根据IDA代码实现) */
    fd2_play_opening_intro(sm);
    
    /* 设置状态为交互 */
    g_n2_0 = FD2_SCENE_STATE_INTERACT;
    
    printf("Scene 0 initialized - opening intro complete\n");
}

void scene_0_exit(struct fd2_state_machine* sm) {
    if (!sm) return;
}

int scene_0_check(struct fd2_state_machine* sm) {
    if (!sm) return 0;
    return 0;
}

/*
 * 场景1: 默认处理 (对应原游戏 sub_22EF6)
 * 地址: 0x22EF6, 大小: 0x41 (65字节)
 */
void scene_1_init(struct fd2_state_machine* sm) {
    if (!sm) return;
    sm->globals.scene_id = 1;
}

void scene_1_exit(struct fd2_state_machine* sm) {
    if (!sm) return;
}

/*
 * 场景2-29: 默认处理 (对应原游戏 sub_21206)
 * 地址: 0x21206, 大小: 0x21 (33字节)
 */
void scene_default_init(struct fd2_state_machine* sm) {
    if (!sm) return;
}

void scene_default_exit(struct fd2_state_machine* sm) {
    if (!sm) return;
}

/*
 * 注册所有场景到状态机
 * 对应原游戏 funcs_25E23[] 和 funcs_25E3A[] 数组初始化
 */
void fd2_register_all_scenes(fd2_state_machine_t* sm) {
    if (!sm) return;
    
    /* 场景0: 主菜单/标题场景 */
    fd2_register_scene(sm, 0, scene_0_init, scene_0_exit, scene_0_check,
                       0, 0, "main_menu");
    
    /* 场景1: 默认处理 */
    fd2_register_scene(sm, 1, scene_1_init, scene_1_exit, NULL,
                       0, 0, "scene_1");
    
    /* 场景2-29: 默认处理 */
    for (int i = 2; i < FD2_SCENE_COUNT; i++) {
        char name[32];
        snprintf(name, sizeof(name), "scene_%d", i);
        fd2_register_scene(sm, i, scene_default_init, scene_default_exit, NULL,
                           0, 0, name);
    }
}
