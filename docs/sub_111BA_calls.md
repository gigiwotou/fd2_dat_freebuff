# sub_111BA 调用分析

## 概述
`sub_111BA` 是FD2.EXE中加载DAT文件的核心函数，负责从DAT文件中根据索引加载数据块到内存。

## 函数签名
```c
_BYTE *__fastcall sub_111BA(
    __int32 a1,    // 未知用途
    int a2,        // 未知用途  
    int a3,        // 未知用途
    int a4,        // 未知用途
    int a5,        // DAT文件名 (如 "FDOTHER.DAT")
    int a6,        // 之前分配的内存指针 (用于释放)
    int a7         // 数据块索引号
);
```

## 所有调用位置汇总

### 1. main函数 (0x25BF4)
共调用 **8次**，加载初始资源文件：

| 序号 | 加载的文件 | 索引 | 保存到变量 |
|------|-----------|------|-----------|
| 1 | FDOTHER.DAT | 31 | FDOTHER_DAT__2 |
| 2 | FDOTHER.DAT | 1 | FDOTHER_DAT__3 |
| 3 | FDOTHER.DAT | 2 | FDOTHER_DAT__4 |
| 4 | FDOTHER.DAT | 3 | FDOTHER_DAT__5 |
| 5 | FDOTHER.DAT | 4 | FDOTHER_DAT__6 |
| 6 | FDOTHER.DAT | 5 | FDOTHER_DAT__7 |
| 7 | FDTXT.DAT | 0 | FDTXT_DAT__0 |
| 8 | FDOTHER.DAT | 6 | FDOTHER_DAT__8 |

### 2. sub_10010 (0x10010) - 存档加载函数
共调用 **6次**，从存档恢复游戏状态时加载资源：

| 序号 | 加载的文件 | 索引 | 保存到变量 |
|------|-----------|------|-----------|
| 1 | FDOTHER.DAT | 0 | FDOTHER_DAT |
| 2 | FDFIELD.DAT | 3*n17+2 | FDFIELD_DAT |
| 3 | FDTXT.DAT | n17+1 | FDTXT_DAT |
| 4 | FDFIELD.DAT | 3*n17 | FDFIELD_DAT__0 |
| 5 | FDSHAP.DAT | 2*byte | FDSHAP_DAT |
| 6 | FDSHAP.DAT | 2*byte+1 | FDSHAP_DAT__0 |

### 3. sub_25EBB (0x25EBB) - 游戏状态加载函数
共调用 **2次**，处理游戏状态切换：

| 序号 | 加载的文件 | 索引 | 保存到变量 |
|------|-----------|------|-----------|
| 1 | FDOTHER.DAT | 13 | FDOTHER_DAT__11 |
| 2 | FDOTHER.DAT | 0 | FDOTHER_DAT |

### 4. sub_1F894 (0x1F894) - 启动画面加载函数
共调用 **14次**，显示启动动画时加载资源：

| 序号 | 加载的文件 | 索引 | 说明 |
|------|-----------|------|------|
| 1 | FDOTHER.DAT | 77 | var_18 |
| 2 | FDOTHER.DAT | 76 | FDOTHER_DAT |
| 3 | FDOTHER.DAT | 74 | var_28 (short*) |
| 4 | FDOTHER.DAT | 99 | FDOTHER_DAT |
| 5 | FDOTHER.DAT | 101 | FDOTHER_DAT |
| 6-10 | FDOTHER.DAT | 69-73 | 循环加载5帧动画 |
| 11 | FDOTHER.DAT | 7 | var_24 (菜单资源) |
| 12 | FDOTHER.DAT | 8 | FDOTHER_DAT |
| 13 | FDOTHER.DAT | 102 | 动画关键帧加载 (在循环中) |
| 14 | FDOTHER.DAT | 101 | 动画关键帧加载 (在循环中) |

## 调用统计

| 调用函数 | 调用次数 | 用途 |
|---------|---------|------|
| main | 8 | 初始资源加载 |
| sub_10010 | 6 | 存档恢复加载 |
| sub_25EBB | 2 | 游戏状态切换 |
| sub_1F894 | 14 | 启动画面动画 |
| **总计** | **30** | |

## 加载的文件类型

| 文件名 | 加载次数 | 说明 |
|--------|---------|------|
| FDOTHER.DAT | 24 | 最大的资源文件，包含至少103个索引 |
| FDFIELD.DAT | 3 | 地图/场资源文件 |
| FDTXT.DAT | 2 | 文本资源文件 |
| FDSHAP.DAT | 2 | 形状资源文件 |

## 调用模式分析

### 典型调用流程
```c
// 1. 释放旧内存
if (old_ptr)
    free(old_ptr);

// 2. 加载新数据
new_ptr = sub_111BA(a1, a2, a3, a4, 
                    (int)"FILENAME.DAT", 
                    old_ptr,  // 旧指针用于释放
                    index);   // 索引号

// 3. 使用新数据
// ...
```

### 索引计算模式
- **固定索引**: 直接使用数字 (如 0, 1, 2, 77, 76)
- **动态索引**: 基于变量计算 (如 `3*n17+2`, `n17+1`)
- **循环索引**: 在循环中递增 (如 `for(i=69; i<74; i++)`)

## 重要观察

1. **FDOTHER.DAT是最核心的资源文件**，占所有调用的80%
2. **内存管理**: 每次调用都会先释放旧内存，避免内存泄漏
3. **索引范围**: FDOTHER.DAT使用的索引从0到102，至少包含103个数据块
4. **动态加载**: 地图相关资源(FDFIELD, FDSHAP)的索引根据当前地图动态计算
