# FD2 游戏状态机与循环分析

**更新日期**: 2026-04-30
**基于**: 代码分析 + IDA MCP反编译

---

## 一、整体架构

FD2使用**状态机模式**管理游戏流程，通过`fd2_game_run()`主循环驱动。

### 主循环结构 (fd2_game.c:1961-1997)

```c
int fd2_game_run(fd2_game_t* game) {
    fd2_state_t next_state = game->current_state;
    bool running = true;

    while (running) {
        /* ---- 1. 状态切换 ---- */
        if (next_state != game->current_state) {
            if (exit_fn) exit_fn(game);  // 退出旧状态
            game->current_state = next_state;
            if (enter_fn) enter_fn(game);  // 进入新状态
        }

        /* ---- 2. 事件处理 ---- */
        fd2_input_update(&game->input);  // 读取键盘/手柄输入

        /* ---- 3. 状态更新 ---- */
        next_state = update_fn(game);  // 各状态处理逻辑，返回下一状态

        /* ---- 4. 渲染 ---- */
        // 在各状态的update()中完成渲染

        /* ---- 5. 帧率控制 ---- */
        uint32_t frame_time = GetTickCount() - frame_start;
        if (frame_time < FRAME_TIME_MS) {
            Sleep(FRAME_TIME_MS - frame_time);
        }
        /* 目标帧率: 60 FPS (16.67ms/帧) */
    }

    return 0;
}
```

---

## 二、状态定义

### 2.1 状态枚举 (fd2_game.h)

```c
typedef enum {
    FD2_STATE_MENU,        // 主菜单
    FD2_STATE_INTRO,       // 开场动画
    FD2_STATE_CHAR_SELECT, // 角色选择
    FD2_STATE_BATTLE,      // 战斗地图
    FD2_STATE_CUTSCENE,    // 剧情场景
    FD2_STATE_DEMO,        // 演示模式
    FD2_STATE_VICTORY,     // 胜利画面
    FD2_STATE_GAME_OVER,   // 游戏结束
    FD2_STATE_CONTINUE,    // 继续游戏
} fd2_state_t;
```

---

## 三、Start按钮后的状态流转

### 3.1 菜单状态 (MENU)

**入口**: `state_menu_enter()` (fd2_game.c:1264-1309)

**资源加载**:
- FDOTHER.DAT[8]: 菜单调色板
- BG.DAT: 背景图像
- FDOTHER.DAT[6]: 菜单背景
- FDOTHER.DAT[90]: 菜单项

**渲染**: 绘制菜单背景和菜单项

**更新逻辑**: `state_menu_update()` (fd2_game.c:1521-1673)

```c
static fd2_state_t state_menu_update(fd2_game_t* game) {
    /* 检测输入 */
    if (FD2_ACTION_START按下) {
        if (当前选中"开始游戏") {
            game->map_index = 32;  // 设置地图ID
            printf("[MENU] Starting 1P story mode - Map 32\n");
            return FD2_STATE_BATTLE;  // 直接进入战斗
        }
    }
    
    /* 上下箭头移动菜单选择 */
    if (FD2_ACTION_UP && 未播放动画) 移动选择;
    if (FD2_ACTION_DOWN && 未播放动画) 移动选择;
    
    /* ESC返回演示模式 */
    if (FD2_ACTION_ESCAPE) return FD2_STATE_DEMO;
    
    return FD2_STATE_MENU;
}
```

**返回**: `FD2_STATE_BATTLE`（选择Start后）

---

### 3.2 战斗状态 (BATTLE) ⭐

**入口**: `state_battle_enter()` (fd2_game.c:1810-1849)

**资源加载**:
```c
fd2_resources_load_dat(FD2_DAT_FDFIELD);   // 地图数据
fd2_resources_load_dat(FD2_DAT_FDSHAP);    // 瓦片集
fd2_resources_load_dat(FD2_DAT_FDOTHER);   // 调色板
```

**地图加载**:
```c
fd2_map_load_from_dat(&data->map, map_id, 
                      fdfield_path, fdshap_path, fdother_path);
// map_id = 32 (当前设置的第一关)
```

**更新逻辑**: `state_battle_update()` (fd2_game.c:1851-1890)

```c
static fd2_state_t state_battle_update(fd2_game_t* game) {
    state_battle_data_t* data = game->state_data;

    /* 1. 输入处理 */
    if (FD2_ACTION_ESCAPE) {
        return FD2_STATE_MENU;  // ESC返回菜单
    }

    /* 2. 地图滚动 */
    int scroll_speed = 8;
    if (FD2_ACTION_UP)    data->scroll_y -= scroll_speed;
    if (FD2_ACTION_DOWN)  data->scroll_y += scroll_speed;
    if (FD2_ACTION_LEFT)  data->scroll_x -= scroll_speed;
    if (FD2_ACTION_RIGHT) data->scroll_x += scroll_speed;

    /* 3. 边界限制 */
    data->scroll_x = clamp(0, scroll_x, max_x);
    data->scroll_y = clamp(0, scroll_y, max_y);

    /* 4. 渲染地图 */
    if (data->map.loaded && data->map.map_rendered) {
        fd2_map_render(&data->map, screen, FD2_SCREEN_W, FD2_SCREEN_H,
                       data->scroll_x, data->scroll_y);
        fd2_render_present(&game->render);
    }

    /* 5. 保持战斗状态 */
    return FD2_STATE_BATTLE;
}
```

**关键特征**:
- **无限循环**: 只要不按ESC，一直返回`FD2_STATE_BATTLE`
- **持续渲染**: 每帧都重新渲染地图
- **输入驱动**: 只响应方向键（滚动）和ESC（退出）
- **无角色逻辑**: 当前没有角色移动、战斗等逻辑

**退出**:
- 按ESC → `FD2_STATE_MENU`
- 未来可扩展：移动到下一关 → 加载新地图
- 未来可扩展：战斗结束 → `FD2_STATE_VICTORY`

---

### 3.3 状态流程图

```
游戏启动
    ↓
[INTRO] 开场动画
    ↓ (自动)
[MENU] 主菜单
    ↓ (选择"开始游戏" + Start)
[BATTLE] 战斗地图  ←────────────────┐
    ↓ (按ESC)                        │
[MENU] 主菜单 ──(选择"开始游戏")──────┘
```

---

## 四、IDA反编译对比

### 4.1 游戏中的sub_205DA (0x205DA)

IDA反编译的地图加载函数：

```c
void sub_205DA() {
    sub_3702F(20);
    dword_51A83 = 0;
    n2_0 = 0;
    sub_1088D(n17);  // 加载地图（n17是地图索引）
    memset(dword_53AD5, 0, 32);
    dword_53AA9 = 0;
    dword_53AAD = 0;
    dword_53AB1 = 0;
    dword_53AB5 = 0;
    n2_2 = 0;
    n2_1 = 0;
    v5 = sub_11CAC(1);  // 初始化战斗系统
    dword_51A83 = 1;
    sub_1F525(v5);  // 启动战斗循环
    dword_53BEF = 1;
    JUMPOUT(0x17EE8);  // 跳转到主循环
}
```

**对应我们的代码**: `state_battle_enter()` + `state_battle_update()`

### 4.2 游戏中的sub_31C49 (0x31C49)

另一个地图加载入口（测试用）：

```c
void sub_31C49() {
    sub_1088D(30);  // 硬编码加载地图30
    // ... 后续处理
}
```

---

## 五、当前实现的BATTLE状态逻辑循环

### 5.1 伪代码

```
loop {
    /* ---- 帧开始 ---- */
    frame_start = GetTickCount();

    /* ---- 1. 读取输入 ---- */
    keys = poll_keyboard();
    update_action_state(keys);

    /* ---- 2. 处理输入 ---- */
    if (ESC按下) {
        return FD2_STATE_MENU;  // 退出战斗
    }

    /* ---- 3. 更新地图滚动 ---- */
    if (UP按下)    scroll_y -= 8;
    if (DOWN按下)  scroll_y += 8;
    if (LEFT按下)  scroll_x -= 8;
    if (RIGHT按下) scroll_x += 8;

    /* ---- 4. 边界检查 ---- */
    scroll_x = clamp(scroll_x, 0, map_width - screen_width);
    scroll_y = clamp(scroll_y, 0, map_height - screen_height);

    /* ---- 5. 渲染地图 ---- */
    if (map已加载 && map已渲染) {
        render_map(screen, scroll_x, scroll_y);
        present(screen);  // 显示到屏幕
    }

    /* ---- 6. 帧率控制 ---- */
    elapsed = GetTickCount() - frame_start;
    if (elapsed < 16.67ms) {
        sleep(16.67ms - elapsed);
    }

    /* ---- 7. 保持循环 ---- */
    return FD2_STATE_BATTLE;  // 继续下一帧
}
```

### 5.2 循环频率

- **目标帧率**: 60 FPS
- **帧时间**: 16.67毫秒
- **实际循环**: 取决于渲染耗时和Sleep时间

### 5.3 关键变量

| 变量 | 类型 | 说明 |
|------|------|------|
| scroll_x | int | 地图X轴滚动位置 |
| scroll_y | int | 地图Y轴滚动位置 |
| scroll_speed | int | 滚动速度（当前=8像素/帧） |
| max_x | int | X轴最大滚动（map_width - screen_width） |
| max_y | int | Y轴最大滚动（map_height - screen_height） |

---

## 六、未来扩展点

### 6.1 需要添加的逻辑

1. **角色系统**
   - 加载角色精灵（FIGANI.DAT）
   - 角色移动逻辑
   - 角色动画播放

2. **事件系统**
   - 解析事件数据（FDFIELD.DAT的3*map_id+2）
   - 加载事件图标（FDICON.B24）
   - 事件交互逻辑

3. **战斗逻辑**
   - 回合制战斗
   - 技能系统
   - 伤害计算

4. **地图切换**
   - 移动到地图边界 → 加载新地图
   - 剧情触发 → 进入CUTSCENE状态

### 6.2 状态转换扩展

```
[BATTLE] ──(移动到边界)──→ [BATTLE]（新地图）
[BATTLE] ──(触发剧情)──→ [CUTSCENE]
[BATTLE] ──(战斗胜利)──→ [VICTORY]
[BATTLE] ──(战斗失败)──→ [GAME_OVER]
[CUTSCENE] ──(剧情结束)──→ [BATTLE]
[VICTORY] ──(确认)──→ [BATTLE]（下一关）
[GAME_OVER] ──(确认)──→ [CONTINUE] 或 [MENU]
```

---

## 七、调试方法

### 7.1 打印日志

当前BATTLE状态已添加以下日志：

```c
printf("state_battle: loading map %d from DAT files\n", map_id);
printf("state_battle: map %d loaded successfully (%dx%d tiles)\n", ...);
printf("state_battle: palette applied\n");
printf("state_battle: map rendered\n");
```

### 7.2 性能监控

可以添加：
```c
static uint32_t frame_count = 0;
static uint32_t last_fps_time = 0;

frame_count++;
uint32_t now = GetTickCount();
if (now - last_fps_time >= 1000) {
    printf("FPS: %d\n", frame_count);
    frame_count = 0;
    last_fps_time = now;
}
```

### 7.3 状态检查

在循环中添加断言：
```c
assert(game->current_state == FD2_STATE_BATTLE);
assert(data->map.loaded);
assert(data->scroll_x >= 0 && data->scroll_x <= max_x);
assert(data->scroll_y >= 0 && data->scroll_y <= max_y);
```

---

## 八、总结

### 8.1 Start后的完整流程

1. **菜单状态** (MENU)
   - 用户看到主菜单
   - 上下箭头选择"开始游戏"
   - 按Start按钮

2. **状态切换** (MENU → BATTLE)
   - `state_menu_update()` 返回 `FD2_STATE_BATTLE`
   - `state_menu_exit()` 清理菜单资源
   - `state_battle_enter()` 加载地图资源

3. **战斗循环** (BATTLE)
   - 持续读取输入
   - 处理地图滚动
   - 渲染地图
   - 保持60 FPS
   - 按ESC退出

### 8.2 关键代码位置

| 功能 | 文件 | 行号 |
|------|------|------|
| 主循环 | fd2_game.c | 1961-1997 |
| 菜单状态 | fd2_game.c | 1264-1673 |
| 战斗状态进入 | fd2_game.c | 1810-1849 |
| 战斗状态更新 | fd2_game.c | 1851-1890 |
| 战斗状态退出 | fd2_game.c | 1892-1899 |
| 地图加载 | fd2_map_loader.c | 200-482 |

---

*分析基于: 代码审查 + IDA MCP反编译*
*更新日期: 2026-04-30*
