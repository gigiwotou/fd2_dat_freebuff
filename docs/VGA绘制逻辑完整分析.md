# FD2 原游戏VGA绘制逻辑完整分析

> 基于IDA Pro MCP对FD2.EXE的反汇编分析
> 分析日期: 2026-05-24

---

## 📋 目录

1. [VGA基础架构](#1-vga基础架构)
2. [位块传输函数 (BitBlt)](#2-位块传输函数-bitblt)
3. [字符/精灵渲染系统](#3-字符精灵渲染系统)
4. [VGA调色板系统](#4-vga调色板系统)
5. [UI绘制系统](#5-ui绘制系统)
6. [文本渲染引擎](#6-文本渲染引擎)
7. [滚动与场景切换](#7-滚动与场景切换)
8. [屏幕刷新管线](#8-屏幕刷新管线)
9. [动画与特效系统](#9-动画与特效系统)
10. [显存布局与地址映射](#10-显存布局与地址映射)
11. [函数调用关系图](#11-函数调用关系图)

---

## 1. VGA基础架构

### 1.1 显存基址

```c
#define VGA_MEM_BASE    655360  // 0xA0000 (十进制)
#define VGA_PITCH       320     // 实际像素宽度
```

### 1.2 键盘缓冲区检测

```c
// sub_10620() - 检查键盘输入
bool __fastcall sub_10620(__int32 a1, int a2, int a3, int a4)
{
  sub_3702F(a1, a2, a3, a4, 8);
  return MEMORY[0x41C] != MEMORY[0x41A];  // 键盘缓冲区头尾指针比较
}
```

### 1.3 垂直同步/刷新函数

```c
// sub_4E381() - 刷新键盘缓冲区
__int16 sub_4E381()
{
  __int16 result = MEMORY[0x41A];     // 读取键盘缓冲区头指针
  MEMORY[0x41C] = MEMORY[0x41A];      // 重置尾指针
  return result;
}
```

---

## 2. 位块传输函数 (BitBlt)

### 2.1 sub_4EBFF() - 正向位块传输

**地址**: 0x4EBFF

**功能**: 从左到右、从上到下复制像素数据

**函数签名**:
```c
void __cdecl sub_4EBFF(_BYTE *a1, __int16 *a2, int a3)
```

**参数说明**:
- `a1`: 目标显存指针
- `a2`: 源数据头指针 (包含宽度、高度信息)
- `a3`: 行跨度 (pitch)

**核心逻辑**:
```c
void __cdecl sub_4EBFF(_BYTE *a1, __int16 *a2, int a3)
{
  __int16 width = *a2;        // 图像宽度
  __int16 height = a2[1];     // 图像高度
  
  for (int y = 0; y < height; y++)
  {
    for (int x = 0; x < width; x++)
    {
      *a1++ = sub_4EC66();    // 获取下一个像素值
    }
    a1 = &v8[a3];             // 跳到下一行 (pitch偏移)
  }
}
```

**像素获取流程**:
1. 调用 `sub_4EC66()` 获取下一个像素
2. 逐像素正向写入显存
3. 每行结束后按pitch跳转到下一行

### 2.2 sub_4EC31() - 反向位块传输

**地址**: 0x4EC31

**功能**: 从左到右、但从右到左写入像素 (水平翻转)

**函数签名**:
```c
void __cdecl sub_4EC31(_BYTE *a1, __int16 *a2, int a3)
```

**核心逻辑**:
```c
void __cdecl sub_4EC31(_BYTE *a1, __int16 *a2, int a3)
{
  __int16 width = *a2;
  __int16 height = a2[1];
  
  for (int y = 0; y < height; y++)
  {
    for (int x = 0; x < width; x++)
    {
      *a1-- = sub_4EC66();    // 注意: 递减写入 (水平翻转)
    }
    a1 = &v8[a3];             // 跳到下一行
  }
}
```

**与正向传输的区别**:
- 使用 `*a1--` 而非 `*a1++`
- 实现水平镜像效果
- 用于对话框从右向左滑入等场景

### 2.3 sub_4EC66() - 获取下一个像素值

**地址**: 0x4EC66

**功能**: RLE解码,从全局源数据流中读取下一个像素值

**汇编代码**:
```asm
4ec66  or      ah, ah
4ec68  jz      short loc_4EC6D
4ec6a  dec     ah
4ec6c  retn
4ec6d  lodsb
4ec6e  cmp     al, 0C0h
4ec70  ja      short loc_4EC75
4ec72  xor     ah, ah
4ec74  retn
4ec75  mov     ah, al
4ec77  sub     ah, 0C1h
4ec7a  lodsb
4ec7b  retn
```

**RLE解码逻辑**:
```c
void sub_4EC66()
{
  if (ah != 0)
  {
    ah--;            // 重复计数器递减
    return;          // 返回al中的像素值
  }
  
  al = *esi++;       // 读取新字节
  
  if (al <= 0xC0)
  {
    ah = 0;          // 非RLE模式
    return;
  }
  
  ah = al - 0xC1;    // 设置重复次数
  al = *esi++;       // 读取要重复的像素值
  return;
}
```

**RLE格式说明**:
- `al <= 0xC0`: 普通像素,直接返回
- `al > 0xC0`: RLE编码, `ah = al - 0xC1` 为重复次数, 下一个字节为像素值

### 2.4 sub_4ECF0() - 行拷贝辅助函数

**地址**: 0x4ECF0

**功能**: 按行拷贝内存数据,支持源/目标行跨度不同

**函数签名**:
```c
__int64 __usercall sub_4ECF0@<edx:eax>(
    int src_pitch@<ebp>, 
    char *dst@<edi>, 
    char *src@<esi>)
```

**核心逻辑**:
```c
__int64 __usercall sub_4ECF0(int src_pitch, char *dst, char *src)
{
  for (int y = 0; y < height; y++)
  {
    memcpy(dst, src, width);   // 拷贝一行
    dst += width;              // 目标指针前进width
    src += src_pitch + width;  // 源指针前进pitch+width
  }
}
```

### 2.5 sub_4ECBF() - 区域复制封装

**地址**: 0x4ECBF

**功能**: 从源显存区域复制数据到缓冲区,并保存尺寸信息

**函数签名**:
```c
void __cdecl sub_4ECBF(
    int buffer,         // 目标缓冲区
    __int16 width,      // 区域宽度
    __int16 height,     // 区域高度
    int src_addr,       // 源显存地址
    int src_offset,     // 源偏移
    int src_pitch)      // 源行跨度
```

**缓冲区格式**:
```
偏移 0-1: 宽度 (__int16)
偏移 2-3: 高度 (__int16)
偏移 4-7: 源显存指针 (__int32)
偏移 8+:  像素数据
```

**核心逻辑**:
```c
void __cdecl sub_4ECBF(int buffer, __int16 width, __int16 height, 
                        int src_addr, int src_offset, int src_pitch)
{
  *(_WORD *)buffer = width;
  *(_WORD *)(buffer + 2) = height;
  *(_DWORD *)(buffer + 4) = src_addr;
  sub_4ECF0(src_pitch, (char *)(buffer + 8), (char *)(src_addr + src_offset));
}
```

### 2.6 sub_4EC7C() - 区域恢复函数

**地址**: 0x4EC7C

**功能**: 将缓冲区数据恢复到显存

**函数签名**:
```c
void __cdecl sub_4EC7C(__int16 *a1, int dst_addr, int dst_pitch)
```

**核心逻辑**:
```c
void __cdecl sub_4EC7C(__int16 *a1, int dst_addr, int dst_pitch)
{
  __int16 width = *a1;
  __int16 height = a1[1];
  sub_4ECA4(dst_pitch, 
            (char *)(*(_DWORD *)(a1 + 2) + dst_addr), 
            (char *)a1 + 8);
}
```

---

## 3. 字符/精灵渲染系统

### 3.1 sub_4ED7A() - 字符/精灵渲染

**地址**: 0x4ED7A

**功能**: 渲染16×16字符或精灵,支持前景色/背景色和边框效果

**函数签名**:
```c
void __cdecl sub_4ED7A(
    int FDOTHER_DAT,        // FDOTHER.DAT数据指针
    int char_index,         // 字符索引
    int n658255,            // 屏幕位置指针
    unsigned __int16 pitch, // 屏幕行距
    char fg_color,          // 前景色
    char bg_color,          // 背景色
    int clear_flag)         // 清空标志
```

**字符位图格式**:
```
每个字符32字节 = 16行 × 2字节/行
每行16位, 每位对应一个像素
bit=1: 绘制前景色
bit=0: 透明
```

**核心逻辑**:
```c
void __cdecl sub_4ED7A(...)
{
  // 1. 可选: 清空字符区域
  if (clear_flag)
  {
    for (int y = 0; y < 16; y++)
    {
      memset32(screen_ptr, clear_value, 4);  // 每行清空4字节
      screen_ptr += pitch;
    }
  }
  
  // 2. 跳过特殊索引10 (可能是空格)
  if (char_index != 10)
  {
    __int16 *bitmap = (__int16 *)(32 * char_index + FDOTHER_DAT);
    
    // 3. 逐行渲染 (16行)
    for (int y = 0; y < 16; y++)
    {
      __int16 row_data = *bitmap++;
      // 字节交换 (小端序调整)
      row_data = (row_data << 8) | (row_data >> 8);
      
      // 4. 逐像素渲染 (16像素)
      for (int x = 0; x < 16; x++)
      {
        if (row_data & 0x8000)  // 检查最高位
        {
          *screen_ptr = fg_color;              // 前景色
          screen_ptr[pitch - 1] = bg_color;    // 左边框
          screen_ptr[pitch] = bg_color;        // 下边框
        }
        screen_ptr++;
        row_data <<= 1;  // 左移检查下一位
      }
      
      screen_ptr = &row_start[pitch];  // 跳到下一行
    }
  }
}
```

**关键特性**:
1. **边框效果**: 绘制字符时自动在左侧和底部绘制背景色边框
2. **透明背景**: bit=0的位置不绘制
3. **特殊字符**: 索引10被跳过 (可能是空格或特殊标记)

### 3.2 sub_4ED34() - 颜色叠加

**地址**: 0x4ED34

**功能**: 对显存区域进行颜色叠加处理

**函数签名**:
```c
void __cdecl sub_4ED34(int addr, int FDOTHER_DAT, __int16 count)
```

**实现**:
```c
void __cdecl sub_4ED34(int addr, int FDOTHER_DAT, __int16 count)
{
  argC = count;
  sub_4ED4F();  // 调用实际的颜色叠加处理
}
```

---

## 4. VGA调色板系统

### 4.1 sub_11D40() - VGA调色板设置

**地址**: 0x11D40

**功能**: 通过VGA DAC端口设置调色板颜色,支持淡入淡出效果

**函数签名**:
```c
void __fastcall sub_11D40(
    __int32 a1,         // 标准参数1
    int a2, a3, a4,     // 标准参数2-4
    int start_color,    // 起始颜色索引 (0-255)
    int end_color,      // 结束颜色索引
    int color_offset)   // 颜色偏移量 (用于淡入淡出)
```

**VGA DAC端口**:
- `0x3C8 (968)`: Palette Write Address Register (写地址寄存器)
- `0x3C9 (969)`: Palette Data Register (写数据寄存器, RGB各1字节)

**核心逻辑**:
```c
void __fastcall sub_11D40(..., int start_color, int end_color, int color_offset)
{
  sub_3702F(a1, a2, a3, a4, 24);
  
  while (start_color <= end_color)
  {
    outp(968, start_color);  // 设置DAC写地址
    
    // 从FDOTHER.DAT读取调色板数据并减去偏移
    int red = *(unsigned __int8 *)(FDOTHER_DAT + 3 * start_color) - color_offset;
    if (red < 0) red = 0;
    outp(969, red);          // 写入红色分量
    
    int green = *(unsigned __int8 *)(FDOTHER_DAT + 3 * start_color + 1) - color_offset;
    if (green < 0) green = 0;
    outp(969, green);        // 写入绿色分量
    
    int blue = *(unsigned __int8 *)(FDOTHER_DAT + 3 * start_color + 2) - color_offset;
    if (blue < 0) blue = 0;
    outp(969, blue);         // 写入蓝色分量
    
    ++start_color;
  }
}
```

**颜色格式**:
- 每个颜色6字节 (RGB各6位, 0-63范围)
- 存储在FDOTHER.DAT中, 每颜色3字节 (可能是压缩格式)

### 4.2 sub_4E31C() - 闪烁调色板动画

**地址**: 0x4E31C

**功能**: 周期性更新16个VGA调色板寄存器,实现闪烁/呼吸效果

**核心逻辑**:
```c
void sub_4E31C()
{
  // 检查时间间隔 (至少2个tick)
  if ((sub_4E310() - word_60000) >= 2)
  {
    // 闪烁帧计数器 (0-15循环)
    if (++byte_60002 == 16)
      byte_60002 = 0;
    
    // 获取当前帧的调色板数据
    v0 = &unk_60003 + 3 * byte_60002;
    
    // 更新16个VGA调色板寄存器 (颜色索引224-239)
    for (int i = 0; i < 16; i++)
    {
      __outbyte(0x3C8, -32 + i);  // VGA写地址 (224+i)
      __outbyte(0x3C9, *v0++);    // R
      __outbyte(0x3C9, *v0++);    // G
      __outbyte(0x3C9, *v0++);    // B
    }
    
    word_60000 = sub_4E310();  // 更新时间戳
  }
}
```

**调色板更新范围**:
- 颜色索引: 224-239 (16个颜色)
- 用途: 对话框背景闪烁效果
- 帧率: 每2个tick更新一次 (约9Hz)

---

## 5. UI绘制系统

### 5.1 sub_1685C() - Tile绘制基础函数

**地址**: 0x1685C

**功能**: 绘制单个UI tile元素

**函数签名**:
```c
void __fastcall sub_1685C(
    __int32 a1,         // 参数1
    int a2,             // 屏幕行距 (320)
    int a3, a4,         // 其他参数
    char *dst,          // 目标显存位置
    int a6,             // tile高度
    int FDOTHER_DAT_7,  // FDOTHER.DAT tile数据指针
    int tile_index)     // tile索引 (1-17)
```

**核心逻辑**:
```c
void __fastcall sub_1685C(..., char *dst, int height, int tile_data, int tile_index)
{
  sub_3702F(a1, a2, a3, a4, 20);
  sub_4ED0B(dst, (_WORD *)(tile_data + 6 + 4 * tile_index), height);
}
```

**tile数据格式**:
- 每个tile有独立的指针存储在 `FDOTHER_DAT_7 + 6 + 4 * index`
- tile通过 `sub_4ED0B()` 绘制 (类似字符渲染)

### 5.2 sub_168B6() - UI对话框/窗口绘制

**地址**: 0x168B6

**功能**: 绘制完整的UI对话框,包含4个角、4条边和中心区域

**函数签名**:
```c
void __fastcall sub_168B6(
    __int32 a1,     // 屏幕缓冲区指针
    int pitch,      // 屏幕行距 (320)
    int a3, a4,     // 其他参数
    int a5,         // X起始位置
    int tile_height,// tile高度
    int a7,         // FDOTHER_DAT_7指针
    int a8,         // 通常为112或7
    int a9,         // tile行数
    int a10)        // tile列数
```

**UI布局**:
```
+---+-------------------+---+
| 1 |        9          | 2 |  ← 顶行 (tile 1,9,2)
+---+-------------------+---+
|10 |       13          |11 |  ← 中间行 (tile 10,13,11)
|   |                   |   |     重复a10-2次
+---+-------------------+---+
| 3 |        12         | 4 |  ← 底行 (tile 3,12,4)
+---+-------------------+---+
```

**绘制顺序**:
1. 四个角 (tile 1-4)
2. 四条边 (tile 5-8, 14-17)
3. 边缘循环部分 (tile 9-12)
4. 中心区域双循环 (tile 13)

**核心逻辑**:
```c
void __fastcall sub_168B6(...)
{
  sub_3702F(a1, a2, a3, a4, 68);
  
  v27 = a10 - 2;           // 中间行数
  v28 = 16 * a6;           // 缩放因子1
  v29 = 3 * a6;            // 缩放因子2
  v10 = a5 + a6 * a8;      // 基础偏移
  v11 = v10 + a7;          // 实际显存偏移
  
  // === 绘制4个角 ===
  sub_1685C(v10, a2, ..., dst, a6, tile_data, 1);   // 左上角
  sub_1685C(16*a9, dst+..., ..., dst, a6, tile_data, 2); // 右上角
  sub_1685C(v11+v29+v13, ..., ..., dst, a6, tile_data, 3); // 左下角
  sub_1685C(dst+v29+v13, ..., ..., dst, a6, tile_data, 4); // 右下角
  
  // === 绘制边缘和中心 ===
  // ... 复杂的位置计算和tile绘制 ...
  
  // === 中心区域双循环 ===
  for (k = 0; k < a10; ++k)
  {
    for (m = 0; m < a9; ++m)
    {
      sub_1685C(16*m + v11 + v29 + 3 + k*v28, ..., tile_data, 13);
    }
  }
}
```

### 5.3 sub_165AC() - 对话框渐显动画

**地址**: 0x165AC

**功能**: 创建对话框并实现5层渐显动画

**函数签名**:
```c
int *__fastcall sub_165AC(
    __int32 a1, a2, a3, a4,  // 标准参数
    int a5, a6,              // 位置参数
    int n2)                  // 对话框类型 (2=小, 112=大)
```

**动画流程**:
```c
int *__fastcall sub_165AC(..., int dialog_type)
{
  // 1. 可选: 平滑滚动到目标位置
  if (n2)
  {
    n6_5 = 0;
    sub_12CEA(a5, a6);  // 平滑滚动
    n6_5 = 1;
    
    // 动画帧插值计算
    for (i = 0; i <= total_frames; ++i)
    {
      v9 = v17 - i * (v17 - 5) / total_frames;
      v10 = v18 - i * (v18 - n2) / total_frames;
      sub_15E9E(..., v9, v10, ...);  // 保存当前帧
      j___delay(10);
      sub_15E71(v13, ..., v9, v10, ...);  // 恢复并绘制
    }
  }
  
  // 2. 分配5个动画帧缓冲区
  for (n5 = 0; n5 < 5; ++n5)
    dword_53A18[n5] = malloc(26668);
  
  // 3. 5层渐显绘制
  sub_4ECBF(buf[0], 310, 86, VGA_BASE, offset, pitch);
  sub_168B6(VGA_BASE, 320, 5, dialog_type, 4, 2);  // 第1层
  delay(10);
  
  sub_4ECBF(buf[1], 310, 86, VGA_BASE, offset, pitch);
  sub_168B6(VGA_BASE, 320, 5, dialog_type, 8, 3);  // 第2层
  delay(10);
  
  // ... 继续第3-5层 ...
  
  return dword_53A18;
}
```

**对话框类型**:
- `n2 = 2`: 小对话框 (n1832 == 1832)
- `n2 = 112`: 大对话框 (n1832 == 36887)

---

## 6. 文本渲染引擎

### 6.1 sub_15F84() - 文本显示引擎

**地址**: 0x15F84

**功能**: 解析文本数据,处理控制码,调用sub_4ED7A渲染每个字符

**函数签名**:
```c
void __usercall sub_15F84(
    unsigned __int8 *a1@<edi>,  // 屏幕缓冲区
    __int32 a2@<eax>,           // 标准参数1
    int a3@<edx>, a4@<ecx>,     // 标准参数2-3
    int a5@<ebx>,               // 标准参数4
    int arg0,                   // 文本数据基地址
    int arg4,                   // 文本起始索引
    int n658255,                // 屏幕位置
    int argC,                   // 屏幕行距
    char arg10,                 // 前景色
    char arg14,                 // 背景色
    int arg18,                  // 清空标志
    int arg1C,                  // 行距倍数
    int arg20)                  // 动画控制
```

**控制码系统**:
```c
while (1)
{
  n10 = *v15;  // 读取下一个字符/控制码
  
  switch (n10)
  {
    case -1:   // 文本结束
      if (v35) {
        sub_16559(0);
        sub_16C57(0);
        sub_16B43(v35, n2);  // 关闭对话框
      }
      return;
      
    case -2:   // 换行
      if (n1832 == 1832 || n1832 == 36887) {
        if (n3 == 3) sub_16E24();  // 等待输入
        --n3;
      }
      n3++;
      n658255_1 = n3 * arg1C * argC + n658255;  // 新行位置
      break;
      
    case -3:   // 换行 (另一种)
      // 类似-2, 但调用sub_16C57(1)开启等待
      break;
      
    case -4:   // 递归显示FDTXT文本
      sub_15F84(a1, FDTXT_DAT__0, dword_53AD9, n658255_1, argC, 205, 76, 74, 19, 1);
      break;
      
    case -5:   // 递归显示FDTXT文本 (另一种)
      sub_15F84(a1, FDTXT_DAT__0, dword_53ADD, n658255_1, argC, 205, 76, 74, 19, 1);
      break;
      
    case -6:   // 显示数字 (n999_1变量)
      sprintf(v31, "%d", n999_1);
      for (i = 0; v37 > i; ++i)
      {
        sub_4ED7A(FDOTHER_DAT__6, v31[i] - 48, n658255_1, argC, arg10, arg14, arg18);
        n658255_1 += 16;
      }
      break;
      
    case -17:  // 创建小对话框
      n1832 = 1832;
      // ... 加载DATO数据 ...
      sub_4EBFF((_BYTE *)(1832 + VGA_BASE), data, 320);  // 正向传输
      break;
      
    case -18:  // 创建大对话框
      n1832 = 36887;
      // ... 加载DATO数据 ...
      sub_4EC31((_BYTE *)(36887 + VGA_BASE), data, 320);  // 反向传输
      break;
      
    case -19:  // 创建小对话框 (另一种)
      n1832 = 1832;
      // ... 
      break;
      
    case -20:  // 创建大对话框 (另一种)
      n1832 = 36887;
      // ...
      break;
      
    default:   // 普通字符
      sub_4ED7A(FDOTHER_DAT__6, n10, n658255_1, argC, arg10, arg14, arg18);
      n658255_1 += 16;  // 下一个字符位置
      
      if (sub_10620()) arg20 = 0;  // 检查输入
      if (arg20) sub_164E8();      // 动画效果
      break;
  }
  
  v15++;  // 下一个文本索引
}
```

**颜色常量**:
- 前景色: 205
- 背景色: 76

---

## 7. 滚动与场景切换

### 7.1 sub_135DD() - 平滑滚动

**地址**: 0x135DD

**功能**: X/Y方向平滑滚动到目标场景位置

**函数签名**:
```c
void __fastcall sub_135DD(
    __int32 a1, a2, a3, a4,  // 标准参数
    int target_x,            // 目标X坐标
    int target_y)            // 目标Y坐标
```

**核心逻辑**:
```c
void __fastcall sub_135DD(..., int target_x, int target_y)
{
  sub_3702F(a1, a2, a3, a4, 20);
  n6_5 = 0;
  
  // X方向平滑滚动
  while (target_x != qword_53AA9)
  {
    if (target_x >= qword_53AA9)
    {
      qword_53AB1++;  // 方向+1
      qword_53AA9++;  // 当前位置+1
    }
    else
    {
      qword_53AB1--;  // 方向-1
      qword_53AA9--;  // 当前位置-1
    }
    sub_11CAC(v6, a2, a3, a4, 0);  // 渲染帧
    sub_4E381();                    // 刷新
  }
  
  // Y方向平滑滚动
  while (target_y != HIDWORD(qword_53AA9))
  {
    if (target_y >= HIDWORD(qword_53AA9))
    {
      HIDWORD(qword_53AB1)++;
      HIDWORD(qword_53AA9)++;
    }
    else
    {
      HIDWORD(qword_53AB1)--;
      HIDWORD(qword_53AA9)--;
    }
    sub_11CAC(v6, a2, a3, a4, 0);
    sub_4E381();
  }
}
```

**关键全局变量**:
- `qword_53AA9`: 当前X/Y坐标 (64位, 低32位=X, 高32位=Y)
- `qword_53AB1`: X/Y方向

### 7.2 sub_12CEA() - 场景滚动动画

**地址**: 0x12CEA

**功能**: 带帧间延迟的场景滚动

**核心逻辑**:
```c
void __fastcall sub_12CEA(..., int target_x, int target_y)
{
  v6 = sub_3702F(..., 20);
  v7 = sub_11CAC(v6, a2, a3, a4, 0);
  
  // X方向滚动
  while (target_x != qword_53AB1)
  {
    if (target_x >= qword_53AB1)
      sub_11BFA(v7, a2, a3, a4);   // 向右滚动
    else
      sub_11C59(v7, a2, a3, a4);   // 向左滚动
    sub_4E381();
  }
  
  // Y方向滚动
  while (target_y != HIDWORD(qword_53AB1))
  {
    if (target_y >= HIDWORD(qword_53AB1))
      sub_11B9B(v7, a2, a3, a4);   // 向下滚动
    else
      sub_11B48(v7, a2, a3, a4);   // 向上滚动
    sub_4E381();
  }
}
```

---

## 8. 屏幕刷新管线

### 8.1 sub_11CAC() - 主渲染帧函数

**地址**: 0x11CAC

**功能**: 完整的单帧渲染管线,包括调色板更新和显存刷新

**核心逻辑**:
```c
int __fastcall sub_11CAC(__int32 a1, int a2, int a3, int a4, int a5)
{
  sub_3702F(a1, a2, a3, a4, 32);
  
  sub_1297D();           // 准备渲染数据
  
  if (!a5)
    sub_4E31C();         // 更新闪烁调色板
  
  // 从逻辑坐标转换到显存坐标
  sub_11EEE(VGA_BASE + 32904, 456, 13, 8, qword_53AA9, HIDWORD(qword_53AA9));
  
  sub_122DC();           // 后处理1
  sub_127A9();           // 后处理2
  
  sub_1ACF3(VGA_BASE + 32904, 456);  // 最终处理
  
  // 显存拷贝到实际显示区域
  return sub_11EB0(VGA_BASE + 32904, a2, a3, a4, 
                   656644, 320, VGA_BASE + 32904, 456, 312, 192);
}
```

**行跨度转换**:
- 逻辑行距: 456 (包含额外数据)
- 实际行距: 320 (像素宽度)
- 转换公式: `456 * (行号 - 4) + 32900`

### 8.2 sub_11EB0() - 显存区域拷贝

**地址**: 0x11EB0

**功能**: 按行拷贝显存数据,支持不同源/目标行跨度

**核心逻辑**:
```c
int __fastcall sub_11EB0(..., int dst, int dst_pitch, int src, int src_pitch, 
                          int row_size, int row_count)
{
  sub_3702F(..., 32);
  
  for (i = 0; i < row_count; ++i)
  {
    memmove(dst, src, row_size);  // 拷贝一行
    dst += dst_pitch;             // 目标指针前进
    src += src_pitch;             // 源指针前进
  }
}
```

---

## 9. 动画与特效系统

### 9.1 sub_16C57() - 对话框等待/动画

**地址**: 0x16C57

**功能**: 对话框等待输入,同时播放闪烁动画

**核心逻辑**:
```c
void __fastcall sub_16C57(..., int wait_mode)
{
  sub_3702F(..., 52);
  
  n18 = 18;       // 初始tile索引
  v6 = 0;         // 帧计数器
  n1132_2 = MEMORY[0x46C];  // DOS定时器
  
  while (!sub_10620())  // 等待键盘输入
  {
    sub_4E31C();  // 更新闪烁调色板
    
    n2 = MEMORY[0x46C] - n1132_2;
    if (n2 >= 2)  // 每2个tick更新
    {
      if (wait_mode == 1 && ++v6 == 3)
      {
        v6 = 0;
        if (++n18 == 20) n18 = 18;  // tile 18-19循环
        sub_1685C(offset + 1600, 320, tile_data, n18);
      }
      
      // 闪烁效果
      if (v17) {
        sub_16559(0);  // 清除闪烁
        v17 = 0;
      } else {
        n2 = v11--;
        if (!n2) {
          sub_16559(3);  // 设置闪烁
          v17 = 1;
        }
      }
      
      n1132_2 = MEMORY[0x46C];
    }
  }
  
  if (wait_mode == 1)
    sub_1685C(offset, 320, tile_data, 13);  // 恢复默认tile
  
  // 读取键盘扫描码
  int386(22, &n3, &n3);
  // 返回键位映射
}
```

### 9.2 sub_15E9E() - 帧保存函数

**地址**: 0x15E9E

**功能**: 保存当前显存区域到缓冲区

**核心逻辑**:
```c
void __fastcall sub_15E9E(..., int x, int y, __int16 *data, int VGA_BASE, int pitch, ...)
{
  sub_3702F(..., 48);
  
  __int16 width = *data;
  __int16 height = data[1];
  int screen_offset = x + pitch * y;
  
  int buffer = malloc(height * width + 8);
  sub_4ECBF(buffer, width, height, VGA_BASE, screen_offset, pitch);
  sub_4ED34(VGA_BASE + screen_offset, (int)data, pitch);  // 颜色叠加
}
```

### 9.3 sub_15E71() - 帧恢复函数

**地址**: 0x15E71

**功能**: 从缓冲区恢复显存数据,并释放缓冲区

**核心逻辑**:
```c
int __fastcall sub_15E71(..., int x, int y, __int16 *buffer)
{
  sub_3702F(..., 20);
  sub_4EC7C(buffer, x, y);  // 恢复显存数据
  return free(buffer);       // 释放缓冲区
}
```

---

## 10. 显存布局与地址映射

### 10.1 显存布局

```
VGA显存 (0xA0000 = 655360十进制)
├─ 偏移 0-63999: 320x200 像素数据
├─ 偏移 32900-693535: 456字节/行格式 (内部处理)
├─ 偏移 32904: 场景渲染基址
├─ 偏移 656644: 实际显示基址 (320行距)
└─ 偏移 658255: 文本渲染基址 (小对话框)
   偏移 693535: 文本渲染基址 (大对话框)
```

### 10.2 行跨度转换

```
逻辑坐标系 (456字节/行)
    ↓ sub_11EB0() 转换
物理坐标系 (320字节/行)
    ↓
VGA硬件显示
```

**转换公式**:
```
物理偏移 = 456 * (逻辑行号 - 4) + 32900
```

### 10.3 颜色系统

**VGA调色板**:
- 256色调色板
- 每颜色: 6位R + 6位G + 6位B (0-63)
- 通过端口0x3C8/0x3C9编程

**常用颜色**:
- 前景色: 205 (文本)
- 背景色: 76 (阴影)
- 闪烁范围: 224-239 (对话框动画)

---

## 11. 函数调用关系图

```
sub_11CAC() [主渲染帧]
    ├── sub_1297D()
    ├── sub_4E31C() [闪烁调色板]
    ├── sub_11EEE() [坐标转换]
    ├── sub_122DC()
    ├── sub_127A9()
    ├── sub_1ACF3()
    └── sub_11EB0() [显存拷贝]
         └── memmove()

sub_15F84() [文本引擎]
    ├── sub_4ED7A() [字符渲染]
    │    └── FDOTHER_DAT [字体位图]
    ├── sub_165AC() [对话框动画]
    │    ├── sub_12CEA() [滚动]
    │    ├── sub_15E9E() [帧保存]
    │    ├── sub_15E71() [帧恢复]
    │    └── sub_168B6() [UI绘制]
    │         └── sub_1685C() [tile绘制]
    ├── sub_4EBFF() [正向传输]
    └── sub_4EC31() [反向传输]

sub_135DD() [平滑滚动]
    ├── sub_11CAC() [渲染帧]
    └── sub_4E381() [刷新]

sub_16C57() [对话框等待]
    ├── sub_4E31C() [闪烁调色板]
    ├── sub_1685C() [tile绘制]
    └── sub_16559() [闪烁控制]

调色板系统:
sub_11D40() [VGA DAC设置]
    └── outp(0x3C8/0x3C9)

sub_4E31C() [闪烁动画]
    └── __outbyte(0x3C8/0x3C9)
```

---

## 📊 函数索引表

| 地址    | 函数名        | 大小    | 功能描述                 |
| ------- | ----------- | ----- | -------------------- |
| 0x4EBFF | sub_4EBFF   | -     | 正向位块传输 (左→右)       |
| 0x4EC31 | sub_4EC31   | -     | 反向位块传输 (右→左,水平翻转)  |
| 0x4EC66 | sub_4EC66   | -     | RLE解码获取下一个像素值      |
| 0x4ECBF | sub_4ECBF   | -     | 区域复制到缓冲区            |
| 0x4EC7C | sub_4EC7C   | -     | 从缓冲区恢复区域            |
| 0x4ECF0 | sub_4ECF0   | -     | 行拷贝辅助函数              |
| 0x4ED34 | sub_4ED34   | -     | 颜色叠加                 |
| 0x4ED7A | sub_4ED7A   | -     | 16×16字符/精灵渲染         |
| 0x4E31C | sub_4E31C   | -     | 闪烁调色板动画 (224-239)    |
| 0x4E381 | sub_4E381   | -     | 刷新键盘缓冲区/垂直同步       |
| 0x11D40 | sub_11D40   | 0xB2  | VGA DAC调色板设置         |
| 0x11EB0 | sub_11EB0   | -     | 显存区域拷贝 (支持不同行距)    |
| 0x11CAC | sub_11CAC   | 0x94  | 主渲染帧函数               |
| 0x12CEA | sub_12CEA   | -     | 场景滚动动画               |
| 0x135DD | sub_135DD   | -     | 平滑滚动到目标位置           |
| 0x15E71 | sub_15E71   | -     | 帧恢复函数                |
| 0x15E9E | sub_15E9E   | -     | 帧保存函数                |
| 0x15F84 | sub_15F84   | 0x2A9 | 文本显示引擎 (控制码解析)     |
| 0x165AC | sub_165AC   | 0x2B1 | 对话框渐显动画 (5层)        |
| 0x1685C | sub_1685C   | -     | Tile绘制基础函数           |
| 0x168B6 | sub_168B6   | 0x19C | UI对话框绘制 (17种tile)   |
| 0x16C57 | sub_16C57   | 0x1CD | 对话框等待/闪烁动画          |
| 0x10620 | sub_10620   | 0x32  | 键盘缓冲区检查             |

---

## 🎯 关键技术要点

### 1. RLE压缩
- 原游戏使用简单的RLE压缩格式
- 阈值: 0xC0 (192)
- 超过阈值: 后续字节为重复次数和像素值

### 2. 双行距系统
- 逻辑行距: 456 (内部处理)
- 物理行距: 320 (VGA显示)
- 通过sub_11EB0()转换

### 3. 垂直同步
- 使用DOS键盘缓冲区 (0x41A/0x41C)
- sub_4E381()刷新缓冲区
- sub_10620()检查输入

### 4. 调色板动画
- 224-239: 对话框闪烁
- 通过outp(0x3C8/0x3C9)直接操作VGA DAC
- 每2个tick更新 (约9Hz)

### 5. 对话框系统
- 小对话框: n1832=1832
- 大对话框: n1832=36887
- 5层渐显动画
- 17种tile元素

---

**分析工具**: IDA Pro MCP Server  
**文件路径**: D:\workspace\fd2ida\FD2\FD2.EXE  
**分析完成日期**: 2026-05-24
