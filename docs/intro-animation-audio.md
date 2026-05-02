# FD2 开场动画音频系统分析

> 来源: IDA Pro MCP 逆向分析 FD2.EXE (地址 0x1F894, 0x20421, 0x25A96, 0x25B45)
> 日期: 2026-05-02

---

## 一、音频系统架构

| 组件 | 说明 |
|------|------|
| **音频库** | Miles Sound System (AIL - Audio Interface Library) |
| **底层驱动** | DOS 声卡驱动 (Sound Blaster / AdLib / XMIDI) |
| **数字音效** | AIL Sample API (`AIL_start_sample`, `AIL_set_sample_address`, ...) |
| **XMIDI 音乐** | AIL Sequence API (`AIL_start_sequence`, `AIL_stop_sequence`, ...) |

### AIL Debug 日志字符串 (地址 0x50313 起)

二进制中保留了完整的 AIL API 调试日志字符串，证明使用了以下 AIL 函数:

| AIL 函数 | 用途 |
|----------|------|
| `AIL_startup()` / `AIL_shutdown()` | 音频系统初始化/关闭 |
| `AIL_install_DIG_INI()` | 安装数字音频驱动 |
| `AIL_install_MDI_INI()` | 安装 MIDI 音频驱动 |
| `AIL_allocate_sample_handle()` | 分配采样句柄 |
| `AIL_init_sample()` | 初始化采样 |
| `AIL_set_sample_address()` | 设置采样数据地址 |
| `AIL_set_sample_loop_count()` | 设置循环次数 |
| `AIL_start_sample()` / `AIL_stop_sample()` | 开始/停止采样 |
| `AIL_start_sequence()` / `AIL_stop_sequence()` | 开始/停止 XMIDI 序列 |
| `AIL_set_sample_volume()` | 设置音量 |
| `AIL_set_sample_pan()` | 设置声像 |
| `AIL_sample_status()` | 查询播放状态 |

---

## 二、核心音频函数

### 2.1 `sub_25A96` — 数字音效播放函数 (地址 0x25A96)

```c
int __fastcall sub_25A96(__int32 a1, int a2, int a3, int a4, int a5, int a6, int a7)
{
  // a5 = 资源基址指针 (FDOTHER.DAT 加载地址)
  // a6 = 资源条目索引 (index)，-1 表示停止所有
  // a7 = 循环次数 (loops)

  if ( byte_53EF1 && byte_51E62 && !dword_54133 )
  {
    sub_39805(dword_53EE4);       // AIL_stop_sample(handle)
    if ( a6 != -1 )
    {
      v8 = a5 + 4 * a6;           // 定位第 a6 个资源条目
      v10 = *(v8 + 6) + a5;       // 数据偏移
      v9  = *(v8 + 10) - *(v8 + 6); // 数据大小
      sub_39521(dword_53EE4);     // AIL_init_sample(handle)
      sub_39694(dword_53EE4, v10, v9); // AIL_set_sample_address(handle, buf, size)
      sub_39AAE(dword_53EE4, a7); // AIL_set_sample_loop_count(handle, loops)
      return sub_39798(dword_53EE4);   // AIL_start_sample(handle)
    }
  }
}
```

**AIL API 映射**:
- `sub_39805` → `AIL_stop_sample(dword_53EE4)`
- `sub_39521` → `AIL_init_sample(dword_53EE4)`
- `sub_39694` → `AIL_set_sample_address(dword_53EE4, buffer, size)`
- `sub_39AAE` → `AIL_set_sample_loop_count(dword_53EE4, loops)`
- `sub_39798` → `AIL_start_sample(dword_53EE4)`

**全局变量**:
- `dword_53EE4` = Sample handle 1 (用于常规音效)
- `byte_53EF1` = 音频系统初始化标志
- `byte_51E62` = 音频启用标志
- `dword_54133` = 静音/禁用标志

### 2.2 `sub_25B45` — 扩展音频播放函数 (地址 0x25B45)

与 `sub_25A96` 结构完全相同，唯一区别是使用 **`dword_53EE8`** 而非 `dword_53EE4` 作为 sample handle。

```c
// sub_25B45 与 sub_25A96 唯一区别:
sub_39805(dword_53EE8);   // 使用 dword_53EE8 而非 dword_53EE4
sub_39521(dword_53EE8);
sub_39694(dword_53EE8, v10, v9);
sub_39AAE(dword_53EE8, a7);
sub_39798(dword_53EE8);
```

**AIL API 映射**:
- `sub_39805` → `AIL_stop_sample(dword_53EE8)`
- `sub_39521` → `AIL_init_sample(dword_53EE8)`
- `sub_39694` → `AIL_set_sample_address(dword_53EE8, buffer, size)`
- `sub_39AAE` → `AIL_set_sample_loop_count(dword_53EE8, loops)`
- `sub_39798` → `AIL_start_sample(dword_53EE8)`

**全局变量**:
- `dword_53EE8` = Sample handle 2 (用于扩展音效/特殊音频)

**重要发现**: sub_25B45 也使用 AIL_start_sample，不是 XMIDI sequence 播放！

### 2.3 `sub_25977` — XMIDI 音乐播放函数 (地址 0x25977)

真正的 XMIDI 音乐播放函数，调用 `sub_3AEEE` (AIL_start_sequence)。

```c
int __fastcall sub_25977(__int32 a1, int a2, int a3, int a4, int n16, int arg4);
// n16 = FDMUS.DAT 中的音乐索引，-1 表示停止
```

**工作流程**:
1. 从 FDMUS.DAT 加载音乐资源: `sub_111BA(..., "FDMUS.DAT", FDMUS_DAT, n16)`
2. 设置音乐数据: `sub_3ADF5(dword_53ED0, FDMUS_DAT, 0)`
3. 开始播放: `sub_3AEEE(dword_53ED0)` → `AIL_start_sequence`
4. 设置音量: `sub_3B124(dword_53ED0, 127, 2000)` (全音量, 2秒淡入)

**全局变量**:
- `dword_53ED0` = XMIDI sequence handle (由 sub_3ACA3 分配)
- `FDMUS_DAT` = FDMUS.DAT 加载指针

**调用者**: sub_10010, sub_19df7, sub_1a30b, sub_22e5c, sub_25bf4, sub_25ebb, sub_26152, sub_2670e, sub_2a43e, sub_2aa00, sub_31529, sub_31c49, sub_3231b

### 2.4 音频句柄初始化 — `sub_25BF4` (main 函数, 地址 0x25BF4)

```c
// 初始化两个 sample handle
sub_392D0(&dword_53EE4);    // AIL_allocate_sample_handle(&dword_53EE4)
sub_392D0(&dword_53EE8);    // AIL_allocate_sample_handle(&dword_53EE8)
```

### 2.5 `sub_20421` — ANI 动画播放函数 (地址 0x20421)

负责播放 ANI.DAT 中的动画，**同时处理音频播放**。

```c
void __fastcall sub_20421(__int32 a1, int a2, int a3, int a4, int a5, int a6, int a7)
{
  // a5 = ANI 索引 (ANI#N)
  // a6 = 帧延迟 (ms)
  // a7 = 是否检测按键退出 (1=检测)

  // ... 解析 ANI.DAT 动画数据 ...

  for ( i = 0; i < frame_count; ++i )
  {
    // 解码动画帧
    sub_36FF4(frame_size, frame_data);

    // ★★★ 关键：只有 ANI#1 且是第一帧时才播放音频 ★★★
    if ( a5 == 1 && !i )    // arg_0 == 1 && esi == 0
      sub_25A96(_FDOTHER_DAT_, 0, 1);  // 播放 FDOTHER#78 条目0

    j___delay(a6);
    if ( a7 && sub_10620() )  // 检测按键退出
      break;
    sub_4E381();  // 屏幕刷新
  }

  // 动画结束，停止音频
  if ( _FDOTHER_DAT_ )
  {
    sub_25A96(_FDOTHER_DAT_, -1, 1);  // 停止所有
    free(_FDOTHER_DAT_);
  }
}
```

**关键条件**: `if ( a5 == 1 && !i )`
- 只有 `sub_20421(1, ...)` 即 **ANI#1 (游戏标题)** 时才触发音频播放
- ANI#0, #3, #4, #5, #6, #7, #8 都 **不会** 触发音频

---

## 三、开场动画主函数 `sub_1F894` (地址 0x1F894)

### 3.1 动画流程概览

```
Phase 0: 标题画面 (FDOTHER#74) → 淡入→等待30tick→淡出 (无音频)
Phase 1: ANI#3 盖亚动画 (12帧, 90ms) → 无音频 (index!=1)
Phase 2: 滚动长图 (帧 535→0) → 多种音效触发
  - 帧450: 特效叠加 (FDOTHER#100)
  - 帧330: ANI#4 索尔 + ANI#5 索尔战斗 → 无音频
  - 帧210: ANI#6 莱汀 + ANI#7 莱汀战斗 → 无音频
  - 帧110: ANI#8 索尔和莱汀 → 无音频
  - 帧25:  ANI#0 星盘动画 → 无音频
  - 帧10:  特效叠加 (FDOTHER#75+76)
Phase 3: 淡出 (40步到黑屏) → 停止音频
Phase 4: ANI#1 游戏标题 (26帧, 15ms) → 播放音频
Phase 5: 菜单循环 (等待玩家输入)
```

### 3.2 音频触发点详解

| 位置 | 调用 | 参数 (index) | 音效/音乐 | 说明 |
|------|------|-------------|----------|------|
| 滚动循环 (dst_匹配) | `sub_25A96(_, 0, 1)` | 0 | 音效触发 | 每匹配到 dst_ 数组中的帧时触发 |
| Fade out 后 | `sub_20421(1, 15, 1)` | - | 播放音频 | 内部触发 `sub_25A96(_, 0, 1)` |
| ANI#1 第一帧 | `sub_25A96(_, 0, 1)` | 0 | 音乐 | FDOTHER#78 条目0 |
| 菜单上/下 | `sub_25A96(_, 2, 1)` | 2 | 光标音效 | 索引2的音频条目 |
| 菜单确认 | `sub_25A96(_, 1, 1)` | 1 | 确认音效 | 索引1的音频条目 |
| 退出菜单 | `sub_25A96(_, -1, 1)` | -1 | 停止所有 | 停止所有音频播放 |
| 滚动结束淡出 | `sub_25B45(_, 3, 1)` | 3 | 停止音频 | 使用 handle #2 停止 |

### 3.3 Palette Flash 音频触发机制

滚动循环 (帧535→0) 中，有一个 dst_ 数组匹配机制触发音频:

```c
__int32 dst_[15];  // 预设的触发帧列表
unsigned __int8 v33;  // 匹配计数器

for ( n535 = 535; n535 >= 0; --n535 )
{
  // ... 渲染帧 ...

  // 如果当前帧匹配 dst_ 数组中的值
  if ( n535 == dst_[v33] )
  {
    n12 = 0;
    sub_25A96(_FDOTHER_DAT_, 0, 1);  // 播放音效 (index=0)
    // 加载 FDOTHER#102
    ++v33;  // 计数器递增，下次匹配下一个
  }
}
```

---

## 四、资源文件映射

| 文件 | 内容 | 在开场中的用途 |
|------|------|----------------|
| **FDOTHER.DAT #78** | 数字音频采样数据 (PCM) | 主要音频资源，包含多个条目 (index 0, 1, 2) |
| **FDOTHER.DAT #79** | 额外音频数据 | 可能用于其他场景音效 |
| **ANI.DAT** | AFM 动画帧 + 内嵌音频字节码 | 每个 ANI#N 的动画数据和内嵌音效 |
| **FDMUS.DAT** | XMIDI 音乐资源 | 游戏内背景音乐 (开场动画中通过 FDOTHER 间接使用) |

### FDOTHER.DAT #78 条目结构

```
条目0 (index=0): 主音乐/音效 (ANI#1 和滚动动画中播放)
条目1 (index=1): 菜单确认音效
条目2 (index=2): 菜单光标移动音效
```

条目通过偏移表定位:
```c
v8 = base + 4 * index;        // 第 index 个条目指针
offset = *(v8 + 6) + base;    // 数据起始偏移
size   = *(v8 + 10) - *(v8 + 6);  // 数据大小
```

---

## 五、完整函数调用关系图

```
sub_1F894 (开场动画主函数, 0x1F894)
│
├── Phase 0: 标题画面
│   ├── sub_1F525()           // 屏幕刷新
│   ├── sub_17AA9(30)         // 延迟30tick
│   └── sub_1F882()           // 淡出
│
├── Phase 1: ANI#3
│   └── sub_20421(3, 90, 1)
│       ├── fopen("ANI.DAT") + 解析
│       ├── sub_36FF4()       // 解码帧
│       └── (a5!=1, 跳过音频)  // ★★★ 不播放音乐 ★★★
│
├── Phase 2: 滚动循环 (535→0)
│   ├── sub_1F81E(4, 90, 99)  → sub_20421(4,...) → 无音频
│   ├── sub_1F81E(5, 50, 0)   → sub_20421(5,...) → 无音频
│   ├── sub_1F81E(6, 90, 99)  → sub_20421(6,...) → 无音频
│   ├── sub_1F81E(7, 50, 0)   → sub_20421(7,...) → 无音频
│   ├── sub_1F81E(8, 90, 99)  → sub_20421(8,...) → 无音频
│   ├── sub_1F81E(0, 15, 0)   → sub_20421(0,...) → 无音频
│   ├── sub_1F73F(100, 99)    // 特效叠加 (无音频)
│   ├── sub_1F73F(75, 76)     // 特效叠加 (无音频)
│   └── dst_[] 匹配时:
│       └── sub_25A96(_, 0, 1) // ★★★ 播放音效 ★★★
│
├── Phase 3: 淡出
│   ├── sub_25B45(_, 3, 1)    // ★★★ 停止音频 (handle #2) ★★★
│   └── sub_11DF2()           // 淡出效果
│
├── Phase 4: ANI#1 游戏标题
│   └── sub_20421(1, 15, 1)
│       ├── sub_25A96(_, 0, 1) // ★★★ 播放音乐 (唯一触发点) ★★★
│       └── sub_25A96(_, -1, 1) // 结束时停止
│
└── Phase 5: 菜单
    ├── sub_25A96(_, 2, 1)    // 光标移动音效
    ├── sub_25A96(_, 1, 1)    // 确认音效
    └── sub_25A96(_, -1, 1)   // 停止所有
```

---

## 六、关键逆向发现

1. **开场动画中只有 ANI#1 (游戏标题) 会播放背景音乐**
   - 条件: `sub_20421` 的参数 `arg_0 == 1` 且是第一帧 (`esi == 0`)
   - 其他 ANI (#0, #3, #4, #5, #6, #7, #8) 都不播放背景音乐

2. **所有 FDOTHER.DAT 音频都通过 Sample API 播放，而非 Sequence API**
   - 音频数据存储在 FDOTHER.DAT #78 中
   - sub_25A96 和 sub_25B45 都使用 AIL_start_sample
   - 不是直接播放 FDMUS.DAT 中的 XMIDI 曲目

3. **XMIDI 音乐由独立函数 sub_25977 处理**
   - 使用 sub_3AEEE (AIL_start_sequence) 播放
   - 数据源为 FDMUS.DAT，非 FDOTHER.DAT
   - 句柄为 dword_53ED0 (非 dword_53EE4/53EE8)

4. **音频从对应资源条目的起点开始播放**
   - index=0: 从头播放
   - index=1: 从条目1起点播放
   - index=-1: 停止所有播放

5. **三种音频句柄的设计**
   - `dword_53EE4` (handle #1): 常规音效 (sub_25A96, AIL_start_sample)
   - `dword_53EE8` (handle #2): 扩展音效 (sub_25B45, AIL_start_sample)
   - `dword_53ED0` (handle #3): XMIDI 音乐 (sub_25977, AIL_start_sequence)

6. **ANI 内嵌音频字节码**
   - `sub_36FF4` 函数解码 ANI.DAT 中的音频字节码
   - 字节码通过函数指针表 `funcs_37012` 执行不同操作

---

## 七、相关 IDA 地址速查表

| 功能 | 地址 | 说明 |
|------|------|------|
| 开场动画主函数 | `0x1F894` | sub_1F894 |
| ANI 播放函数 | `0x20421` | sub_20421 |
| 音效播放函数 | `0x25A96` | sub_25A96 (handle #1, AIL_start_sample) |
| 扩展音效函数 | `0x25B45` | sub_25B45 (handle #2, AIL_start_sample) |
| XMIDI 音乐函数 | `0x25977` | sub_25977 (handle #3, AIL_start_sequence) |
| AIL_start_sequence 包装 | `0x3AEEE` | sub_3AEEE |
| AIL_set_sequence_address 包装 | `0x3ADF5` | sub_3ADF5 |
| AIL_set_sequence_volume 包装 | `0x3B124` | sub_3B124 |
| 音频字节码解码 | `0x36FF4` | sub_36FF4 |
| 音频初始化 | `0x25BF4` | main 函数 |
| AIL_stop_sample 包装 | `0x39805` | sub_39805 |
| AIL_init_sample 包装 | `0x39521` | sub_39521 |
| AIL_set_sample_address 包装 | `0x39694` | sub_39694 |
| AIL_set_sample_loop_count 包装 | `0x39AAE` | sub_39AAE |
| AIL_start_sample 包装 | `0x39798` | sub_39798 |
| AIL_allocate_sample_handle 包装 | `0x392D0` | sub_392D0 |
| AIL_allocate_sequence_handle | `0x3ACA3` | sub_3ACA3 |
| 屏幕刷新 | `0x4E381` | sub_4E381 |
| 淡出效果 | `0x2DF01` | sub_2DF01 |
| 淡入效果 | `0x11D40` | sub_11D40 |
| 按键检测 | `0x10620` | sub_10620 |
| Sample handle #1 | `0x53EE4` | dword_53EE4 |
| Sample handle #2 | `0x53EE8` | dword_53EE8 |
| Sequence handle #3 | `0x53ED0` | dword_53ED0 |
| 音频启用标志 | `0x53EF1` | byte_53EF1 |
| AIL Debug 字符串 | `0x50313` | "AIL_DEBUG" |
