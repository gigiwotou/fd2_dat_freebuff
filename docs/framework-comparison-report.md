# FD2 原游戏框架 vs 项目实现对比分析报告

**分析日期**: 2026-05-05  
**分析工具**: IDA Pro MCP Server + 项目代码审查  
**原游戏文件**: D:\workspace\fd2ida\FD2\FD2.EXE  
**项目路径**: D:\workspace\fd2_dat_freebuff

---

## 一、总体架构对比

### 1.1 架构模式对比

| 维度 | 原游戏 (FD2.EXE) | 当前项目 | 差异评估 |
|------|------------------|----------|----------|
| 架构模式 | 基于全局变量的16位DOS程序 | 基于结构体的SDL2现代架构 | **架构重构，但核心逻辑映射中** |
| 状态管理 | 3层嵌套状态机 | 扁平化状态枚举 (fd2_state_t) | **重大差异** |
| 渲染系统 | VGA Mode 13h (0xA0000) | SDL2 ARGB8888纹理 | **适配良好** |
| 输入处理 | BIOS中断 int16h/int386 | SDL事件系统 | **适配良好** |
| 音频系统 | AIL (Miles Sound System) | SDL2 Audio | **适配中** |

### 1.2 核心差异总结

```
原游戏架构:
main() → sub_25EBB() → n2_0状态判断 → funcs_25E23/funcs_25E3A → sub_26152()

项目架构:
main() → fd2_game_run() → state_ops[当前状态] → enter/update/exit
```

---

## 二、状态管理系统详细对比

### 2.1 原游戏三层状态机架构

#### 第一层: 主循环状态 (main + sub_25EBB)

**原游戏代码** (从IDA MCP反编译确认):

```c
// main() - 0x25BF4, 大小: 0x2C7
while (1) {
    v14 = sub_25977(18, 0);     // 获取游戏状态
    v15 = sub_25EBB(v14);       // 处理游戏状态, 返回0或-1
    
    if (v15 == 0) {
        do {
            i = sub_117E7(v16, n80, i);  // 第一层状态机调用
            
            if (n2_0 == 1) {
                // 初始化场景
                byte_51AAC = 0;
                sub_22E5C();
                byte_51AAC = 1;
                n2_0 = 0;
                i = 1;
            }
            else if (n2_0 == 2) {
                // 场景交互循环
                byte_51AAC = 0;
                sub_25977(-1, 1);                    // 停止音乐
                funcs_25E23[n17]((unsigned __int8 *)v17);  // 场景初始化
                i = sub_26152();                     // 场景交互
                if (i) {
                    v17 = 1;
                } else {
                    funcs_25E3A[n17]((unsigned __int8 *)v17);  // 场景结束
                    sub_25977((unsigned __int8)byte_51E63[n17], 0);  // 切换音乐
                }
                byte_51AAC = 1;
                n2_0 = 0;
                sub_4E381();
            }
        } while (!i);
        if (i == -1) v17 = 1;
    }
    
    if (v17) {
        sub_37ED8();
        // 退出游戏
        JUMPOUT(0x16F04);
    }
}
```

**关键全局变量**:
- `n17` (0x53C03): 当前场景索引 (0-29)
- `n2_0`: 游戏状态标志 (0=主循环, 1=初始化, 2=场景交互)
- `byte_51AAC` (0x51AAC): 场景激活标志
- `byte_51E63[]` (0x51E63): 场景音乐映射表

#### 第二层: 场景生命周期管理 (funcs_25E23 / funcs_25E3A)

**原游戏数据结构** (从IDA MCP确认):

```c
// funcs_25E3A - 场景结束处理函数数组
// 地址: 0x51D71, 大小: 120字节 (30个函数指针 × 4字节)
void (*funcs_25E3A[30])();

// funcs_25E23 - 场景初始化函数数组
// 地址: 0x51DE9, 大小: 120字节 (30个函数指针 × 4字节)
void (*funcs_25E23[30])();
```

**函数指针数组内容** (已确认):
- `funcs_25E3A[0]` = `sub_3231B` (主菜单/标题场景初始化)
- `funcs_25E3A[1-29]` = 大部分为 `sub_21206` (默认空处理)
- `funcs_25E23[0-29]` = 大部分为 `sub_22EF6` (默认处理)

#### 第三层: 场景交互循环 (sub_26152)

**原游戏核心逻辑** (从IDA MCP反编译确认):

```c
// sub_26152() - 0x26152, 大小: 0x49A
bool sub_26152() {
    // 1. 释放旧场景资源
    if (n8_1) free(n8_1); n8_1 = 0;
    if (FDFIELD_DAT__1) free(FDFIELD_DAT__1); FDFIELD_DAT__1 = 0;
    if (FDSHAP_DAT) free(FDSHAP_DAT); FDSHAP_DAT = 0;
    // ... 更多资源释放
    
    // 2. 加载场景配置
    FILE *_rb = fopen("fdicon.b24", "rb");
    for (n16 = 0; n16 < n16_1; ++n16) {
        sub_11019(*(unsigned char *)(n8_3 + 80*n16 + 7), ...);
    }
    fclose(_rb);
    
    // 3. 检查特殊场景
    if (byte_523E7[n17]) {
        // 特殊场景处理 (对话框/过场)
        // ...
        return 0;
    }
    
    // 4. 普通场景 - 加载图形
    FDSHAP_DAT = malloc(153216);
    dword_53F56 = (int)sub_4E809(n17);
    n5 = 0;  // 初始化菜单选择索引
    
    // 5. 主交互循环
    do {
        sub_265EC(&v20);  // 渲染更新
        
        // 等待按键 (带定时器控制动画帧)
        while (!sub_10620()) {
            if ((MEMORY[0x46C] - v13) >= 4) {
                if (++n3_4 == 4) n3_4 = 0;
                sub_265EC(&v20);
                v13 = MEMORY[0x46C];
            }
        }
        
        // 读取按键
        HIBYTE(n3) = 16;
        v14 = int386(22, &n3, &n3);
        
        // 按键处理
        switch (HIBYTE(n3)) {
            case 0xE0: case 0x52: HIBYTE(n3) = 28; break;  // Insert→回车
            case 0x22:  // Tab - 切换子场景
                if (++n16_1 == 10) n16_1 = 0;
                sub_25977(n16_1, 34, v13, n8, n16_1, 0);
                break;
            case 0x4D:  // 右箭头
                sub_25A96(v14, 77, v13, n8, FDOTHER_DAT__2, 0, 1);
                if (--n5 < 0) n5 = 5;
                break;
            case 0x4B:  // 左箭头
                sub_25A96(v14, 75, v13, n8, FDOTHER_DAT__2, 0, 1);
                if (++n5 > 5) n5 = 0;
                break;
        }
        
        // 确认处理
        n3 = HIBYTE(n3);
        if (HIBYTE(n3) != 28) {
            n3 = (unsigned char)n3;
            if ((unsigned char)n3 != 32) continue;
        }
        
        if (n5 != 2) sub_25A96(n3, v15, v13, n8, FDOTHER_DAT__2, 1, 3);
        sub_2670E(a5, &v20);  // 执行选择
        v21 = v17;
    } while (!v21);
    
    free(FDOTHER_DAT__12);
    return (n5 != 2);
}
```

### 2.2 项目实现状态

#### 当前状态机架构 (`fd2_game.h`):

```c
typedef enum {
    FD2_STATE_NONE = 0,
    FD2_STATE_INIT,           /* 加载资源 */
    FD2_STATE_INTRO,          /* 开场动画 */
    FD2_STATE_MENU,           /* 主菜单 */
    FD2_STATE_DEMO,           /* 演示模式 */
    FD2_STATE_CHAR_SELECT,    /* 角色选择 */
    FD2_STATE_CUTSCENE,       /* 过场动画 */
    FD2_STATE_BATTLE,         /* 战斗 */
    FD2_STATE_VICTORY,        /* 胜利 */
    FD2_STATE_CONTINUE,       /* 继续游戏 */
    FD2_STATE_GAME_OVER,      /* 游戏结束 */
    FD2_STATE_QUIT,           /* 退出 */
    FD2_STATE_COUNT
} fd2_state_t;

typedef struct fd2_state_ops {
    void (*enter)(struct fd2_game* game);
    fd2_state_t (*update)(struct fd2_game* game);
    void (*exit)(struct fd2_game* game);
} fd2_state_ops_t;
```

#### 项目主循环 (`fd2_game_core.c`):

```c
int fd2_game_run(fd2_game_t* game) {
    // 调用enter
    const fd2_state_ops_t* init_ops = game->state_ops[game->current_state];
    if (init_ops && init_ops->enter) init_ops->enter(game);
    
    while (game->running && game->current_state != FD2_STATE_QUIT) {
        fd2_input_begin_frame(&game->input);
        
        // SDL事件处理
        while (SDL_PollEvent(&e)) {
            // ...
            fd2_input_process_event(&game->input, &e);
        }
        
        // 调用update, 返回下一个状态
        const fd2_state_ops_t* ops = game->state_ops[game->current_state];
        if (ops && ops->update) {
            fd2_state_t next = ops->update(game);
            
            if (next != game->current_state && next != FD2_STATE_NONE) {
                if (ops->exit) ops->exit(game);
                game->state_data = NULL;
                game->current_state = next;
                const fd2_state_ops_t* new_ops = game->state_ops[next];
                if (new_ops && new_ops->enter) new_ops->enter(game);
            }
        }
        
        // 帧率控制 (60 FPS)
        game->frame_count++;
    }
    
    return 0;
}
```

### 2.3 状态机差异分析

| 对比项 | 原游戏 | 项目实现 | 差异程度 |
|--------|--------|----------|----------|
| 状态层级 | 3层嵌套 | 1层扁平化 | **重大差异** |
| 场景数量 | 30个场景 (n17: 0-29) | 12个状态枚举 | **映射不完整** |
| 场景生命周期 | funcs_25E23 → sub_26152 → funcs_25E3A | enter → update → exit | **结构不同** |
| 场景切换驱动 | n2_0变量 + 函数指针数组 | update()返回值 | **驱动方式不同** |
| 子场景系统 | n16_1 (0-9) + Tab键切换 | 无实现 | **缺失** |
| 场景完成条件 | funcs_1197B数组检查 | 无实现 | **缺失** |
| 场景索引管理 | n17变量动态切换 | 状态枚举固定切换 | **灵活性差异** |

**关键缺失**:
1. **场景生命周期函数数组** (`funcs_25E23` / `funcs_25E3A`) - 未实现
2. **场景完成条件检查** (`funcs_1197B`) - 未实现
3. **子场景切换系统** (n16_1变量) - 未实现
4. **场景交互循环** (`sub_26152`) - 未实现
5. **场景音乐切换** (`sub_25977`) - 未完整实现
6. **场景完成标志** (`n2_0`) - 未实现

---

## 三、绘制框架对比

### 3.1 原游戏绘制架构

**渲染管道** (原游戏):

```
数据加载 → 后备缓冲 → 格式转换 → 元素渲染 → 调色板 → 垂直同步 → 屏幕刷新
   ↓          ↓          ↓          ↓          ↓         ↓          ↓
 文件读取   malloc    320→456   文本/图形  VGA DAC   等待回扫   memmove
```

**核心渲染函数** (已确认存在):

| 函数 | 地址 | 大小 | 功能 | 状态 |
|------|------|------|------|------|
| `sub_15F84` | 0x15F84 | 0x564 | 文本/UI渲染引擎 | ✅ 已分析 |
| `sub_4EBFF` | 0x4EBFF | - | 正向BitBlt | ✅ 已分析 |
| `sub_4EC31` | 0x4EC31 | - | 反向BitBlt (镜像) | ✅ 已分析 |
| `sub_4ED7A` | 0x4ED7A | - | 16x16字符渲染 | ✅ 已分析 |
| `sub_11D40` | 0x11D40 | 0xB2 | VGA调色板设置 | ✅ 已分析 |
| `sub_19953` | 0x19953 | 0x4A4 | 场景主渲染循环 | ✅ 已分析 |
| `sub_2670E` | 0x2670E | 0x288 | 场景特效和过渡 | ✅ 已分析 |
| `sub_190AC` | 0x190AC | 0x4BF | 场景交互和绘制 | ✅ 已分析 |
| `sub_165AC` | 0x165AC | 0x2B0 | 精灵加载/处理 | ✅ 已分析 |
| `sub_16B43` | 0x16B43 | 0x114 | 精灵释放 | ✅ 已分析 |
| `sub_16C57` | 0x16C57 | 0x1CD | 精灵渲染 | ✅ 已分析 |
| `sub_11EB0` | 0x11EB0 | 0x3E | 文本渲染辅助 | ✅ 已分析 |
| `sub_164E8` | 0x164E8 | 0x71 | 刷新显示 | ✅ 已分析 |
| `sub_16559` | 0x16559 | 0x53 | 显示控制 | ✅ 已分析 |
| `sub_10620` | 0x10620 | 0x32 | 垂直同步等待 | ✅ 已分析 |

**双缓冲系统** (原游戏):

```c
// 主缓冲区: 0xA0000 (VGA显存, 十进制655360)
// 后备缓冲区: n655360_0 (malloc分配)
// 格式转换缓冲区: n655360 + 32904 (456字节/行格式)

// 页面翻转流程:
memmove(655360, n655360_0, 64000);  // 后备→主缓冲

for (n200 = 0; n200 < 200; ++n200) {
    memmove(456*(n200-4) + n655360 + 32900, 
            &n655360_0[320*n200], 320);  // 格式转换
}

// 渲染到后备缓冲
// ... sub_4EBFF, sub_15F84, sub_4EC31 ...

while (!sub_10620());  // 等待垂直同步
sub_11D40(...);  // 更新调色板
```

**行跨度转换** (320 → 456):
- 320: 实际像素宽度
- 456: 包含额外数据的行跨度 (用于特殊效果或对齐)
- 转换公式: `456 * (行号 - 4) + 32900`

### 3.2 项目实现状态

**渲染系统** (`fd2_render.h` / `fd2_render.c`):

```c
typedef struct fd2_render {
    void*   window;       /* SDL_Window* */
    void*   renderer;     /* SDL_Renderer* */
    void*   texture;      /* SDL_Texture* (STREAMING, ARGB8888) */
    
    u8      screen[FD2_SCREEN_SIZE];     // 320x200 索引缓冲
    u8      palette[FD2_PALETTE_BYTES];  // 768字节 RGB调色板
    u32*    argb;         // ARGB转换缓冲
    u32*    argb_palette; // 256色ARGB调色板
    
    int     scale;        // 窗口缩放 (1-5)
    int     window_w;     // 窗口宽度
    int     window_h;     // 窗口高度
    bool    initialized;
    bool    fullscreen;
} fd2_render_t;
```

**项目提供的渲染函数**:

| 函数 | 功能 | 对应原游戏 | 实现状态 |
|------|------|-----------|----------|
| `fd2_render_init` | 初始化SDL窗口/纹理 | VGA模式设置 | ✅ 完成 |
| `fd2_render_shutdown` | 清理资源 | 无 | ✅ 完成 |
| `fd2_render_fill_screen` | 填充屏幕 | memset(0xA0000, ...) | ✅ 完成 |
| `fd2_render_blit` | 透明混合blit | sub_4EBFF | ✅ 完成 |
| `fd2_render_blit_trans` | 自定义透明blit | sub_4EC31 | ✅ 完成 |
| `fd2_render_blit_rle` | RLE解压+blit | sub_4E809 + sub_4EBFF | ✅ 完成 |
| `fd2_render_plot` | 画像素 | 直接写0xA0000 | ✅ 完成 |
| `fd2_render_set_palette_6bit` | 设置6位调色板 | sub_11D40 | ✅ 完成 |
| `fd2_render_set_palette_8bit` | 设置8位调色板 | sub_11D40 | ✅ 完成 |
| `fd2_render_set_brightness` | 亮度调整 | sub_11D40 (带offset) | ✅ 完成 |
| `fd2_render_fade_palette` | 调色板淡入淡出 | sub_2DF01 | ✅ 完成 |
| `fd2_render_fade_to_black` | 淡出到黑 | sub_2DF01 (降序) | ✅ 完成 |
| `fd2_render_fade_from_black` | 从黑淡入 | sub_2DF01 (升序) | ✅ 完成 |
| `fd2_render_palette_add_6bit` | 调色板加法 | sub_11DF2 | ✅ 完成 |
| `fd2_render_blit_afm` | AFM动画帧blit | sub_4EBFF + AFM解码 | ✅ 完成 |
| `fd2_render_present` | 显示帧 | memmove + VGA刷新 | ✅ 完成 |
| `fd2_render_toggle_fullscreen` | 全屏切换 | 无 | ✅ 完成 |

### 3.3 绘制框架差异分析

| 对比项 | 原游戏 | 项目实现 | 差异程度 |
|--------|--------|----------|----------|
| 显示模式 | VGA Mode 13h (0xA0000) | SDL2 ARGB8888纹理 | **适配完成** |
| 分辨率 | 320x200 256色 | 320x200 256色 | **一致** |
| 双缓冲 | 手动malloc + memmove | SDL2纹理自动管理 | **适配完成** |
| 调色板 | VGA DAC端口968/969 | ARGB转换表 | **适配完成** |
| 垂直同步 | sub_10620 () 等待回扫 | SDL_RENDERER_PRESENTVSYNC | **适配完成** |
| 行跨度转换 | 320 → 456字节/行 | 无此转换 (SDL自动处理) | **简化完成** |
| 文本渲染 | sub_15F84 (复杂标记系统) | 未实现 | **缺失** |
| 字符渲染 | sub_4ED7A (16x16字形) | 未实现 | **缺失** |
| 精灵系统 | sub_165AC/16B43/16C57 | 部分实现 (fd2_sprite.c) | **部分实现** |
| 场景特效 | sub_2670E (波纹动画) | 未实现 | **缺失** |
| 场景渲染循环 | sub_19953 (多层叠加+动画) | 未实现 | **缺失** |

**关键缺失**:
1. **文本渲染引擎** (`sub_15F84`) - 完整标记系统未实现
2. **字符/字形渲染** (`sub_4ED7A`) - 16x16字体渲染未实现
3. **场景特效系统** (`sub_2670E`) - 波纹/扩散动画未实现
4. **场景主渲染循环** (`sub_19953`) - 多层叠加效果未实现
5. **精灵管理系统** - 仅有基础实现，缺少完整生命周期

---

## 四、场景管理系统对比

### 4.1 原游戏场景系统

#### 场景数据加载流程

```
main() → 加载FDOTHER.DAT索引0-6
       → 加载FDTXT.DAT索引0
       → malloc分配缓冲区
       → int386(16) 获取键盘状态
       → rand()初始化随机种子
       → while(1) 主循环
```

**从IDA MCP确认的main()加载顺序**:

```c
// main() 中的资源加载 (按执行顺序):
FDOTHER_DAT__2 = sub_111BA(..., "FDOTHER.DAT", ..., 31);  // 索引31
FDOTHER_DAT__3 = sub_111BA(..., "FDOTHER.DAT", ..., 1);   // 索引1
FDOTHER_DAT__4 = sub_111BA(..., "FDOTHER.DAT", ..., 2);   // 索引2
FDOTHER_DAT__5 = sub_111BA(..., "FDOTHER.DAT", ..., 3);   // 索引3
FDOTHER_DAT__6 = sub_111BA(..., "FDOTHER.DAT", ..., 4);   // 索引4
FDOTHER_DAT__7 = sub_111BA(..., "FDOTHER.DAT", ..., 5);   // 索引5
FDTXT_DAT__0 = sub_111BA(..., "FDTXT.DAT", ..., 0);       // 索引0
FDOTHER_DAT__8 = sub_111BA(..., "FDOTHER.DAT", ..., 6);   // 索引6

n8_0 = malloc(32);         // 32字节缓冲区
n655360 = malloc(65536);   // 64KB 屏幕缓冲
n8_3 = malloc(2560);       // 2560字节场景数据
```

#### 场景数据结构

**场景数据格式** (从FD2.SAV加载):

```c
struct SceneData {
    char padding[12587];      // 前12587字节
    char sceneData[2560];     // 场景数据
    char sceneId;             // 场景ID (n17)
    char subSceneId;          // 子场景ID (n16_1)
    int someValue;            // n999_0 (进度数据)
    char flags[3];            // 标志位
};
```

**场景切换机制**:

```c
// funcs_25E3A[n17]() - 场景结束处理
// funcs_25E23[n17]() - 场景初始化
// funcs_1197B[n17]() - 场景完成条件检查

// 场景完成标志: n2_0
// 0 = 未完成，继续游戏
// 1 = 完成，进入下一场景
// 2 = 特殊完成 (可能触发特殊事件)
```

#### 场景音乐切换 (sub_25977)

**函数签名** (从IDA MCP确认):

```c
void sub_25977(__int32 a1, int a2, int a3, int a4, int n16, int arg4);
```

**功能**: 根据场景索引切换背景音乐，通过`byte_51E63[n17]`映射场景到音乐ID

### 4.2 项目实现状态

#### 场景系统 (`fd2_scene.c`):

```c
// 仅实现3个场景:
static const struct raw_scene raw_scenes[] = {
    { .scene_id = 97, .raw_data = scene_97_raw, ... },   // 战场地图
    { .scene_id = 99, .raw_data = scene_99_raw, ... },   // 开场动画
    { .scene_id = 100, .raw_data = scene_100_raw, ... }, // 开场场景1
};
```

#### 资源加载 (`fd2_states.c` - state_init_update):

```c
fd2_resources_load_dat(&game->resources, FD2_DAT_FDOTHER);
fd2_resources_load_dat(&game->resources, FD2_DAT_FDTXT);
fd2_resources_load_dat(&game->resources, FD2_DAT_BG);
fd2_resources_load_dat(&game->resources, FD2_DAT_FIGANI);
fd2_resources_load_dat(&game->resources, FD2_DAT_TAI);
fd2_resources_load_dat(&game->resources, FD2_DAT_ANI);
```

### 4.3 场景管理差异分析

| 对比项 | 原游戏 | 项目实现 | 差异程度 |
|--------|--------|----------|----------|
| 场景数量 | 30个 (0-29) | 3个 (97, 99, 100) | **严重不足** |
| 场景数据源 | FD2.SAV + FDOTHER.DAT | 硬编码raw数组 | **架构不同** |
| 场景生命周期 | funcs_25E23/funcs_25E3A | enter/update/exit | **结构不同** |
| 场景完成条件 | funcs_1197B检查 | 无实现 | **缺失** |
| 场景音乐映射 | byte_51E63[]数组 | 无实现 | **缺失** |
| 场景切换驱动 | n2_0 + n17变量 | 状态枚举返回值 | **驱动不同** |
| 场景资源加载 | sub_111BA动态加载 | fd2_resources_load_dat | **实现方式不同** |
| 子场景系统 | n16_1 (0-9) | 无实现 | **缺失** |
| 场景数据解析 | 从FD2.SAV解密加载 | 无实现 | **缺失** |
| 场景特效 | sub_2670E 波纹动画 | 无实现 | **缺失** |

**关键缺失**:
1. **场景生命周期函数数组** (`funcs_25E23` / `funcs_25E3A` / `funcs_1197B`)
2. **场景音乐切换系统** (`sub_25977`)
3. **场景完成条件检查** (`n2_0` 标志系统)
4. **存档数据加载** (FD2.SAV解析)
5. **场景索引动态切换** (`n17` 变量系统)
6. **子场景切换** (`n16_1` 变量系统)

---

## 五、输入处理系统对比

### 5.1 原游戏输入系统

#### 输入获取方式

```c
// 1. BIOS键盘中断
HIBYTE(n3) = 16;
v14 = int386(22, &n3, &n3);  // 读取按键扫描码

// 2. DOS定时器 (用于动画帧控制)
WORD v13 = MEMORY[0x46C];  // BIOS计时器 (18.2 ticks/sec)
while (!sub_10620()) {
    if ((MEMORY[0x46C] - v13) >= 4) {
        if (++n3_4 == 4) n3_4 = 0;
        sub_265EC(&v20);  // 更新渲染
        v13 = MEMORY[0x46C];
    }
}
```

#### 按键映射 (已确认)

| 按键 | 扫描码 | 功能 | 原游戏处理 |
|------|--------|------|-----------|
| ESC | 1 (0x01) | 取消/退出 | 特殊处理 |
| Tab | 34 (0x22) | 切换子场景 | n16_1 = (n16_1+1)%10 |
| 回车 | 28 (0x1C) | 确认 | sub_2670E() |
| 空格 | 57 (0x39) | 确认 | sub_2670E() |
| Insert | 82 (0x52) | 确认 (转回车) | 转换为28 |
| 左箭头 | 75 (0x4B) | 菜单左移 | n5 = (n5+1)%6 |
| 右箭头 | 77 (0x4D) | 菜单右移 | n5 = (n5-1)%6 |
| 上箭头 | 72 (0x48) | 上移 | sub_25A96(72) |
| 下箭头 | 80 (0x50) | 下移 | sub_25A96(80) |
| 扩展键 | 224 (0xE0) | 前缀 | 转换为回车 |

#### 输入处理函数 (sub_117E7)

**功能**: 处理键盘输入，调用第一层状态机 (`funcs_1197B`)

```c
int sub_117E7(...) {
    n44 = sub_11AA8();  // 获取按键扫描码
    
    // 特殊按键处理
    if (n44 == 1 || n44 == 44 || n44 == 76) {
        sub_12D7B(v8);
        sub_4E381();
        return 0;
    }
    
    // 方向键处理
    switch (n44) {
        case 'I': case ';': sub_2000A(); break;  // 信息
        case 'G': case '<': 
            n3_1 = sub_12C0D();
            if (条件) sub_17AED(n3, a3);  // 交互
            break;
        case 'H': sub_25A96(72, ...); sub_11B48(); break;  // 上
        case 'P': sub_25A96(80, ...); sub_11B9B(); break;  // 下
        case 'K': sub_25A96(75, ...); sub_11C59(); break;  // 左
        case 'M': sub_25A96(77, ...); sub_11BFA(); break;  // 右
    }
    
    // 确认键处理
    if (n44 == 28 || n44 == 57) {
        n6_2 = sub_12C0D();  // 获取当前选择
        if (n6_2 != -1) {
            // 检查项目状态
            if (v16[7] != 121 && v16[31] != 10) {
                if (n2 == 2 && 条件) {
                    sub_25A96(0, 2, n10, ...);  // 显示魔法
                    while (!sub_18890(n6_1));
                } else {
                    sub_17AED(n6_1, a3);  // 执行交互
                }
                
                sub_11CAC(0);
                sub_1E292(a6, n6_1);
                funcs_1197B[n17]();  // 第一层状态机调用
                sub_13565();
                
                if (n255 != 255)
                    funcs_1199C[n255](a6);  // 特殊事件
                n255 = 255;
            }
        }
    }
    
    return 0;
}
```

### 5.2 项目实现状态

**输入系统** (`fd2_input.h` / `fd2_input.c`):

```c
// SDL事件处理
fd2_input_begin_frame(&game->input);
while (SDL_PollEvent(&e)) {
    fd2_input_process_event(&game->input, &e);
}

// 动作检测
fd2_action_pressed(&game->input, FD2_ACTION_ESCAPE);
fd2_action_pressed(&game->input, FD2_ACTION_START);
fd2_input_any_pressed(&game->input);
```

### 5.3 输入处理差异分析

| 对比项 | 原游戏 | 项目实现 | 差异程度 |
|--------|--------|----------|----------|
| 输入源 | BIOS int386(22) | SDL事件系统 | **适配完成** |
| 按键映射 | 扫描码直接处理 | 动作抽象层 | **适配完成** |
| 定时器控制 | MEMORY[0x46C] | SDL_GetTicks() | **适配完成** |
| 垂直同步 | sub_10620() | SDL_RENDERER_PRESENTVSYNC | **适配完成** |
| 按键计数器 | n3_4 (动画帧控制) | 无实现 | **缺失** |
| 输入处理函数 | sub_117E7 (复杂逻辑) | 简化为动作检测 | **大幅简化** |
| 第一层状态机 | funcs_1197B调用 | 无实现 | **缺失** |
| 特殊事件处理 | funcs_1199C调用 | 无实现 | **缺失** |

---

## 六、总结与建议

### 6.1 整体差异评估

| 系统 | 原游戏 | 项目实现 | 完成度 | 差异程度 |
|------|--------|----------|--------|----------|
| **状态管理** | 3层嵌套状态机 | 1层扁平状态机 | ~30% | **重大差异** |
| **场景系统** | 30场景+生命周期函数 | 3场景+硬编码 | ~10% | **重大差异** |
| **绘制框架** | 完整VGA渲染管线 | SDL2适配+基础函数 | ~60% | **中等差异** |
| **输入处理** | BIOS中断+复杂逻辑 | SDL事件+简化抽象 | ~50% | **中等差异** |
| **音频系统** | AIL库+音乐切换 | SDL2音频+基础实现 | ~40% | **中等差异** |
| **资源管理** | sub_111BA动态加载 | fd2_resources封装 | ~70% | **中等差异** |

### 6.2 关键缺失列表

#### 高优先级 (核心架构差异):

1. **三层状态机架构** → 需要重构为原游戏的嵌套状态机
   - 实现 `funcs_25E23` / `funcs_25E3A` 函数指针数组
   - 实现 `funcs_1197B` 场景完成条件检查数组
   - 实现 `n2_0` 场景状态标志系统

2. **场景生命周期管理** → 需要完整的场景系统
   - 实现 `sub_25EBB` 主状态管理器
   - 实现 `sub_26152` 场景交互循环
   - 实现 `sub_25977` 场景音乐切换器

3. **场景数据系统** → 需要动态场景数据
   - 实现FD2.SAV存档加载和解析
   - 实现场景索引动态切换 (`n17`)
   - 实现子场景系统 (`n16_1`)

#### 中优先级 (功能缺失):

4. **文本渲染引擎** (`sub_15F84`)
   - 完整标记系统 (-1到-20)
   - 递归调用支持
   - 动态图片加载

5. **场景特效系统** (`sub_2670E`)
   - 波纹/扩散动画
   - 调色板淡入淡出
   - 多层叠加效果

6. **第一层状态机** (`funcs_1197B`)
   - 30个场景完成条件检查
   - 对象状态检查
   - 进度依赖检查

#### 低优先级 (增强功能):

7. **精灵管理系统** - 完善生命周期
8. **特殊场景处理** (`sub_2AF28`) - 背包/物品界面
9. **场景渲染循环** (`sub_19953`) - 多层叠加

### 6.3 架构建议

#### 方案A: 保持当前架构, 补充缺失功能

**优点**:
- 代码结构清晰, 易于维护
- SDL2适配已完成, 兼容性好
- 可以逐步补充缺失功能

**缺点**:
- 与原游戏架构差异大, 1:1复原困难
- 需要大量桥梁代码映射原游戏逻辑

**建议实施步骤**:
1. 添加场景生命周期函数数组 (`funcs_25E23` / `funcs_25E3A`)
2. 实现场景完成条件检查 (`funcs_1197B`)
3. 实现场景音乐切换 (`sub_25977`)
4. 实现文本渲染引擎 (`sub_15F84`)
5. 实现场景交互循环 (`sub_26152`)

#### 方案B: 重构为原游戏架构

**优点**:
- 1:1复原原游戏逻辑
- 符合开发原则 ("按ida pro mcp汇编代码1:1复制游戏功能")
- 便于后续功能移植

**缺点**:
- 需要大幅重构现有代码
- SDL2适配需要重新设计
- 开发周期长

**建议实施步骤**:
1. 创建原游戏全局变量映射表
2. 实现三层状态机核心架构
3. 实现所有场景生命周期函数
4. 实现场景交互循环和输入处理
5. 逐步替换SDL2适配层为原游戏逻辑

### 6.4 结论

**当前项目与原游戏存在重大架构差异**, 主要体现在:

1. **状态管理系统**: 原游戏的3层嵌套状态机被简化为1层扁平状态机
2. **场景管理系统**: 30个场景的生命周期管理被简化为3个硬编码场景
3. **场景完成条件**: `funcs_1197B` 数组完全未实现
4. **场景交互循环**: `sub_26152` 未实现
5. **文本渲染引擎**: `sub_15F84` 完整标记系统未实现

**建议**: 根据开发原则 ("按ida pro mcp汇编代码1:1复制游戏功能"), 应优先考虑**方案B**, 重构为原游戏的三层状态机架构, 以确保100%还原游戏逻辑。

---

**分析完成时间**: 2026-05-05  
**分析工具**: IDA Pro MCP Server + 项目代码审查  
**参考文档**: 
- `docs/游戏逻辑框架分析.md`
- `docs/第二层状态机分析.md`
- `docs/第三层状态机分析.md`
- `docs/状态管理框架分析.md`
- `docs/绘制框架分析.md`
