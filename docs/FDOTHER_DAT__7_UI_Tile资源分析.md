# FDOTHER.DAT__7 (地址: 0x53a81) 分析报告

## 基本信息

| 项目 | 值 |
|------|-----|
| 全局变量名 | `_FDOTHER.DAT__7` |
| 内存地址 | 0x53a81 |
| 资源类型 | 动态索引 UI tile 图集 |
| 数据文件 | FDOTHER.DAT |
| 使用场景 | 战场场景 UI 渲染 (过场动画、范围显示、光标效果) |

---

## 动态索引分析

`_FDOTHER.DAT__7` **不是固定索引资源**，而是通过动态索引加载的资源。

### 索引来源 1: sub_2FF01 (0x2ff01)

在 [2FF01.c:132](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/2FF01.c#L132) 定义索引数组：
```c
qmemcpy(v73, "RRSTUVWXYZ", 10);
```

在 [2FF01.c:188-196](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/2FF01.c#L188-L196) 加载资源：
```c
FDOTHER_DAT__7 = 0;
FDOTHER_DAT__7 = (int)sub_111BA(
        (unsigned __int8)v73[n28],  // 动态索引
        v21,
        _FIGANI.DAT__1,
        0,
        (int)aFdotherDat,
        0,
        (unsigned __int8)v73[n28]);
```

**动态索引映射表 (n28 为场景编号):**

| n28 场景编号 | v73[n28] ASCII | 十进制值 | FDOTHER.DAT 文件索引 |
|-------------|----------------|----------|---------------------|
| 0 | 'R' | 82 | 82 |
| 1 | 'R' | 82 | 82 |
| 2 | 'S' | 83 | 83 |
| 3 | 'T' | 84 | 84 |
| 4 | 'U' | 85 | 85 |
| 5 | 'V' | 86 | 86 |
| 6 | 'W' | 87 | 87 |
| 7 | 'X' | 88 | 88 |
| 8 | 'Y' | 89 | 89 |
| 9 | 'Z' | 90 | 90 |
| 10+ | 越界 | - | 未定义 |

### 索引来源 2: sub_2D80D (0x2d80d)

在 [2D80D.c:42](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/2D80D.c#L42) 和 [2D80D.c:61](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/2D80D.c#L61):
```c
_DWORD v40[2]; // [esp+0h] [ebp-54h]
...
qmemcpy(v46, "?355[\\]^", sizeof(v46));
```

在 [2D80D.c:88-96](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/2D80D.c#L88-L96) 加载资源：
```c
FDOTHER_DAT__7 = 0;
FDOTHER_DAT__7 = (int)sub_111BA(
        *((unsigned __int8 *)v40 + n28),  // 动态索引
        v12,
        (int)_FIGANI.DAT__2,
        n2_1,
        (int)aFdotherDat,
        0,
        *((unsigned __int8 *)v40 + n28));
```

**注意**: `v40` 与 `v46` 在栈上相邻，实际使用的是 `v46` 数组的值作为索引。

**动态索引映射表 (n28 为场景编号 32-35):**

| n28 场景编号 | v46 对应字符 | ASCII 十进制 | FDOTHER.DAT 文件索引 |
|-------------|-------------|-------------|---------------------|
| 32 (0x20 ' ') | '?' | 63 | 63 |
| 33 (0x21 '!') | '3' | 51 | 51 |
| 34 (0x22 '"') | '5' | 53 | 53 |
| 35 (0x23 '#') | '5' | 53 | 53 |

---

## 使用场景

### 场景 1: sub_2D80D - 战场过场动画渲染

该函数负责战场场景 32-35 的过场动画渲染。

#### 1.1 双缓冲渲染 (场景 34-35)

在 [2D80D.c:126-152](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/2D80D.c#L126-L152):
```c
if ( n28 == 33 || n28 == 34 )
  sub_2EB9F((int)_FDOTHER.DAT_, 0, v9, 320, -1);

for ( n2 = 1; n2 < (unsigned __int8)*_FDOTHER.DAT_; ++n2 )
{
  // ... 渲染背景 ...
  
  // 场景 35 且 tile 索引为 2 时，使用双缓冲
  if ( n28 == 35 && n2 == 1 )
  {
    sub_25B45(v24, SHIDWORD(v24), n2, n2_1, FDOTHER_DAT__7, 2, n2);
  }
  
  // 场景 33 且 tile 索引为 6 时，使用单缓冲
  if ( n28 == 33 && n2 == 6 )
  {
    sub_25A96(v24, SHIDWORD(v24), n2, n2_1, FDOTHER_DAT__7, 1, 1);
  }
  
  // 场景 32 且 tile 索引为 1 时，使用双缓冲
  if ( n28 == 32 && n2 == 1 )
  {
    sub_25B45(v24, SHIDWORD(v24), n2, n2_1, FDOTHER_DAT__7, 2, n2);
  }
}
```

#### 1.2 循环动画渲染 (场景 32, 35)

在 [2D80D.c:153-180](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/2D80D.c#L153-L180):
```c
v54 = n28 - 32;
if ( n28 == 32 || n28 == 35 )
{
  for ( n10 = 0; n10 <= 10; ++n10 )
  {
    // 偶数帧渲染 UI tile
    if ( !(n10 % 2) )
      sub_25A96(n10 / 2, 0, n10, 2, FDOTHER_DAT__7, 1, 1);
    
    // ... 渲染背景和淡入淡出效果 ...
  }
}
```

**动画帧说明:**
- 循环 11 帧 (n10 = 0 到 10)
- 偶数帧 (0, 2, 4, 6, 8, 10) 渲染 UI tile
- tile 索引使用 `n10 / 2`，即索引 0-5
- 用于实现渐进式动画效果

#### 1.3 淡出效果

在 [2D80D.c:208-225](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/2D80D.c#L208-L225):
```c
for ( n40 = 0; n40 <= 40; ++n40 )
{
  // ... 延迟和颜色过渡 ...
  v32 = j___delay(6);
}
sub_25A96(v32, n50, n40, n2_1, FDOTHER_DAT__7, -1, 1);
```

#### 1.4 资源释放

在 [2D80D.c:226-227](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/2D80D.c#L226-L227):
```c
v34 = free(FDOTHER_DAT__7);
```

### 场景 2: sub_30E9D - 地图事件渲染

在 [30E9D.c:73-81](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/30E9D.c#L73-L81):
```c
if ( n28 < 10 || n28 >= 32 )
{
  n6 = 6;
  _FDOTHER.DAT_ = FDOTHER_DAT__3;
  v20 = FDOTHER_DAT__3 + *(_DWORD *)(FDOTHER_DAT__3 + 4 * n11 + 6);
  sub_4E8D3(_BG.DAT_, 0, 50, a10, 320, v20);
  LOBYTE(v15) = sub_4E8D3(_TAI.DAT_, 164, 157, a10, 320, v20);
  sub_25A96(v15, _FDOTHER.DAT_, n3, n2, FDOTHER_DAT__7, 0, 1);
}
```

**使用条件:**
- n28 < 10 (场景 0-9) 或 n28 >= 32 (场景 32+)
- 用于在地图事件渲染后绘制 UI 覆盖层

### 场景 3: sub_2FF01 - 主战场渲染

在 [2FF01.c:511-512](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/2FF01.c#L511-L512):
```c
sub_25A96(v64, _FDOTHER.DAT__1, _FIGANI.DAT__1, v9, FDOTHER_DAT__7, -1, 1);
free(FDOTHER_DAT__7);
```

**使用场景:**
- 战场渲染结束时，使用 tile 索引 -1 进行淡出清除
- 随后释放资源

---

## 渲染函数说明

### sub_25A96 - 单缓冲渲染

```c
sub_25A96(tile索引, 未知参数, 帧索引, 未知参数, FDOTHER_DAT__7, 颜色模式, 1);
```

- 直接在显存 (0xA0000) 上绘制
- 用于静态 UI 或简单动画

### sub_25B45 - 双缓冲渲染

```c
sub_25B45(tile索引, 未知参数, 帧索引, 未知参数, FDOTHER_DAT__7, 颜色模式, n2);
```

- 先在后台缓冲区绘制，再翻转到显存
- 用于复杂动画，避免闪烁

---

## Tile 索引使用总结

| 场景编号 | Tile 索引范围 | 渲染方式 | 用途 |
|---------|--------------|---------|------|
| 32 | 0-5 | sub_25A96 (单缓冲) | 渐进式动画 |
| 32 | 1 | sub_25B45 (双缓冲) | 特效叠加 |
| 33 | 0 | sub_25A96 (单缓冲) | UI 覆盖层 |
| 33 | 6 | sub_25A96 (单缓冲) | 特效动画 |
| 34 | - | - | 未直接使用 |
| 35 | 1 | sub_25B45 (双缓冲) | 特效叠加 |
| 0-9 | 0 | sub_25A96 (单缓冲) | UI 覆盖层 |
| 结束淡出 | -1 | sub_25A96 (单缓冲) | 清除效果 |

---

## 资源加载流程

```
sub_2FF01 / sub_2D80D
    │
    ├── 加载 FDOTHER.DAT 主资源 (_FDOTHER.DAT_)
    │   └── 索引: n28+33 或其他动态计算值
    │
    ├── 加载 FDOTHER.DAT__7 (UI tile 图集)
    │   └── 索引: v73[n28] 或 v46[n28-32]
    │
    ├── 渲染循环
    │   ├── sub_25A96 (单缓冲绘制)
    │   └── sub_25B45 (双缓冲绘制)
    │
    └── free(FDOTHER_DAT__7) 释放资源
```

---

## 结论

`_FDOTHER.DAT__7` (0x53a81) 是一个**动态索引的 UI tile 图集资源**，主要用于：

1. **战场过场动画** - 场景 32-35 的渐入渐出效果
2. **UI 覆盖层** - 在地图事件渲染后绘制额外 UI 元素
3. **特效动画** - 使用 tile 索引 0-6 实现不同帧的动画效果
4. **淡出清除** - 使用 tile 索引 -1 实现屏幕清除效果

该资源的特点：
- **动态索引**: 根据场景编号 (n28) 从预定义数组获取实际文件索引
- **临时性**: 在渲染函数开始时加载，结束时立即释放
- **多用途**: 支持单缓冲和双缓冲两种渲染模式
- **动画支持**: 通过 tile 索引循环实现逐帧动画效果
