# FD2 现代化架构计划

**创建日期**: 2026-05-06  
**状态**: 待确认  
**基于**: IDA Pro MCP 反编译分析 + 当前项目状态

---

## 设计目标

1. **1:1还原原游戏** - 所有游戏逻辑基于IDA反编译，不猜测
2. **兼容原版资产** - 100%支持原DAT/B24文件格式
3. **现代化架构** - 清晰的模块分离，易于维护和扩展
4. **MOD支持** - 数据驱动，脚本系统，插件API
5. **确定性** - 固定帧率模拟，行为可重现

---

## 架构分层

```
FD2 Modern Architecture
┌─────────────────────────────────────────────────┐
│           Application Layer (app/)              │
│  ┌──────────┬──────────┬──────────┬──────────┐  │
│  │  main.c  │ config.c │  mods.c  │ input.c │  │
│  └──────────┴──────────┴──────────┴──────────┘  │
├─────────────────────────────────────────────────┤
│         Platform Abstraction Layer              │
│  ┌──────────┬──────────┬──────────┬──────────┐  │
│  │ video.h  │ audio.h  │ input.h  │  file.h  │  │
│  └──────────┴──────────┴──────────┴──────────┘  │
├─────────────────────────────────────────────────┤
│              Game Core Layer                    │
│  ┌──────────────────────────────────────────┐   │
│  │        Simulation Engine (sim/)          │   │
│  │  ┌────────┬──────┬───────┬──────┬─────┐  │   │
│  │  │ world  │entity│ battle│ map  │event│  │   │
│  │  └────────┴──────┴───────┴──────┴─────┘  │   │
│  └──────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────┐   │
│  │        Data Parser (data/)               │   │
│  │  ┌────┬────┬────┬──────┬─────┬──────┐   │   │
│  │  │ dat│ rle│ afm│palette│xmidi│b24   │   │   │
│  │  └────┴────┴────┴──────┴─────┴──────┘   │   │
│  └──────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────┐   │
│  │        Script Engine (script/)           │   │
│  │  ┌──────────┬──────────┬──────────┐      │   │
│  │  │  vm.c    │  api.c   │  mod.c   │      │   │
│  │  └──────────┴──────────┴──────────┘      │   │
│  └──────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────┐   │
│  │        MOD System (mod/)                 │   │
│  │  ┌──────────┬──────────┬──────────┐      │   │
│  │  │ loader.c │ manager.c│  api.h   │      │   │
│  │  └──────────┴──────────┴──────────┘      │   │
│  └──────────────────────────────────────────┘   │
├─────────────────────────────────────────────────┤
│            Renderer Layer (render/)             │
│  ┌──────────┬──────────┬──────────┬──────────┐  │
│  │pipeline.c│sprite.c  │  ui.c    │effect.c  │  │
│  └──────────┴──────────┴──────────┴──────────┘  │
├─────────────────────────────────────────────────┤
│            SDL2 Platform (platform/)            │
│  ┌──────────┬──────────┬──────────┬──────────┐  │
│  │ sdl_vid.c│ sdl_aud.c│ sdl_inp.c│ sdl_file│  │
│  └──────────┴──────────┴──────────┴──────────┘  │
└─────────────────────────────────────────────────┘
```

---

## 核心设计原则

### 1. 确定性模拟

```c
// 固定帧率模拟，与渲染帧率解耦
typedef struct {
    uint8_t* world_state;      // 世界状态（可序列化）
    uint32_t tick_count;       // 模拟tick数
    uint32_t tick_rate;        // 例如 60 Hz
    uint32_t accumulator;      // 时间累积器
} sim_context_t;

// 核心更新循环
void sim_update(sim_context_t* ctx, uint32_t elapsed_ms) {
    ctx->accumulator += elapsed_ms;
    uint32_t tick_time = 1000 / ctx->tick_rate;
    
    while (ctx->accumulator >= tick_time) {
        sim_process_input(ctx);        // 处理输入
        sim_process_events(ctx);       // 处理事件
        sim_process_scripts(ctx);      // 执行脚本
        sim_update_entities(ctx);      // 更新实体
        ctx->accumulator -= tick_time;
        ctx->tick_count++;
    }
}
```

### 2. 实体组件系统 (ECS)

```c
// 简化的ECS，用于游戏实体管理
typedef uint32_t entity_id_t;

// 组件定义
typedef struct {
    int16_t tile_x, tile_y;          // 地图格子坐标
    uint8_t direction;               // 朝向
    uint8_t anim_frame;              // 动画帧
    uint8_t icon_id;                 // 图标ID
} sprite_component_t;

typedef struct {
    uint16_t hp, max_hp;             // 生命值
    uint16_t mp, max_mp;             // 魔法值
    uint8_t str, def, agi;           // 属性
    uint8_t level;                   // 等级
    uint8_t class_id;                // 职业ID
} stats_component_t;

typedef struct {
    uint16_t script_id;              // 绑定的脚本ID
    uint8_t event_flags[8];          // 事件标志位
    uint8_t dialog_id;               // 对话ID
} npc_component_t;

// 实体管理器
typedef struct {
    entity_id_t next_id;
    sprite_component_t sprites[MAX_ENTITIES];
    stats_component_t stats[MAX_ENTITIES];
    npc_component_t npcs[MAX_ENTITIES];
    bool active[MAX_ENTITIES];
} entity_manager_t;

// 系统处理
void sprite_system_update(entity_manager_t* em, sim_context_t* ctx);
void npc_system_update(entity_manager_t* em, sim_context_t* ctx);
void battle_system_update(entity_manager_t* em, sim_context_t* ctx);
```

### 3. 事件总线

```c
// 事件类型定义
typedef enum {
    // 原版游戏事件
    EVENT_ENTITY_MOVED,              // 实体移动
    EVENT_ENTITY_SELECTED,           // 实体选择
    EVENT_DAMAGE_DEALT,              // 造成伤害
    EVENT_ENTITY_DIED,               // 实体死亡
    EVENT_SCRIPT_TRIGGERED,          // 脚本触发
    EVENT_DIALOG_STARTED,            // 对话开始
    EVENT_DIALOG_FINISHED,           // 对话结束
    EVENT_BATTLE_STARTED,            // 战斗开始
    EVENT_BATTLE_FINISHED,           // 战斗结束
    EVENT_MAP_LOADED,                // 地图加载完成
    
    // MOD扩展事件
    EVENT_MOD_CUSTOM_0,              // MOD自定义事件起点
    EVENT_MOD_CUSTOM_1,
    EVENT_MOD_CUSTOM_2,
    EVENT_MOD_CUSTOM_3,
} event_type_t;

// 事件数据结构
typedef struct {
    event_type_t type;
    uint32_t timestamp;
    uint8_t data[EVENT_DATA_SIZE];   // 事件数据
} game_event_t;

// 事件处理器
typedef void (*event_handler_t)(const game_event_t* event, void* user_data);

// 事件总线API
void event_bus_init(void);
void event_bus_subscribe(event_type_t type, event_handler_t handler, void* user_data);
void event_bus_publish(event_type_t type, const void* data, size_t size);
void event_bus_process(void);  // 在主循环中调用
```

### 4. MOD系统

```c
// MOD定义
typedef struct {
    char id[64];                   // MOD唯一标识
    char name[128];                // MOD名称
    char version[16];              // 版本号
    char author[64];               // 作者
    
    // MOD生命周期
    int (*init)(void);             // MOD初始化
    void (*update)(void);          // MOD每帧更新
    void (*shutdown)(void);        // MOD卸载
    
    // MOD能力声明
    bool overrides_data;           // 是否覆盖数据
    bool adds_scripts;             // 是否添加脚本
    bool adds_events;              // 是否注册事件
    bool adds_ui;                  // 是否添加UI
} mod_definition_t;

// MOD管理器
typedef struct {
    mod_definition_t* mods[MAX_MODS];
    int mod_count;
    char mods_dir[256];            // MOD目录
} mod_manager_t;

// MOD API (暴露给MOD开发者的接口)
typedef struct {
    // 数据访问
    const void* (*get_resource)(const char* dat_name, int index, uint32_t* size);
    void (*override_resource)(const char* dat_name, int index, const void* data, uint32_t size);
    
    // 事件系统
    void (*subscribe_event)(event_type_t type, event_handler_t handler, void* user_data);
    void (*publish_event)(event_type_t type, const void* data, size_t size);
    
    // 脚本系统
    void (*register_script)(uint16_t script_id, script_fn_t fn);
    
    // 实体系统
    entity_id_t (*create_entity)(void);
    void (*add_sprite_component)(entity_id_t id, const sprite_component_t* comp);
    void (*add_stats_component)(entity_id_t id, const stats_component_t* comp);
    void (*add_npc_component)(entity_id_t id, const npc_component_t* comp);
    void (*destroy_entity)(entity_id_t id);
    
    // UI系统
    void (*draw_text)(int x, int y, const char* text, uint8_t color);
    void (*draw_image)(int x, int y, const uint8_t* pixels, int w, int h);
} mod_api_t;
```

### 5. 脚本系统 (Lua集成)

```lua
-- 示例：MOD脚本
-- mods/my_story/script.lua

function on_map_loaded(map_id)
    if map_id == 32 then
        -- 原版开场剧情
        npc.init(15)  -- 初始化15个NPC
        dialog.show(0)  -- 播放对话0
        script.execute(99)  -- 执行脚本99
    end
end

function on_entity_move(entity, x, y)
    if x == 20 and y == 20 then
        event.publish("secret_found", {entity = entity})
    end
end

function on_battle_start(battle_id)
    world.set_music("custom_track_1")
    dialog.show("战斗开始！")
end
```

---

## 实现阶段

### Phase 1: 核心架构重构 (2-3周)

**目标**: 分离关注点，建立现代化基础架构

**任务**:
- [ ] 1.1 创建平台抽象层接口
  - `platform/video.h` - 渲染API
  - `platform/audio.h` - 音频API
  - `platform/input.h` - 输入API
  - `platform/file.h` - 文件API
  - `platform/time.h` - 时间API

- [ ] 1.2 实现SDL2平台层
  - `platform/sdl_video.c` - SDL2渲染实现
  - `platform/sdl_audio.c` - SDL2音频实现
  - `platform/sdl_input.c` - SDL2输入实现
  - `platform/sdl_file.c` - 文件系统实现

- [ ] 1.3 实现事件总线
  - `core/event_bus.h/c` - 事件发布/订阅系统

- [ ] 1.4 实现ECS基础框架
  - `core/sim/entity.h/c` - 实体管理
  - `core/sim/components.h` - 组件定义
  - `core/sim/systems.h/c` - 系统更新

- [ ] 1.5 迁移现有代码到新架构
  - 迁移地图渲染
  - 迁移光标系统
  - 迁移菜单系统
  - 验证行为一致性

**验收标准**:
- 所有现有功能正常工作
- 帧对比测试通过（与原项目对比）
- 新架构编译通过，无内存泄漏

---

### Phase 2: 数据驱动系统 (1-2周)

**目标**: 完善数据解析，支持MOD覆盖

**任务**:
- [ ] 2.1 完善DAT解析器
  - 统一资源加载接口
  - 实现资源缓存系统
  - 添加资源元数据

- [ ] 2.2 实现资源配置系统
  - `core/data/resource_config.h/c`
  - 从JSON/配置加载资源映射
  - 支持运行时重新加载

- [ ] 2.3 实现MOD数据覆盖
  - MOD可以替换任何DAT资源
  - 支持添加新资源
  - 资源优先级系统

- [ ] 2.4 实现MOD加载器基础
  - `core/mod/loader.h/c`
  - 扫描MOD目录
  - 解析MOD元数据
  - 加载MOD DLL/so（可选）

**验收标准**:
- 所有DAT资源正确加载
- MOD可以覆盖原版资源
- 资源加载性能无退化

---

### Phase 3: 脚本系统 (2-3周)

**目标**: 集成Lua，支持MOD脚本

**任务**:
- [ ] 3.1 集成Lua虚拟机
  - 编译Lua到项目
  - 实现脚本VM包装器
  - 实现错误处理

- [ ] 3.2 实现脚本API
  - 暴露游戏API给Lua
  - 世界操作API
  - 实体操作API
  - UI操作API
  - 事件API

- [ ] 3.3 实现MOD脚本加载
  - 自动加载MOD脚本
  - 脚本热重载（开发模式）
  - 脚本沙箱（安全）

- [ ] 3.4 测试脚本系统
  - 编写测试脚本
  - 验证API完整性
  - 性能测试

**验收标准**:
- Lua脚本可以调用所有游戏API
- MOD脚本正确加载和执行
- 脚本错误不会导致崩溃

---

### Phase 4: 剧情系统 (2-3周)

**目标**: 1:1还原原游戏剧情系统

**基于IDA分析**:
- `sub_3231B` - 开场剧情场景
- `sub_1366A` - 剧情脚本执行
- `sub_15F84` - 对话显示
- `sub_135DD` - 事件触发
- `sub_13185` - NPC初始化

**任务**:
- [ ] 4.1 实现剧情脚本解析器
  - 解析原游戏剧情数据
  - 实现脚本VM（基于IDA逻辑）
  - 1:1还原脚本执行顺序

- [ ] 4.2 实现对话系统
  - 对话文本加载 (FDTXT.DAT)
  - 对话UI渲染
  - 对话流程控制
  - 选项分支支持

- [ ] 4.3 实现NPC系统
  - NPC数据加载
  - NPC状态管理
  - NPC交互逻辑
  - NPC移动AI

- [ ] 4.4 实现事件触发系统
  - 事件数据解析 (FDFIELD.DAT)
  - 事件触发条件
  - 事件效果执行
  - 事件标志位管理

- [ ] 4.5 实现开场剧情场景
  - 1:1还原 `sub_3231B` 逻辑
  - NPC初始化序列
  - 对话序列控制
  - 战斗动画演示

**验收标准**:
- 开场剧情1:1还原
- 对话系统正常工作
- NPC系统正常工作
- 事件触发系统正常工作
- 与原游戏行为对比测试通过

---

### Phase 5: 战斗系统 (3-4周)

**目标**: 1:1还原原游戏战斗系统

**基于IDA分析**:
- `sub_1F525` - 战斗主循环
- `sub_11CAC` - 战斗系统初始化
- `sub_32999` - 战斗动画播放

**任务**:
- [ ] 5.1 实现战斗菜单系统
  - 攻击/魔法/物品/逃跑
  - 目标选择
  - 菜单UI渲染

- [ ] 5.2 实现回合制逻辑
  - 行动顺序计算
  - 回合状态管理
  - 玩家/敌人回合切换

- [ ] 5.3 实现战斗状态机
  - 战斗开始
  - 玩家行动
  - 敌人行动
  - 战斗结束判定

- [ ] 5.4 实现伤害计算
  - 攻击公式 (基于IDA逆向)
  - 防御计算
  - 魔法伤害
  - 暴击判定
  - 状态异常

- [ ] 5.5 实现战斗AI
  - 敌人行为逻辑
  - 目标选择策略
  - 技能使用策略
  - 难度调整

- [ ] 5.6 实现战斗动画
  - 攻击动画
  - 技能动画
  - 受伤动画
  - 死亡动画
  - 胜利动画

**验收标准**:
- 战斗系统完整可玩
- 伤害计算与原游戏一致
- 战斗AI正常工作
- 动画播放正确
- 与原游戏行为对比测试通过

---

### Phase 6: MOD系统完善 (2-3周)

**目标**: 完善MOD生态

**任务**:
- [ ] 6.1 MOD配置系统
  - MOD元数据格式 (JSON)
  - MOD依赖管理
  - MOD加载顺序

- [ ] 6.2 MOD数据覆盖
  - 资源替换系统
  - 新资源添加
  - 数据合并策略

- [ ] 6.3 MOD脚本热重载
  - 开发模式热重载
  - 脚本状态保存/恢复
  - 实时调试

- [ ] 6.4 MOD管理UI
  - MOD列表显示
  - MOD启用/禁用
  - MOD配置界面
  - MOD安装/卸载

- [ ] 6.5 MOD文档和示例
  - MOD开发文档
  - API参考手册
  - 示例MOD
  - 教程

**验收标准**:
- MOD可以完整扩展游戏
- MOD管理UI易用
- MOD开发文档完整
- 示例MOD正常工作

---

## 兼容性保证

### 1. 原版资产100%兼容
- 所有DAT/B24文件格式解析保持原样
- 不修改任何原版资源文件
- 解析器基于IDA反编译实现

### 2. 行为1:1还原
- 模拟逻辑基于IDA反编译
- 所有数值计算与原游戏一致
- 动画播放时序一致
- 渲染顺序一致

### 3. 回归测试
- 每阶段都有自动化测试
- 帧对比测试（与原游戏/DOSBox对比）
- 音频事件对比测试
- 输入响应测试

### 4. 可选增强
- MOD增强不影响原版体验
- 可以开关MOD功能
- MOD与原版数据隔离

---

## 扩展性设计

### 1. 插件API
```c
// MOD通过明确定义的API扩展游戏
MOD_API int mod_create_custom_entity(const char* type);
MOD_API void mod_register_custom_event(const char* name, event_handler_t handler);
MOD_API void mod_add_menu_item(const char* label, menu_action_t action);
```

### 2. MOD目录结构
```
mods/my_mod/
├── mod.json              # MOD元数据
├── data/                 # 数据覆盖
│   └── FDOTHER.DAT      # 覆盖原版资源
├── scripts/              # MOD脚本
│   └── main.lua
├── assets/               # 新资源
│   └── custom_anim.afm
└── lib/                  # 可选本地库
    └── my_mod.dll
```

### 3. 脚本扩展
- Lua脚本可以访问完整游戏API
- 可以注册新事件处理器
- 可以创建自定义实体
- 可以修改UI

### 4. 事件扩展
- MOD可以注册自定义事件类型
- 事件可以携带任意数据
- 事件可以跨MOD通信

### 5. UI扩展
- MOD可以添加自定义UI元素
- 支持自定义对话框
- 支持自定义菜单
- 支持自定义HUD

---

## 目录结构

```
fd2_dat_freebuff/
├── src/                          # 源代码
│   ├── app/                      # 应用层
│   │   ├── main.c
│   │   ├── config.c
│   │   └── mods.c
│   │
│   ├── platform/                 # 平台抽象层
│   │   ├── video.h
│   │   ├── audio.h
│   │   ├── input.h
│   │   ├── file.h
│   │   ├── time.h
│   │   ├── sdl_video.c
│   │   ├── sdl_audio.c
│   │   ├── sdl_input.c
│   │   └── sdl_file.c
│   │
│   ├── core/                     # 游戏核心
│   │   ├── sim/                  # 模拟引擎
│   │   │   ├── world.c
│   │   │   ├── entity.c
│   │   │   ├── map.c
│   │   │   ├── battle.c
│   │   │   └── event.c
│   │   │
│   │   ├── data/                 # 数据解析
│   │   │   ├── dat_parser.c
│   │   │   ├── dat_rle.c
│   │   │   ├── dat_afm.c
│   │   │   ├── dat_palette.c
│   │   │   └── dat_xmidi.c
│   │   │
│   │   ├── script/               # 脚本系统
│   │   │   ├── vm.c
│   │   │   ├── api.c
│   │   │   └── mod.c
│   │   │
│   │   ├── mod/                  # MOD系统
│   │   │   ├── loader.c
│   │   │   ├── manager.c
│   │   │   └── api.h
│   │   │
│   │   └── event_bus.c           # 事件总线
│   │
│   ├── render/                   # 渲染层
│   │   ├── pipeline.c
│   │   ├── sprite.c
│   │   ├── ui.c
│   │   └── effect.c
│   │
│   └── legacy/                   # 旧代码（迁移期间保留）
│       ├── fd2_game_core.c
│       ├── fd2_states_intro.c
│       └── ...
│
├── include/                      # 头文件
│   ├── fd2/
│   │   ├── types.h
│   │   ├── sim.h
│   │   ├── entity.h
│   │   ├── event_bus.h
│   │   ├── mod_api.h
│   │   └── ...
│   └── ...
│
├── tools/                        # 工具
│   ├── mod_packager.py           # MOD打包工具
│   ├── dat_inspector.py          # DAT查看器
│   └── ...
│
├── mods/                         # MOD目录
│   └── example_mod/
│       ├── mod.json
│       ├── data/
│       └── scripts/
│
├── docs/                         # 文档
│   ├── mod_development_guide.md
│   ├── api_reference.md
│   └── ...
│
└── output/                       # 测试输出
    └── ...
```

---

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 游戏核心 | C99 | 确定性模拟，无外部依赖 |
| 平台层 | SDL2 | 跨平台支持 |
| 脚本 | Lua 5.4 | 轻量、嵌入简单 |
| 构建 | CMake/Make | 跨平台构建 |
| 测试 | Unity + CMock | C单元测试 |
| MOD格式 | JSON + Lua | 易读易写 |

---

## 关键设计决策（待确认）

### 1. 脚本语言
- **推荐**: Lua 5.4
- **理由**: 轻量、嵌入简单、MOD友好、广泛使用
- **备选**: 不集成脚本语言，使用纯C（开发MOD更复杂）

### 2. MOD热重载
- **优点**: 快速迭代，不需要重启游戏
- **缺点**: 增加复杂度，需要状态管理
- **建议**: 仅在开发模式启用

### 3. MOD管理UI
- **优点**: 用户体验好
- **缺点**: 增加开发工作量
- **建议**: 后期实现

### 4. ECS复杂度
- **完整版**: 更灵活，适合复杂游戏
- **简化版**: 仅用于游戏实体，更简单
- **建议**: 使用简化版，满足需求即可

### 5. Lua沙箱
- **优点**: 防止恶意MOD
- **缺点**: 限制MOD能力
- **建议**: 不提供沙箱，MOD需要信任

### 6. Phase优先级
- **建议顺序**: Phase 1→2→4→5→3→6
- **理由**: 先完成核心功能（剧情+战斗），再完善MOD

---

## 下一步行动

1. 确认以上设计决策
2. 确认Phase优先级
3. 开始实现Phase 1

---

**文档版本**: v1.0  
**最后更新**: 2026-05-06  
**状态**: 待审核
