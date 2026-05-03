# fd2_game.c 代码重构计划

## 分析结果

`fd2_game.c` 文件目前约3000行，包含以下功能模块：

### 当前文件结构分析

| 行号范围 | 功能模块 | 代码行数 |
|---------|---------|---------|
| 1-137 | 头文件、状态声明、状态表 | ~137行 |
| 85-129 | 工具函数（数据目录查找、路径构建等） | ~45行 |
| 131-293 | 游戏生命周期（init/run/shutdown） | ~162行 |
| 299-353 | INIT状态实现 | ~55行 |
| 355-1383 | INTRO状态实现（含ANM播放、滚动、覆盖层、调色板闪烁等） | ~1028行 |
| 1385-1700 | MENU状态实现（含菜单绘制） | ~315行 |
| 1702-1720 | DEMO状态实现 | ~18行 |
| 1722-1751 | CHAR_SELECT状态实现 | ~29行 |
| 1753-1812 | CUTSCENE状态实现 | ~59行 |
| 1814-2712 | BATTLE状态实现（含光标、精灵、RLE、地图渲染等） | ~898行 |
| 2714-2722 | VICTORY状态实现 | ~8行 |
| 2724-2925 | 存档加载与解密（含checksum等） | ~201行 |
| 2927-3023 | CONTINUE状态实现 | ~96行 |
| 3025-3033 | GAME_OVER状态实现 | ~8行 |

## 重构目标

1. **保持功能1:1不变** - 仅做代码组织结构调整，不修改任何逻辑
2. **按功能模块拆分** - 每个游戏状态独立文件，公共逻辑提取到单独模块
3. **遵循现有项目结构** - 使用 `src/` 目录放 `.c` 文件，`include/` 目录放 `.h` 文件

## 拆分方案

### 新建文件清单

| 文件名 | 来源代码段 | 说明 |
|-------|-----------|------|
| `src/fd2_states.c` | INIT/DEMO/CHAR_SELECT/VICTORY/GAME_OVER | 简单状态实现 |
| `src/fd2_intro.c` | INTRO状态（已有，需重构） | 开场动画（需从现有fd2_intro.c整合） |
| `src/fd2_menu.c` | MENU状态 | 主菜单 |
| `src/fd2_battle.c` | BATTLE状态核心 | 战斗地图 |
| `src/fd2_battle_sprite.c` | BATTLE中的精灵系统 | 地图精灵渲染 |
| `src/fd2_battle_cursor.c` | BATTLE中的光标系统 | 地图光标移动 |
| `src/fd2_save_load.c` | 存档加载解密逻辑 | 通用存档功能 |
| `src/fd2_continue.c` | CONTINUE状态 | 继续游戏 |
| `src/fd2_cutscene.c` | CUTSCENE状态 | 过场动画 |
| `src/fd2_game_core.c` | 原fd2_game.c核心部分 | 游戏主循环、状态机 |

### 头文件清单

| 文件名 | 说明 |
|-------|------|
| `include/fd2_states.h` | 简单状态的声明 |
| `include/fd2_intro.h` | 开场动画状态声明 |
| `include/fd2_menu.h` | 菜单状态声明 |
| `include/fd2_battle.h` | 战斗状态声明（含精灵/光标结构体） |
| `include/fd2_save_load.h` | 存档加载函数声明 |
| `include/fd2_continue.h` | 继续游戏状态声明 |
| `include/fd2_cutscene.h` | 过场动画状态声明 |

## 实施步骤

> **重要：每次拆分后都需要编译验证，确保功能不变。每步完成后提交git。**

### 步骤1: 创建所有头文件

创建以下头文件，定义状态数据结构、函数接口：

#### `include/fd2_states.h`
```c
#ifndef FD2_STATES_H
#define FD2_STATES_H
#include "fd2_game.h"

/* INIT状态 */
void state_init_enter(fd2_game_t* game);
fd2_state_t state_init_update(fd2_game_t* game);
void state_init_exit(fd2_game_t* game);

/* DEMO状态 */
void state_demo_enter(fd2_game_t* game);
fd2_state_t state_demo_update(fd2_game_t* game);
void state_demo_exit(fd2_game_t* game);

/* CHAR_SELECT状态 */
void state_char_select_enter(fd2_game_t* game);
fd2_state_t state_char_select_update(fd2_game_t* game);
void state_char_select_exit(fd2_game_t* game);

/* VICTORY状态 */
void state_victory_enter(fd2_game_t* game);
fd2_state_t state_victory_update(fd2_game_t* game);
void state_victory_exit(fd2_game_t* game);

/* GAME_OVER状态 */
void state_game_over_enter(fd2_game_t* game);
fd2_state_t state_game_over_update(fd2_game_t* game);
void state_game_over_exit(fd2_game_t* game);

#endif
```

#### `include/fd2_intro.h`
```c
#ifndef FD2_INTRO_STATE_H
#define FD2_INTRO_STATE_H
#include "fd2_game.h"

void state_intro_enter(fd2_game_t* game);
fd2_state_t state_intro_update(fd2_game_t* game);
void state_intro_exit(fd2_game_t* game);

#endif
```

#### `include/fd2_menu.h`
```c
#ifndef FD2_MENU_H
#define FD2_MENU_H
#include "fd2_game.h"

void state_menu_enter(fd2_game_t* game);
fd2_state_t state_menu_update(fd2_game_t* game);
void state_menu_exit(fd2_game_t* game);

#endif
```

#### `include/fd2_battle.h`
```c
#ifndef FD2_BATTLE_H
#define FD2_BATTLE_H
#include "fd2_game.h"

/* 光标移动函数 */
void cursor_move_up(void* battle_data, int map_height);
void cursor_move_down(void* battle_data, int map_height);
void cursor_move_left(void* battle_data, int map_width);
void cursor_move_right(void* battle_data, int map_width);

/* 精灵相关函数 */
bool load_map_sprite_icon(void* sprite, int icon_id);
void update_map_sprite_animation(void* sprite);
void move_sprite_to_tile(void* sprite, int new_tile_x, int new_tile_y);

/* BATTLE状态 */
void state_battle_enter(fd2_game_t* game);
fd2_state_t state_battle_update(fd2_game_t* game);
void state_battle_exit(fd2_game_t* game);

#endif
```

#### `include/fd2_save_load.h`
```c
#ifndef FD2_SAVE_LOAD_H
#define FD2_SAVE_LOAD_H
#include <stdint.h>

/* 存档数据结构 */
#define BATTLE_SAVE_SIZE 22987
/* ... 所有宏定义 ... */

typedef struct {
    /* 从fd2_game.c搬移battle_save_data_t完整定义 */
} battle_save_data_t;

/* 解密与加载函数 */
void decrypt_battle_save(uint8_t* data, int size);
int calculate_battle_save_checksum(uint8_t* data, int size);
int load_battle_save(const char* save_path, battle_save_data_t* save);

#endif
```

#### `include/fd2_continue.h`
```c
#ifndef FD2_CONTINUE_H
#define FD2_CONTINUE_H
#include "fd2_game.h"

void state_continue_enter(fd2_game_t* game);
fd2_state_t state_continue_update(fd2_game_t* game);
void state_continue_exit(fd2_game_t* game);

#endif
```

#### `include/fd2_cutscene.h`
```c
#ifndef FD2_CUTSCENE_H
#define FD2_CUTSCENE_H
#include "fd2_game.h"

void state_cutscene_enter(fd2_game_t* game);
fd2_state_t state_cutscene_update(fd2_game_t* game);
void state_cutscene_exit(fd2_game_t* game);

#endif
```

### 步骤2: 提取存档加载模块

- 从 `fd2_game.c` 复制 `BATTLE_SAVE_SIZE` 宏、`battle_save_data_t`、`rol16()`、`decrypt_battle_save()`、`calculate_battle_save_checksum()`、`load_battle_save()` 到 `src/fd2_save_load.c`
- `fd2_game.c` 中 `#include "fd2_save_load.h"`

### 步骤3: 提取简单状态模块

- 将 INIT、DEMO、CHAR_SELECT、VICTORY、GAME_OVER 的 enter/update/exit 函数复制到 `src/fd2_states.c`
- 包含 `state_init_data_t` 结构体定义

### 步骤4: 提取INTRO状态模块

- 将 `state_intro_data_t`、所有 `intro_*` 辅助函数、`state_intro_enter/update/exit` 复制到 `src/fd2_states_intro.c`
- 注意：现有 `fd2_intro.c` 是独立演示程序，不修改

### 步骤5: 提取MENU状态模块

- 将 `state_menu_data_t`、`menu_draw()`、`state_menu_enter/update/exit` 复制到 `src/fd2_menu.c`

### 步骤6: 提取BATTLE状态模块

创建三个文件：
- `src/fd2_battle.c` - 战斗主状态逻辑（enter/update/exit）
- `src/fd2_battle_sprite.c` - 精灵系统（`map_sprite_t`、`load_map_sprite_icon`、`update_map_sprite_animation`、`move_sprite_to_tile`、坐标转换函数）
- `src/fd2_battle_cursor.c` - 光标系统（`cursor_move_*`、`update_camera_from_cursor`、`load_cursor_image`、`decode_rle_image`）

### 步骤7: 提取CONTINUE状态模块

- 将 `state_continue_data_t`、`state_continue_enter/update/exit` 复制到 `src/fd2_continue.c`
- 依赖 `fd2_save_load.h` 中的存档加载函数

### 步骤8: 提取CUTSCENE状态模块

- 将 `state_cutscene_enter/update/exit` 复制到 `src/fd2_cutscene.c`

### 步骤9: 重构主游戏核心

- 原 `fd2_game.c` 精简为 `src/fd2_game_core.c`，仅保留：
  - 所有状态的 forward declarations（改为 include 头文件）
  - `builtin_states[]` 状态表
  - `find_data_dir()`、`fd2_game_data_path()`、`fd2_game_request_quit()`
  - `fd2_game_register_state()`
  - `fd2_game_init()`、`fd2_game_run()`、`fd2_game_shutdown()`

### 步骤10: 更新构建系统

- 查看 `Makefile` 或 `CMakeLists.txt`，添加新源文件到编译列表
- 需要添加的文件：
  - `src/fd2_game_core.c`（替代原 `fd2_game.c`）
  - `src/fd2_states.c`
  - `src/fd2_states_intro.c`
  - `src/fd2_menu.c`
  - `src/fd2_battle.c`
  - `src/fd2_battle_sprite.c`
  - `src/fd2_battle_cursor.c`
  - `src/fd2_save_load.c`
  - `src/fd2_continue.c`
  - `src/fd2_cutscene.c`

### 步骤11: 编译验证

- 执行 `make` 或对应构建命令
- 解决编译错误（头文件缺失、符号未定义等）
- 确保程序能正常运行

### 步骤12: 功能验证

- 运行程序，验证各个状态正常工作：
  - 启动加载（INIT）
  - 开场动画（INTRO）
  - 主菜单（MENU）
  - 战斗场景（BATTLE）
  - 继续游戏（CONTINUE）

## 关键注意事项

1. **状态数据结构的可见性** - 每个状态的结构体（如 `state_intro_data_t`）应放在对应头文件中，对外部不可见
2. **函数命名前缀** - 各模块函数使用统一前缀，如 `intro_`、`menu_`、`battle_` 等
3. **依赖关系** - 新模块仅依赖现有的底层系统（render、input、audio、resources等）
4. **不修改逻辑** - 1:1复制原代码，仅做文件拆分和函数重命名

## 最终文件结构

```
src/
├── fd2_game_core.c       # 游戏核心（主循环、状态机）
├── fd2_states.c          # 简单状态（INIT/DEMO/CHAR_SELECT/VICTORY/GAME_OVER）
├── fd2_intro.c           # INTRO状态（合并现有逻辑）
├── fd2_menu.c            # MENU状态
├── fd2_battle.c          # BATTLE状态核心
├── fd2_battle_sprite.c   # BATTLE精灵系统
├── fd2_battle_cursor.c   # BATTLE光标系统
├── fd2_save_load.c       # 存档加载解密
├── fd2_continue.c        # CONTINUE状态
├── fd2_cutscene.c        # CUTSCENE状态
└── ... (其他现有文件)

include/
├── fd2_game.h            # 已有，不变
├── fd2_states.h          # 简单状态声明
├── fd2_intro.h           # INTRO状态声明
├── fd2_menu.h            # MENU状态声明
├── fd2_battle.h          # BATTLE状态声明
├── fd2_save_load.h       # 存档加载声明
├── fd2_continue.h        # CONTINUE状态声明
└── fd2_cutscene.h        # CUTSCENE状态声明
```
