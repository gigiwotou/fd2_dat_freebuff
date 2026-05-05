#ifndef FD2_STATE_MACHINE_H
#define FD2_STATE_MACHINE_H

/*
 * FD2 三层状态机架构
 * 基于原游戏 (FD2.EXE) 的IDA反汇编代码1:1实现
 * 
 * 原游戏架构:
 * - 第一层: sub_117E7() + funcs_1197B[] (场景完成条件检查)
 * - 第二层: funcs_25E23[] / funcs_25E3A[] (场景生命周期管理)
 * - 第三层: sub_26152() (场景交互循环)
 */

#include "fd2_types.h"
#include "fd2_render.h"
#include <SDL2/SDL.h>

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int8_t s8;
typedef int16_t s16;
typedef int32_t s32;

/* 场景数量常量 */
#define FD2_SCENE_COUNT 30
#define FD2_SUBSCENE_COUNT 10
#define FD2_MENU_ITEMS 6

/* 场景状态标志 (n2_0) */
#define FD2_SCENE_STATE_IDLE        0  /* 主循环 */
#define FD2_SCENE_STATE_INIT        1  /* 初始化场景 */
#define FD2_SCENE_STATE_INTERACT    2  /* 场景交互 */

/* 场景激活标志 (byte_51AAC) */
#define FD2_SCENE_INACTIVE 0
#define FD2_SCENE_ACTIVE   1

/* 菜单选择索引范围 */
#define FD2_MENU_ITEM_MIN 0
#define FD2_MENU_ITEM_MAX 5
#define FD2_MENU_ITEM_BACK 2  /* "返回"选项 */

/* 动画帧常量 */
#define FD2_ANIM_FRAME_COUNT 4
#define FD2_ANIM_FRAME_DELAY 4  /* BIOS ticks */

/* 按键扫描码常量 */
#define FD2_KEY_ESC       1
#define FD2_KEY_ENTER    28
#define FD2_KEY_SPACE    57
#define FD2_KEY_TAB      34
#define FD2_KEY_LEFT     75
#define FD2_KEY_RIGHT    77
#define FD2_KEY_UP       72
#define FD2_KEY_DOWN     80
#define FD2_KEY_INSERT   82
#define FD2_KEY_EXTEND  224

/* 特殊按键映射 */
#define FD2_KEY_MAP_INSERT FD2_KEY_ENTER  /* Insert转换为回车 */

/* 场景音乐映射表大小 */
#define FD2_SCENE_MUSIC_MAP_SIZE 30

/*
 * 原游戏全局变量映射
 * 这些变量完全对应原游戏的内存地址
 */
typedef struct fd2_scene_globals {
    /* 场景控制变量 */
    int scene_id;              /* n17 (0x53C03) - 当前场景索引 (0-29) */
    int subscene_id;           /* n16_1 (0x53BFB) - 子场景索引 (0-9) */
    int scene_state;           /* n2_0 - 场景状态 (0/1/2) */
    int menu_index;            /* n5 (0x53F4A) - 菜单选择索引 (0-5) */
    int anim_frame;            /* n3_4 (0x53F52) - 动画帧计数器 */
    int key_code;              /* n3 (0x53A8D) - 按键扫描码 */
    int progress;              /* n999_0 (0x53BF3) - 游戏进度 */
    int key_count;             /* 按键计数器 */
    
    /* 场景激活标志 */
    int scene_active_flag;     /* byte_51AAC (0x51AAC) */
    
    /* 退出标志 */
    int exit_flag;             /* v17/v21 - 退出循环标志 */
    int interact_result;       /* i - 交互结果 */
    
    /* BIOS定时器 */
    u16 bios_tick_base;        /* 基础定时器值 (MEMORY[0x46C]) */
    u16 bios_tick_current;     /* 当前定时器值 */
    
    /* 资源指针 */
    void* fdother_data[20];    /* FDOTHER.DAT数据指针数组 */
    void* fdtxt_data;          /* FDTXT.DAT文本数据 */
    void* fdshap_data;         /* FDSHAP.DAT形状数据 */
    void* fdfield_data;        /* FDFIELD.DAT场景数据 */
    void* fdicon_data;         /* FDICON.B24图标数据 */
    void* scene_buffer;        /* n8_3 (2560字节场景数据) */
    void* screen_buffer;       /* n655360 (64KB屏幕缓冲) */
    void* backup_buffer;       /* 后备缓冲区 */
    
    /* 场景特殊标志 */
    int is_special_scene;      /* byte_523E7[n17] - 是否为特殊场景 */
    
    /* 菜单选项音效索引 */
    int menu_sound_index;      /* FDOTHER_DAT__2相关 */
} fd2_scene_globals_t;

/* 前置声明 */
struct fd2_state_machine;

/*
 * 函数指针类型定义
 * 对应原游戏的函数指针数组
 */

/* 场景初始化函数 (funcs_25E23) */
typedef void (*fd2_scene_init_fn)(struct fd2_state_machine* sm);

/* 场景结束函数 (funcs_25E3A) */
typedef void (*fd2_scene_exit_fn)(struct fd2_state_machine* sm);

/* 场景完成条件检查函数 (funcs_1197B) */
typedef int (*fd2_scene_check_fn)(struct fd2_state_machine* sm);

/* 特殊事件处理函数 (funcs_1199C) */
typedef void (*fd2_special_event_fn)(struct fd2_state_machine* sm);

/*
 * 第二层状态机: 场景生命周期管理
 * 对应原游戏 funcs_25E23[] 和 funcs_25E3A[]
 */
typedef struct fd2_scene_lifecycle {
    fd2_scene_init_fn  init_fn;    /* funcs_25E23[n17] - 场景初始化 */
    fd2_scene_exit_fn  exit_fn;    /* funcs_25E3A[n17] - 场景结束 */
    fd2_scene_check_fn check_fn;   /* funcs_1197B[n17] - 完成条件检查 */
    u8 music_id;                   /* byte_51E63[n17] - 场景音乐ID */
    u8 is_special;                 /* byte_523E7[n17] - 是否为特殊场景 */
    const char* name;              /* 场景名称 (调试用) */
} fd2_scene_lifecycle_t;

/*
 * 第三层状态机: 场景交互循环
 * 对应原游戏 sub_26152()
 */
typedef struct fd2_scene_interaction {
    /* 输入处理 */
    int (*handle_key)(struct fd2_state_machine* sm, int key_code);
    void (*handle_menu_nav)(struct fd2_state_machine* sm, int direction);
    void (*handle_confirm)(struct fd2_state_machine* sm);
    void (*handle_subscene_switch)(struct fd2_state_machine* sm);
    
    /* 渲染更新 */
    void (*render_update)(struct fd2_state_machine* sm);
    void (*render_menu)(struct fd2_state_machine* sm);
    
    /* 结果处理 */
    int (*process_selection)(struct fd2_state_machine* sm);
} fd2_scene_interaction_t;

/*
 * 第一层状态机: 输入处理和场景完成检查
 * 对应原游戏 sub_117E7() + funcs_1197B[]
 */
typedef struct fd2_input_processor {
    int (*get_key_code)(void);
    int (*check_scene_complete)(struct fd2_state_machine* sm);
    void (*process_special_key)(struct fd2_state_machine* sm, int key_code);
    void (*process_direction_key)(struct fd2_state_machine* sm, int key_code);
    void (*process_confirm_key)(struct fd2_state_machine* sm);
} fd2_input_processor_t;

/*
 * 全局状态机管理器
 */
typedef struct fd2_state_machine {
    /* 全局变量映射 */
    fd2_scene_globals_t globals;
    fd2_scene_globals_t* globals_ptr;  /* 指向globals的指针，用于API兼容 */
    
    /* 三层状态机函数表 */
    fd2_scene_lifecycle_t    scenes[FD2_SCENE_COUNT];    /* 第二层 */
    fd2_scene_check_fn       scene_checks[FD2_SCENE_COUNT]; /* 第一层检查 */
    fd2_special_event_fn     special_events[30];         /* 特殊事件 */
    
    /* 交互系统 */
    fd2_scene_interaction_t  interaction;
    fd2_input_processor_t    input;
    
    /* 渲染系统 */
    fd2_render_t render;
    
    /* 当前状态 */
    int current_scene;
    int current_subscene;
    int scene_state;
    int menu_index;
    
    /* 运行标志 */
    int running;
    int initialized;
} fd2_state_machine_t;

/*
 * API函数声明
 */

/* 状态机初始化 */
int fd2_state_machine_init(fd2_state_machine_t* sm);
void fd2_state_machine_shutdown(fd2_state_machine_t* sm);

/* 主循环 (对应原游戏 main) */
int fd2_state_machine_run(fd2_state_machine_t* sm);

/* 第一层: 输入处理 (对应原游戏 sub_117E7) */
int fd2_input_process(fd2_state_machine_t* sm);
int fd2_get_key_code(void);

/* 第二层: 场景生命周期 (对应原游戏 funcs_25E23/funcs_25E3A) */
void fd2_scene_init(fd2_state_machine_t* sm, int scene_id);
void fd2_scene_exit(fd2_state_machine_t* sm, int scene_id);
int fd2_scene_check_complete(fd2_state_machine_t* sm, int scene_id);

/* 第三层: 场景交互循环 (对应原游戏 sub_26152) */
int fd2_scene_interact_loop(fd2_state_machine_t* sm);
int fd2_scene_handle_key(fd2_state_machine_t* sm);
void fd2_scene_render_update(fd2_state_machine_t* sm);

/* 场景切换控制 */
void fd2_set_scene_state(fd2_state_machine_t* sm, int state);
void fd2_switch_scene(fd2_state_machine_t* sm, int scene_id);
void fd2_switch_subscene(fd2_state_machine_t* sm, int subscene_id);

/* 菜单系统 */
void fd2_menu_navigate(fd2_state_machine_t* sm, int direction);
void fd2_menu_confirm(fd2_state_machine_t* sm);
int fd2_menu_get_index(fd2_state_machine_t* sm);

/* 场景注册 */
void fd2_register_all_scenes(fd2_state_machine_t* sm);
int fd2_register_scene(fd2_state_machine_t* sm,
                       int scene_id,
                       fd2_scene_init_fn init_fn,
                       fd2_scene_exit_fn exit_fn,
                       fd2_scene_check_fn check_fn,
                       u8 music_id,
                       u8 is_special,
                       const char* name);

int fd2_register_special_event(fd2_state_machine_t* sm,
                                int event_id,
                                fd2_special_event_fn event_fn);

/* 工具函数 */
int fd2_wait_vsync(void);
int fd2_check_anim_frame(fd2_state_machine_t* sm);
void fd2_update_anim_frame(fd2_state_machine_t* sm);

#endif /* FD2_STATE_MACHINE_H */
