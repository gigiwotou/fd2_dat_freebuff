# FD2 场景播放系统实现

> 实现时间：2026-04-28  
> 基于：IDA MCP 分析结果

## 概述

本文档记录了炎龍騎士團2 (FD2) 场景播放系统的实现细节。该系统负责播放游戏中的剧情动画，包括角色移动、动画播放和场景切换。

---

## 1. IDA MCP 分析总结

### 1.1 关键函数

| 函数 | 地址 | 功能 |
|------|------|------|
| sub_1366A | 0x1366A | 场景播放器 - 解析场景数据并执行命令 |
| sub_15F84 | 0x15F84 | 场景绘制函数 - 渲染场景背景和角色精灵 |
| sub_165AC | 0x165AC | 角色动画加载和渲染 |
| sub_16B43 | 0x16B43 | 动画序列显示 |
| sub_4EB48 | 0x4EB48 | 获取场景数据: `return *(&off_627D8 + scene_id)` |

### 1.2 场景数据表

- **地址**: 0x627D8 (硬编码在exe数据段中)
- **格式**: 每个场景由命令列表组成
- **命令格式**: 类型(1字节) + 参数数量(1字节) + 参数(2字节每个)

### 1.3 场景ID列表

从sub_3231B分析得到的场景播放序列：
- 99: 开场动画
- 100-105: 开场剧情场景
- 90-98: 战斗入场场景
- 0-5: 战场场景

---

## 2. 实现的文件

### 2.1 fd2_scene.h

定义了场景播放系统的数据结构和API：

```c
/* 场景命令类型 */
typedef enum {
    SCENE_CMD_END = 0xFF,          /* 场景结束 */
    SCENE_CMD_LINE_BREAK = 0xFE,   /* 切换行/层 */
    SCENE_CMD_CHAR_SPRITE = 0xEF,  /* 加载角色精灵 */
    SCENE_CMD_CHAR_SPRITE_ALT = 0xEE,  /* 备用精灵加载 */
    SCENE_CMD_CHAR_STATE_LOAD = 0xED,  /* 从角色状态加载 */
    SCENE_CMD_CHAR_ANIM = 0xEC,    /* 角色动画 */
    SCENE_CMD_MOVE = 0x00,         /* 移动命令 */
    SCENE_CMD_WAIT = 0x01,         /* 等待/延迟 */
    SCENE_CMD_FADE = 0x02,         /* 淡入淡出效果 */
    SCENE_CMD_SHOW = 0x03,         /* 显示/隐藏元素 */
    SCENE_CMD_EFFECT = 0x04,       /* 特殊效果 */
    SCENE_CMD_POSITION = 0x05,     /* 设置位置 */
} scene_cmd_type_t;

/* 场景命令 */
typedef struct {
    u8  type;                  /* 命令类型 */
    u8  param_count;           /* 参数数量 */
    u16 params[SCENE_MAX_PARAMS];  /* 命令参数 */
} scene_cmd_t;

/* 角色状态 (80字节/角色) */
typedef struct {
    u16 char_id;               /* 角色ID */
    u16 sprite_id;             /* DATO.DAT中的精灵索引 */
    u8  action;                /* 当前动作 */
    u8  frame;                 /* 动画帧 */
    u16 x, y;                  /* 屏幕坐标 */
    s16 dx, dy;                /* 每帧移动增量 */
    /* ... 更多字段 */
} scene_char_state_t;

/* 场景播放器状态 */
typedef struct {
    int current_scene_id;      /* 当前场景ID */
    int current_cmd_idx;       /* 当前命令索引 */
    const scene_data_t* scene; /* 当前场景数据 */
    scene_char_state_t characters[32];  /* 角色状态数组 */
    bool playing;              /* 是否正在播放 */
    /* ... 更多字段 */
} scene_player_t;
```

### 2.2 fd2_scene.c

实现了完整的场景播放逻辑：

- **scene_player_init()**: 初始化场景播放器
- **scene_player_play()**: 播放指定ID的场景
- **scene_player_update()**: 每帧更新场景状态
- **scene_player_render()**: 渲染当前场景到屏幕
- **scene_execute_cmd()**: 执行单个场景命令
- **scene_get_data()**: 获取场景数据

### 2.3 场景数据示例

```c
/* 场景0 - 第一个战场场景 */
static const scene_cmd_t scene_0_cmds[] = {
    { .type = 0x06, .param_count = 1, .params = {0x0004} },
    { .type = 0x00, .param_count = 2, .params = {0x0001, 0x0002} },
    /* ... 更多命令 */
};

/* 场景99 - 开场动画 */
static const scene_cmd_t scene_99_cmds[] = {
    { .type = 0x05, .param_count = 6, .params = {0x0001, 0x0002, ...} },
    /* ... 更多命令 */
};
```

---

## 3. 游戏状态机集成

### 3.1 新增状态

在fd2_game.h中添加了新的游戏状态：

```c
typedef enum {
    /* ... 其他状态 ... */
    FD2_STATE_CHAR_SELECT,    /* 角色选择 */
    FD2_STATE_CUTSCENE,       /* 剧情播放 (新增) */
    FD2_STATE_BATTLE,         /* 战斗 */
    /* ... */
} fd2_state_t;
```

### 3.2 游戏上下文扩展

```c
typedef struct fd2_game {
    /* ... 原有字段 ... */
    
    /* 剧情状态 */
    scene_player_t   scene_player;     /* 场景播放器 */
    int              cutscene_sequence[32];  /* 场景序列 */
    int              cutscene_count;   /* 场景数量 */
    int              cutscene_index;   /* 当前场景索引 */
} fd2_game_t;
```

### 3.3 状态处理函数

```c
static void state_cutscene_enter(fd2_game_t* game);
static fd2_state_t state_cutscene_update(fd2_game_t* game);
static void state_cutscene_exit(fd2_game_t* game);
```

**状态转换流程**:
```
MENU (选择Start) → CUTSCENE (播放场景99) → CUTSCENE (播放更多场景) → BATTLE
```

### 3.4 菜单修改

修改了state_menu_update()函数，使1 Player模式直接进入剧情播放：

```c
case 0:  /* 1 Player - Play cutscenes then battle */
    game->game_mode = 0;
    game->cutscene_sequence[0] = 99;  /* 开场动画 */
    game->cutscene_count = 1;
    return FD2_STATE_CUTSCENE;
```

---

## 4. 构建系统

### 4.1 Makefile更新

添加了fd2_scene.c到构建系统：

```makefile
GAME_SRCS = ... $(SRC_DIR)/fd2_scene.c ...
GAME_OBJS = ... $(OBJ_DIR)/fd2_scene.o ...
```

---

## 5. 待完成的工作

### 5.1 场景数据完善

当前只实现了场景0、99、100的完整数据。需要从IDA MCP提取更多场景：
- 场景101-105 (开场剧情)
- 场景90-98 (战斗入场)
- 场景1-5 (其他战场场景)

### 5.2 精灵渲染集成

需要实现sub_15F84的完整渲染逻辑：
- 从DATO.DAT加载角色精灵
- 根据角色状态绘制精灵到屏幕
- 处理透明度和动画帧

### 5.3 完整场景序列

根据原游戏流程，完整的场景序列应该是：
```
99 → 100 → 101 → 102 → 103 → 104 → 105 → 90 → 91 → ... → 98 → 0 → 1 → 2 → 5
```

需要在state_cutscene_enter()中正确设置这个序列。

---

## 6. 编译说明

由于当前环境缺少MSYS2 GCC，代码尚未编译测试。编译需要：

1. 安装MSYS2和ucrt64工具链
2. 安装SDL2开发库
3. 运行 `make game` 或 `.\build.bat`

---

## 7. 参考资料

- [IDA MCP分析文档](./fd2_game_start_and_cutscene.md)
- [场景数据解析工具](../tools/parse_scenes.py)
- [场景数据简单解析器](../tools/parse_scene_simple.py)
