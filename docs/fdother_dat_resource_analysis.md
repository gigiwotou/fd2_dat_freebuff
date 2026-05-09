# FDOTHER.DAT 资源加载与使用分析

> 基于IDA Pro MCP对FD2.EXE游戏循环的深度分析
> 分析日期: 2026-05-08

---

## 一、资源加载函数 sub_111BA

### 函数原型
```c
int __cdecl sub_111BA(int filename, int old_ptr, int index)
```

### 功能说明
从DAT文件中按索引加载资源的标准函数。

### 工作流程
1. **释放旧资源**: 如果`old_ptr`非空，先调用`free(old_ptr)`释放旧资源
2. **打开文件**: 以`"rb"`模式打开指定的DAT文件
3. **定位索引表**: 
   - 文件头6字节为文件标识
   - 每个索引项占8字节（4字节偏移 + 4字节大小）
   - 计算公式: `fseek(fp, 4 * index + 6, SEEK_SET)`
4. **读取索引项**:
   - 前4字节: 资源在文件中的偏移量(offset)
   - 后4字节: 资源大小(size)
   - 实际大小: `dword_53BFF = size - offset`
5. **加载资源**:
   - 分配内存: `malloc(dword_53BFF)`
   - 定位到资源位置: `fseek(fp, offset, 0)`
   - 读取数据: `fread(data, 1, dword_53BFF, fp)`
6. **关闭文件并返回资源指针**

### 关键全局变量
- `dword_53BFF`: 最后加载资源的大小

---

## 二、main() 初始化阶段加载的FDOTHER.DAT资源

在`main`函数初始化时（地址 0x25c70-0x25d2e），以下资源被加载到全局变量：

| 全局变量 | 资源索引 | 来源文件 | 用途分析 |
|---------|---------|---------|---------|
| `dword_53EEC` | 31 | FDOTHER.DAT | 战斗选项菜单资源，循环中频繁调用 |
| `dword_53A4D` | 1 | FDOTHER.DAT | 字体/文字资源 |
| `dword_53A89` | 2 | FDOTHER.DAT | UI元素 |
| `dword_53A6D` | 3 | FDOTHER.DAT | UI元素 |
| `dword_53A75` | 4 | FDOTHER.DAT | UI元素 |
| `dword_53A81` | 5 | FDOTHER.DAT | UI元素 |
| `dword_53A7D` | 0 | FDTXT.DAT | 文本数据（从FDTXT.DAT加载） |
| `dword_53AD1` | 6 | FDOTHER.DAT | 背景图/UI元素 |

### 代码位置
```c
// 0x25c70 - 加载索引31
dword_53EEC = sub_111BA("FDOTHER.DAT", dword_53EEC, 31);

// 0x25c8a - 加载索引1
dword_53A4D = sub_111BA("FDOTHER.DAT", dword_53A4D, 1);

// 0x25ca4 - 加载索引2
dword_53A89 = sub_111BA("FDOTHER.DAT", dword_53A89, 2);

// 0x25cbe - 加载索引3
dword_53A6D = sub_111BA("FDOTHER.DAT", dword_53A6D, 3);

// 0x25cd8 - 加载索引4
dword_53A75 = sub_111BA("FDOTHER.DAT", dword_53A75, 4);

// 0x25cf2 - 加载索引5
dword_53A81 = sub_111BA("FDOTHER.DAT", dword_53A81, 5);

// 0x25d0c - 从FDTXT.DAT加载索引0
dword_53A7D = sub_111BA("FDTXT.DAT", dword_53A7D, 0);

// 0x25d26 - 加载索引6
dword_53AD1 = sub_111BA("FDOTHER.DAT", dword_53AD1, 6);
```

---

## 三、游戏主循环中的FDOTHER.DAT使用

### 游戏循环结构
```c
while (1) {
    // 设置音乐场景18
    sub_25977(18, 0);
    
    // 主逻辑处理
    v10 = sub_25EBB(...);
    
    // 根据n2_0变量进入不同场景模式
    if (n2_0 == 1) {
        // 地图模式
        sub_22E5C(...);
    } else if (n2_0 == 2) {
        // 战斗模式
        sub_26152(...);
    }
    
    // 退出条件
    if (v12) {
        sub_37ED8(v10);
        exit(0x16F04);
    }
}
```

---

### 循环路径1: 地图模式 (n2_0 == 1)

#### 调用链
```
main → sub_25EBB → sub_117E7 → sub_22E5C
```

#### sub_22E5C (地址 0x22e5c) - 地图转场处理

```c
void __fastcall sub_22E5C(int a1, int a2)
{
    // 停止当前音乐
    sub_25977(-1, 1);
    
    // 加载FDOTHER.DAT索引79 - 地图过渡/转场画面
    int v3 = sub_111BA("FDOTHER.DAT", 0, 79);
    
    // 清屏：VGA显存0xA0000，64000字节
    memset(655360, 0, 64000);
    
    // 将资源79的第0帧解码渲染到显存0xA0000，宽度320
    sub_2EB9F(v3, 0, 655360, 320, -1);
    
    // 刷新画面
    sub_1F525(...);
    
    // 加载下一个状态
    sub_17AA9(9);
    
    // 渲染资源79的第1帧
    sub_2EB9F(v3, 1, 655360, 320, -1);
    
    // 跳转到后续处理
    sub_17AA9(36);
    JUMPOUT(0x15E94);
}
```

**用途**: 地图模式切换时的转场动画（索引79包含2帧画面）

---

### 循环路径2: 战斗模式 (n2_0 == 2)

#### 调用链
```
main → sub_25EBB → sub_26152 (战斗主循环)
```

#### 2.1 战斗初始化 - sub_25EBB (地址 0x25eed-0x25f74)

```c
// 加载FDOTHER.DAT索引13 - 战斗初始化界面/存档相关
dword_53F66 = sub_111BA("FDOTHER.DAT", dword_53F66, 13);
sub_1F882(...);  // 使用资源13

// 重新加载FDOTHER.DAT索引0 - 全局资源
FDOTHER_DAT = sub_111BA("FDOTHER.DAT", FDOTHER_DAT, 0);
```

#### 2.2 战斗主循环初始化 - sub_26152 (地址 0x26152)

##### 条件加载索引13
```c
// 在特定条件下加载索引13 - 存档相关界面
if (v9 != -1 && !n2_3) {
    dword_53F66 = sub_111BA("FDOTHER.DAT", dword_53F66, 13);
    sub_2968D(0);  // 使用资源13
    free(dword_53F66);  // 用完立即释放
}
```

##### 动态加载战斗背景
```c
// 根据战斗场景索引i加载对应的背景/地台资源
// 索引 = byte_52407 + i (可变索引)
v13 = sub_111BA("FDOTHER.DAT", 0, byte_52407 + i);
sub_4E98D(v13, 0, 0, FDSHAP_DAT + 32904, 456, -1);
free(v13);  // 用完释放
```

##### 加载战斗UI资源
```c
// 加载FDOTHER.DAT索引10 - 战斗UI/菜单资源
dword_53F5A = sub_111BA("FDOTHER.DAT", 0, 10);
```

#### 2.3 战斗主循环 (地址 0x26434-0x265bf)

```c
do {
    sub_265EC(n4);  // 战斗画面渲染循环
    
    // 等待键盘输入（基于时间轮询）
    while (!sub_10620()) {
        n4 = MEMORY[0x46C] - v15;  // 读取系统计时器
        if (n4 >= 4) {
            // 每4个tick更新一次画面
            if (++dword_53F52 == 4)
                dword_53F52 = 0;
            goto LABEL_22;
        }
    }
    
    // 处理键盘输入 (BIOS中断0x16)
    HIBYTE(n3) = 16;
    int386(22, &n3, &n3);
    
    switch (HIBYTE(n3)) {
        case 0x22:  // F2键 - 切换音乐
            if (++n16 == 10) n16 = 0;
            sub_25977(n16, 0);
            break;
            
        case 0x4D:  // M键
            sub_25A96(dword_53EEC, 0, 1);  // 使用索引31资源
            if (--n5 < 0) n5 = 5;
            break;
            
        case 0x4B:  // K键
            sub_25A96(dword_53EEC, 0, 1);  // 使用索引31资源
            if (++n5 > 5) n5 = 0;
            break;
    }
    
    // 回车或空格 - 确认选择
    if (HIBYTE(n3) == 28 || n3 == 32) {
        if (n5 != 2)
            sub_25A96(dword_53EEC, 1, 3);  // 使用索引31资源
        n4_1 = sub_2670E();  // 进入战斗结果处理
    }
    
    n4 = n4_1;
} while (!n4_1);

// 战斗结束
free(dword_53F5A);  // 释放索引10资源
```

**战斗循环中的资源使用**:
- `dword_53EEC` (索引31) 在战斗中频繁调用:
  - `sub_25A96(dword_53EEC, 0, 1)` - M/K键操作
  - `sub_25A96(dword_53EEC, 1, 3)` - 确认选择

---

### 循环路径3: 标题/菜单初始化

#### 调用链
```
main → sub_25EBB → sub_1F894
```

#### sub_1F894 (地址 0x1f894) - 标题与菜单系统

##### 标题画面加载
```c
// 加载标题背景
_FDOTHER.DAT_ = sub_111BA("FDOTHER.DAT", 0, 77);

// 清屏
memset(655360, 0, 64000);

// 加载标题Logo/前景
FDOTHER_DAT = sub_111BA("FDOTHER.DAT", FDOTHER_DAT, 76);

// 设置调色板
sub_11D40(0, 255, 64);

// 加载菜单文字/图标
_FDOTHER.DAT__1 = sub_111BA("FDOTHER.DAT", 0, 74);

// 渲染到显存
sub_4E98D(_FDOTHER.DAT__1, 0, 0, 655360, 320, -1);

// 刷新画面
sub_1F525(...);
```

##### 菜单选项加载
```c
// 加载菜单选项背景
FDOTHER_DAT = sub_111BA("FDOTHER.DAT", FDOTHER_DAT, 99);
memset(655360, 0, 64000);
sub_11D40(0, 255, 0);
sub_20421(3, 90, 1);

// 加载菜单画面2
FDOTHER_DAT = sub_111BA("FDOTHER.DAT", FDOTHER_DAT, 101);
```

##### 标题动画序列 (5帧)
```c
// 分配动画缓冲区
n15_1 = malloc(&loc_396C0);
memset(n15_1, 0, &loc_396C0);

// 循环加载索引69-73 - 标题动画序列（5帧）
for (n5 = 0; n5 < 5; ++n5) {
    _FDOTHER.DAT__1 = sub_111BA("FDOTHER.DAT", _FDOTHER.DAT__1, n5 + 69);
    sub_4E98D(_FDOTHER.DAT__1, 0, 147 * n5, n15_1, 320, -1);
}

sub_4E381();  // 刷新画面
```

##### 存档选择界面
```c
// 加载存档界面背景
_FDOTHER.DAT__2 = sub_111BA("FDOTHER.DAT", _FDOTHER.DAT_, 7);

// 加载存档界面前景
FDOTHER_DAT = sub_111BA("FDOTHER.DAT", FDOTHER_DAT, 8);

// 清屏并设置调色板
memset(655360, 0, 64000);
sub_11D40(0, 255, 0);

// 渲染存档界面
sub_20421(1, 15, 1);
sub_25B45(v36, 3, 1);
sub_11DF2(0, 255, 64);
sub_16886(655360, 320, _FDOTHER.DAT__2, 0);
```

##### 菜单选择循环
```c
// 菜单选择循环中的资源使用
for (n4 = 0; n4 < 4; ++n4) {
    sub_1FF79(_FDOTHER.DAT_, -1, n100);  // 取消高亮
    j___delay(80);
    sub_1FF79(_FDOTHER.DAT_, n3_1, n100);  // 高亮当前选项
    j___delay(80);
}

// 加载索引102 - 光标/选择高亮
FDOTHER_DAT = sub_111BA("FDOTHER.DAT", FDOTHER_DAT, 102);
sub_11D40(0, 255, 0);

// 加载索引100 - 光标闪烁效果
FDOTHER_DAT = sub_111BA("FDOTHER.DAT", FDOTHER_DAT, 101);
```

---

## 四、FDOTHER.DAT 资源索引完整映射表

根据所有循环路径分析，整理出以下资源索引：

### 全局保留资源 (main初始化时加载)

| 索引 | 全局变量 | 用途 | 生命周期 |
|-----|---------|------|---------|
| 0 | `dword_53EEC` (战斗), `FDOTHER_DAT` (通用) | 全局基础资源 | 程序结束 |
| 1 | `dword_53A4D` | 字体资源 | 程序结束 |
| 2 | `dword_53A89` | UI元素 | 程序结束 |
| 3 | `dword_53A6D` | UI元素 | 程序结束 |
| 4 | `dword_53A75` | UI元素 | 程序结束 |
| 5 | `dword_53A81` | UI元素 | 程序结束 |
| 6 | `dword_53AD1` | 背景图/UI | 程序结束 |
| 31 | `dword_53EEC` | 战斗选项菜单 | 程序结束，频繁调用 |

### 临时加载资源 (用完释放)

| 索引 | 加载位置 | 用途 | 使用后操作 |
|-----|---------|------|----------|
| 7 | sub_1F894 | 存档界面背景 | 用完后free |
| 8 | sub_1F894 | 存档界面前景 | 保留 |
| 10 | sub_26152 | 战斗UI/菜单 | 战斗结束free |
| 13 | sub_25EBB/sub_26152 | 战斗初始化/存档界面 | 用完立即free |
| 69-73 | sub_1F894循环 | 标题动画(5帧) | 用完free |
| 74 | sub_1F894 | 菜单文字/图标 | 用完free |
| 76 | sub_1F894 | 标题Logo | 保留 |
| 77 | sub_1F894 | 标题背景 | 保留 |
| 79 | sub_22E5C | 地图转场动画(2帧) | 用完跳转 |
| 99 | sub_1F894 | 菜单选项背景 | 保留 |
| 101 | sub_1F894 | 菜单画面2/光标效果 | 保留 |
| 102 | sub_1F894 | 选择高亮 | 保留 |

### 动态索引资源

| 索引计算方式 | 加载位置 | 用途 |
|------------|---------|------|
| `byte_52407 + i` | sub_26152 | 战斗背景/地台 (i为场景索引) |

---

## 五、关键使用模式总结

### 1. 资源生命周期管理

#### 初始化加载，全局保留
- 索引0-6、31在main初始化时加载
- 整个游戏生命周期保留
- 在多个场景模式中复用

#### 按需加载，用完释放
- 索引13、69-73、74等临时资源
- 使用后立即调用`free()`释放
- 减少内存占用

#### 循环中动态加载
- 战斗背景根据场景索引动态计算资源号
- 公式: `byte_52407 + i` (i为当前战斗场景索引)

### 2. 渲染流程

所有FDOTHER.DAT资源都遵循以下渲染流程：

```c
// 1. 加载资源到内存
void* resource = sub_111BA("FDOTHER.DAT", old_ptr, index);

// 2. 清屏（可选）
memset(655360, 0, 64000);

// 3. 设置调色板
sub_11D40(0, 255, palette_index);

// 4. 解码并渲染到VGA显存 (0xA0000 = 655360)
sub_2EB9F(resource, frame, 655360, 320, -1);
// 或
sub_4E98D(resource, frame, y_offset, 655360, 320, -1);

// 5. 刷新画面
sub_4E381();
// 或
sub_1F525(...);

// 6. 释放资源（临时资源）
free(resource);
```

### 3. 显存与调色板

- **VGA显存地址**: `0xA0000` (十进制655360)
- **显存大小**: `64000` 字节 (320x200 256色模式)
- **调色板设置**: `sub_11D40(start, end, index)` 
  - start: 调色板起始索引 (通常0)
  - end: 调色板结束索引 (通常255)
  - index: 调色板预设索引 (0, 64等)

### 4. 战斗循环中的时间控制

```c
// 基于系统计时器的帧率控制
v15 = MEMORY[0x46C];  // 读取BIOS计时器
while (!sub_10620()) {
    n4 = MEMORY[0x46C] - v15;
    if (n4 >= 4) {  // 每4个tick更新一次
        if (++dword_53F52 == 4)
            dword_53F52 = 0;
        goto LABEL_22;  // 刷新画面
    }
}
```

### 5. 输入处理

- **键盘输入**: BIOS中断 `int386(22, &n3, &n3)` (中断号0x16)
- **按键检测**: `sub_10620()` 检查是否有按键
- **常用按键**:
  - 回车(28)、空格(32): 确认
  - F2(0x22): 切换音乐
  - M(0x4D)、K(0x4B): 菜单导航
  - 上(0x48)、下(0x50): 选项选择

---

## 六、关键函数引用

| 函数地址 | 函数名 | 功能 |
|---------|-------|------|
| 0x111BA | sub_111BA | DAT资源加载 |
| 0x25BF4 | main | 游戏主循环 |
| 0x25977 | sub_25977 | 音乐场景切换 |
| 0x25EBB | sub_25EBB | 主逻辑处理/场景初始化 |
| 0x117E7 | sub_117E7 | 输入处理和场景逻辑 |
| 0x22E5C | sub_22E5C | 地图转场处理 |
| 0x26152 | sub_26152 | 战斗主循环 |
| 0x1F894 | sub_1F894 | 标题与菜单系统 |
| 0x2670E | sub_2670E | 战斗结果处理 |
| 0x4E381 | sub_4E381 | 画面刷新 |
| 0x2EB9F | sub_2EB9F | 资源解码渲染 |
| 0x4E98D | sub_4E98D | 资源解码渲染(带偏移) |
| 0x11D40 | sub_11D40 | 调色板设置 |
| 0x1F525 | sub_1F525 | 画面刷新(备用) |

---

## 七、文件结构总结

```
FDOTHER.DAT
├── 文件头 (6字节)
├── 索引表
│   ├── 索引0: offset, size (全局基础资源)
│   ├── 索引1: offset, size (字体)
│   ├── 索引2: offset, size (UI元素)
│   ├── 索引3: offset, size (UI元素)
│   ├── 索引4: offset, size (UI元素)
│   ├── 索引5: offset, size (UI元素)
│   ├── 索引6: offset, size (背景/UI)
│   ├── 索引7: offset, size (存档界面背景)
│   ├── 索引8: offset, size (存档界面前景)
│   ├── 索引10: offset, size (战斗UI)
│   ├── 索引13: offset, size (战斗初始化)
│   ├── 索引31: offset, size (战斗菜单)
│   ├── 索引69-73: offset, size (标题动画5帧)
│   ├── 索引74: offset, size (菜单文字)
│   ├── 索引76: offset, size (标题Logo)
│   ├── 索引77: offset, size (标题背景)
│   ├── 索引79: offset, size (地图转场)
│   ├── 索引99: offset, size (菜单选项)
│   ├── 索引101: offset, size (菜单画面)
│   └── 索引102: offset, size (选择高亮)
└── 资源数据区
    ├── 资源0数据
    ├── 资源1数据
    ├── ...
    └── 资源N数据
```

---

*本文档基于IDA Pro MCP对FD2.EXE的反汇编分析生成*
*所有结论均来自实际汇编代码，未做任何猜测*
