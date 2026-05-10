# DAT文件加载函数分析报告

## 概述
通过分析FD2.EXE的汇编代码，发现了多个与DAT文件加载和处理相关的函数。这些函数主要负责从磁盘加载游戏资源文件（如FDOTHER.DAT、FDTXT.DAT、FDFIELD.DAT等）到内存中。

## DAT文件列表

根据代码中的字符串引用，发现了以下DAT文件：
- **ANI.DAT** - 动画资源文件
- **FDTXT.DAT** - 文本资源文件
- **FDOTHER.DAT** - 其他资源文件
- **FDFIELD.DAT** - 地图/场资源文件
- **FDSHAP.DAT** - 形状资源文件
- **DATO.DAT** - 数据文件
- **FDMUS.DAT** - 音乐资源文件
- **BG.DAT** - 背景资源文件
- **FIGANI.DAT** - 角色动画文件
- **TAI.DAT** - 其他资源文件
- **FDICON.B24** - 图标文件

## 关键函数分析

### 1. sub_111BA (地址: 0x111BA) - 核心DAT文件加载函数

这是加载DAT文件的核心函数。

```c
// 函数功能：加载DAT文件的指定索引数据到内存
// 参数说明：
//   a1, a2, a3, a4 - 寄存器传递的参数
//   a5 - DAT文件名（如"FDOTHER.DAT"）
//   a6 - 之前分配的内存指针（用于释放）
//   a7 - 数据索引号
// 返回值：指向加载数据的指针

_BYTE *__fastcall sub_111BA(__int32 a1, int a2, int a3, int a4, int a5, int a6, int a7)
{
  int file_handle;      // 文件句柄 (esi)
  int *temp_buffer;     // 临时缓冲区 (ebx)
  int data_offset;      // 数据偏移 (edi)
  _BYTE *data_buffer;   // 数据指针 (ebx)

  sub_3702F(a1, a2, a3, a4, 32); // 栈帧初始化
  
  // 如果之前有分配的内存，先释放
  if (a6)
    free(a6);
  
  // 以二进制只读模式打开DAT文件
  file_handle = fopen(a5, "rb");
  if (!file_handle)
  {
    printf("\n\n File not found %s!!! \n\n"); // 文件未找到
    goto LABEL_8;
  }
  
  // 分配8字节缓冲区读取偏移信息
  temp_buffer = (int *)malloc(8);
  
  // 定位到文件中的索引表位置
  // 公式：offset = 4 * a7 + 6
  // 每个索引项占4字节，文件头有6字节
  fseek(file_handle, 4 * a7 + 6, 0);
  
  // 读取两个值：数据起始偏移和数据结束偏移
  sub_373CA(temp_buffer, 1u, 8, file_handle); // 读取8字节
  data_offset = *temp_buffer; // 数据起始偏移
  dword_53BFF = temp_buffer[1] - *temp_buffer; // 数据大小 = 结束偏移 - 起始偏移
  
  free(temp_buffer); // 释放临时缓冲区
  
  // 分配数据缓冲区
  data_buffer = (_BYTE *)malloc(dword_53BFF);
  if (!data_buffer)
  {
    printf("Out of Memory at Load %s Number:%d!!\n");
LABEL_8:
    JUMPOUT(0x1005E);
  }
  
  // 定位到数据位置并读取
  fseek(file_handle, data_offset, 0);
  sub_373CA(data_buffer, 1u, dword_53BFF, file_handle);
  
  fclose(file_handle); // 关闭文件
  return data_buffer; // 返回数据指针
}
```

### 2. sub_11019 (地址: 0x11019) - 图标加载函数（带缓存）

```c
// 函数功能：从FDICON.B24加载图标数据，具有缓存机制
// 参数说明：
//   a5 - 图标索引
//   a6 - 文件句柄（保持打开状态）
// 返回值：图标在缓存中的索引

int __fastcall sub_11019(__int32 a1, int a2, int a3, int a4, int a5, int a6)
{
  // 定位到文件头（偏移6）
  fseek(a6, 6, 0);
  
  // 分配6720字节缓冲区
  v6 = malloc(6720);
  sub_373CA(v6, 1u, 6720, a6);
  
  // 提取指定图标的13个偏移值
  for (n13 = 0; n13 < 13; ++n13)
    v13[n13] = *(_DWORD *)&v6[48 * a5 + 4 * n13];
  
  v14 = v13[12] - v13[0]; // 数据大小
  free(v6);
  
  // 检查缓存
  if (dword_53BDF) // 缓存已初始化
  {
    // 查找是否已缓存
    for (i = 0; i < dword_53BDF; ++i)
    {
      if (a5 == dword_53B17[i])
        return i; // 返回缓存索引
    }
    
    // 未缓存，添加到缓存
    dword_53B17[i] = a5;
    fseek(a6, v13[0], 0);
    sub_373CA((buf__3 + dword_53A61), 1u, v14, a6);
    // 存储偏移值...
    buf__3 += v14;
    return dword_53BDF++;
  }
  else // 首次加载，初始化缓存
  {
    dword_53B17[0] = a5;
    dword_53A61 = malloc(...);
    // 读取并存储图标数据...
    return 0;
  }
}
```

### 3. sub_4E98D (地址: 0x4E98D) - RLE解压缩函数

```c
// 函数功能：RLE解压缩并渲染到屏幕缓冲区
// 参数说明：
//   arg0 - 压缩数据指针 (__int16*)
//   arg4 - 目标缓冲区基地址
//   arg8 - X坐标
//   argC - 目标缓冲区指针
//   arg10 - 行距 (pitch)
//   value_1 - 颜色值/模式标志 (-1表示原始模式)

char __cdecl sub_4E98D(__int16 *arg0, int arg4, int arg8, int argC, int arg10, int value_1)
{
  count_0 = *arg0; // 宽度
  src = (char *)(arg0 + 2); // 数据起始
  word_627B6 = arg0[1]; // 高度
  dst = (_BYTE *)(arg4 + arg10 * arg8 + argC);
  
  if (value_1 == -1)
  {
    // 原始模式：直接解压缩
    do
    {
      count = count_0;
      do
      {
        value = *src++;
        
        // RLE解码：根据位标志判断操作类型
        if (!__CFSHL__(value, 1)) // bit15=0
        {
          if (__CFSHL__(2*value, 1)) // bit14=1
          {
            // 类型1: 跳过像素（透明）
            count_1 = ((value*4) >> 2) + 1;
            dst += count_1;
          }
          else // bit14=0
          {
            // 类型2: 直接复制
            count_1 = ((value*4) >> 2) + 1;
            qmemcpy(dst, src, count_1);
            src += count_1;
            dst += count_1;
          }
        }
        else // bit15=1
        {
          if (!__CFSHL__(2*value, 1)) // bit14=0
          {
            // 类型3: 重复填充
            count_1 = ((value*4) >> 2) + 1;
            memset(dst, value, count_1);
            dst += count_1;
          }
          else // bit14=1
          {
            // 类型4: 复杂复制（交替模式）
            count_1 = ((value*4) >> 2) + 1;
            do {
              *dst++ = value;
              *dst++ = value;
            } while (--count_1);
          }
        }
      }
      while (count);
      
      dst += v8; // 移动到下一行
      --word_627B6;
    }
    while (word_627B6);
  }
  else if ((unsigned __int16)value_1 > 0xFFu)
  {
    // 颜色偏移模式：value_1 + ((BYTE1(value_1) + v20) & 7)
    // ... 类似逻辑，但添加颜色偏移
  }
  else
  {
    // 单色填充模式：使用value_1填充
    // ... 类似逻辑，但固定使用value_1
  }
}
```

**RLE编码规则：**
```
每个字节value:
  - bit15 (CF标志): 主要类型标记
  - bit14 (CF标志): 子类型标记
  - 低6位: 计数值 = (value*4 >> 2) + 1

操作类型:
  bit15=0, bit14=0: 跳过像素（透明区域）
  bit15=0, bit14=1: 直接复制数据（memcpy）
  bit15=1, bit14=0: 重复填充（memset）
  bit15=1, bit14=1: 交替模式复制
```

**DAT文件格式分析：**
```
[文件头 6字节]
[索引表 - 每项4字节]
  - 索引0: 数据块0的起始偏移
  - 索引1: 数据块1的起始偏移
  - ...
[数据块0]
[数据块1]
[数据块2]
...
```

### 2. sub_373CA (地址: 0x373CA) - 文件读取函数

这是一个类似于fread的文件读取函数，实现了带缓冲区的读取逻辑。

```c
// 函数功能：从文件流读取数据
// 参数说明：
//   a1 - 目标缓冲区
//   a2 - 单个元素大小
//   a3 - 元素个数
//   a4 - FILE结构体指针
// 返回值：成功读取的元素个数

int __cdecl sub_373CA(_BYTE *a1, unsigned int a2, int a3, int a4)
{
  // 实现带缓冲区的文件读取
  // 处理文本模式下的CR/LF转换
  // 处理EOF标记（0x1A）
  // ...
}
```

### 3. main函数 (地址: 0x25BF4) - 主函数

主函数中多次调用sub_111BA加载各种DAT文件。

```c
int __cdecl main(int argc, const char **argv, const char **envp)
{
  // ... 初始化代码 ...
  
  // 加载FDOTHER.DAT的多个数据块
  FDOTHER_DAT__2 = (int)sub_111BA(v9, v10, n80, n16, (int)aFdotherDat, FDOTHER_DAT__2, 31);
  FDOTHER_DAT__3 = (int)sub_111BA(FDOTHER_DAT__2, v10, n80, n16, (int)aFdotherDat, FDOTHER_DAT__3, 1);
  FDOTHER_DAT__4 = (int)sub_111BA(FDOTHER_DAT__3, v10, n80, n16, (int)aFdotherDat, FDOTHER_DAT__4, 2);
  FDOTHER_DAT__5 = (int)sub_111BA(FDOTHER_DAT__4, v10, n80, n16, (int)aFdotherDat, FDOTHER_DAT__5, 3);
  FDOTHER_DAT__6 = (int)sub_111BA(FDOTHER_DAT__5, v10, n80, n16, (int)aFdotherDat, FDOTHER_DAT__6, 4);
  FDOTHER_DAT__7 = (int)sub_111BA(FDOTHER_DAT__6, v10, n80, n16, (int)aFdotherDat, FDOTHER_DAT__7, 5);
  
  // 加载FDTXT.DAT
  FDTXT_DAT__0 = (int)sub_111BA(FDOTHER_DAT__7, v10, n80, n16, (int)aFdtxtDat, FDTXT_DAT__0, 0);
  
  // 继续加载FDOTHER.DAT的其他数据块
  FDOTHER_DAT__8 = (int)sub_111BA(FDTXT_DAT__0, v10, n80, n16, (int)aFdotherDat, FDOTHER_DAT__8, 6);
  
  // ... 主循环 ...
}
```

### 4. sub_10010 (地址: 0x10010) - 存档加载函数

此函数从FD2.SAV加载存档数据，并加载相关的DAT文件。

```c
void __usercall sub_10010(...)
{
  // 分配22987字节缓冲区
  v5 = malloc(22987);
  
  // 读取FD2.SAV存档文件
  _rb_ = fopen("FD2.SAV", "rb");
  sub_373CA((_BYTE *)v5, 1u, 22987, _rb_);
  fclose(_rb_);
  
  // 校验存档数据
  sub_4DF28((char *)v5, 22987);
  if (sub_4DF09((_BYTE *)v5, 22987) != *(_DWORD *)(v5 + 22983))
  {
    // 校验失败处理
    sub_1956B(75);
    // ...
  }
  
  // 从存档中提取数据
  FDOTHER_DAT = sub_111BA(..., "FDOTHER.DAT", FDOTHER_DAT, 0);
  
  // 获取地图索引
  n17 = *(unsigned __int8 *)(v5 + 12485);
  
  // 加载FDFIELD.DAT
  FDFIELD_DAT = sub_111BA(..., "FDFIELD.DAT", FDFIELD_DAT, 3 * n17 + 2);
  
  // 分配并复制地图数据
  FDFIELD_DAT__1 = malloc(2211);
  memmove(FDFIELD_DAT__1, v5, 2211);
  
  // 加载FDTXT.DAT
  FDTXT_DAT = sub_111BA(..., "FDTXT.DAT", FDTXT_DAT, n17 + 1);
  
  // 加载FDFIELD.DAT的另一部分
  FDFIELD_DAT__0 = sub_111BA(..., "FDFIELD.DAT", FDFIELD_DAT__0, 3 * n17);
  
  // 获取地图尺寸
  dword_53AC1 = *(__int16 *)FDFIELD_DAT__0;
  n40 = *(__int16 *)(FDFIELD_DAT__0 + 2);
  
  // 加载FDSHAP.DAT
  FDSHAP_DAT = sub_111BA(..., "FDSHAP.DAT", FDSHAP_DAT, v10);
  FDSHAP_DAT__0 = sub_111BA(..., "FDSHAP.DAT", FDSHAP_DAT__0, v10 + 1);
  
  // 加载图标文件
  _rb__1 = fopen("FDICON.B24", "rb");
  // ...
  fclose(_rb__1);
}
```

### 5. sub_25EBB (地址: 0x25EBB) - 游戏状态加载函数

此函数处理游戏状态加载，包括从存档恢复数据。

```c
bool __usercall sub_25EBB(...)
{
  // ...
  
  // 加载FDOTHER.DAT索引13
  FDOTHER_DAT__11 = (int)sub_111BA(1, ..., "FDOTHER.DAT", FDOTHER_DAT__11, 13);
  
  // 加载FDOTHER.DAT索引0
  FDOTHER_DAT = (int)sub_111BA(v8, ..., "FDOTHER.DAT", FDOTHER_DAT, 0);
  
  // 分配存档缓冲区
  v10 = (unsigned __int8 *)malloc(22987);
  
  // 读取FD2.SAV
  v12 = fopen("FD2.SAV", &unk_50220);
  if ((_DWORD)v12)
  {
    sub_373CA(v10, 1u, 22987, v12);
    sub_4DF28((char *)v10, 22987);
    fclose(v13);
  }
  
  // 处理存档数据
  // ...
}
```

### 6. sub_1F894 (地址: 0x1F894) - 启动画面加载函数

此函数在程序启动时加载并显示启动画面，使用大量的DAT文件索引。

```c
void __fastcall sub_1F894(...)
{
  // 加载FDOTHER.DAT索引77
  _FDOTHER.DAT_ = sub_111BA(..., "FDOTHER.DAT", 0, 77);
  
  // 加载FDOTHER.DAT索引76
  FDOTHER_DAT = sub_111BA(..., "FDOTHER.DAT", FDOTHER_DAT, 76);
  
  // 加载FDOTHER.DAT索引74
  _FDOTHER.DAT__1 = sub_111BA(..., "FDOTHER.DAT", 0, 74);
  
  // ...
  
  // 循环加载FDOTHER.DAT索引69-73
  for (n5 = 0; n5 < 5; ++n5)
  {
    _FDOTHER.DAT__1 = sub_111BA(n5 + 69, ..., "FDOTHER.DAT", ..., n5 + 69);
    // 处理数据...
  }
  
  // 加载FDOTHER.DAT索引7
  _FDOTHER.DAT__3 = sub_111BA(..., "FDOTHER.DAT", ..., 7);
  
  // 加载FDOTHER.DAT索引8
  FDOTHER_DAT = sub_111BA(..., "FDOTHER.DAT", FDOTHER_DAT, 8);
  
  // 读取FD2.SAV检查存档状态
  _rb_ = fopen("FD2.SAV", "rb");
  if (_rb_)
  {
    v22 = malloc(22987);
    sub_373CA((_BYTE *)v22, 1u, 22987, _rb_);
    fclose(_rb_);
    // ...
  }
}
```

### 7. sub_2B996 (地址: 0x2B996) - DAT数据处理函数

此函数处理已加载的DAT数据，特别是FDOTHER.DAT的内容。

```c
void __fastcall sub_2B996(__int32 a1, int a2, int a3, int a4, int a5, int a6, int a7, int a8, unsigned __int8 a9)
{
  // 根据a9的值进行不同处理
  switch (a9)
  {
    case 3:
      // 处理类型3数据
      for (n8_1 = 0; n8_1 < 8; ++n8_1)
        dword_53F76[n8_1] = -2 * n8_1;
      break;
      
    case 4:
      // 处理类型4数据，调用sub_2EB9F
      for (n7_1 = 0; n7_1 < 7; ++n7_1)
      {
        if (dword_53F76[n7_1] == 3)
          sub_25A96(...);
        // ...
        v12 = sub_2EB9F(a6, dword_53F76[n7_1], n8, a8, -1);
      }
      break;
      
    case 5:
      // 处理类型5数据
      for (n7_2 = 0; n7_2 < 7; ++n7_2)
      {
        sub_2EB9F(a6, dword_53F76[n7_2], ...);
        if (++dword_53F76[n7_2] == 9)
          v21 = 1;
      }
      break;
  }
}
```

## 其他文件I/O相关函数

### 基础C运行时函数

| 函数名 | 地址 | 功能 |
|--------|------|------|
| fopen | 0x37324 | 打开文件，内部调用fsopen |
| _fsopen | 0x372F9 | 带共享模式打开文件 |
| open | 0x3D074 | 低级文件打开，调用sopen |
| sopen | 0x3D093 | 带共享模式打开文件 |
| read | 0x3CF9B | 低级文件读取 |
| filelength | 0x3D3A6 | 获取文件长度 |
| __MkTmpFile | 0x375FF | 创建临时文件 |
| freopen | 0x3739E | 重新打开文件 |

## 全局变量（与DAT文件相关）

| 变量名 | 描述 |
|--------|------|
| FDOTHER_DAT | FDOTHER.DAT数据指针 |
| FDOTHER_DAT__2 到 FDOTHER_DAT__11 | FDOTHER.DAT不同索引的数据指针 |
| FDTXT_DAT | FDTXT.DAT数据指针 |
| FDTXT_DAT__0 | FDTXT.DAT数据指针 |
| FDFIELD_DAT | FDFIELD.DAT数据指针 |
| FDFIELD_DAT__0 | FDFIELD.DAT数据指针 |
| FDFIELD_DAT__1 | FDFIELD.DAT数据指针 |
| FDSHAP_DAT | FDSHAP.DAT数据指针 |
| FDSHAP_DAT__0 | FDSHAP.DAT数据指针 |
| dword_53BFF | 最后加载的数据块大小 |
| dword_53AC1 | 地图宽度 |
| n40 | 地图高度 |
| n6_0 | 地图单元数量 |
| n8_1 | 地图单元数据指针 |

## 调用关系图

```
main (0x25BF4)
  └── sub_111BA - 加载DAT文件
  └── sub_25EBB - 游戏状态加载
      └── sub_111BA
      └── sub_1F894 - 启动画面
          └── sub_111BA
          └── sub_1F882
      └── sub_10010 - 存档加载
          └── sub_111BA
          └── sub_373CA - 文件读取
          └── sub_4DF28
          └── sub_4DF09
          └── sub_11019
  └── sub_117E7 - 输入处理
      └── sub_25A96
      └── sub_17AED
```

## DAT文件结构总结

### 完整格式定义

根据实际解析结果，DAT文件的格式如下：

```
偏移0-5:    文件头（6字节，固定为"LLLLLL"，即0x4C4C4C4C4C4C）
偏移6开始:  索引表
           - 每个索引项4字节（32位小端整数）
           - 索引N表示第N个数据块的起始偏移
           - 最后一个索引表示文件末尾位置
           - 索引数量 = (文件末尾偏移 - 6) / 4
索引表之后: 数据块区域
           - 数据块N的大小 = 索引[N+1] - 索引[N]
           - 数据块N的起始位置 = 索引[N]
```

### 文件头6字节说明

**发现**: 所有标准DAT文件的前6字节都是 `4C 4C 4C 4C 4C 4C` (ASCII: "LLLLLL")

**代码中的使用**:
- `sub_111BA`: `fseek(file_handle, 4 * index + 6, SEEK_SET)` - 直接跳过
- `sub_11019`: `fseek(file_handle, 6, SEEK_SET)` - 直接跳过
- `sub_20421`: `fseek(file_handle, 4 * index + 6, SEEK_SET)` - 直接跳过

**结论**: 文件头6字节从未被读取或使用，程序直接跳过，可能是预留空间或格式兼容性用途

**特例**: PASS.DAT文件头为 `436F6D706172` ("Compar")，不是标准DAT格式

### 数据块类型

| 类型 | 特征 | 说明 |
|------|------|------|
| RLE图片 | 前2字节为宽度，第3-4字节为高度 | RLE压缩的图片数据 |
| 调色板 | 大小=768字节 | 256色*3字节RGB |
| AFM动画 | 以"AFM "开头 | 动画文件，包含版权信息 |
| LMI音频 | 以"LMI1"开头 | 可能是压缩音频 |
| 嵌套DAT | 以"LLLLLL"开头 | 内部有完整的DAT结构 |
| 二进制 | 其他格式 | 各种游戏数据 |

### 各DAT文件统计

| 文件名 | 大小 | 索引数 | 数据块数 | 主要类型 |
|--------|------|--------|----------|----------|
| FDOTHER.DAT | 3.30MB | 104 | 103 | 58图片 + 45二进制 |
| FDTXT.DAT | 117KB | 35 | 34 | 34图片 |
| ANI.DAT | 2.38MB | 10 | 9 | 9个AFM动画文件 |
| FIGANI.DAT | 14.60MB | ? | ? | 角色动画 |
| FDSHAP.DAT | 3.39MB | ? | ? | 形状/精灵 |
| BG.DAT | 610KB | ? | ? | 背景 |
| FDFIELD.DAT | 237KB | ? | ? | 地图 |
| TAI.DAT | 92KB | ? | ? | 其他 |
| TITLE.DAT | 22KB | ? | ? | 标题 |
| PASS.DAT | 110B | ? | ? | 非标准格式 |

### FDOTHER.DAT关键索引

| 索引 | 大小 | 类型 | 用途 |
|------|------|------|------|
| 0 | 768 | 二进制 | 调色板 (256色*3) |
| 1 | 2,235 | 图片 | 24x24图标 |
| 7 | 23,377 | 二进制 | 嵌套DAT (LLLLLL开头) |
| 11 | 53,587 | 图片 | 320x200全屏 |
| 15 | 64,004 | 图片 | 320x200全屏 |
| 69-73 | ? | 图片 | 启动画面帧 |
| 74-77 | ? | 图片 | 启动画面帧 |
| 99-102 | ? | 图片 | 菜单/动画 |

### 示例解析

```
FDOTHER.DAT文件:
偏移0-5:    4C4C4C4C4C4C  (文件头 "LLLLLL")
偏移6:      0x000001A6    (索引0: 数据块0从偏移422开始)
偏移10:     0x000004A6    (索引1: 数据块1从偏移1190开始)
偏移14:     0x00000D61    (索引2: 数据块2从偏移3425开始)
...

数据块0:
  起始: 0x1A6 (422)
  大小: 0x4A6 - 0x1A6 = 768 字节
  内容: 调色板数据

数据块1:
  起始: 0x4A6 (1190)
  大小: 0xD61 - 0x4A6 = 2235 字节
  内容: 24x24 RLE图片
```

## 结论

1. 程序使用sub_111BA作为主要的DAT文件加载函数
2. DAT文件采用索引表+数据块的结构
3. 文件头6字节固定为"LLLLLL"，从未被使用
4. FDOTHER.DAT是最大的资源文件，包含103个数据块
5. 数据块类型包括：RLE图片、调色板、AFM动画、LMI音频等
6. 存档文件FD2.SAV大小为22987字节
7. 数据加载后存储在全局变量中供后续使用

## 分析工具

### Python解析脚本
位置: `d:\workspace\fd2_ida_hex\analyze_dat_files.py`

功能:
- 解析文件头6字节
- 提取索引表
- 识别数据块类型
- 输出详细分析结果

运行方式:
```bash
python d:\workspace\fd2_ida_hex\analyze_dat_files.py
```

### 分析结果文档
- 详细分析: `d:\workspace\fd2_ida_hex\DAT文件格式深度分析.md`
- 解析结果: `d:\workspace\fd2_ida_hex\fd2\dat_analysis_result.md`
