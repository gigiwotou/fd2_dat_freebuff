# sub_2D80D、sub_2FF01、sub_2EB9F 函数完整分析

> 基于 IDA Pro MCP 反编译代码 1:1 分析
> 分析日期: 2026-05-23
> 重点关注: FDOTHER_DAT__7 作为"动画配置数据"的使用方式

---

## 一、sub_2EB9F - FIGANI.DAT tile数据解压函数

### 1.1 函数基本信息

**地址**: 0x2EB9F  
**大小**: 小函数（20字节栈帧）  
**调用者**: 32个函数（包括 sub_2D80D, sub_2FF01 等）  
**被调用**: sub_3702F, sub_4E98D

### 1.2 函数签名

```c
char __fastcall sub_2EB9F(
    __int32 a1,     // 栈帧参数1
    int a2,         // 栈帧参数2
    int a3,         // 栈帧参数3
    int a4,         // 栈帧参数4
    int arg0,       // FIGANI.DAT数据指针
    int arg4,       // tile索引
    int arg8,       // 目标缓冲区
    int argC,       // pitch (320或640)
    int value)      // 调色板偏移 (-1表示不使用)
```

### 1.3 核心实现

```c
char __fastcall sub_2EB9F(__int32 a1, int a2, int a3, int a4, 
                          int arg0, int arg4, int arg8, int argC, int value)
{
  unsigned __int16 *v9;

  sub_3702F(a1, a2, a3, a4, 32);  // 栈帧初始化
  
  // 计算tile数据指针：arg0 + *(DWORD *)(arg0 + 4*arg4 + 8)
  v9 = (unsigned __int16 *)(*(_DWORD *)(arg0 + 4 * arg4 + 8) + arg0);
  
  // 调用 sub_4E98D 解压tile数据
  // 参数: (tile_data+9, tile_width, tile_height, dst, pitch, value)
  return sub_4E98D((__int16 *)((char *)v9 + 9), *v9, v9[1], arg8, argC, value);
}
```

### 1.4 FIGANI.DAT tile数据结构

```
FIGANI.DAT tile数据格式：

[头部]
  偏移 0-1: 未知 (WORD)
  偏移 2-3: tile数量 (WORD)
  偏移 4-7: 未知 (DWORD)
  偏移 8+:  tile偏移表 (DWORD数组)

[Tile偏移表]
  tile 0: 偏移 8-11 (DWORD)
  tile 1: 偏移 12-15 (DWORD)
  ...
  tile N: 偏移 8 + 4*N

[Tile数据]
  每个tile:
    偏移 0-1: tile宽度 (WORD)
    偏移 2-3: tile高度 (WORD)
    偏移 4-7: 未知 (DWORD)
    偏移 8+:  RLE压缩的像素数据
```

### 1.5 关键公式

```
tile数据指针 = arg0 + *(DWORD *)(arg0 + 4*tile_index + 8)
解压调用 = sub_4E98D(tile_data+9, width, height, dst, pitch, value)
```

### 1.6 功能总结

sub_2EB9F 是一个**tile数据解压函数**：
1. 从 FIGANI.DAT 数据中根据索引获取tile偏移
2. 计算tile数据指针
3. 调用 sub_4E98D 将RLE压缩的tile数据解压到目标缓冲区
4. 支持调色板偏移参数

---

## 二、FDOTHER_DAT__7 - 动画配置数据结构

### 2.1 加载方式

在 **sub_2D80D** 中加载：
```c
// 行 88-96
FDOTHER_DAT__7 = 0;
FDOTHER_DAT__7 = (int)sub_111BA(
                        *((unsigned __int8 *)v40 + n28),  // 资源索引
                        v12,
                        (int)_FIGANI.DAT__2,
                        n2_1,
                        (int)aFdotherDat,
                        0,
                        *((unsigned __int8 *)v40 + n28));  // "FDOTHER.DAT"
```

在 **sub_2FF01** 中加载：
```c
// 行 188-196
FDOTHER_DAT__7 = 0;
FDOTHER_DAT__7 = (int)sub_111BA(
                        (unsigned __int8)v73[n28],  // v73="RRSTUVWXYZ"
                        v21,
                        _FIGANI.DAT__1,
                        0,
                        (int)aFdotherDat,
                        0,
                        (unsigned __int8)v73[n28]);  // "FDOTHER.DAT"
```

### 2.2 数据结构定义

根据 [FDOTHER索引7_tile数据结构分析.md](file:///d:/workspace/fd2_dat_freebuff/docs/FDOTHER索引7_tile数据结构分析.md)：

```
FDOTHER.DAT 索引7（动画配置数据/tile集）结构：

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

### 2.3 C语言数据结构

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
    u8* data;           // 原始数据
} fd2_tileset_t;
```

### 2.4 Tile索引映射表

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
| 18-19 | 对话框动画帧 | 对话框等待输入 |
| 83-91 | 进度条动画帧 | 进度条/闪烁效果 |
| 526 | 边框tile | 场景渲染 |

### 2.5 Tile数据指针计算公式

```c
// 从 FDOTHER_DAT__7 获取指定tile的数据指针
tile_data_ptr = FDOTHER_DAT__7 + *(DWORD *)(FDOTHER_DAT__7 + 4*tile_index + 6)

// 读取tile尺寸
width = *(WORD *)(tile_data_ptr)
height = *(WORD *)(tile_data_ptr + 2)

// 像素数据
pixels = tile_data_ptr + 4
```

---

## 三、sub_2D80D - UI界面渲染主函数

### 3.1 函数基本信息

**地址**: 0x2D80D  
**调用者**: sub_2FF01  
**被调用**: 33个函数

### 3.2 函数签名

```c
void __fastcall sub_2D80D(
    __int32 a1,           // 栈帧参数1
    int a2,               // 栈帧参数2
    int a3,               // 栈帧参数3
    int n2_1,             // 栈帧参数4
    int n6,               // 地图行索引
    int n28,              // UI类型 (32-35)
    int n30,              // 参数1
    unsigned __int8 *a8)  // 参数2
```

### 3.3 核心流程

#### 3.3.1 资源加载阶段（行 59-96）

```c
// 1. 获取场景数据
v8 = (unsigned __int8 *)(80 * n6 + n8_0);
sub_12E38(*v8, n6, a3, n2_1, *v8, v8[1], (int)&v42);

// 2. 加载TAI.DAT和BG.DAT
_TAI.DAT_ = sub_111BA(v43, n6, a3, n2_1, (int)aTaiDat, 0, v43);
_BG.DAT_ = sub_111BA((unsigned __int8)a3, n6, a3, n2_1, (int)aBgDat, 0, (unsigned __int8)a3);

// 3. 分配缓冲区
v9 = malloc(64000);      // 背景缓冲区
v11 = malloc(&loc_1F400); // 工作缓冲区

// 4. 渲染背景
sub_4E98D(_BG.DAT_, 0, 50, v9, 320, -1);
sub_2FACD(v9, n6);
sub_1F882(v10, SHIDWORD(v10), a3, n2_1);

// 5. 加载FIGANI.DAT资源
v12 = v8[7];
v13 = 3 * v12;
_FIGANI.DAT_ = sub_111BA(v10, v12, v13, n2_1, (int)aFiganiDat, 0, v13);
_FIGANI.DAT__2 = sub_111BA((__int32)_FIGANI.DAT_, v12, v13 + 1, n2_1, (int)aFiganiDat, 0, v13 + 1);

// 6. 加载FDOTHER.DAT资源
_FDOTHER.DAT_ = sub_111BA(n28 + 33, v12, (int)_FIGANI.DAT__2, n2_1, (int)aFdotherDat, 0, n28 + 33);

// 7. 加载FDOTHER_DAT__7（动画配置数据）
FDOTHER_DAT__7 = (int)sub_111BA(
                        *((unsigned __int8 *)v40 + n28),  // 根据UI类型选择索引
                        v12,
                        (int)_FIGANI.DAT__2,
                        n2_1,
                        (int)aFdotherDat,
                        0,
                        *((unsigned __int8 *)v40 + n28));
```

#### 3.3.2 FIGANI.DAT tile解压阶段（行 112-125）

```c
// 解压FIGANI.DAT tile数据（8次循环）
v16 = sub_17AA9(v10, v12, (int)_FIGANI.DAT__2, n2_1, 6);
for ( n8 = 0; n8 < 8; ++n8 )
{
  sub_11EB0(v16, v12, n8, n2_1, v11, 640, v9, 320, 320, 200);
  LOBYTE(v18) = sub_2EB9F((int)_FIGANI.DAT__1, 0, v11 + 20 * n8, 640, -1);
  v19 = sub_11EB0(v18, v12, n8, n2_1, 655360, 320, v11, 640, 320, 200);
  v16 = sub_17AA9(v19, v12, n8, n2_1, 1);
}

// 反向解压FIGANI.DAT tile数据（9次循环）
for ( n8_1 = 8; n8_1 >= 0; --n8_1 )
{
  sub_11EB0(v16, v12, n8_1, n2_1, v11, 640, v9, 320, 320, 200);
  LOBYTE(v21) = sub_2EB9F((int)_FDOTHER.DAT_, 0, v11 + 30 * n8_1, 640, -1);
  v22 = sub_11EB0(v21, v12, n8_1, n2_1, 655360, 320, v11, 640, 320, 200);
  v16 = sub_17AA9(v22, v12, n8_1, n2_1, 1);
}
```

#### 3.3.3 FDOTHER_DAT__7 使用阶段（行 128-152）

```c
// 循环解压FDOTHER.DAT资源，并使用FDOTHER_DAT__7进行动画配置
for ( n2 = 1; n2 < (unsigned __int8)*_FDOTHER.DAT_; ++n2 )
{
  v24 = memmove(v11, v9, 64000);
  LOBYTE(v24) = sub_2EB9F((int)_FDOTHER.DAT_, n2, v11, 320, -1);
  LODWORD(v24) = sub_11EB0(v24, SHIDWORD(v24), n2, n2_1, 655360, 320, v11, 320, 320, 200);
  
  // 根据UI类型和循环次数，使用FDOTHER_DAT__7进行特殊处理
  if ( n28 == 34 && n2 == 2 )
    goto LABEL_18;
  if ( n28 == 35 && n2 == 1 )
  {
    LABEL_13:
    LODWORD(v24) = sub_25B45(v24, SHIDWORD(v24), n2, n2_1, FDOTHER_DAT__7, 2, n2);
    goto LABEL_14;
  }
  if ( n28 == 33 && n2 == 6 )
  {
    LABEL_18:
    LODWORD(v24) = sub_25A96(v24, SHIDWORD(v24), n2, n2_1, FDOTHER_DAT__7, 1, 1);
  }
  else if ( n28 == 32 && n2 == 1 )
  {
    goto LABEL_13;
  }
  LABEL_14:
  sub_17AA9(v24, SHIDWORD(v24), n2, n2_1, 2);
}
```

#### 3.3.4 特殊UI类型处理（行 153-181）

```c
v54 = n28 - 32;
if ( n28 == 32 || n28 == 35 )
{
  for ( n10 = 0; n10 <= 10; ++n10 )
  {
    n2_1 = 2;
    if ( !(n10 % 2) )
      sub_25A96(n10 / 2, 0, n10, 2, FDOTHER_DAT__7, 1, 1);  // 使用FDOTHER_DAT__7
    
    memmove(v11, v9, 64000);
    v41 = -1;
    v40[1] = 320;
    v40[0] = v11;
    v26 = (unsigned __int8)*_FDOTHER.DAT_ - 2;
    LOBYTE(v27) = sub_2EB9F((int)_FDOTHER.DAT_, v26 + (n10 & 1), v11, 320, -1);
    v28 = sub_11EB0(v27, v26, n10, 2, 655360, 320, v11, 320, 320, 200);
    sub_17AA9(v28, v26, n10, 2, 2);
    
    // 使用预定义字符串进行动画效果
    sub_2DF01(
      4 * n10,
      40 - 4 * n10,
      n10,
      2,
      0,
      255,
      40 - 4 * n10,
      *((_BYTE *)v46 + v54),      // 从 "?355[\\]^" 中取字符
      *((_BYTE *)&v46[-1] + v54), // 从 "?355[\\]^" 中取字符
      *((_BYTE *)&v44 + v54));    // 从全局变量中取字符
  }
}
```

#### 3.3.5 最终UI分支处理（行 229-256）

```c
switch ( n28 )
{
  case 32:  // ' '
    sub_2111A((__int32)v35, n50, n2_1, n40, v9, (int)_FDOTHER.DAT_, n6, n30, a8, 32);
    break;
  case 33:  // '!'
    for ( n40 = 0; n40 < n30; ++n40 )
    {
      n50 = 80 * a8[n40];
      v35 = (_BYTE *)memset(n50 + n8_0 + 37, 0, 3);
    }
    sub_211A4((__int32)v35, n50, n40, n2_1, n6, n30, a8, 950);
    break;
  case 34:  // '"'
    sub_22721((__int32)v35, n50, n40, n2_1, n6, n30, a8);
    dword_53EC4 = 0;
    sub_22866(v36, n50, n40, n2_1, n6, n30, a8);
    dword_53EC4 = 0;
    sub_22997(v37, n50, n40, n2_1, n6, n30, a8);
    break;
  case 35:  // '#'
    sub_22D1B((__int32)v35, n50, n40, n2_1, n6, 26, n30, (int)a8, 37);
    dword_53EC4 = 0;
    sub_22D1B(v38, n50, n40, n2_1, n6, 22, n30, (int)a8, 39);
    dword_53EC4 = 0;
    sub_22D1B(v39, n50, n40, n2_1, n6, 27, n30, (int)a8, 38);
    break;
}
```

### 3.4 FDOTHER_DAT__7 使用总结

在 sub_2D80D 中，FDOTHER_DAT__7 作为**动画配置数据**被以下函数使用：

| 行号 | 函数 | 用途 |
|------|------|------|
| 138 | sub_25B45 | UI类型35，循环索引1时 |
| 144 | sub_25A96 | UI类型33，循环索引6时 |
| 160 | sub_25A96 | UI类型32/35，偶数循环时 |
| 225 | sub_25A96 | 最终清理时 |

---

## 四、sub_2FF01 - 复杂UI渲染主函数

### 4.1 函数基本信息

**地址**: 0x2FF01  
**调用者**: sub_15311, sub_1CFF0  
**被调用**: 38个函数

### 4.2 函数签名

```c
void __fastcall sub_2FF01(
    __int32 a1,           // 栈帧参数1
    int a2,               // 栈帧参数2
    int n6,               // 参数1
    int a4,               // 栈帧参数4
    int n6a,              // 地图行索引
    int n28,              // UI类型 (0-31)
    int n30,              // 参数1
    unsigned __int8 *n2)  // 参数2
```

### 4.3 核心流程

#### 4.3.1 UI类型分支（行 133-539）

```c
if ( n28 < 32 )
{
  if ( n28 == 24 || n28 > 27 )
  {
    // 调用 sub_2CF30 处理其他UI类型
    sub_2CF30(v8, a2, n6, 0, n6a, n28, n30, n2);
  }
  else
  {
    // 处理 n28 = 25, 26, 27 的UI类型
    // ... 复杂逻辑
  }
}
else
{
  // n28 >= 32: 调用 sub_2D80D
  sub_2D80D(v8, a2, n6, 0, n6a, n28, n30, n2);
}
```

#### 4.3.2 资源加载阶段（行 155-227）

```c
// 1. 初始化v73字符串 "RRSTUVWXYZ"（用于根据UI类型选择FDOTHER资源索引）
qmemcpy(v73, "RRSTUVWXYZ", 10);

// 2. 获取场景数据
_FIGANI.DAT__5 = (unsigned __int8 *)(80 * n6a + n8_0);

// 3. 加载BG.DAT和TAI.DAT
_BG.DAT_ = sub_111BA(v14, v16, v13, 0, (int)aBgDat, (int)_BG.DAT__1, v15);
_TAI.DAT_ = sub_111BA((__int32)_BG.DAT_, v16, v13, 0, (int)aTaiDat, (int)_TAI.DAT_, v13);

// 4. 分配缓冲区
v18 = malloc(64000);
arg8_4 = malloc(&loc_2A300);

// 5. 加载FIGANI.DAT资源
_FIGANI.DAT_ = sub_111BA(v80, v21, v18, 0, (int)aFiganiDat, (int)_FIGANI.DAT_, 3 * v21);
_FIGANI.DAT__1 = (int)sub_111BA(v22 + 2, v21, v18, 0, (int)aFiganiDat, (int)n3, v22 + 2);

// 6. 加载FDOTHER_DAT__7（使用v73字符串索引）
FDOTHER_DAT__7 = (int)sub_111BA(
                        (unsigned __int8)v73[n28],  // "RRSTUVWXYZ"[n28]
                        v21,
                        _FIGANI.DAT__1,
                        0,
                        (int)aFdotherDat,
                        0,
                        (unsigned __int8)v73[n28]);
```

#### 4.3.3 FIGANI.DAT tile解压循环（行 241-261）

```c
if ( n28 == 9 )
{
  for ( n10 = 0; n10 <= 10; ++n10 )
  {
    v31 = sub_11EB0(v28, v21, arg8_3 + 320, 0, arg8_3 + 320, 640, v97, 320, 320, 200);
    if ( n10 != 10 )
      LOBYTE(v31) = sub_2EB9F(
                      10 * n10,
                      v21,
                      arg8_3 + 320 - 10 * n10,
                      0,
                      (int)_FIGANI.DAT_,
                      0,
                      arg8_3 + 320 - 10 * n10,
                      640,
                      -1);
    _FIGANI.DAT__1 = arg8_3 + 320;
    LOBYTE(v30) = sub_2EB9F(v31, v21, arg8_3 + 320, 0, (int)v68[0], 0, arg8_3 + 320, 640, -1);
    v28 = sub_11EB0(v30, v21, arg8_3 + 320, 0, 655360, 320, arg8_3 + 320, 640, 320, 200);
  }
  j___delay(500);
}
```

#### 4.3.4 函数指针数组调用（行 264-471）

```c
// 调用 funcs_30469[n28] 函数指针数组
((void (__fastcall *)(__int32, int, int, int, int, int, int, int, unsigned __int8))funcs_30469[n28])(
  n28,
  v21,
  _FIGANI.DAT__1,
  0,
  n6a,
  _FDOTHER.DAT_,
  arg8_3,
  320,
  0);

// 循环调用，包含sub_2EB9F解压tile
for ( i = 0; i < v89; ++i )
{
  // ...
  if ( n28 != 9 )
    sub_2EB9F(v38, v21, arg8, 0, (int)n3, arg4, arg8, 640, -1);
  // ...
}
```

#### 4.3.5 清理和FDOTHER_DAT__7使用（行 511-537）

```c
// 使用FDOTHER_DAT__7进行最终渲染
sub_25A96(v64, _FDOTHER.DAT__1, _FIGANI.DAT__1, v9, FDOTHER_DAT__7, -1, 1);
free(FDOTHER_DAT__7);

// 清理资源
free(_FDOTHER.DAT_);
for ( n30_4 = 0; n30_4 < n30; ++n30_4 )
  free(v68[n30_4]);
free(v97);
free(arg8_3);
free(_FIGANI.DAT_);
free(n3);
free(_BG.DAT__1);
free(_TAI.DAT_);

// 重新加载FDSHAP.DAT
n655360 = malloc(153216);
n655360_0 = n655360;
::n7 = (int)sub_111BA(
              n655360,
              SHIDWORD(n655360),
              _FIGANI.DAT__1,
              v9,
              (int)aFdshapDat,
              ::n7,
              2 * *(unsigned __int8 *)dword_53A55);
```

### 4.4 FDOTHER_DAT__7 使用总结

在 sub_2FF01 中，FDOTHER_DAT__7 的加载和使用：

| 行号 | 操作 | 说明 |
|------|------|------|
| 188-196 | 加载 | 使用 `v73[n28]` 即 `"RRSTUVWXYZ"[n28]` 作为FDOTHER资源索引 |
| 511 | 使用 | 调用 sub_25A96 进行最终渲染 |
| 512 | 释放 | free(FDOTHER_DAT__7) |

---

## 五、完整调用关系图

```
sub_2FF01 (0x2FF01)
  │
  ├─ n28 >= 32: 调用 sub_2D80D
  │     │
  │     ├─ 加载FDOTHER_DAT__7 (索引根据n28选择)
  │     ├─ sub_2EB9F: 解压FIGANI.DAT tile数据
  │     ├─ sub_25A96/sub_25B45: 使用FDOTHER_DAT__7
  │     └─ switch(n28): 调用不同UI处理函数
  │
  └─ n28 < 32: 直接处理
        │
        ├─ 加载FDOTHER_DAT__7 (使用"RRSTUVWXYZ"[n28])
        ├─ sub_2EB9F: 解压FIGANI.DAT tile数据
        ├─ funcs_30469[n28]: 函数指针数组调用
        └─ sub_25A96: 使用FDOTHER_DAT__7

sub_2EB9F (0x2EB9F)
  │
  ├─ 从FIGANI.DAT获取tile偏移
  ├─ 计算tile数据指针
  └─ sub_4E98D: RLE解压tile数据到目标缓冲区
```

---

## 六、关键数据结构总结

### 6.1 FIGANI.DAT tile数据结构

```
[头部 8字节]
  0-1: WORD - 未知
  2-3: WORD - tile数量
  4-7: DWORD - 未知

[Tile偏移表]
  8-11: DWORD - tile 0偏移
  12-15: DWORD - tile 1偏移
  ...

[Tile数据]
  每个tile:
    0-1: WORD - 宽度
    2-3: WORD - 高度
    4-7: DWORD - 未知
    8+: RLE压缩像素数据
```

### 6.2 FDOTHER_DAT__7 动画配置数据结构

```
[头部 6字节]
  0-1: WORD - 总宽度
  2-3: WORD - 总高度
  4-5: WORD - tile数量

[Tile偏移表]
  6-9: DWORD - tile 0偏移
  10-13: DWORD - tile 1偏移
  ...

[Tile数据]
  每个tile:
    0-1: WORD - 宽度
    2-3: WORD - 高度
    4+: 像素数据（未压缩，8位调色板索引）
```

### 6.3 FDOTHER资源索引映射

```
UI类型(n28) → FDOTHER资源索引:
  32 → v40[n28] (来自sub_2D80D)
  33 → v40[n28]
  34 → v40[n28]
  35 → v40[n28]
  0-9  → "RRSTUVWXYZ"[n28] (来自sub_2FF01)
```

---

## 七、实现建议

### 7.1 数据结构定义

```c
// FIGANI.DAT tile头
typedef struct {
    u16 unknown;
    u16 tile_count;
    u32 unknown2;
    u32 tile_offsets[];  // 可变长度数组
} figani_header_t;

// FIGANI.DAT tile数据
typedef struct {
    u16 width;
    u16 height;
    u32 unknown;
    u8 rle_data[];  // RLE压缩数据
} figani_tile_t;

// FDOTHER.DAT 索引7 tile集
typedef struct {
    u16 total_width;
    u16 total_height;
    u16 tile_count;
    u32 tile_offsets[];  // 可变长度数组
} fdother_tileset_header_t;

// FDOTHER.DAT 索引7 tile数据
typedef struct {
    u16 width;
    u16 height;
    u8 pixels[];  // 未压缩像素数据
} fdother_tile_t;
```

### 7.2 核心函数实现

```c
// sub_2EB9F: 从FIGANI.DAT解压tile数据
char sub_2EB9F(int figani_data, int tile_index, int dst, int pitch, int palette_offset) {
    // 计算tile数据指针
    u16* tile_ptr = (u16*)(figani_data + *(u32*)(figani_data + 4*tile_index + 8));
    
    // 读取tile尺寸
    u16 width = tile_ptr[0];
    u16 height = tile_ptr[1];
    
    // 调用RLE解压函数
    return sub_4E98D((u16*)((u8*)tile_ptr + 9), width, height, dst, pitch, palette_offset);
}

// 获取FDOTHER_DAT__7中的tile数据
u8* get_fdother_tile(int fdother_data, int tile_index, u16* out_width, u16* out_height) {
    // 计算tile数据指针
    u32 offset = *(u32*)(fdother_data + 4*tile_index + 6);
    u8* tile_data = fdother_data + offset;
    
    // 读取尺寸
    *out_width = *(u16*)(tile_data);
    *out_height = *(u16*)(tile_data + 2);
    
    // 返回像素数据
    return tile_data + 4;
}
```

---

## 八、分析总结

### 8.1 sub_2EB9F 功能

- **核心功能**: 从 FIGANI.DAT 中根据索引解压tile数据
- **数据格式**: RLE压缩的tile数据
- **调用频率**: 极高（32个函数调用）
- **关键公式**: `tile_ptr = arg0 + *(DWORD *)(arg0 + 4*arg4 + 8)`

### 8.2 FDOTHER_DAT__7 功能

- **核心功能**: 存储动画配置数据/tile集
- **数据格式**: 未压缩的tile数据（8位调色板索引）
- **tile数量**: 526+个tile
- **主要用途**: 
  - 对话框边框渲染（tile 1-17）
  - 对话框动画帧（tile 18-19）
  - 进度条动画（tile 83-91）
  - 场景边框（tile 526）

### 8.3 sub_2D80D 和 sub_2FF01 关系

- **sub_2FF01**: 处理 UI类型 0-31
- **sub_2D80D**: 处理 UI类型 32-35
- **共同点**: 
  - 都加载FDOTHER_DAT__7
  - 都调用sub_2EB9F解压tile
  - 都使用sub_25A96进行最终渲染
- **差异**:
  - sub_2FF01 使用函数指针数组 `funcs_30469`
  - sub_2D80D 使用 switch 分支

---

*分析完成时间: 2026-05-23*  
*分析工具: IDA Pro MCP Server + 项目文档*  
*参考文档:*  
- `docs/FDOTHER索引7_tile数据结构分析.md`  
- `tools/analyze_fdother_index7.py`  
- `tools/export-for-ai/decompile/2D80D.c`  
- `tools/export-for-ai/decompile/2FF01.c`  
- `tools/export-for-ai/decompile/2EB9F.c`
