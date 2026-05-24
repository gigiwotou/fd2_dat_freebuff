# FDOTHER_DAT__3 资源分析报告

> 基于 IDA Pro MCP 反编译代码 1:1 分析
> 分析日期: 2026-05-24

---

## 一、基本信息

| 项目 | 值 |
|------|-----|
| **全局变量名** | `_FDOTHER.DAT__3` |
| **变量地址** | 0x53a4d |
| **实际文件索引** | **3** |
| **所属文件** | FDOTHER.DAT |
| **加载位置** | main (0x25BF4) |

---

## 二、加载代码

### 2.1 main 函数中的加载

在 [main(0x25BF4)](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/25BF4.c#L49) 中：

```c
FDOTHER_DAT__3 = (int)sub_111BA(n30_0, v9, v6, v5, (int)aFdotherDat, FDOTHER_DAT__3, 3);  // "FDOTHER.DAT" 索引3
FDOTHER_DAT__4 = (int)sub_111BA(FDOTHER_DAT__3, v9, v6, v5, (int)aFdotherDat, FDOTHER_DAT__4, 4);  // "FDOTHER.DAT" 索引4
```

**注意**: 变量名中的 `__3` 与实际文件索引 `3` 恰好一致（这是巧合，其他变量如 `FDOTHER_DAT__2` 实际加载的是索引31）。

---

## 三、使用场景

### 3.1 战场渲染函数

`_FDOTHER.DAT__3` 主要在以下战场相关函数中使用：

| 函数 | 地址 | 用途 |
|------|------|------|
| `sub_30E9D` | 0x30E9D | 战场角色/特效渲染 |
| `sub_2FF01` | 0x2FF01 | 战场主渲染循环 |

### 3.2 sub_30E9D 中的使用

在 [sub_30E9D.c:74-80](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/30E9D.c#L74-L80) 中：

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

### 3.3 sub_2FF01 中的使用

在 [sub_2FF01.c:493-500](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/2FF01.c#L493-L500) 中：

```c
for ( n4 = 1; n4 < 4; ++n4 )
{
    sub_11EB0(v49, _FDOTHER.DAT__1, _FIGANI.DAT__1, v9, arg8_3, 320, v97, 320, 320, 200);
    _FDOTHER.DAT__1 = FDOTHER_DAT__3;
    v79 = FDOTHER_DAT__3 + *(_DWORD *)(FDOTHER_DAT__3 + 4 * (n4 + n11) + 6);
    sub_4E8D3(_BG.DAT__1, 0, 50, v97, 320, v79);
    LOBYTE(v59) = sub_4E8D3(_TAI.DAT_, 164, 157, v97, 320, v79);
    sub_2EB9F(v59, _FDOTHER.DAT__1, _FIGANI.DAT__1, v9, (int)n3, 0, arg8_3, 320, -1);
    // ...
}
```

---

## 四、Tile 索引分析

### 4.1 索引计算逻辑

资源使用 tile 图集索引公式：

```c
tile_data_ptr = *(DWORD*)(资源基址 + 4*tile索引 + 6) + 资源基址;
```

### 4.2 实际使用的 Tile 索引

根据 `n11` 和 `n4` 变量的值，使用的 tile 索引范围：

| 战场类型 (n28) | n11 值 | 使用的 tile 索引范围 |
|----------------|--------|---------------------|
| n28 < 10 或 n28 >= 32 | 11 | **11** |
| n28 > 3 | 15 | **15** |
| n28 == 8 或 32 或 33 | 19 | **19** |

在 `sub_2FF01` 循环中，还会额外使用：
- **n4 + n11**: 即 12-14, 16-18, 20-22 等索引

### 4.3 n11 的计算逻辑

在 `sub_30E9D` 中：

```c
n11 = 11;  // 默认值
if ( n28 == 8 || n28 == 32 || n28 == 33 )
{
    n11 = 19;
}
else if ( n28 > 3 )
{
    n11 = 15;
}
```

---

## 五、sub_4E8D3 函数分析

### 5.1 函数定义

**地址**: 0x4E8D3

```c
char __cdecl sub_4E8D3(
    __int16 *_BG.DAT_,    // 目标缓冲区指针
    int n164,             // X偏移
    int n50,              // Y偏移
    int arg0,             // 目标屏幕地址
    int n320,             // 行距(320)
    int a6                // tile数据指针
);
```

### 5.2 功能说明

这是一个 **RLE解压缩并写入目标缓冲区** 的函数：
- 从 tile 数据源读取 RLE 压缩数据
- 解压后写入到目标缓冲区的指定偏移位置
- 支持透明色处理

### 5.3 绘制位置

| 缓冲区 | X偏移 | Y偏移 | 用途 |
|--------|-------|-------|------|
| _BG.DAT_ | 0 | 50 | 背景叠加层 |
| _TAI.DAT_ | 164 | 157 | 敌人/目标叠加层 |

---

## 六、功能总结

### 6.1 资源内容

`_FDOTHER.DAT__3` (FDOTHER.DAT 索引3) 存储的是 **战场叠加层/高亮效果 tile 图集**。

### 6.2 具体用途

1. **战场特殊效果叠加**
   - 叠加在地图背景之上的视觉效果
   - 可能是攻击范围/移动范围的高亮显示

2. **战场 UI 覆盖层**
   - 非基础地图，而是叠加在地图之上的效果层
   - 用于突出显示特定区域或单位

3. **动画帧支持**
   - 包含多个 tile (索引 11-22)
   - 可能用于不同战场类型的不同效果

### 6.3 与其他资源的关系

| 资源 | 索引 | 用途 | 与 FDOTHER_DAT__3 的关系 |
|------|------|------|-------------------------|
| FDOTHER_DAT__7 | 5 | UI Tiles | 作为后续渲染的数据源 |
| BG.DAT | 动态 | 地图背景 | 接收 FDOTHER_DAT__3 的叠加层 |
| TAI.DAT | 动态 | 敌人数据 | 接收 FDOTHER_DAT__3 的目标叠加层 |
| FIGANI.DAT | 动态 | 角色动画 | 与 FDOTHER_DAT__3 配合渲染 |

---

## 七、调用链

```
main (0x25BF4)
├── 加载 FDOTHER.DAT 索引3 → FDOTHER_DAT__3
│
└── sub_25EBB (主菜单)
    └── sub_117E7 (战场入口)
        └── funcs_1197B[n17] (战场函数表)
            └── sub_2FF01 (战场主渲染)
                ├── sub_30E9D (角色/特效渲染)
                │   └── sub_4E8D3 (使用 FDOTHER_DAT__3 绘制叠加层)
                └── sub_4E8D3 (直接使用 FDOTHER_DAT__3)
```

---

## 八、关键发现

### 8.1 战场类型与 tile 索引的对应

游戏根据战场类型 (`n28`) 选择不同的 tile 索引：
- **普通战场**: 使用 tile 11
- **特殊战场**: 使用 tile 15
- **特定战场 (8/32/33)**: 使用 tile 19

### 8.2 循环渲染

在 `sub_2FF01` 中，对 tile 12-14/16-18/20-22 进行了循环渲染（n4 从 1 到 3），这可能是：
- 动画帧序列
- 不同状态下的显示效果
- 多层次的叠加效果

### 8.3 与 FDOTHER_DAT__5 的配合

在 `sub_2FF01` 的后半部分，`FDOTHER_DAT__5` (索引3) 也被用于类似的目的：

```c
_FDOTHER.DAT__1 = FDOTHER_DAT__5;
v81 = FDOTHER_DAT__5 + *(_DWORD *)(FDOTHER_DAT__5 + 4 * (n4 + n11_1) + 6);
sub_4E8D3((__int16 *)_BG.DAT__1, 0, 50, arg0_1, 320, v81);
```

---

*分析完成日期: 2026-05-24*
*分析方法: IDA Pro MCP 反编译代码分析*
*分析范围: FDOTHER_DAT__3 战场资源完整追踪*
