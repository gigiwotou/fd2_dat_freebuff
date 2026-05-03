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

### 步骤1: 创建公共头文件

创建所有需要的头文件，定义状态数据结构、函数接口。

### 步骤2: 提取存档加载模块

- 将 `decrypt_battle_save()`、`load_battle_save()`、`calculate_battle_save_checksum()` 等提取到 `fd2_save_load.c`
- 定义 `include/fd2_save_load.h`

### 步骤3: 提取简单状态模块

- INIT、DEMO、CHAR_SELECT、VICTORY、GAME_OVER 提取到 `fd2_states.c`
- 这些状态逻辑简单，可以放在一起

### 步骤4: 提取INTRO状态模块

- 检查现有 `fd2_intro.c`，确定是否需要整合
- 如果现有文件已包含INTRO逻辑，则整合进去
- 否则创建新的 `fd2_states_intro.c`

### 步骤5: 提取MENU状态模块

- 将 `menu_draw()` 和 MENU状态的enter/update/exit提取到 `fd2_menu.c`

### 步骤6: 提取BATTLE状态模块

- 战斗状态最复杂，需进一步拆分：
  - `fd2_battle.c` - 战斗主状态逻辑
  - `fd2_battle_sprite.c` - 精灵系统
  - `fd2_battle_cursor.c` - 光标系统

### 步骤7: 提取CONTINUE状态模块

- 将 CONTINUE状态的enter/update/exit提取到 `fd2_continue.c`

### 步骤8: 提取CUTSCENE状态模块

- 将 CUTSCENE状态的enter/update/exit提取到 `fd2_cutscene.c`

### 步骤9: 重构主游戏核心

- 原 `fd2_game.c` 精简为 `fd2_game_core.c`，仅保留：
  - 状态表定义
  - `fd2_game_init()`
  - `fd2_game_run()`
  - `fd2_game_shutdown()`
  - `fd2_game_register_state()`
  - 工具函数

### 步骤10: 更新构建系统

- 更新 Makefile/CMakeLists.txt 添加新源文件

### 步骤11: 编译验证

- 确保所有模块能正常编译
- 运行程序验证功能一致

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
