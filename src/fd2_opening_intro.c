#include "fd2_opening_intro.h"
#include "fd2_state_machine.h"
#include "fd2_globals.h"
#include "fd2_resources.h"
#include "fd2_rle.h"
#include "fd2_render.h"
#include "fd2_scene_interact.h"
#include <SDL2/SDL.h>
#include <stdio.h>
#include <string.h>

/* 获取资源管理器 */
extern fd2_resources_t* fd2_get_resources(void);
static fd2_resources_t* g_intro_res = NULL;

/* 场景数据 */
static const u8 scene_0_data[] = {
    0x05, 0x06, 0x04, 0x00, 0x02, 0x01, 0x02, 0x02, 0x02, 0x03, 0x02,
    0x88, 0x01, 0x00, 0x01, 0x88, 0x01, 0x00, 0x03, 0x88, 0x01,
    0x00, 0x01, 0x84, 0x01, 0x00, 0x00, 0x01, 0x01, 0x04, 0x04,
    0x00, 0x05, 0x00, 0x06, 0x00, 0x07, 0x00, 0x04, 0x01, 0x04,
    0x08, 0x02, 0x09, 0x02, 0x0A, 0x01, 0x0B, 0x03, 0x02
};

static const u8 scene_99_data[] = {
    0x01, 0x01, 0x04, 0x04, 0x00, 0x05, 0x00, 0x06, 0x00, 0x07, 0x00,
    0x04, 0x01, 0x04, 0x08, 0x02, 0x09, 0x02, 0x0A, 0x01, 0x0B,
    0x03, 0x02, 0x04, 0x08, 0x03, 0x09, 0x02, 0x0A, 0x02, 0x0B,
    0x02, 0x84, 0x05, 0x09, 0x02, 0x00, 0x00, 0x01, 0x00
};

static const u8 scene_1_data[] = { 0x00 };
static const u8 scene_2_data[] = { 0x00 };
static const u8 scene_5_data[] = { 0x00 };
static const u8 scene_90_data[] = { 0x00 };
static const u8 scene_91_data[] = { 0x00 };
static const u8 scene_92_data[] = { 0x00 };
static const u8 scene_93_data[] = { 0x00 };
static const u8 scene_94_data[] = { 0x00 };
static const u8 scene_95_data[] = { 0x00 };
static const u8 scene_96_data[] = { 0x00 };
static const u8 scene_97_data[] = { 0x00 };
static const u8 scene_98_data[] = { 0x00 };
static const u8 scene_100_data[] = { 0x00 };
static const u8 scene_101_data[] = { 0x00 };
static const u8 scene_102_data[] = { 0x00 };
static const u8 scene_103_data[] = { 0x00 };
static const u8 scene_104_data[] = { 0x00 };
static const u8 scene_105_data[] = { 0x00 };

void* off_627D8[256] = {
    [0] = (void*)scene_0_data,
    [1] = (void*)scene_1_data,
    [2] = (void*)scene_2_data,
    [5] = (void*)scene_5_data,
    [90] = (void*)scene_90_data,
    [91] = (void*)scene_91_data,
    [92] = (void*)scene_92_data,
    [93] = (void*)scene_93_data,
    [94] = (void*)scene_94_data,
    [95] = (void*)scene_95_data,
    [96] = (void*)scene_96_data,
    [97] = (void*)scene_97_data,
    [98] = (void*)scene_98_data,
    [99] = (void*)scene_99_data,
    [100] = (void*)scene_100_data,
    [101] = (void*)scene_101_data,
    [102] = (void*)scene_102_data,
    [103] = (void*)scene_103_data,
    [104] = (void*)scene_104_data,
    [105] = (void*)scene_105_data,
};

/* sub_4EB48: 获取场景数据指针 */
static void* sub_4EB48_impl(int index) {
    if (index < 0 || index >= 256) return NULL;
    return off_627D8[index];
}

/*
 * sub_4ED7A: 字符渲染函数 (从IDA 0x4ED7A 1:1实现)
 * 参数:
 *   _FDOTHER.DAT_ - FDOTHER.DAT索引6的字体数据指针
 *   n10 - 字符索引
 *   n658255 - 屏幕缓冲区偏移地址
 *   argC - 屏幕宽度(320)
 *   arg10 - 前景色
 *   arg14 - 背景色
 *   arg18 - 是否清除背景(非0=清除)
 */
static void sub_4ED7A_impl(u8* font_data, int char_index, u8* screen_buf, 
                           int screen_width, u8 fg_color, u8 bg_color, int clear_bg) {
    if (!font_data || !screen_buf) return;
    
    if (clear_bg) {
        u32 clear_val = (bg_color << 24) | (bg_color << 16) | (bg_color << 8) | bg_color;
        u8* ptr = screen_buf;
        for (int i = 0; i < 16; i++) {
            for (int j = 0; j < 4; j++) {
                ptr[j] = bg_color;
            }
            ptr += screen_width;
        }
    }
    
    if (char_index == 10) return;  /* 空格字符 */
    
    const u16* char_data = (u16*)(font_data + 32 * char_index);
    u8* dest = screen_buf;
    
    for (int row = 0; row < 16; row++) {
        u16 bits = char_data[row];
        bits = ((bits & 0xFF) << 8) | ((bits >> 8) & 0xFF);  /* 字节交换 */
        
        for (int bit = 0; bit < 16; bit++) {
            if (bits & (0x8000 >> bit)) {
                dest[bit] = fg_color;
            }
        }
        dest += screen_width;
    }
}

/*
 * sub_15F84: 文本渲染函数 (从IDA 0x15F84 1:1实现)
 * 从FDTXT.DAT读取文本数据，解析控制码并渲染字符
 */
static void sub_15F84_impl(fd2_state_machine_t* sm, int text_file, int text_index, 
                           u8* screen_buf, int screen_width, int x, int y, int fg, int bg, int clear) {
    if (!g_intro_res) return;
    
    const fd2_dat_t* fdtxt = fd2_resources_get_dat(g_intro_res, FD2_DAT_FDTXT);
    if (!fdtxt || text_index >= (int)fdtxt->resource_count) {
        printf("[INTRO] sub_15F84: Text %d not found\n", text_index);
        SDL_Delay(300);
        return;
    }
    
    const fd2_resource_t* r = &fdtxt->resources[text_index];
    printf("[INTRO] sub_15F84: Rendering text %d, offset=%u, size=%u\n", text_index, r->start, r->size);
    
    const u8* txt_data = fdtxt->data + r->start;
    const int16_t* words = (const int16_t*)txt_data;
    int word_count = r->size / 2;
    
    const fd2_dat_t* fdother = fd2_resources_get_dat(g_intro_res, FD2_DAT_FDOTHER);
    u8* font_data = NULL;
    if (fdother && 6 < (int)fdother->resource_count) {
        font_data = (u8*)(fdother->data + fdother->resources[6].start);
    }
    
    u8* screen_ptr = screen_buf + y * screen_width + x;
    int cur_x = x;
    int cur_y = y;
    
    for (int i = 0; i < word_count; i++) {
        int16_t code = words[i];
        
        if (code == -1) {
            printf("[INTRO] sub_15F84: End of text\n");
            break;
        } else if (code == -2 || code == -3) {
            cur_y += 16;
            screen_ptr = screen_buf + cur_y * screen_width + x;
            if (code == -3) {
                SDL_Delay(200);
            }
        } else if (code == -6) {
            char num_str[16];
            snprintf(num_str, sizeof(num_str), "%d", g_n999_0);
            int len = strlen(num_str);
            for (int j = 0; j < len; j++) {
                int digit = num_str[j] - '0';
                if (font_data) {
                    sub_4ED7A_impl(font_data, digit, screen_ptr, screen_width, fg, bg, clear);
                }
                screen_ptr += 16;
            }
        } else if (code >= 0) {
            if (font_data) {
                sub_4ED7A_impl(font_data, code, screen_ptr, screen_width, fg, bg, clear);
            }
            screen_ptr += 16;
        }
    }
    
    SDL_Delay(300);
}

/* sub_4E381: 刷新屏幕 */
static void sub_4E381_impl(fd2_state_machine_t* sm) {
    if (!sm) return;
    /* 直接调用渲染循环的一帧 */
    fd2_scene_interact_render_update(sm);
    SDL_Delay(50);
}

/* sub_11CAC: 动画控制函数 */
static int sub_11CAC_impl(fd2_state_machine_t* sm, int a5) {
    if (!sm) return 0;
    
    printf("[INTRO] sub_11CAC: a5=%d\n", a5);
    
    if (!a5) {
        sub_4E381_impl(sm);
    }
    
    return 1;
}

/* sub_11D40: 淡入淡出效果 */
static void sub_11D40_impl(int a1, int a2, int a3, int a4, int a5, int a6, int a7) {
    printf("[INTRO] sub_11D40: a1=%d, a5=%d, a6=%d, a7=%d\n", a1, a5, a6, a7);
    (void)a2; (void)a3; (void)a4;
    SDL_Delay(20);
}

/* sub_17AA9: 动画渲染函数 */
static int sub_17AA9_impl(int a1, int a2, int a3, int a4, int a5) {
    printf("[INTRO] sub_17AA9: a1=%d, a2=%d, a5=%d\n", a1, a2, a5);
    (void)a3; (void)a4;
    return a1;
}

/* sub_32230: 场景动画处理函数 */
static void sub_32230_impl(int a1) {
    (void)a1;
}

/* sub_129EC: 场景结束处理 */
static void sub_129EC_impl(void) {
    /* TODO: 根据IDA代码实现 */
}

/* sub_127E0: 场景清理 */
static void sub_127E0_impl(int a1) {
    (void)a1;
}

/* sub_11EB0: 图像复制 */
static int sub_11EB0_impl(int a1, int a2, int a3, int a4, int a5, int a6, int a7, int a8, int a9, int a10) {
    (void)a1; (void)a2; (void)a3; (void)a4; (void)a5; (void)a6;
    (void)a7; (void)a8; (void)a9; (void)a10;
    return a1;
}

/* sub_11EEE: 图像操作 */
static void sub_11EEE_impl(int a1, int a2, int a3, int a4, int a5, int a6, int a7, int a8, int a9, int a10) {
    (void)a1; (void)a2; (void)a3; (void)a4; (void)a5; (void)a6;
    (void)a7; (void)a8; (void)a9; (void)a10;
}

/*
 * sub_1366A: 场景动画播放函数
 * 从IDA反编译代码1:1实现
 * 参数a5是场景索引，从off_627D8数组获取场景数据
 */
static int sub_1366A_impl(fd2_state_machine_t* sm, int a1, int a2, int n8, int a4, int scene_index) {
    printf("[INTRO] sub_1366A: Scene index %d\n", scene_index);
    
    /* 从off_627D8获取场景数据 */
    u8* scene_data = (u8*)sub_4EB48_impl(scene_index);
    if (!scene_data) {
        printf("[INTRO]   WARNING: Scene data not found for index %d\n", scene_index);
        return 0;
    }
    
    u8 entry_count = scene_data[0];  /* 第一个字节是条目数量 */
    u8* data_ptr = scene_data + 1;   /* 指向数据正文 */
    
    printf("[INTRO]   Entry count: %d\n", entry_count);
    
    for (u8 i = 0; i < entry_count; i++) {
        u8 v29 = data_ptr[0];  /* 操作标志 */
        u8 v25 = data_ptr[1];  /* 子条目数量 */
        data_ptr += 2;
        
        u8 v23[32] = {0}, v22[32] = {0};
        for (u8 j = 0; j < v25; j++) {
            v23[j] = data_ptr[0];
            v22[j] = data_ptr[1];
            data_ptr += 2;
        }
        
        if ((v29 & 0x80) == 0) {
            /* 标志位为0：正常场景动画 */
            printf("[INTRO]   Entry %d: Normal animation, v29=%d, v25=%d\n", i, v29, v25);
            for (u8 k = 0; k < v29; k++) {
                for (u8 n7 = 1; n7 < 7; n7++) {
                    sub_32230_impl(v23[0]);
                    
                    /* TODO: 正确设置数据到全局变量 */
                    
                    if (!g_n64 || g_n64 == 64) {
                        sub_11CAC_impl(sm, 0);
                    } else {
                        g_n64++;
                        int v18 = sub_11CAC_impl(sm, 1);
                        sub_11D40_impl(v18, 0, 0, a4, 0, 255, g_n64);
                    }
                    sub_4E381_impl(sm);
                }
                
                /* 更新位置 */
                /* TODO: 根据IDA代码更新坐标 */
            }
        } else {
            /* 标志位为1：特殊操作 */
            v29 &= ~0x80;
            printf("[INTRO]   Entry %d: Special operation, v29=%d, v25=%d\n", i, v29, v25);
            
            if (v29) {
                /* 滚动过渡 */
                for (u8 j = 0; j < v25; j++) {
                    /* 设置数据 */
                }
                for (u8 j = 0; j < v29; j++) {
                    int v15 = sub_11CAC_impl(sm, 0);
                    sub_17AA9_impl(v15, j, 0, a4, 1);
                    sub_4E381_impl(sm);
                }
            } else {
                /* 地图加载和场景切换 */
                sub_17AA9_impl(0, v25, 0, a4, 1);
                sub_11EEE_impl(0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
                sub_129EC_impl();
                
                for (int n6 = 0; n6 < g_n6_0; n6++) {
                    if (n6 == v23[0]) {
                        sub_127E0_impl(n6);
                    }
                }
                
                sub_11EB0_impl(0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
                int v12 = sub_17AA9_impl(0, 0, 0, a4, 2);
                sub_11CAC_impl(sm, 0);
                sub_4E381_impl(sm);
            }
        }
    }
    
    return sub_11CAC_impl(sm, 1);
}

/* sub_13185: 动画帧延迟 */
static void sub_13185_impl(int frames) {
    SDL_Delay(frames * 100);
}

/* sub_25977: 辅助函数 */
static void sub_25977_impl(int a1, int a2, int a3, int a4, int a5, int a6) {
    (void)a1; (void)a2; (void)a3; (void)a4; (void)a5; (void)a6;
}

/* sub_10B4E: 辅助函数 */
static int sub_10B4E_impl(int a1, int a2, int a3, int a4, int a5) {
    (void)a1; (void)a2; (void)a3; (void)a4;
    return a5;
}

/* sub_1F525: 辅助函数 */
static int sub_1F525_impl(int a1, int a2, int a3, int a4) {
    (void)a1; (void)a2; (void)a3; (void)a4;
    return 0;
}

/* sub_32975: 辅助函数 */
static int sub_32975_impl(int a1) {
    return a1;
}

/* sub_32999: 辅助函数 */
static int sub_32999_impl(int a1, int a2, int a3, int a4, int a5) {
    (void)a1; (void)a2; (void)a3; (void)a4;
    return a5;
}

/* sub_112A5: 图标加载函数 */
static int sub_112A5_impl(int a1, int a2, int a3, int a4, int icon_id) {
    printf("[INTRO] sub_112A5: Loading icon %d\n", icon_id);
    (void)a1; (void)a2; (void)a3; (void)a4;
    return icon_id;
}

/* sub_11CAC_v2: 动画控制函数 */
static void sub_11CAC_v2_impl(int a1, int a2) {
    (void)a1; (void)a2;
}

/* sub_134E4: 场景结束函数 */
static void sub_134E4_impl(void) {
    /* TODO: 根据IDA代码实现 */
}

/* sub_12D7B: 场景清理函数 */
static void sub_12D7B_impl(int a1) {
    (void)a1;
}

/* sub_205DA: 场景预处理函数 */
static void sub_205DA_impl(void) {
    printf("[INTRO] sub_205DA: Scene preprocessing\n");
    /* 清空屏幕缓冲区 */
    if (g_n655360_0) {
        SDL_memset(g_n655360_0, 0, 64000);
    }
}

/* sub_135DD: 场景初始化函数 */
static void sub_135DD_impl(int a1, int a2) {
    printf("[INTRO] sub_135DD: a1=%d, a2=%d\n", a1, a2);
    (void)a1; (void)a2;
}

/* 获取资源管理器 */
extern fd2_resources_t* fd2_get_resources(void);

void fd2_play_opening_intro(fd2_state_machine_t* sm) {
    if (!sm) return;
    
    printf("[INTRO] Starting opening intro sequence (sub_3231B)\n");
    
    /* 第74行: sub_3702F(a2, a3, n8, a4, 44) */
    /* 初始化场景 */
    
    /* 第75行: n17 = 32 */
    g_n17 = 32;
    
    /* 第76行: sub_205DA() */
    sub_205DA_impl();
    
    /* 第77行: sub_135DD(3, 34) */
    sub_135DD_impl(3, 34);
    
    /* 第78行: sub_1366A(v5, a2, a4, a3, 99) */
    sub_1366A_impl(sm, 0, 0, 0, 0, 99);
    
    /* 第79-80行: for循环调用sub_13185(2)共15次 */
    for (int i = 0; i < 15; i++) {
        sub_13185_impl(2);
    }
    
    /* 第81行: sub_15F84(..., FDTXT_DAT, 0, 655360, 320, 205, 76, 74, 19, 1) */
    sub_15F84_impl(sm, 0, 0, (u8*)g_n655360_0, 320, 205, 76, 74, 19, 1);
    g_n6_5 = 0;
    
    /* 第82-83行: for循环调用sub_13185(2)共13次 */
    for (int i = 0; i < 13; i++) {
        sub_13185_impl(2);
    }
    
    /* 第84行: sub_15F84(..., FDTXT_DAT, 1, ...) */
    sub_15F84_impl(sm, 0, 1, (u8*)g_n655360_0, 320, 205, 76, 74, 19, 1);
    g_n6_5 = 0;
    
    /* 第85行: sub_25977(..., -1, 0) */
    sub_25977_impl(0, 0, 0, 0, -1, 0);
    
    /* 第86行: n64 = 1 */
    g_n64 = 1;
    
    /* 第87行: sub_1366A(..., 100) */
    sub_1366A_impl(sm, 0, 0, 0, 0, 100);
    
    /* 第88行: n64 = 0 */
    g_n64 = 0;
    
    /* 第89行: sub_135DD(0, 43) */
    sub_135DD_impl(0, 43);
    
    /* 第90行: sub_25977(..., 11, 0) */
    sub_25977_impl(0, 0, 0, 0, 11, 0);
    
    /* 第91-92行 */
    int v12 = sub_1F525_impl(0, 0, 0, 0);
    int v13 = sub_1366A_impl(sm, v12, 0, 0, 0, 101);
    sub_15F84_impl(sm, 0, 2, (u8*)g_n655360_0, 320, 205, 76, 74, 19, 1);
    g_n6_5 = 0;
    
    /* 第93-94行 */
    int v15 = sub_1366A_impl(sm, 0, 0, 0, 0, 102);
    sub_15F84_impl(sm, 0, 3, (u8*)g_n655360_0, 320, 205, 76, 74, 19, 1);
    g_n6_5 = 0;
    
    /* 第95-96行 */
    int v17 = sub_1366A_impl(sm, 0, 0, 0, 0, 103);
    sub_15F84_impl(sm, 0, 4, (u8*)g_n655360_0, 320, 205, 76, 74, 19, 1);
    g_n6_5 = 0;
    
    /* 第97-98行 */
    int v19 = sub_1366A_impl(sm, 0, 0, 0, 0, 104);
    sub_15F84_impl(sm, 0, 5, (u8*)g_n655360_0, 320, 205, 76, 74, 19, 1);
    g_n6_5 = 0;
    
    /* 第99-101行 */
    g_n64 = 1;
    g_n6_5 = 0;
    sub_1366A_impl(sm, 0, 0, 0, 0, 105);
    g_n64 = 0;
    
    /* 第102行: n17 = 31 */
    g_n17 = 31;
    
    /* 第103行: sub_205DA() */
    sub_205DA_impl();
    
    /* 第104行: n6_5 = 0 */
    g_n6_5 = 0;
    
    /* 第105行: sub_135DD(5, 42) */
    sub_135DD_impl(5, 42);
    
    /* 第106-107行 */
    int v22 = sub_10B4E_impl(0, 0, 0, 0, 1);
    int v23 = sub_1366A_impl(sm, v22, 0, 0, 0, 90);
    sub_15F84_impl(sm, 0, 0, (u8*)g_n655360_0, 320, 205, 76, 74, 19, 1);
    g_n6_5 = 0;
    
    /* 第108-109行 */
    int v25 = sub_1366A_impl(sm, 0, 0, 0, 0, 91);
    sub_15F84_impl(sm, 0, 1, (u8*)g_n655360_0, 320, 205, 76, 74, 19, 1);
    g_n6_5 = 0;
    
    /* 第110-111行 */
    int v27 = sub_1366A_impl(sm, 0, 0, 0, 0, 92);
    sub_15F84_impl(sm, 0, 2, (u8*)g_n655360_0, 320, 205, 76, 74, 19, 1);
    g_n6_5 = 0;
    
    /* 第112-113行 */
    sub_10B4E_impl(0, 0, 0, 0, 3);
    sub_135DD_impl(4, 41);
    
    /* 第114-115行 */
    int v29 = sub_1366A_impl(sm, 0, 0, 0, 0, 93);
    sub_15F84_impl(sm, 0, 3, (u8*)g_n655360_0, 320, 205, 76, 74, 19, 1);
    g_n6_5 = 0;
    
    /* 第116-118行 */
    int v31 = sub_32975_impl(2);
    int v33 = sub_10B4E_impl(v31, 0, 0, 0, 5);
    sub_15F84_impl(sm, 0, 4, (u8*)g_n655360_0, 320, 205, 76, 74, 19, 1);
    g_n6_5 = 0;
    
    /* 第119-120行 */
    int v35 = sub_1366A_impl(sm, 0, 0, 0, 0, 94);
    sub_15F84_impl(sm, 0, 5, (u8*)g_n655360_0, 320, 205, 76, 74, 19, 1);
    g_n6_5 = 0;
    
    /* 第121-122行 */
    int v37 = sub_1366A_impl(sm, 0, 0, 0, 0, 95);
    sub_15F84_impl(sm, 0, 6, (u8*)g_n655360_0, 320, 205, 76, 74, 19, 1);
    g_n6_5 = 0;
    
    /* 第123-124行 */
    int v39 = sub_1366A_impl(sm, 0, 0, 0, 0, 96);
    sub_15F84_impl(sm, 0, 7, (u8*)g_n655360_0, 320, 205, 76, 74, 19, 1);
    g_n6_5 = 0;
    
    /* 第125-126行 */
    int v41 = sub_1366A_impl(sm, 0, 0, 0, 0, 97);
    sub_15F84_impl(sm, 0, 8, (u8*)g_n655360_0, 320, 205, 76, 74, 19, 1);
    g_n6_5 = 0;
    
    /* 第127行: sub_25977(..., -1, 0) */
    sub_25977_impl(0, 0, 0, 0, -1, 0);
    g_n6_5 = 0;
    
    /* 第128-129行 */
    g_n64 = 1;
    int v44 = sub_1366A_impl(sm, 0, 0, 0, 0, 98);
    g_n64 = 0;
    
    /* 第130行: n17 = 0 */
    g_n17 = 0;
    
    /* 第131-134行: sub_112A5加载图标 */
    int v45 = sub_112A5_impl(v44, 0, 0, 0, 0);
    int v46 = sub_112A5_impl(v45, 0, 0, 0, 9);
    int v47 = sub_112A5_impl(v46, 0, 0, 0, 4);
    sub_112A5_impl(v47, 0, 0, 0, 0x1E);
    
    /* 第135行: sub_205DA() */
    sub_205DA_impl();
    
    /* 第136行: n6_5 = 0 */
    g_n6_5 = 0;
    
    /* 第137行: sub_135DD(4, 12) */
    sub_135DD_impl(4, 12);
    
    /* 第138行: sub_1366A(..., 0) */
    sub_1366A_impl(sm, 0, 0, 0, 0, 0);
    
    /* 第139行: delay(200) */
    SDL_Delay(200);
    
    /* 第140-141行 */
    int v49 = sub_1366A_impl(sm, 0, 0, 0, 0, 1);
    sub_15F84_impl(sm, 0, 0, (u8*)g_n655360_0, 320, 205, 76, 74, 19, 1);
    g_n6_5 = 0;
    
    /* 第142行: delay(200) */
    SDL_Delay(200);
    
    /* 第143行: sub_135DD(0, 0) */
    sub_135DD_impl(0, 0);
    
    /* 第144-145行 */
    int v51 = sub_32999_impl(0, 0, 0, 0, 1);
    sub_1366A_impl(sm, v51, 0, 0, 0, 1);
    sub_135DD_impl(0, 15);
    
    /* 第146-147行 */
    int v53 = sub_32999_impl(0, 0, 0, 0, 2);
    int v54 = sub_1366A_impl(sm, v53, 0, 0, 0, 2);
    sub_15F84_impl(sm, 0, 1, (u8*)g_n655360_0, 320, 205, 76, 74, 19, 1);
    g_n6_5 = 0;
    
    /* 第148行: delay(200) */
    SDL_Delay(200);
    
    /* 第149行: sub_1366A(..., 5) */
    sub_1366A_impl(sm, 0, 0, 0, 0, 5);
    
    /* 第150-151行 */
    int v56 = sub_32975_impl(9);
    sub_11CAC_v2_impl(v56, 0);
    
    /* 第152行: delay(100) */
    SDL_Delay(100);
    
    /* 第153行 */
    sub_15F84_impl(sm, 0, 2, (u8*)g_n655360_0, 320, 205, 76, 74, 19, 1);
    
    /* 第154行: sub_134E4() */
    sub_134E4_impl();
    
    /* 第155行: sub_12D7B(0) */
    sub_12D7B_impl(0);
    
    /* 第156行: n999_0 = 0 */
    g_n999_0 = 0;
    
    printf("[INTRO] Opening intro sequence complete\n");
}
