# FD2游戏UI界面绘制逻辑完整分析

> 基于 IDA Pro MCP 反编译代码 1:1 分析
> 分析日期: 2026-05-23
> 源文件: FD2.EXE

---

## 一、核心函数调用关系

```
sub_168B6 (0x168B6) - 窗口边框/Tile渲染主函数
  ├─ 调用者: sub_165AC, sub_17EEF, sub_1956B, sub_31C49
  └─ 内部调用:
      ├─ sub_3702F (初始化)
      └─ sub_1685C (绘制单个tile)
          └─ sub_4ED0B (实际的tile数据复制)

sub_165AC (0x165AC) - 对话框动画/菜单创建
  ├─ 调用者: sub_15F84 (文字渲染系统)
  └─ 内部调用: sub_168B6 (绘制对话框边框)

sub_17EEF (0x17EEF) - 对话框渲染
  ├─ 调用者: sub_17E0B, sub_1BFFE, sub_1CFF0
  └─ 内部调用: sub_168B6, sub_111BA (资源加载)

sub_1956B (0x1956B) - 通用菜单渲染 (最核心的UI函数)
  ├─ 调用者: 25+个函数 (包括sub_10010, sub_16F55, sub_19DF7等)
  └─ 内部调用: sub_168B6, sub_111BA (资源加载)

sub_31C49 (0x31C49) - 战场菜单渲染
  ├─ 调用者: sub_31529
  └─ 内部调用: sub_168B6, sub_15F84 (文字渲染)

sub_15F84 (0x15F84) - 文字/文本渲染系统
  ├─ 调用者: 100+个函数 (几乎所有场景)
  └─ 内部调用: sub_165AC (对话框创建), sub_4ED7A (字符绘制)

sub_135DD (0x135DD) - 场景切换/地图滚动
  ├─ 调用者: 50+个函数 (场景相关)
  └─ 功能: 平滑过渡到目标场景坐标
```

---

## 二、sub_168B6 窗口绘制函数详解

### 2.1 函数签名

**地址**: 0x168B6

```c
void __fastcall sub_168B6(
    __int32 a1,   // 数据源指针（DATO_DAT或其他）
    int a2,       // 屏幕行距 (pitch) = 320
    int a3,       // 未知参数
    int a4,       // 未知参数
    int a5,       // tile列数
    int a6,       // tile高度
    int a7,       // FDOTHER_DAT__7 指针
    int a8,       // 通常为112或7
    int a9,       // tile行数
    int a10)      // 通常为5
```

### 2.2 核心实现逻辑

```c
void __fastcall sub_168B6(...)
{
  sub_3702F(a1, a2, a3, a4, 68);
  v27 = a10 - 2;                   // v27 = 5 - 2 = 3
  v28 = 16 * a6;                   // v28 = 16 * tile_height
  v29 = 3 * a6;                    // v29 = 3 * tile_height
  v10 = a5 + a6 * a8;              // v10 = tile_cols + tile_height * 112(or 7)
  v11 = v10 + a7;                  // v11 = base_offset
  
  // === 绘制4个角 (tile 1-4) ===
  sub_1685C(v10, a2, a3, a4, v10 + a7, a6, dword_53A81, 1);   // 左上角
  v12 = 16 * a9 + v11 + 3;
  sub_1685C(16 * a9, v12, a3, a4, v12, a6, dword_53A81, 2);   // 右上角
  v13 = a10 * v28;
  sub_1685C(v11 + v29 + a10 * v28, v12, a10 * v28, a4, v11 + v29 + a10 * v28, a6, dword_53A81, 3); // 左下角
  v14 = sub_1685C(v13 + v29 + v12, v12, v13, a4, v13 + v29 + v12, a6, dword_53A81, 4); // 右下角
  
  // === 绘制4条边 (tile 5-8, 14-17) ===
  sub_1685C(v14, v12, a10 * 16 * a6, a4, v11 + 3, a6, dword_53A81, 5);  // 下边中间
  v15 = v11 + 19 + 16 * (a9 - 2);
  sub_1685C(v11 + 19, v15, a10 * 16 * a6, a4, v15, a6, dword_53A81, 6);  // 右上区域
  sub_1685C(v13 + v29 + v11 + 3, v15, v13, a4, v13 + v29 + v11 + 3, a6, dword_53A81, 7); // 右下区域
  v16 = sub_1685C(v13 + v29 + v15, v15, v13, a4, v13 + v29 + v15, a6, dword_53A81, 8); // 左下区域
  v17 = sub_1685C(v16, v15, a10 * 16 * a6, a4, v11 + 3 * a6, a6, dword_53A81, 14); // 左侧中间
  v18 = 16 * (a9 - 2) + v11 + 3 * a6 + 35;
  sub_1685C(v17, v15, v18, a4, v18, a6, dword_53A81, 15); // 右侧中间
  v19 = (a10 - 1) * 16 * a6;
  v20 = sub_1685C(a10 - 1, v19, v18, a4, v19 + v11 + 3 * a6, a6, dword_53A81, 16); // 底部中间
  sub_1685C(v20, v19, v19 + v18, a4, v19 + v18, a6, dword_53A81, 17); // 底部右下
  
  // === 循环绘制边缘 (tile 9-12) ===
  if ( a9 - 2 > 0 )
  {
    for ( i = 0; i < a9 - 2; ++i )
    {
      sub_1685C(16 * i, v19, i, a4, 16 * i + v11 + 19, a6, dword_53A81, 9);  // 上边中间
      sub_1685C(a10 * v28, v19, i, a4, v29 + a10 * v28 + 16 * i + v11 + 19, a6, dword_53A81, 12); // 下边中间
    }
  }
  if ( v27 > 0 )
  {
    for ( j = 0; j < v27; j = v23 )
    {
      v23 = j + 1;
      v24 = v11 + v29 + (j + 1) * v28;
      sub_1685C(v11 + v29, v19, v24, a4, v24, a6, dword_53A81, 10);  // 左边中间
      sub_1685C(v24 + 16 * a9 + 3, v19, v24, a4, v24 + 16 * a9 + 3, a6, dword_53A81, 11); // 右边中间
    }
  }
  
  // === 绘制中心区域 (tile 13, 双循环) ===
  for ( k = 0; k < a10; ++k )
  {
    for ( m = 0; m < a9; ++m )
      sub_1685C(16 * m + v11 + v29 + 3 + k * v28, 16 * m + v11 + v29 + 3, m, a4, 16 * m + v11 + v29 + 3 + k * v28, a6, dword_53A81, 13);
  }
}
```

### 2.3 Tile索引映射表

| Tile索引 | 用途 | 位置 |
|----------|------|------|
| 1 | 左上角 | 窗口左上 |
| 2 | 右上角 | 窗口右上 |
| 3 | 左下角 | 窗口左下 |
| 4 | 右下角 | 窗口右下 |
| 5 | 下边中间 | 窗口底部 |
| 6 | 右上区域 | 窗口右上 |
| 7 | 右下区域 | 窗口右下 |
| 8 | 左下区域 | 窗口左下 |
| 9 | 上边中间 (循环) | 窗口顶部 |
| 10 | 左边中间 (循环) | 窗口左侧 |
| 11 | 右边中间 (循环) | 窗口右侧 |
| 12 | 下边中间 (循环) | 窗口底部 |
| 13 | 中心区域 (双循环) | 窗口内部 |
| 14 | 左侧中间 | 窗口左侧 |
| 15 | 右侧中间 | 窗口右侧 |
| 16 | 底部中间 | 窗口底部 |
| 17 | 底部右下 | 窗口底部右下 |

### 2.4 调用示例

```c
// sub_165AC - 对话框动画 (5层渐显)
sub_168B6(655360, 320, 5, n2, 4, 2);   // 第1层: 4列2行
sub_168B6(655360, 320, 5, n2, 8, 3);   // 第2层: 8列3行
sub_168B6(655360, 320, 5, n2, 12, 4);  // 第3层: 12列4行
sub_168B6(655360, 320, 5, n2, 16, 5);  // 第4层: 16列5行
sub_168B6(655360, 320, 5, n2, 19, 5);  // 第5层: 19列5行

// sub_17EEF - 对话框渲染
sub_168B6(DATO_DAT, a2, v6, a4, a6, 320, 5, 7, 5, 5);

// sub_1956B - 通用菜单
sub_168B6(v5, SHIDWORD(v5), a5, a4, dword_53C63, 320, 5, 112, 19, 5);

// sub_31C49 - 战场菜单
sub_168B6(DATO_DAT, SHIDWORD(v11), (int)arg0, a3, v23, 320, 5, 7, 5, 5);
```

---

## 三、sub_165AC 对话框动画函数

### 3.1 函数签名

**地址**: 0x165AC

```c
int *__fastcall sub_165AC(__int32 a1, int a2, int a3, int a4, int a5, int a6, int n2)
```

### 3.2 功能说明

- 创建对话框动画效果（5层渐显）
- 根据 `n1832` 值确定对话框类型
- 分配5个26668字节缓冲区用于动画帧
- 每层之间延迟10ms

### 3.3 核心实现

```c
int *__fastcall sub_165AC(..., int n2)
{
  v7 = sub_3702F(a1, a2, a3, a4, 40);
  
  // 根据n2值决定是否显示动画
  if ( n2 )
  {
    // 动画模式
    n6_5 = 0;
    sub_12CEA(v7, a2, a3, a4, a5, a6);
    n6_5 = 1;
    v18 = 24 * n10 + 4;
    v19 = 24 * n2_1 + 4;
    v8 = n2_1 + n10;
    if ( n2_1 + n10 )
    {
      for ( i = 0; i <= v8; ++i )
      {
        v10 = v18 - i * (v18 - 5) / v8;
        v11 = v19 - i * (v19 - n2) / v8;
        v12 = dword_53A81;
        sub_15E9E(dword_53A81 + *(__int16 *)(dword_53A81 + 6), ..., v10, v11, ..., 655360, 320, v10, v11);
        j___delay(10);
        LOWORD(v14) = sub_4E381();
        sub_15E71(v14, v12, v10, v11, dword_53A18[0], 655360, 320);
      }
    }
  }
  else if ( n1832 == 1832 )
  {
    n2 = 2;      // 小对话框
  }
  else if ( n1832 == 36887 )
  {
    n2 = 112;    // 大对话框
  }
  
  // 分配5个动画帧缓冲区
  for ( n5 = 0; n5 < 5; ++n5 )
    dword_53A18[n5] = malloc(26668);
  
  v16 = 320 * n2 + 5;
  
  // 5层渐显动画
  sub_4ECBF(dword_53A18[0], 310, 86, 655360, v16);
  sub_168B6(655360, 320, 5, n2, 4, 2);   // 第1层
  j___delay(10);
  
  sub_4ECBF(dword_53A1C, 310, 86, 655360, v16);
  sub_168B6(655360, 320, 5, n2, 8, 3);   // 第2层
  j___delay(10);
  
  sub_4ECBF(dword_53A20, 310, 86, 655360, v16);
  sub_168B6(655360, 320, 5, n2, 12, 4);  // 第3层
  j___delay(10);
  
  sub_4ECBF(dword_53A24, 310, 86, 655360, v16);
  sub_168B6(655360, 320, 5, n2, 16, 5);  // 第4层
  j___delay(10);
  
  sub_4ECBF(dword_53A28, 310, 86, 655360, v16);
  sub_168B6(655360, 320, 5, n2, 19, 5);  // 第5层
  
  sub_4E381();
  return dword_53A18;
}
```

### 3.4 对话框类型

| n1832值 | 类型 | 高度 |
|---------|------|------|
| 1832 | 小对话框 | 2 |
| 36887 | 大对话框 | 112 |

---

## 四、sub_1956B 通用菜单渲染函数

### 4.1 函数签名

**地址**: 0x1956B

```c
int __fastcall sub_1956B(__int32 a1, int a2, int a3, int a4, int a5)
```

### 4.2 菜单类型映射

```c
switch ( a5 )
{
  case 128: n1832 = 4283; break;   // 菜单类型1
  case 129: n1832 = 1707; break;   // 菜单类型2
  case 130: n1832 = 3939; break;   // 菜单类型3
  case 131: n1832 = 1398; break;   // 菜单类型4
  case 132: n1832 = 3644; break;   // 菜单类型5
  default:  n1832 = 36887; break;  // 默认/大对话框
}
```

### 4.3 核心实现

```c
int __fastcall sub_1956B(..., int a5)
{
  sub_3702F(a1, a2, a3, a4, 32);
  
  // 分配3个64000字节缓冲区
  dword_53C5B = malloc(64000);
  dword_53C5F = malloc(64000);
  v5 = malloc(64000);
  dword_53C63 = v5;
  
  // 备份当前屏幕
  memmove(dword_53C5F, 655360, 64000);
  LODWORD(v5) = memmove(dword_53C63, dword_53C5F, 64000);
  
  // 绘制窗口边框 (112x19 tile)
  sub_168B6(v5, SHIDWORD(v5), a5, a4, dword_53C63, 320, 5, 112, 19, 5);
  
  // 根据a5设置对话框类型
  switch ( a5 )
  {
    case 128: n1832 = 4283; break;
    case 129: n1832 = 1707; break;
    case 130: n1832 = 3939; break;
    case 131: n1832 = 1398; break;
    case 132: n1832 = 3644; break;
    default:  n1832 = 36887; break;
  }
  
  // 加载DATO.DAT资源
  DATO_DAT = (int)sub_111BA(v5, SHIDWORD(v5), a5, a4, (int)aDatoDat, DATO_DAT, a5);
  
  // 渲染菜单内容
  result = sub_4EC31(n1832 + dword_53C63, *(unsigned __int8 *)DATO_DAT + DATO_DAT, 320);
  
  // 6次循环渲染菜单项
  for ( n5 = 5; n5 >= 0; --n5 )
    result = sub_1974C(13 * n5 + 112, dword_53C5B, dword_53C63);
  
  return result;
}
```

### 4.4 调用者列表 (25+个)

- sub_10010 (加载战场)
- sub_16F55
- sub_190AC
- sub_19DF7 (营地菜单)
- sub_1A866
- sub_1AA1D
- sub_1E292
- sub_26152
- sub_2670E
- sub_279BC
- sub_2872B
- sub_28CBD
- sub_28F65
- sub_29300
- sub_2968D (保存战场)
- sub_2986F
- sub_29DAA
- sub_2A43E
- sub_2AA00
- sub_2AC7D
- sub_2AF28
- sub_2B439
- sub_31BDF
- sub_35854
- sub_35A0D
- sub_35FCF

---

## 五、sub_15F84 文字渲染系统

### 5.1 函数签名

**地址**: 0x15F84

```c
void __usercall sub_15F84(
    unsigned __int8 *a1@<edi>,
    __int32 a2@<eax>,
    int a3@<edx>,
    int a4@<ecx>,
    int a5@<ebx>,
    int arg0,     // 文本文件索引
    int arg4,     // 文本子索引
    int n658255,  // 屏幕偏移
    int argC,     // pitch (320)
    int arg10,    // X坐标
    int arg14,    // Y坐标
    int arg18,    // 宽度相关
    int arg1C,    // 高度相关
    int arg20)    // 标志
```

### 5.2 控制码系统

| 控制码 | 功能 |
|--------|------|
| -1 | 结束文本，关闭对话框 |
| -2 | 翻页 (等待输入) |
| -3 | 翻页 (不等待) |
| -4 | 递归调用 (索引44) |
| -5 | 递归调用 (索引45) |
| -6 | 显示数字 (dword_53AE1) |
| -17 | 创建小对话框 (n1832=1832) |
| -18 | 创建大对话框 (n1832=36887) |
| -19 | 创建小对话框 (从配置) |
| -20 | 创建大对话框 (从配置) |

### 5.3 核心实现 (简化版)

```c
void __usercall sub_15F84(..., int arg0, int arg4, ...)
{
  sub_3702F(a2, a3, a5, a4, 92);
  v15 = (__int16 *)(*(__int16 *)(arg0 + 2 * arg4) + arg0);  // 获取文本指针
  
  while ( 1 )
  {
    v18 = *v15;  // 读取当前字符/控制码
    
    if ( v18 == -1 )  // 结束
    {
      if ( v35 ) { sub_16559(0); sub_16C57(0); sub_16B43(v35, n2); }
      JUMPOUT(0x15309);
    }
    if ( v18 == -2 )  // 翻页等待
    {
      if ( (n1832 == 1832 || n1832 == 36887) && n3 == 3 ) { sub_16E24(); --n3; }
      n658255_1 = ++n3 * arg1C * argC + n658255;
      goto LABEL_50;
    }
    if ( v18 == -3 )  // 翻页不等待
    {
      if ( (n1832 == 1832 || n1832 == 36887) && n3 == 3 ) { sub_16E24(); --n3; }
      n658255_1 = ++n3 * arg1C * argC + n658255;
      ++v15;
      if ( n1832 == 1832 || n1832 == 36887 ) sub_16559(0);
      sub_16C57(1);
      arg20 = 1;
    }
    // ... 其他控制码处理 ...
    
    if ( v18 == -17 )  // 创建小对话框
    {
      if ( v35 ) { sub_16559(0); sub_16C57(0); v18 = sub_16B43(v35, n2); }
      n1832 = 1832;
      n39 = (unsigned __int16)v15[1];
      v20 = sub_12C60(v18, v16, a5, a4, n39);
      if ( v20 == -1 ) n2 = 0; else n2 = 2;
      if ( n39 != 39 ) { a1 = (unsigned __int8 *)dword_53C1B; n39 = *(unsigned __int8 *)(dword_53C1B + 7); }
      DATO_DAT = (int)sub_111BA(v20, v16, a5, a4, (int)aDatoDat, DATO_DAT, n39);
      v21 = sub_165AC(*a1, v16, a5, a4, *a1, a1[1], n2);
      // ...
    }
    if ( v18 == -18 )  // 创建大对话框
    {
      if ( v35 ) { sub_16559(0); sub_16C57(0); v18 = sub_16B43(v35, n2); }
      n1832 = 36887;
      v22 = sub_12C60(v18, v16, a5, a4, (unsigned __int16)v15[1]);
      if ( v22 == -1 ) n2 = 0; else n2 = 112;
      v23 = (unsigned __int8 *)dword_53C1B;
      DATO_DAT = (int)sub_111BA(v22, v16, a5, a4, (int)aDatoDat, DATO_DAT, *(unsigned __int8 *)(dword_53C1B + 7));
      v24 = sub_165AC(*v23, v16, a5, a4, *v23, v23[1], n2);
      // ...
    }
    
    // 普通字符绘制
    sub_4ED7A(dword_53A75, v18, n658255_1, argC, arg10, arg14, arg18);
    n658255_1 += 16;  // 下一个字符位置
    v15 = v32;
    if ( sub_10620() ) arg20 = 0;  // 检查输入
    if ( arg20 ) sub_164E8();       // 动画效果
  }
}
```

### 5.4 调用示例

```c
// 标准文本渲染
sub_15F84(a1, v7, SHIDWORD(v7), a3, n658255,
          arg0=0,      // 文本文件
          arg4=44,     // 文本索引
          n658255=..., // 屏幕偏移
          argC=320,    // pitch
          arg10=205,   // X坐标
          arg14=76,    // Y坐标
          arg18=74,    // 宽度
          arg1C=19,    // 高度
          arg20=0)     // 标志

// 战场文本
sub_15F84(n220_1, arg8 + 5865, SHIDWORD(v11), a3, (int)arg0, arg0_0, 10, arg8 + 5865, 320, 205, 76, 0, 0, 0);
sub_15F84(n220_1, (unsigned __int8)v13[8] + 1, SHIDWORD(v11), a3, (int)arg0, ::arg0, (unsigned __int8)v13[8] + 1, arg8 + 5915, 320, 205, 76, 0, 0, 0);
sub_15F84(n220_1, arg8 + 12265, SHIDWORD(v11), a3, (int)arg0, arg0_0, 11, arg8 + 12265, 320, 205, 76, 0, 0, 0);
sub_15F84(n220_1, (unsigned __int8)v13[32] + 150, SHIDWORD(v11), a3, (int)arg0, ::arg0, (unsigned __int8)v13[32] + 150, arg8 + 12315, 320, 205, 76, 0, 0, 0);
sub_15F84(n220_1, (unsigned __int8)arg0, SHIDWORD(v11), a3, (int)arg0, arg0_0, (unsigned __int8)arg0, arg8 + 32008, 320, 205, 76, 0, 20, 0);
```

---

## 六、sub_135DD 场景切换函数

### 6.1 函数签名

**地址**: 0x135DD

```c
void __fastcall sub_135DD(__int32 a1, int a2, int a3, int a4, int a5, int a6)
```

**参数**:
- `a5`: 目标X坐标
- `a6`: 目标Y坐标

### 6.2 功能说明

平滑滚动到目标场景坐标，每帧移动1个单位直到到达目标位置。

### 6.3 核心实现

```c
void __fastcall sub_135DD(..., int a5, int a6)
{
  v6 = sub_3702F(a1, a2, a3, a4, 20);
  dword_51A83 = 0;
  
  // X方向平滑滚动
  while ( a5 != dword_53AA9 )
  {
    if ( a5 >= dword_53AA9 )
    {
      ++dword_53AB1;
      ++dword_53AA9;
    }
    else
    {
      --dword_53AB1;
      --dword_53AA9;
    }
    sub_11CAC(v6, a2, a3, a4, 0);  // 渲染帧
    LOWORD(v6) = sub_4E381();       // 等待垂直同步
  }
  
  // Y方向平滑滚动
  while ( a6 != dword_53AAD )
  {
    if ( a6 >= dword_53AAD )
    {
      ++dword_53AB5;
      ++dword_53AAD;
    }
    else
    {
      --dword_53AB5;
      --dword_53AAD;
    }
    sub_11CAC(v6, a2, a3, a4, 0);
    LOWORD(v6) = sub_4E381();
  }
  JUMPOUT(0x13181);
}
```

### 6.4 关键全局变量

| 变量 | 地址 | 说明 |
|------|------|------|
| `dword_53AA9` | 0x53AA9 | 当前X坐标 |
| `dword_53AAD` | 0x53AAD | 当前Y坐标 |
| `dword_53AB1` | 0x53AB1 | X方向 |
| `dword_53AB5` | 0x53AB5 | Y方向 |

### 6.5 调用示例 (从第二层状态机分析)

```c
// 标题场景
sub_135DD(3, 34);   // X=3, Y=34

// 菜单场景
sub_135DD(0, 43);   // X=0, Y=43

// 场景31
sub_135DD(5, 42);   // X=5, Y=42

// 场景41
sub_135DD(4, 41);   // X=4, Y=41

// 初始文本
sub_135DD(4, 12);   // X=4, Y=12

// 重置
sub_135DD(0, 0);    // X=0, Y=0
sub_135DD(0, 15);   // X=0, Y=15
```

### 6.6 调用者列表 (50+个)

- sub_22F37
- sub_23296
- sub_235BC
- sub_23B5F
- sub_24336
- sub_244B6
- sub_24754
- sub_24DF2
- sub_250CC
- sub_2548C
- sub_25757
- sub_3231B
- sub_32D18
- sub_32E8C
- sub_32FB2
- sub_33049
- sub_33169
- sub_33219
- sub_3327D
- sub_3332B
- sub_33367
- sub_333F5
- sub_3347C
- sub_334D9
- sub_335DA
- sub_3367E
- sub_336A0
- sub_338C4
- sub_3396A
- sub_33AAE
- sub_33AF1
- sub_33C9D
- sub_33DBA
- sub_33E3C
- sub_34531
- sub_3460B
- sub_34673
- sub_346CD
- sub_34778
- sub_34818
- sub_34984
- sub_34B9A
- sub_34C7A
- sub_34D2F
- sub_34EB3
- sub_34FCC
- sub_35022
- sub_350C8
- sub_35321
- sub_35468
- sub_3553F
- sub_355B7
- sub_356B3
- sub_357DD
- sub_35B78
- sub_362E8

---

## 七、各UI界面详细分析

### 7.1 主菜单界面 (sub_25EBB)

**函数地址**: 0x25EBB
**调用者**: sub_25BF4

**绘制流程**:
```
sub_25EBB → sub_1F894 (开场动画处理)
          → 根据v8值分支:
             ├─ v8 == 0: 新游戏流程
             │   ├─ sub_1F882 (清屏)
             │   ├─ 加载FDOTHER.DAT索引0
             │   └─ 调用funcs_25E3A[n17]场景函数
             │
             ├─ v8 == 1: 读档流程
             │   ├─ 加载FDOTHER.DAT索引13
             │   ├─ 加载FD2.SAV存档文件
             │   ├─ sub_29BCB (存档选择界面)
             │   └─ sub_26152 (继续战斗)
             │
             └─ 其他: 直接加载战场 (sub_10010)
```

**关键参数**:
- `n17`: 场景ID (0-32)
- `funcs_25E3A`: 场景函数数组
- `byte_51E63[n17]`: 场景对应的音乐ID

### 7.2 属性界面/营地菜单 (sub_19DF7)

**函数地址**: 0x19DF7
**功能**: 营地菜单，包含存档、加载、查看属性等功能

**绘制流程**:
```
sub_19DF7 → 加载FD2.SAV
          → sub_1741C (初始化菜单数据)
          → sub_177FC (菜单循环处理)
          → 根据n3_3分支:
             ├─ n3_3 == 0: sub_1B1E7 (查看属性)
             ├─ n3_3 == 1: sub_1956B(75) + sub_15F84 (存档界面)
             │   └─ 保存数据到FD2.SAV
             ├─ n3_3 == 2: sub_1956B(75) + sub_15F84 (加载界面)
             │   └─ sub_10010 (加载战场)
             └─ 其他: sub_1956B(75) + sub_15F84 (确认界面)
```

**存档界面参数** (sub_15F84调用):
```c
sub_15F84(dst_, v16, n6, 0, v10,
          arg0=0,      // 文本索引
          arg4=410,    // 文本子索引
          n658255=696099, // 屏幕偏移
          argC=320,    // pitch
          arg10=205,   // X坐标
          arg14=76,    // Y坐标
          arg18=74,    // 宽度相关
          arg1C=19,    // 高度相关
          arg20=1)     // 标志
```

**坐标信息**:
- 存档界面: X=205, Y=76
- 确认界面: X=205, Y=76
- 菜单偏移: 410/411/412/413/414/415/416

### 7.3 读盘菜单 (sub_29BCB - 存档选择)

**函数地址**: 0x29BCB
**调用者**: sub_25EBB

**功能**: 显示存档槽位选择界面，让用户选择要加载的存档

**绘制流程**:
```
sub_29BCB → 显示存档槽位UI
          → 等待用户输入
          → 返回选择的槽位索引 (-1=取消)
```

### 7.4 战场菜单 (sub_31C49)

**函数地址**: 0x31C49
**调用者**: sub_31529

**绘制流程**:
```
sub_31C49 → sub_1088D(30) (加载地图30)
          → sub_15F84 (显示初始文本)
          → 淡入淡出循环 (500次)
          → 加载TAI.DAT和FDOTHER.DAT
          → 循环处理每个角色:
             ├─ sub_111BA (加载FIGANI.DAT角色动画)
             ├─ sub_2E9A8 (角色渲染)
             ├─ sub_311E5 (角色位置计算)
             ├─ sub_11EB0 (滚动过渡)
             └─ sub_168B6 (绘制对话框)
          → 循环内处理:
             ├─ 文本显示 (sub_15F84)
             ├─ 角色属性显示
             └─ 屏幕刷新 (sub_17AA9)
```

**关键参数**:
- 地图ID: 30
- 对话框: sub_168B6(DATO_DAT, ..., 7, 5, 5)
- 文本位置: 多个sub_15F84调用，坐标各不相同

### 7.5 加载战场界面 (sub_10010)

**函数地址**: 0x10010
**调用者**: sub_19DF7, sub_25EBB

**绘制流程**:
```
sub_10010 → 加载FD2.SAV
          → 校验存档完整性
          → memmove恢复存档数据
          → 加载FDFIELD.DAT, FDTXT.DAT, FDSHAP.DAT
          → sub_4DF4C (处理地形数据)
          → sub_10652 (加载额外资源)
          → sub_12263 (地图初始化)
          → sub_11CAC (渲染)
          → sub_1F525 (屏幕刷新)
          → 过渡动画 (sub_15F0E, 9次循环)
          → 角色头像显示 (sub_187D6)
          → sub_11EB0 (滚动过渡)
          → sub_17AA9 (刷新)
          → sub_11CAC(0) (最终渲染)
```

---

## 八、屏幕缓冲区信息

| 项目 | 值 |
|------|------|
| 主屏幕缓冲区 | 655360 (0xA0000) - DOS VGA模式 |
| 屏幕尺寸 | 320×200 |
| Pitch | 320字节/行 |
| 总大小 | 320×200 = 64000字节 |

---

## 九、关键全局变量

| 变量 | 地址 | 说明 |
|------|------|------|
| `dword_53A81` | 0x53A81 | FDOTHER索引7指针 (tile集) |
| `dword_53C63` | 0x53C63 | 菜单渲染缓冲区 |
| `dword_53C5B` | 0x53C5B | 备份缓冲区1 |
| `dword_53C5F` | 0x53C5F | 备份缓冲区2 |
| `n1832` | 全局 | 对话框类型标志 |
| `DATO_DAT` | 全局 | DATO.DAT数据指针 |
| `dword_53AA9` | 0x53AA9 | 当前X坐标 |
| `dword_53AAD` | 0x53AAD | 当前Y坐标 |
| `dword_53AB1` | 0x53AB1 | X方向 |
| `dword_53AB5` | 0x53AB5 | Y方向 |

---

## 十、sub_17EEF 对话框渲染函数

### 10.1 函数签名

**地址**: 0x17EEF

```c
int __fastcall sub_17EEF(__int32 a1, int a2, int a3, int a4, int a5, int a6)
```

### 10.2 核心实现

```c
int __fastcall sub_17EEF(..., int a5, int a6)
{
  sub_3702F(a1, a2, a3, a4, 32);
  n1832 = 3208;
  
  // 加载DATO.DAT资源
  DATO_DAT = (int)sub_111BA(
      *(unsigned __int8 *)(80 * a5 + dword_53A45 + 7),
      a2, 80 * a5, a4, (int)aDatoDat, DATO_DAT,
      *(unsigned __int8 *)(80 * a5 + dword_53A45 + 7));  // "DATO.DAT"
  
  v6 = DATO_DAT + *(unsigned __int8 *)DATO_DAT;
  
  // 绘制对话框边框
  sub_168B6(DATO_DAT, a2, v6, a4, a6, 320, 5, 7, 5, 5);
  
  // 渲染对话框内容
  sub_4EBFF(n1832 + a6, v6, 320);
  sub_4EBFF(a6 + 2332, *(_DWORD *)(dword_53A81 + 86) + dword_53A81, 320);
  sub_4EBFF(a6 + 30085, *(_DWORD *)(dword_53A81 + 90) + dword_53A81, 320);
  
  return sub_17FC0(a5, a6);
}
```

---

## 十一、总结

### 11.1 UI界面汇总

| UI界面 | 核心函数 | 坐标/尺寸 | 调用关系 |
|--------|----------|-----------|----------|
| **主菜单** | sub_25EBB | 全屏 | → sub_1F894, → sub_29BCB |
| **属性界面** | sub_19DF7 | X=205, Y=76 | → sub_1956B(75), → sub_15F84 |
| **读盘菜单** | sub_29BCB | 存档槽位 | → sub_25EBB |
| **战场菜单** | sub_31C49 | 多位置 | → sub_168B6, → sub_15F84 |
| **对话框** | sub_165AC | 动态大小 | → sub_168B6 (5层) |
| **通用菜单** | sub_1956B | 112×19 tile | → sub_168B6 |

### 11.2 核心函数调用链

```
sub_168B6 (窗口绘制)
  ↑
  ├─ sub_165AC (对话框动画)
  │   ↑
  │   └─ sub_15F84 (文字渲染)
  │       ↑
  │       └─ 100+ 调用者
  │
  ├─ sub_17EEF (对话框渲染)
  │   ↑
  │   └─ sub_17E0B, sub_1BFFE, sub_1CFF0
  │
  ├─ sub_1956B (通用菜单)
  │   ↑
  │   └─ 25+ 调用者 (sub_10010, sub_19DF7, etc.)
  │
  └─ sub_31C49 (战场菜单)
      ↑
      └─ sub_31529
```

### 11.3 资源文件

| 资源文件 | 用途 |
|----------|------|
| FDOTHER.DAT | 基础图片资源 (索引0,7,13等) |
| DATO.DAT | 对话框/菜单资源 |
| FDTXT.DAT | 文本数据 |
| FDFIELD.DAT | 地图数据 |
| FDSHAP.DAT | 地形/瓦片数据 |
| FIGANI.DAT | 角色动画数据 |
| TAI.DAT | 战斗相关数据 |
| FD2.SAV | 存档文件 |

---

*分析完成日期: 2026-05-23*
*分析方法: IDA Pro MCP + 汇编代码分析*
