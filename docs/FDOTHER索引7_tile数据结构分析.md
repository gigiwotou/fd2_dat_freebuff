# FDOTHER.DAT 索引7 - Tile数据结构和渲染系统分析

## 一、函数调用关系

```
sub_168B6 (0x168B6) - 窗口边框/Tile渲染主函数
  ├─ 调用者: sub_165AC, sub_17EEF, sub_1956B, sub_31C49
  └─ 被调用:
      ├─ sub_3702F (初始化)
      ├─ sub_1685C (绘制单个tile)
          └─ sub_4ED0B (实际的tile数据复制)
```

---

## 二、sub_168B6 函数签名（IDA Pro反编译）

```c
void __fastcall sub_168B6(
    __int32 a1,   // 数据源指针（DATO_DAT或其他数据）
    int a2,        // 屏幕行距 (pitch) = 320
    int a3,        // 未知参数（通常为数据指针相关）
    int a4,        // 未知参数
    int a5,        // tile列数 (tile_width)
    int a6,        // tile高度 (tile_height)
    int a7,        // FDOTHER_DAT__7 指针（对话框背景数据）
    int a8,        // 未知参数（通常为112或7）
    int a9,        // tile行数 (tile_height_count)
    int a10)       // 未知参数（通常为5）
```

---

## 三、sub_168B6 核心实现逻辑

### 3.1 初始化

```c
sub_3702F(a1, a2, a3, a4, 68);  // 栈帧初始化
v27 = a10 - 2;                   // v27 = 5 - 2 = 3
v28 = 16 * a6;                   // v28 = 16 * tile_height
v29 = 3 * a6;                    // v29 = 3 * tile_height
v10 = a5 + a6 * a8;              // v10 = tile_cols + tile_height * 112(or 7)
v11 = v10 + a7;                  // v11 = base_offset
```

### 3.2 绘制边框tile（4个角 + 4条边）

```c
// 左上角 (tile索引1)
sub_1685C(v10, a2, a3, a4, v10 + a7, a6, dword_53A81, 1);

// 右上角 (tile索引2)
v12 = 16 * a9 + v11 + 3;
sub_1685C(16 * a9, v12, a3, a4, v12, a6, dword_53A81, 2);

// 左下角 (tile索引3)
v13 = a10 * v28;
sub_1685C(v11 + v29 + a10 * v28, v12, a10 * v28, a4, 
          v11 + v29 + a10 * v28, a6, dword_53A81, 3);

// 右下角 (tile索引4)
v14 = sub_1685C(v13 + v29 + v12, v12, v13, a4, 
                v13 + v29 + v12, a6, dword_53A81, 4);

// 下边中间 (tile索引5)
sub_1685C(v14, v12, a10 * 16 * a6, a4, v11 + 3, a6, dword_53A81, 5);

// 右上区域 (tile索引6)
v15 = v11 + 19 + 16 * (a9 - 2);
sub_1685C(v11 + 19, v15, a10 * 16 * a6, a4, v15, a6, dword_53A81, 6);

// 右下区域 (tile索引7)
sub_1685C(v13 + v29 + v11 + 3, v15, v13, a4, 
          v13 + v29 + v11 + 3, a6, dword_53A81, 7);

// 左下区域 (tile索引8)
v16 = sub_1685C(v13 + v29 + v15, v15, v13, a4, 
                v13 + v29 + v15, a6, dword_53A81, 8);

// 左侧中间 (tile索引14)
v17 = sub_1685C(v16, v15, a10 * 16 * a6, a4, 
                v11 + 3 * a6, a6, dword_53A81, 14);

// 右侧中间 (tile索引15)
v18 = 16 * (a9 - 2) + v11 + 3 * a6 + 35;
sub_1685C(v17, v15, v18, a4, v18, a6, dword_53A81, 15);

// 底部中间 (tile索引16)
v19 = (a10 - 1) * 16 * a6;
v20 = sub_1685C(a10 - 1, v19, v18, a4, 
                v19 + v11 + 3 * a6, a6, dword_53A81, 16);

// 底部右下 (tile索引17)
sub_1685C(v20, v19, v19 + v18, a4, v19 + v18, a6, dword_53A81, 17);
```

### 3.3 绘制内部tile（循环）

```c
// 列循环 (i: 0 到 a9-2)
if ( a9 - 2 > 0 )
{
  for ( i = 0; i < a9 - 2; ++i )
  {
    // 上边中间 (tile索引9)
    sub_1685C(16 * i, v19, i, a4, 16 * i + v11 + 19, a6, dword_53A81, 9);
    
    // 下边中间 (tile索引12)
    sub_1685C(a10 * v28, v19, i, a4, 
              v29 + a10 * v28 + 16 * i + v11 + 19, a6, dword_53A81, 12);
  }
}

// 行循环 (j: 0 到 v27-1)
if ( v27 > 0 )
{
  for ( j = 0; j < v27; j = v23 )
  {
    v23 = j + 1;
    v24 = v11 + v29 + (j + 1) * v28;
    
    // 左边中间 (tile索引10)
    sub_1685C(v11 + v29, v19, v24, a4, v24, a6, dword_53A81, 10);
    
    // 右边中间 (tile索引11)
    sub_1685C(v24 + 16 * a9 + 3, v19, v24, a4, 
              v24 + 16 * a9 + 3, a6, dword_53A81, 11);
  }
}

// 中心区域 (tile索引13)
for ( k = 0; k < a10; ++k )
{
  for ( m = 0; m < a9; ++m )
    sub_1685C(
      16 * m + v11 + v29 + 3 + k * v28,
      16 * m + v11 + v29 + 3,
      m,
      a4,
      16 * m + v11 + v29 + 3 + k * v28,
      a6,
      dword_53A81,
      13);
}
```

---

## 四、sub_1685C - Tile绘制函数

### 4.1 函数签名

```c
int __fastcall sub_1685C(
    __int32 a1,  // 目标偏移
    int a2,      // 屏幕行距 (pitch)
    int a3,      // 未知
    int a4,      // 未知
    char *dst,   // 目标缓冲区指针
    int a6,      // tile高度
    int a7,      // FDOTHER_DAT__7 指针
    int a8)      // tile索引（帧索引）
```

### 4.2 实现逻辑

```c
sub_3702F(a1, a2, a3, a4, 20);  // 初始化
return sub_4ED0B(dst, 
                 *(_DWORD *)(a7 + 4 * a8 + 6) + a7,  // 获取tile数据指针
                 a6);
```

**关键公式**:
```
tile数据指针 = FDOTHER_DAT__7 + *(DWORD *)(FDOTHER_DAT__7 + 4*tile_index + 6)
```

---

## 五、sub_4ED0B - Tile数据复制函数

### 5.1 函数签名

```c
void __cdecl sub_4ED0B(
    char *dst,    // 目标缓冲区
    _WORD *a2,    // tile数据指针
    int a3)       // 屏幕行距 (pitch)
```

### 5.2 实现逻辑

```c
count = *a2;        // tile宽度（像素）
src = (char *)(a2 + 2);  // 跳过宽度字段
v6 = a2[1];         // tile高度（行数）

do {
  qmemcpy(dst, src, count);  // 复制一行像素
  src += count;              // 下一行源数据
  dst += a3;                 // 下一行目标（按pitch偏移）
  --v6;
} while ( v6 );
```

**原理**:
1. 读取tile宽度（WORD）
2. 读取tile高度（WORD）
3. 逐行复制像素数据到屏幕缓冲区
4. 每行复制后按pitch前进目标指针

---

## 六、FDOTHER.DAT 索引7 数据结构

### 6.1 数据格式

```
FDOTHER.DAT索引7（对话框背景/tile集）结构：

[头部]
  偏移 0-1: 总宽度 (WORD)
  偏移 2-3: 总高度 (WORD)
  偏移 4-5: tile数量 (WORD)
  偏移 6+:  tile偏移表 (DWORD数组)

[Tile偏移表]
  每个tile: DWORD (4字节)
  tile 0: 偏移 6-9
  tile 1: 偏移 10-13
  ...
  tile N: 偏移 6 + 4*N

[Tile数据]
  每个tile:
    偏移 0-1: tile宽度 (WORD)
    偏移 2-3: tile高度 (WORD)
    偏移 4+:  像素数据 (宽度 × 高度 字节)
```

### 6.2 Tile索引映射

根据 `sub_168B6` 的调用，tile索引映射如下：

| Tile索引 | 用途 | 位置 |
|----------|------|------|
| 1 | 左上角 | 窗口左上 |
| 2 | 右上角 | 窗口右上 |
| 3 | 左下角 | 窗口左下 |
| 4 | 右下角 | 窗口右下 |
| 5 | 下边中间 | 窗口底部中间 |
| 6 | 右上区域 | 窗口右上区域 |
| 7 | 右下区域 | 窗口右下区域 |
| 8 | 左下区域 | 窗口左下区域 |
| 9 | 上边中间 | 窗口顶部中间（循环） |
| 10 | 左边中间 | 窗口左侧中间（循环） |
| 11 | 右边中间 | 窗口右侧中间（循环） |
| 12 | 下边中间 | 窗口底部中间（循环） |
| 13 | 中心区域 | 窗口内部（双循环） |
| 14 | 左侧中间 | 窗口左侧 |
| 15 | 右侧中间 | 窗口右侧 |
| 16 | 底部中间 | 窗口底部 |
| 17 | 底部右下 | 窗口底部右下 |

### 6.3 已知的tile索引使用

根据代码分析：

```c
// sub_16C57 - 对话框等待输入
sub_1685C(..., FDOTHER_DAT__7, 18);  // 对话框背景帧18
sub_1685C(..., FDOTHER_DAT__7, 19);  // 对话框背景帧19
sub_1685C(..., FDOTHER_DAT__7, 13);  // 最终显示帧13

// sub_31C49 - 场景渲染
sub_1685C(..., FDOTHER_DAT__7, 526); // 边框tile

// sub_15F0E - 进度条/闪烁效果
sub_15F0E(FDOTHER_DAT__7, ..., 83-91); // 动画帧83-91
```

---

## 七、调用示例

### 7.1 sub_165AC - 对话框动画

```c
// 创建对话框图层，调用sub_168B6绘制边框
sub_168B6(655360, 320, 5, n2, 4, 2);   // 第1层
sub_168B6(655360, 320, 5, n2, 8, 3);   // 第2层
sub_168B6(655360, 320, 5, n2, 12, 4);  // 第3层
sub_168B6(655360, 320, 5, n2, 16, 5);  // 第4层
sub_168B6(655360, 320, 5, n2, 19, 5);  // 第5层
```

**参数**:
- a1 = 655360 (屏幕缓冲区)
- a2 = 320 (pitch)
- a5 = 4/8/12/16/19 (tile列数)
- a6 = 2/3/4/5 (tile行数)
- a10 = 5 (未知)

### 7.2 sub_17EEF - 对话框渲染

```c
sub_168B6(DATO_DAT, a2, v6, a4, a6, 320, 5, 7, 5, 5);
```

### 7.3 sub_1956B - 菜单渲染

```c
sub_168B6(v5, SHIDWORD(v5), a5, a4, dword_53C63, 320, 5, 112, 19, 5);
```

---

## 八、完整的tile渲染流程

```
sub_168B6 (窗口边框渲染)
  │
  ├─ 步骤1: 初始化参数
  │   ├─ v27 = a10 - 2
  │   ├─ v28 = 16 * a6
  │   └─ v29 = 3 * a6
  │
  ├─ 步骤2: 绘制4个角 (tile 1-4)
  │   ├─ 左上角 (tile 1)
  │   ├─ 右上角 (tile 2)
  │   ├─ 左下角 (tile 3)
  │   └─ 右下角 (tile 4)
  │
  ├─ 步骤3: 绘制4条边 (tile 5-8, 14-17)
  │   ├─ 下边 (tile 5)
  │   ├─ 右上 (tile 6)
  │   ├─ 右下 (tile 7)
  │   ├─ 左下 (tile 8)
  │   ├─ 左侧 (tile 14)
  │   ├─ 右侧 (tile 15)
  │   ├─ 底部 (tile 16)
  │   └─ 底部右下 (tile 17)
  │
  ├─ 步骤4: 循环绘制边缘 (tile 9-12)
  │   ├─ 上边中间 (tile 9, 循环)
  │   ├─ 左边中间 (tile 10, 循环)
  │   ├─ 右边中间 (tile 11, 循环)
  │   └─ 下边中间 (tile 12, 循环)
  │
  └─ 步骤5: 绘制中心区域 (tile 13, 双循环)
      └─ for k in 0..a10
          └─ for m in 0..a9
              └─ sub_1685C(..., tile 13)
```

---

## 九、数据格式总结

### 9.1 Tile数据格式

```
每个tile:
  [0-1]: WORD - 宽度 (像素)
  [2-3]: WORD - 高度 (像素)
  [4-N]: BYTE[N] - 像素数据 (N = 宽度 × 高度)
```

### 9.2 索引表格式

```
FDOTHER_DAT__7头部:
  [0-1]: WORD - 总宽度
  [2-3]: WORD - 总高度
  [4-5]: WORD - tile数量
  [6-9]: DWORD - tile 0 偏移
  [10-13]: DWORD - tile 1 偏移
  ...

tile数据指针计算:
  tile_ptr = FDOTHER_DAT__7 + *(DWORD *)(FDOTHER_DAT__7 + 4*tile_index + 6)
```

### 9.3 像素格式

- **格式**: 8位调色板索引
- **尺寸**: 可变（由tile头部定义）
- **布局**: 逐行存储，无压缩
- **渲染**: 直接复制到屏幕缓冲区，按pitch对齐

---

## 十、关键发现

### 10.1 Tile索引不是连续的

- `sub_168B6` 使用的tile索引：1-17（跳过某些索引）
- 对话框背景使用的tile索引：13, 18, 19
- 其他场景使用的tile索引：83-91, 526等

### 10.2 Tile尺寸可变

- 每个tile有自己的宽度和高度
- 通过tile头部的WORD字段读取
- 渲染时按实际尺寸复制

### 10.3 渲染机制

1. **sub_168B6**: 计算窗口布局，调用sub_1685C绘制每个tile
2. **sub_1685C**: 根据tile索引获取数据指针，调用sub_4ED0B
3. **sub_4ED0B**: 逐行复制像素数据到屏幕缓冲区

### 10.4 与FDOTHER索引4的区别

| 特征 | 索引4 (字体) | 索引7 (tile集) |
|------|-------------|---------------|
| 数据格式 | 固定32字节/字符 | 可变大小tile |
| 尺寸 | 16×16像素 | 可变 |
| 索引方式 | 线性 (32*N) | 偏移表 (DWORD数组) |
| 用途 | 文字渲染 | 对话框/窗口边框 |
| 位深度 | 1位 (位图) | 8位 (调色板索引) |

---

## 十一、实现建议

### 11.1 数据结构定义

```c
typedef struct {
    u16 width;      // tile宽度
    u16 height;     // tile高度
    u8* pixels;     // 像素数据
} fd2_tile_t;

typedef struct {
    u16 total_width;
    u16 total_height;
    u16 tile_count;
    u32* tile_offsets;  // tile偏移表
    fd2_tile_t* tiles;  // tile数组
} fd2_tileset_t;
```

### 11.2 Tile获取函数

```c
fd2_tile_t* fd2_tileset_get_tile(fd2_tileset_t* tileset, int index) {
    if (index < 0 || index >= tileset->tile_count) return NULL;
    
    u32 offset = tileset->tile_offsets[index];
    u8* data = tileset->data + offset;
    
    fd2_tile_t* tile = &tileset->tiles[index];
    tile->width = *(u16*)(data);
    tile->height = *(u16*)(data + 2);
    tile->pixels = data + 4;
    
    return tile;
}
```

### 11.3 Tile渲染函数

```c
void fd2_render_tile(u8* screen, int pitch, 
                     fd2_tile_t* tile, int dx, int dy) {
    for (int y = 0; y < tile->height; y++) {
        u8* src = tile->pixels + y * tile->width;
        u8* dst = screen + (dy + y) * pitch + dx;
        memcpy(dst, src, tile->width);
    }
}
```

---

## 分析日期

2026-05-23
