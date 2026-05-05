#ifndef FD2_SCENE_MANAGER_H
#define FD2_SCENE_MANAGER_H

#include "fd2_types.h"
#include "fd2_state_machine.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================
 * FD2 场景管理系统 (对应原游戏 sub_25EBB, sub_26152, sub_22E5C)
 *
 * 原游戏场景架构:
 * - funcs_25E3A[30]: 场景初始化/清理函数数组
 * - funcs_25E23[30]: 场景处理函数数组
 * - funcs_1197B[30]: 场景完成条件检查
 * - funcs_1199C[256]: 特殊事件处理函数
 * ======================================================================== */

/* 场景数据结构 (对应FD2.SAV中的2600字节/场景) */
typedef struct {
    u8 sceneData[12587];      /* 前12587字节保留数据 */
    u8 sceneEntries[2600];    /* 2600字节场景条目数据 */
    u8 sceneId;               /* 场景ID (n17) */
    u8 subSceneId;            /* 子场景ID (dword_53BFB) */
    u32 someValue;            /* n6_6 */
    u8 flag1;                 /* byte_51AAB */
    u8 flag2;                 /* byte_53AF9 */
    u8 n127;                  /* n127 */
    u8 flag3;                 /* byte_51E62 */
    u8 padding[3];            /* 填充 */
} fd2_scene_entry_t;

/* 场景条目 (80字节/条目) */
typedef struct {
    u8 field0;
    u8 field1;
    u8 field2;
    u8 field3;
    u8 field4;
    u8 field5;                /* 标志位 (与0x85测试) */
    u8 fieldType;             /* 类型 (==2表示可交互) */
    u8 field7;                /* 标志 (121表示禁用) */
    u8 field8;
    u8 field9;
    u8 field10;
    u8 field11;
    u8 field12;
    u8 field13;
    u8 field14;
    u8 field15;
    u8 field16;
    u8 field17;
    u8 field18;
    u8 field19;
    u8 field20;
    u8 field21;
    u8 field22;
    u8 field23;
    u8 field24;
    u8 field25;
    u8 field26;
    u8 field27;
    u8 field28;
    u8 field29;
    u8 field30;
    u8 field31;               /* 标志 (10表示禁用) */
    u8 field32;
    u8 field33;
    u8 field34;
    u8 field35;
    u8 field36;
    u8 field37;
    u8 field38;               /* 标志 */
} fd2_scene_item_t;

/* 场景管理器上下文 */
typedef struct {
    fd2_state_machine_t* sm;
    
    /* 当前场景状态 */
    int currentScene;         /* n17 - 当前场景ID (0-29) */
    int subSceneId;           /* dword_53BFB - 子场景ID */
    int sceneItemCount;       /* n6_0 - 场景条目数量 */
    
    /* 场景数据缓冲 */
    void* sceneDataBuffer;    /* 22987字节存档数据 */
    u8* currentSceneData;     /* 当前场景的2560字节数据 */
    
    /* FD2.SAV加载的状态 */
    u32 someValue;            /* n6_6 */
    u8 flag1;                 /* byte_51AAB */
    u8 flag2;                 /* byte_53AF9 */
    u8 n127;                  /* n127 */
    u8 flag3;                 /* byte_51E62 */
    
    /* 场景条目指针 */
    u8* sceneItems;           /* dword_53BF7 - 当前场景条目数据 */
    u8* sceneItemActive;      /* dword_53A45 - 活动条目指针 */
    
    /* 交互状态 */
    int selectedItem;         /* dword_53AE9 - 当前选中条目 */
    int menuIndex;            /* n5 - 菜单索引 (0-5) */
    int animFrame;            /* dword_53F52 - 动画帧 (0-3) */
    
    /* 图标数据 */
    void* fdiconData;         /* dword_53A55 - FDICON.B24数据 */
    void* fdiconHandle;       /* v4 - FDICON.B24文件句柄 */
    
    /* 其他状态 */
    int n3_3;                 /* 存档场景索引 */
    int dword_53A51;          /* 标志 */
    int dword_53A61;          /* 未知 */
    int dword_53F56;          /* 场景图形数据指针 */
    int dword_53F5A;          /* FDOTHER.DAT索引10数据 */
    int dword_53F66;          /* FDOTHER.DAT索引13数据 */
    int dword_53EEC;          /* 未知 */
    int dword_53EC8;          /* 未知 */
} fd2_scene_manager_t;

/* 场景管理器生命周期 */
int fd2_scene_manager_init(fd2_scene_manager_t* mgr, fd2_state_machine_t* sm);
void fd2_scene_manager_shutdown(fd2_scene_manager_t* mgr);

/* sub_25EBB: 状态管理主函数 */
int fd2_state_management(fd2_scene_manager_t* mgr, int state);

/* sub_26152: 场景主逻辑 */
bool fd2_scene_main_loop(fd2_scene_manager_t* mgr);

/* sub_22E5C: 场景初始化 */
void fd2_scene_initialize(fd2_scene_manager_t* mgr);

/* FD2.SAV加载 */
int fd2_load_save_data(fd2_scene_manager_t* mgr, const char* filename);

/* 场景切换 */
void fd2_scene_manager_switch(fd2_scene_manager_t* mgr, int sceneId);

/* 场景条目处理 */
int fd2_process_scene_item(fd2_scene_manager_t* mgr, int itemIndex);

/* 场景渲染 */
void fd2_render_scene(fd2_scene_manager_t* mgr);

#ifdef __cplusplus
}
#endif

#endif /* FD2_SCENE_MANAGER_H */
