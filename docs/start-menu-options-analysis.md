# FD2 开始菜单3个选项逻辑分析

> 来源: IDA Pro MCP 逆向分析 FD2.EXE
> 日期: 2026-05-02

---

## 一、概述

开始菜单通过 `sub_1F894` (0x1F894) 显示，包含 **3个选项**（根据存档状态动态显示）：

| 选项索引 (n3) | 显示条件 | 说明 | 存档类型 |
|--------------|----------|------|----------|
| 0 | 始终显示 | Start (新游戏) | 无 |
| 1 | n100 >= 2 | Load (读取营地存档) | 营地存档 |
| 2 | n100 >= 3 | Continue (读取战场存档) | 战场存档 |

### 菜单选项数量判断

```c
// 检查存档状态
_rb_ = fopen("FD2.SAV", "rb");
if (_rb_) {
    v21 = malloc(22987);
    sub_373CA(v21, 1u, 22987, _rb_);
    sub_4DF28(v21, 22987);
    if (sub_4DF09(v21, 22987) == *(_DWORD *)(v21 + 22983)) {
        n100 = 2;  // 有营地存档，显示 Load
        if (*(unsigned __int8 *)(v21 + 12485) != 255)
            n100 = 3;  // 有战场存档，显示 Continue
    }
    free(v34);
}
```

**存档判断条件**:
- **营地存档**: 存档文件存在且校验和匹配 (n100 = 2)
- **战场存档**: `v21 + 12485 != 255` (场景索引有效) (n100 = 3)

---

## 二、菜单选项状态分析

### 选项0：Start (新游戏)

**返回值**: `v8 = 0`

**执行路径** ([25EBB.c:31-47](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/25EBB.c#L31-L47)):

```c
// sub_25EBB 判断 v8 == 0
n17 = 0;  // 设置场景索引为 0
FDOTHER_DAT = sub_111BA(..., 0);  // 加载 FDOTHER#0
funcs_25E3A[0]();  // 调用开场剧情场景 (sub_3231B)
sub_25977(byte_51E63[0], ...);  // 播放场景音乐
byte_51AAC = 1;  // 启用操作
sub_4E381();  // 刷新屏幕
return 0;  // 返回 main 循环
```

**进入状态循环**:

```
main()
  └── sub_25EBB() 返回 0
       └── while (!i) {
            sub_117E7()  // 状态 0: 主输入处理
            if (n2_0 == 1) {
                sub_22E5C()  // 状态 1: 过渡/加载
                n2_0 = 0;
            }
            if (n2_0 == 2) {
                funcs_25E23[n17]()  // 状态 2: 战斗/场景
                if (!sub_26152()) {
                    funcs_25E3A[n17]()
                    sub_25977(...)
                }
                n2_0 = 0;
            }
         }
```

**状态流程**:

```
开场动画
  └── sub_3231B (开场剧情)
       ├── 加载地图资源
       ├── 播放剧情动画
       ├── 播放对话 0-12
       ├── 战斗动画演示 (sub_32999)
       └── sub_12D7B() 设置 n6_6 = 0
            └── 进入主循环
                 ├── sub_117E7() 处理输入
                 ├── sub_134E4() 切换到交互模式
                 └── 通用地图系统
```

---

### 选项1：Load (读取营地存档)

**返回值**: `v8 = 1`

**说明**: 读取玩家在营地的存档，加载角色状态、地图数据等，回到营地界面。

**执行路径** ([25EBB.c:49-118](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/25EBB.c#L49-L118)):

```c
// sub_25EBB 判断 v8 == 1
// 加载营地存档相关资源
dword_53F66 = sub_111BA(..., 13);  // 加载 FDOTHER#13
FDOTHER_DAT = sub_111BA(..., 0);  // 加载 FDOTHER#0
sub_11D40(..., 0, 255, 0);  // 淡出效果

// 读取 FD2.SAV
v14 = malloc(22987);
v15 = fopen("FD2.SAV", "rb");
if (v15) {
    sub_373CA(v12, 1u, 22987, v14);
    sub_4DF28(v12, 22987);
    fclose(v15);
}

// 解析营地存档数据
do {
    v16 = sub_29BCB(v13, 0);
    if (v16 != -1) {
        n17 = *v12;  // 恢复场景索引
        dword_53BFB = v12[1];  // 地图数量
        n6_6 = *(_DWORD *)(v12 + 2);  // 当前位置
        byte_51AAB = v12[6];
        byte_53AF9 = v12[7];
        n127 = v12[8];
        byte_51E62 = v12[9];
    }
    sub_26996();
} while (!v16);

// 初始化场景
if (v16 == 1) {
    byte_51AAC = 0;
    v16 = sub_26152();  // 场景初始化
    if (!v16) {
        funcs_25E3A[n17]();
        sub_25977(byte_51E63[n17], ...);
    }
    byte_51AAC = 1;
}
sub_4E381();
return v16;  // 返回 sub_26152 的结果
```

**进入状态循环**:

```
main()
  └── sub_25EBB() 返回 v16 (sub_26152 结果)
       ├── 返回 0: 进入主循环
       └── 返回 1: 跳过主循环，直接进入下一轮
```

**状态流程**:

```
加载营地存档
  └── sub_26152() 场景初始化
       ├── byte_523E7[n17] == 1: 特殊场景
       │    ├── sub_1956B() 加载场景
       │    ├── sub_15F84() 显示对话
       │    └── sub_2AF28() 等待交互
       └── byte_523E7[n17] == 0: 通用场景
            ├── sub_4E809() 加载地图
            ├── sub_2EB9F() 渲染场景
            └── 按键检测循环
                 ├── 方向键 (0x4D/0x4B)
                 ├── 确认键 (0x22)
                 └── 场景切换 (sub_2670E)
```

---

### 选项2：Continue (读取战场存档)

**返回值**: `v8 != 0 && v8 != 1` (根据菜单选择返回值)

**说明**: 读取玩家在战场的存档，直接回到战场继续战斗。

**执行路径** ([25EBB.c:49-55](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/25EBB.c#L49-L55)):

```c
// sub_25EBB 判断 v8 != 0 && v8 != 1
sub_25977(v8, ..., -1, 0);  // 停止当前音乐
sub_10010();  // 加载战场存档
sub_25977(byte_51E63[n17], ...);  // 播放场景音乐
return 0;  // 返回 0，进入主循环
```

**sub_10010 函数 - 战场存档加载**:

```c
void sub_10010() {
    v0 = malloc(22987);
    v3 = fopen("FD2.SAV", "rb");
    sub_373CA(v0, 1, 22987, v3);
    sub_4DF28(v0, 22987);
    
    // 校验存档完整性
    if (sub_4DF09(v0, 22987) != *(_DWORD *)(v0 + 22983)) {
        // 校验失败，显示错误
        sub_1956B(75);
        sub_15F84(dword_53A7D, 436, ...);
        sub_16559(0);
        sub_16C57(0);
        sub_196CB();
    }
    
    // 加载战场数据
    sub_1F882();
    memmove(dword_53BF7, v0 + 2211, 2560);  // 复制地图数据
    FDOTHER_DAT = sub_111BA(..., 0);  // 加载 FDOTHER#0
    n17 = *(unsigned __int8 *)(v0 + 12485);  // 恢复场景索引
    dword_53A59 = sub_111BA(..., 3 * n17 + 2);  // 加载 FDFIELD.DAT
    
    // 加载地图形状和文本
    dword_53A55 = malloc(2211);
    memmove(dword_53A55, v0, 2211);
    sub_10652(v4);
    dword_53A79 = sub_111BA(..., n17 + 1);  // 加载 FDTXT.DAT
    dword_53A51 = sub_111BA(..., 3 * n17);  // 加载 FDFIELD.DAT
    
    // 加载形状数据
    v5 = 2 * *(unsigned __int8 *)dword_53A55;
    dword_53A5D = sub_111BA(..., v5);  // 加载 FDSHAP.DAT
    dword_53A69 = sub_111BA(..., v5 + 1);  // 加载 FDSHAP.DAT
    
    // 恢复角色和地图状态
    ::n6 = *(unsigned __int8 *)(dword_53A55 + 1);
    dword_53BE3 = *(unsigned __int8 *)(dword_53A55 + 2);
    n6_0 = *(unsigned __int8 *)(v0 + 12484);  // 角色数量
    
    // 加载角色数据
    dword_53A45 = malloc(7680);
    memmove(dword_53A45, v0 + 4771, 80 * n6_0);
    memmove(dword_53AD5, v0 + 12451, 32);
    
    // 加载图标
    v14 = fopen("fdicon.b24", "rb");
    for (i = 0; i < n6_0; ++i)
        *(dword_53A45 + 80 * i + 2) = sub_11019(..., v14);
    
    // 恢复游戏状态变量
    dword_53BEF = *(v0 + 12483);
    dword_53AA9 = *(v0 + 12486);
    dword_53AAD = *(v0 + 12487);
    // ... 更多状态恢复
    
    // 播放音乐，显示过渡动画
    sub_25977(byte_51E63[n17], 0);
    sub_12263();  // 过渡处理
    sub_11CAC(1);  // 淡入
    sub_1F525();  // 刷新屏幕
    
    // 播放对话和动画
    for (n6 = 0; n6 < 9; ++n6) {
        sub_15F0E(..., n6 + 83);  // 播放对话
        if (n6 > 6)
            sub_187D6(...);
        delay(70);
        sub_15E71();
    }
    
    // 进入战斗准备状态
    dword_53AE9 = 0;
    dword_51A83 = 1;  // 设置战斗标志
    sub_4E381();  // 刷新屏幕
}
```

**进入状态循环**:

```
main()
  └── sub_25EBB() 返回 0
       └── while (!i) {
            sub_117E7()  // 状态 0: 主输入处理
            if (n2_0 == 2) {
                funcs_25E23[n17]()  // 状态 2: 战斗循环
                sub_26152()  // 检查战斗状态
                ...
            }
         }
```

**状态流程**:

```
加载战场存档
  └── sub_10010()
       ├── 加载 FDFIELD.DAT (地图数据)
       ├── 加载 FDSHAP.DAT (形状数据)
       ├── 加载 FDTXT.DAT (文本数据)
       ├── 恢复角色状态
       ├── 播放过渡动画
       ├── 显示对话 (9组)
       └── 设置 dword_51A83 = 1 (战斗标志)
            └── 进入主循环
                 └── sub_117E7() 状态 0
                      ├── 角色移动 (n44=1,44,76)
                      ├── 事件触发 (n44=57,28)
                      ├── 战斗循环
                      └── sub_18890() 等待战斗结束
```

---

## 三、菜单选择逻辑

### 菜单循环 ([1F894.c:158-190](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/1F894.c#L158-L190))

```c
n12 = 0;  // 选择标志
while (!n12) {
    sub_1FF79(_FDOTHER.DAT_, n3, n100);  // 渲染菜单
    int386(22, &::n3, &::n3);  // 获取按键
    
    switch (HIBYTE(::n3)) {
        case 72:  // 上方向键
            sub_25A96(v40, 2, 1);  // 播放音效
            if (n3)
                --n3;
            else
                n3 = n100 - 1;  // 循环到最后一个选项
            break;
        case 80:  // 下方向键
            sub_25A96(v40, 2, 1);  // 播放音效
            if (n3 == n100 - 1)
                n3 = 0;  // 循环到第一个选项
            else
                ++n3;
            break;
        default:
            // 确认键 (Enter/Space)
            if ((unsigned __int8)::n3 == 13 || 
                (unsigned __int8)::n3 == 32 || 
                HIBYTE(::n3) == 224 || 
                HIBYTE(::n3) == 82) {
                sub_25A96(v40, 1, 1);  // 播放确认音效
                n12 = 1;  // 设置选择标志，退出循环
            }
            break;
    }
}
```

### 选择闪烁效果

```c
// 选择后闪烁 4 次
for (n4 = 0; n4 < 4; ++n4) {
    sub_1FF79(_FDOTHER.DAT_, -1, n100);  // 隐藏光标
    delay(80);
    sub_1FF79(_FDOTHER.DAT_, n3, n100);  // 显示光标
    delay(80);
}
```

---

## 四、函数指针表调用关系

### 各选项调用的函数指针表

| 选项 | 返回值 | 函数指针表 | 场景索引 | 音乐索引 | 加载资源 |
|------|--------|-----------|---------|---------|---------|
| Start | 0 | funcs_25E3A[0] | n17 = 0 | byte_51E63[0] | FDOTHER#0 |
| Load | 1 | funcs_25E3A[n17] | 从存档恢复 | byte_51E63[n17] | FDOTHER#0, FD2.SAV |
| Continue | != 0,1 | sub_10010() | 从存档恢复 | byte_51E63[n17] | FDFIELD.DAT, FDSHAP.DAT, FDTXT.DAT |

---

## 五、完整状态流程图

```
sub_1F894 (开始菜单)
  ├── 播放开场动画 (sub_20421)
  ├── 检查存档 (FD2.SAV)
  │    ├── 无存档: n100 = 1 (只显示 Start)
  │    ├── 有营地存档: n100 = 2 (显示 Start + Load)
  │    └── 有战场存档: n100 = 3 (显示 Start + Load + Continue)
  ├── 显示菜单循环
  │    ├── 上方向键 (72): n3--
  │    ├── 下方向键 (80): n3++
  │    └── 确认键 (13/32): n12 = 1, 退出循环
  └── 返回值判断
       ├── v8 = 0 (Start)
       │    └── sub_25EBB 返回 0
       │         └── main 进入主循环
       │              └── sub_117E7() 状态 0
       │                   ├── n2_0 == 1: sub_22E5C() 状态 1
       │                   ├── n2_0 == 2: funcs_25E23[n17]() 状态 2
       │                   └── sub_26152() 场景初始化
       │
       ├── v8 = 1 (Load - 营地存档)
       │    └── sub_25EBB 返回 v16
       │         ├── 加载 FD2.SAV
       │         ├── 解析营地存档数据
       │         ├── sub_26152() 初始化场景
       │         └── 返回 v16 (场景初始化结果)
       │
       └── v8 != 0,1 (Continue - 战场存档)
            └── sub_25EBB 返回 0
                 └── sub_10010() 加载战场存档
                      ├── 加载 FDFIELD.DAT
                      ├── 加载 FDSHAP.DAT
                      ├── 加载 FDTXT.DAT
                      ├── 恢复角色状态
                      ├── 播放过渡动画
                      └── 进入主循环
```

---

## 六、关键函数说明

### sub_1F894 - 开始菜单主函数

```c
void sub_1F894(...);
```

**功能**: 显示开始菜单，等待用户选择

**返回值**: 通过 eax 返回选择结果 (0=Start, 1=Load, 其他=Continue)

### sub_1FF79 - 菜单渲染函数

```c
char sub_1FF79(..., int _FDOTHER.DAT_, int n3, int n2);
```

**参数**:
- `n3`: 当前选中项索引
- `n2`: 菜单选项数量

**功能**: 渲染菜单，高亮显示选中项

### sub_10010 - Continue 处理函数 (战场存档加载)

```c
void sub_10010();
```

**功能**: 加载战场存档，恢复战场状态
- 加载 FDFIELD.DAT、FDSHAP.DAT、FDTXT.DAT
- 恢复角色数据、地图数据
- 播放过渡动画和对话
- 设置战斗标志 dword_51A83 = 1

---

## 七、总结

1. **Start (选项0)**:
   - 返回值: 0
   - 进入主循环，执行开场剧情场景 (sub_3231B)
   - 使用函数指针表: funcs_25E3A[0]
   - 场景索引: n17 = 0

2. **Load (选项1 - 营地存档)**:
   - 返回值: 1
   - 加载营地存档，恢复游戏状态
   - 使用函数指针表: funcs_25E3A[n17] (从存档恢复)
   - 场景索引: 从存档读取
   - 数据源: FD2.SAV

3. **Continue (选项2 - 战场存档)**:
   - 返回值: != 0,1
   - 调用 sub_10010() 加载战场存档
   - 加载资源: FDFIELD.DAT, FDSHAP.DAT, FDTXT.DAT
   - 设置战斗标志 dword_51A83 = 1
   - 进入战场战斗循环

4. **菜单循环**:
   - 上/下方向键选择
   - 确认键 (Enter/Space) 确认
   - 选择后闪烁 4 次

5. **存档类型区别**:
   - **营地存档**: 包含角色状态、地图数据、进度信息
   - **战场存档**: 包含完整的战场状态，可直接回到战场继续战斗
   - **判断条件**: `v21 + 12485 != 255` 表示有战场存档

---

## 相关文档

- [游戏循环状态机分析](game-loop-states-analysis.md)
- [开场场景逻辑分析](opening-scene-logic-analysis.md)
- [开场动画音频系统分析](intro-animation-audio.md)
- [FDOTHER 完整资源分析](fdother-all-resources-analysis.md)
- [核心函数调用分析](core-functions-usage-analysis.md)
- IDA 反编译文件目录：`tools/export-for-ai/decompile/`
