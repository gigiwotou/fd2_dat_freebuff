#include "fd2_input_scan.h"
#include "fd2_globals.h"
#include "fd2_data_loader.h"
#include <stdio.h>

/*
 * SDL按键码到原游戏扫描码映射表
 * 根据原游戏BIOS中断22h返回的扫描码
 */
const fd2_key_mapping_t fd2_key_map[] = {
    { SDL_SCANCODE_ESCAPE,    1   },   /* Esc */
    { SDL_SCANCODE_RETURN,    28  },   /* Enter */
    { SDL_SCANCODE_SPACE,     57  },   /* Space */
    { SDL_SCANCODE_TAB,       15  },   /* Tab */
    { SDL_SCANCODE_INSERT,    82  },   /* Insert */
    { SDL_SCANCODE_DELETE,    83  },   /* Delete */
    { SDL_SCANCODE_UP,        72  },   /* Up */
    { SDL_SCANCODE_DOWN,      80  },   /* Down */
    { SDL_SCANCODE_LEFT,      75  },   /* Left */
    { SDL_SCANCODE_RIGHT,     77  },   /* Right */
    { SDL_SCANCODE_SEMICOLON, 39  },   /* ; */
    { SDL_SCANCODE_COMMA,     51  },   /* , */
    { SDL_SCANCODE_PERIOD,    52  },   /* . */
    { SDL_SCANCODE_SLASH,     53  },   /* / */
    { SDL_SCANCODE_A,         30  },   /* A */
    { SDL_SCANCODE_B,         48  },   /* B */
    { SDL_SCANCODE_C,         46  },   /* C */
    { SDL_SCANCODE_D,         32  },   /* D */
    { SDL_SCANCODE_E,         18  },   /* E */
    { SDL_SCANCODE_F,         33  },   /* F */
    { SDL_SCANCODE_G,         34  },   /* G */
    { SDL_SCANCODE_H,         35  },   /* H */
    { SDL_SCANCODE_I,         23  },   /* I */
    { SDL_SCANCODE_J,         36  },   /* J */
    { SDL_SCANCODE_K,         37  },   /* K */
    { SDL_SCANCODE_L,         38  },   /* L */
    { SDL_SCANCODE_M,         50  },   /* M */
    { SDL_SCANCODE_N,         49  },   /* N */
    { SDL_SCANCODE_O,         24  },   /* O */
    { SDL_SCANCODE_P,         25  },   /* P */
    { SDL_SCANCODE_Q,         16  },   /* Q */
    { SDL_SCANCODE_R,         19  },   /* R */
    { SDL_SCANCODE_S,         31  },   /* S */
    { SDL_SCANCODE_T,         20  },   /* T */
    { SDL_SCANCODE_U,         22  },   /* U */
    { SDL_SCANCODE_V,         47  },   /* V */
    { SDL_SCANCODE_W,         17  },   /* W */
    { SDL_SCANCODE_X,         45  },   /* X */
    { SDL_SCANCODE_Y,         21  },   /* Y */
    { SDL_SCANCODE_Z,         44  },   /* Z */
    { SDL_SCANCODE_0,         11  },   /* 0 */
    { SDL_SCANCODE_1,         2   },   /* 1 */
    { SDL_SCANCODE_2,         3   },   /* 2 */
    { SDL_SCANCODE_3,         4   },   /* 3 */
    { SDL_SCANCODE_4,         5   },   /* 4 */
    { SDL_SCANCODE_5,         6   },   /* 5 */
    { SDL_SCANCODE_6,         7   },   /* 6 */
    { SDL_SCANCODE_7,         8   },   /* 7 */
    { SDL_SCANCODE_8,         9   },   /* 8 */
    { SDL_SCANCODE_9,         10  },   /* 9 */
    { SDL_SCANCODE_F1,        59  },   /* F1 */
    { SDL_SCANCODE_F2,        60  },   /* F2 */
    { SDL_SCANCODE_F3,        61  },   /* F3 */
    { SDL_SCANCODE_F4,        62  },   /* F4 */
    { SDL_SCANCODE_F5,        63  },   /* F5 */
    { SDL_SCANCODE_F6,        64  },   /* F6 */
    { SDL_SCANCODE_F7,        65  },   /* F7 */
    { SDL_SCANCODE_F8,        66  },   /* F8 */
    { SDL_SCANCODE_F9,        67  },   /* F9 */
    { SDL_SCANCODE_F10,       68  },   /* F10 */
    { SDL_SCANCODE_F11,       87  },   /* F11 */
    { SDL_SCANCODE_F12,       88  },   /* F12 */
};

const int fd2_key_map_size = sizeof(fd2_key_map) / sizeof(fd2_key_map[0]);

/*
 * fd2_sdl_to_scan_code: SDL按键码转原游戏扫描码
 */
int fd2_sdl_to_scan_code(SDL_Scancode sdl_key) {
    for (int i = 0; i < fd2_key_map_size; i++) {
        if (fd2_key_map[i].sdl_key == sdl_key) {
            return fd2_key_map[i].original_scan_code;
        }
    }
    return 0; /* 未知按键返回0 */
}

/*
 * sub_11AA8: BIOS中断读取按键 (原游戏 0x11AA8)
 *
 * SDL2实现:
 *   1. 等待按键事件 (使用非阻塞轮询，每10ms检查一次)
 *   2. 转换SDL扫描码为原游戏扫描码
 *   3. 处理特殊映射 (224/82->28, 83->1)
 *   4. 返回扫描码
 */
int fd2_input_get_scan_code(void) {
    SDL_Event event;
    
    /* 非阻塞轮询按键事件 (对应原游戏 while (!sub_10620())) */
    while (1) {
        if (SDL_PollEvent(&event)) {
            if (event.type == SDL_KEYDOWN) {
                SDL_Scancode sdl_key = event.key.keysym.scancode;
                int scan_code = fd2_sdl_to_scan_code(sdl_key);
                
                /* 处理特殊映射 (对应原游戏 0x11b23-0x11b38) */
                if (scan_code == 224 || scan_code == 82) {
                    scan_code = 28; /* Insert -> Enter */
                }
                if (scan_code == 83) {
                    scan_code = 1; /* Delete -> Esc */
                }
                
                return scan_code;
            }
            else if (event.type == SDL_QUIT) {
                return 1; /* 返回Esc */
            }
        }
        else {
            /* 没有事件，短暂等待后重试 */
            SDL_Delay(10);
        }
    }
}

/*
 * sub_117E7: 复杂输入处理 (原游戏 0x117E7)
 *
 * SDL2实现:
 *   1. 获取按键扫描码
 *   2. 根据扫描码处理不同功能
 *   3. 返回处理结果
 */
int fd2_input_process_key(int key_code) {
    int n44 = key_code;
    
    /* 处理特殊按键 (1, 44, 76 - 场景对象导航) (对应原游戏 0x11805) */
    if (n44 == 1 || n44 == 44 || n44 == 76) {
        /* 遍历场景对象列表 */
        /* sub_12D7B(v8) */
        /* dword_53AE9 = v8+1 */
        /* sub_4E381() - 更新屏幕 */
        return 0;
    }
    
    /* 处理Enter/Space (57, 28 - 确认) (对应原游戏 0x1188c) */
    if (n44 == 57 || n44 == 28) {
        /* 确认键处理 */
        if (g_byte_51A42) --g_byte_51A42;
        
        /* sub_12C0D() - 获取当前选中对象 */
        /* sub_17AED(n6_1, a3) - 执行对象动作 */
        /* sub_11CAC(0) */
        /* sub_1E292(a6, n6_1) */
        /* funcs_1197B[n17]() - 场景完成条件检查 */
        /* sub_13565() */
        /* if (n255 != 255) funcs_1199C[n255](a6) */
        /* n255 = 255 */
        return 1; /* 确认键返回1 */
    }
    
    /* 处理Tab (34 - 子场景切换) (对应原游戏 0x119b8) */
    if (n44 == 34) {
        /* Tab键处理 */
        return 0;
    }
    
    /* 处理功能键 (对应原游戏 0x119c6) */
    switch (n44) {
        case 39: /* 分号键 */
        case 23: /* I键 */
            /* sub_2000A() */
            return 0;
            
        case 51: /* 逗号键 */
        case 34: /* G键 */
            /* n3 = sub_12C0D() */
            /* if (n3 != -1) sub_17AED(n3, a3) */
            return 0;
            
        case 72: /* 上方向键 */
            /* sub_25A96(72, ...) */
            /* sub_11B48() */
            return 0;
            
        case 80: /* 下方向键 */
            /* sub_25A96(80, ...) */
            /* sub_11B9B() */
            return 0;
            
        case 75: /* 左方向键 */
            /* sub_25A96(75, ...) */
            /* sub_11C59() */
            return 0;
            
        case 77: /* 右方向键 */
            /* sub_25A96(77, ...) */
            /* sub_11BFA() */
            return 0;
    }
    
    return 0;
}
