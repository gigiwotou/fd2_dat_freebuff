# FDOTHER.DAT 音效资产分析报告

## 概述

本文档详细分析了FD2.EXE中FDOTHER.DAT文件的音效资产，包括加载方式、播放流程、数据结构和控制参数。

---

## 1. 音效资产位置

### 1.1 主要音效数据

| 索引 | 变量名 | 用途 | 加载函数 |
|------|--------|------|----------|
| **31** | FDOTHER_DAT__2 | 主要音效 (菜单、对话、战斗等) | main函数 |
| **10** | FDOTHER_DAT__12 | 地图切换音效 | sub_26152 |

### 1.2 加载代码

```c
// main函数中加载索引31
FDOTHER_DAT__2 = (int)sub_111BA(
    v9, v10, n80, n16,
    (int)aFdotherDat,    // "FDOTHER.DAT"
    FDOTHER_DAT__2,      // 旧指针（用于释放）
    31                   // 索引号
);

// sub_26152函数中加载索引10
FDOTHER_DAT__12 = (int)sub_111BA(
    _FDSHAP.DAT_, SHIDWORD(_FDSHAP.DAT_),
    n16, n8,
    (int)aFdotherDat,
    0,
    10
);
```

---

## 2. 音效数据结构

### 2.1 FDOTHER_DAT__2文件结构

```
偏移0-5:   文件头 (6字节)
偏移6+:    目录表 (每项8字节)
           - 偏移+0: 音效起始位置 (4字节)
           - 偏移+4: 音效结束位置 (4字节)
           - 音效大小 = 结束位置 - 起始位置
目录表后:  音效数据 (WAV或PCM格式)
```

### 2.2 示例结构

```
[文件头 6字节]
[索引0: 起始=0x00000010, 结束=0x00000100] -> 大小240字节
[索引1: 起始=0x00000100, 结束=0x00000200] -> 大小256字节
[索引2: 起始=0x00000200, 结束=0x00000300] -> 大小256字节
...
[音效0数据 - 240字节]
[音效1数据 - 256字节]
[音效2数据 - 256字节]
...
```

---

## 3. 音效播放流程

### 3.1 完整播放链路

```
FDOTHER.DAT (索引31)
    ↓
sub_111BA() - 加载到内存 (不需要解密)
    ↓
FDOTHER_DAT__2 - 音效数据指针
    ↓
sub_25A96() - 音效播放控制
    ↓
sub_39805() → AIL_stop_sample() - 停止当前音效
    ↓
sub_39521() → AIL_init_sample() - 初始化音效样本
    ↓
sub_39694() → AIL_set_sample_address() - 设置音效数据地址
    ↓
sub_39AAE() → AIL_set_sample_loop_count() - 设置循环次数
    ↓
sub_39798() → AIL_start_sample() - 开始播放
    ↓
音频硬件输出
```

### 3.2 核心播放函数 sub_25A96

```c
/*
 * 函数名称: sub_25A96
 * 功能: 播放FDOTHER_DAT__2中的指定音效
 * 
 * 参数说明:
 *   a5 - FDOTHER_DAT__2 (音效数据指针)
 *   a6 - 音效索引 (-1表示不播放)
 *   a7 - 循环次数
 */
void __fastcall sub_25A96(
    __int32 a1,
    int a2,
    int a3,
    int a4,
    int a5,       // FDOTHER_DAT__2 (音效数据指针)
    int a6,       // 音效索引
    int a7        // 循环次数
)
{
    int v7, v8, v9, v10, v11, v12, v13;

    v7 = sub_3702F(a1, a2, a3, a4, 28);

    // 检查音效是否启用
    if (byte_53EF1 && byte_51E62 && !n3_9)
    {
        // 1. 停止当前播放的音效
        sub_39805(v7, dword_53EE4);  // AIL_stop_sample

        if (a6 != -1)
        {
            // 2. 计算音效数据的地址和大小
            v8 = a5 + 4 * a6;
            v13 = *(_DWORD *)(v8 + 6) + a5;   // 音效起始地址
            v12 = *(_DWORD *)(v8 + 10) - *(_DWORD *)(v8 + 6);  // 音效大小

            // 3. 初始化音效样本
            sub_39521(v12, dword_53EE4);  // AIL_init_sample

            // 4. 设置音效数据地址
            sub_39694(v9, dword_53EE4, v13, v12);  // AIL_set_sample_address

            // 5. 设置循环次数
            sub_39AAE(v10, dword_53EE4, a7);  // AIL_set_sample_loop_count

            // 6. 开始播放
            sub_39798(v11, dword_53EE4);  // AIL_start_sample
        }
    }
}
```

---

## 4. AIL音频库函数

### 4.1 包装函数映射

| 包装函数 | AIL函数 | 功能 |
|----------|---------|------|
| sub_39805 | AIL_stop_sample | 停止音效 |
| sub_39521 | AIL_init_sample | 初始化音效 |
| sub_39694 | AIL_set_sample_address | 设置音效地址 |
| sub_39AAE | AIL_set_sample_loop_count | 设置循环次数 |
| sub_39798 | AIL_start_sample | 开始播放 |

### 4.2 AIL_init_sample (sub_414E0)

```c
int *__cdecl sub_414E0(int *a1)
{
    int *result;
    int v2;

    result = a1;
    if (a1)
    {
        a1[1] = 2;            // 状态
        a1[2] = 0;            // 数据地址 (低32位)
        a1[3] = 0;            // 数据地址 (高32位)
        a1[4] = 0;            // 数据大小
        a1[5] = 0;
        a1[6] = 0;
        a1[7] = 0;
        a1[8] = 0;
        a1[9] = 1;
        a1[10] = 0;
        a1[11] = -2;
        a1[12] = 1;
        a1[13] = 0;
        a1[14] = 0;
        a1[15] = 11025;       // 采样率 (11025 Hz)
        a1[16] = v2;          // 句柄
        a1[17] = 64;          // 音量
        a1[530] = 0;          // 循环相关
        a1[531] = 0;          // 循环相关
        a1[532] = 0;          // 循环相关
        return sub_40240((int)a1);
    }
    return result;
}
```

### 4.3 AIL_set_sample_address (sub_415A0)

```c
_DWORD *__cdecl sub_415A0(_DWORD *a1, int a2, int a3)
{
    _DWORD *result;

    result = a1;
    if (a1)
    {
        a1[3] = 0;            // 数据地址 (高32位)
        a1[5] = 0;
        a1[2] = a2;           // 数据地址 (低32位)
        a1[4] = a3;           // 数据大小
    }
    return result;
}
```

### 4.4 AIL_set_sample_loop_count (sub_416E0)

```c
int __cdecl sub_416E0(int a1, int a2)
{
    int result;

    result = a1;
    if (a1)
        *(_DWORD *)(a1 + 48) = a2;  // 设置循环次数
    return result;
}
```

---

## 5. 音效参数控制

### 5.1 sub_40240 - 音效参数处理

```c
/*
 * 函数名称: sub_40240
 * 功能: 处理音效的音量和声像控制
 * 
 * 参数:
 *   a1 - 音效样本结构指针
 * 
 * 返回: 处理后的指针
 */
int *__cdecl sub_40240(int a1)
{
    int n127, n127_1, v3, v4, v26, n2, v7, v8, v9, v25;
    int v11, v12, v13, v15, v17, v18, v19, v20, v21, v23, v24;
    int *result;

    // 1. 限制音量范围 (0-127)
    n127 = *(_DWORD *)(a1 + 64);
    if (n127 > 127) n127 = 127;
    if (n127 < 0) n127 = 0;
    *(_DWORD *)(a1 + 64) = n127;

    // 2. 限制声像范围 (0-127)
    n127_1 = *(_DWORD *)(a1 + 68);
    if (n127_1 > 127) n127_1 = 127;
    if (n127_1 < 0) n127_1 = 0;
    *(_DWORD *)(a1 + 68) = n127_1;

    v3 = *(_DWORD *)(a1 + 64);
    v4 = *(_DWORD *)(a1 + 68);
    v26 = v3;
    if (v3)
        v26 = v3 + 1;

    n2 = *(_DWORD *)(*(_DWORD *)a1 + 24);

    // 3. 使用byte_5360C表进行音量衰减计算
    if (n2 == 2 || n2 == 3)
    {
        result = (int *)(a1 + 72);
        v7 = a1 + 1096;
        v8 = (unsigned __int8)byte_5360C[127 - v4];  // 左声道音量
        v9 = (unsigned __int8)byte_5360C[v4];         // 右声道音量
        v25 = v26 << 8;

        // 根据状态(2/3)设置左右声道音量表
        if ((*(_BYTE *)(a1 + 56) & 1) != 0)
        {
            // 立体声模式处理
            // ... (详细音量计算)
        }
        else
        {
            // 单声道模式处理
            // ... (详细音量计算)
        }
    }
    else
    {
        // 其他模式处理
        // ...
    }

    return result;
}
```

---

## 6. 音效使用场景

### 6.1 菜单操作音效 (sub_117E7)

```c
// 菜单上移
case 'H':
    sub_25A96(72, a1, n80_1, a5, FDOTHER_DAT__2, 0, 1);
    sub_11B48();
    break;

// 菜单下移
case 'P':
    sub_25A96(80, a1, n80_1, a5, FDOTHER_DAT__2, 0, 1);
    sub_11B9B();
    break;

// 菜单左移
case 'K':
    sub_25A96(75, a1, n80_1, a5, FDOTHER_DAT__2, 0, 1);
    sub_11C59();
    break;

// 菜单右移
case 'M':
    sub_25A96(77, a1, n80_1, a5, FDOTHER_DAT__2, 0, 1);
    sub_11BFA();
    break;
```

### 6.2 所有音效使用场景汇总

| 场景 | 调用函数 | 音效索引 | 循环次数 | 说明 |
|------|----------|----------|----------|------|
| 菜单上移 | sub_117E7 | 0 | 1 | 光标移动音效 |
| 菜单下移 | sub_117E7 | 0 | 1 | 光标移动音效 |
| 菜单左移 | sub_117E7 | 0 | 1 | 光标移动音效 |
| 菜单右移 | sub_117E7 | 0 | 1 | 光标移动音效 |
| 确认选择 | sub_117E7 | 1 | 1 | 确认音效 |
| 对话开始 | sub_117E7 | 2 | 1 | 对话音效 |
| 获取物品 | sub_117E7 | 6 | 1 | 物品音效 |
| 战斗相关 | sub_117E7 | 7 | 1 | 战斗音效 |
| 地图切换 | sub_25A96 | 动态 | 动态 | 切换音效 |
| 存档操作 | sub_26152 | 10 | 动态 | 存档音效 |

---

## 7. 音效规格汇总

| 参数 | 值 |
|------|------|
| **是否需要解密** | 不需要 |
| **音效格式** | WAV或原始PCM |
| **采样率** | 11025 Hz |
| **位深度** | 8位或16位 |
| **声道** | 单声道或立体声 |
| **播放库** | AIL (Audio Interface Library) |
| **音量范围** | 0-127 |
| **声像范围** | 0-127 (左-右) |
| **循环支持** | 是 (可设置循环次数) |
| **数据位置** | FDOTHER.DAT索引31 |
| **硬件错误提示** | "Digital sound hardware not found" |
|                  | "XMIDI sound hardware not found" |

---

## 8. 音效控制变量

| 变量 | 说明 |
|------|------|
| byte_53EF1 | 音效开关标志 |
| byte_51E62 | 音效启用标志 |
| n3_9 | 特殊模式标志 (为1时禁用音效) |
| dword_53EE4 | 当前音效样本句柄 |

---

## 9. 音效数据提取方法

### 9.1 从FDOTHER.DAT提取音效

```c
// 1. 加载FDOTHER.DAT
data = sub_111BA(..., "FDOTHER.DAT", 0, 31);

// 2. 获取音效索引表
// 目录表从偏移6开始，每项8字节
// 项0: 起始=*(DWORD*)(data+6), 结束=*(DWORD*)(data+10)

// 3. 提取指定音效
sound_start = *(DWORD*)(data + 4*index + 6) + data;
sound_end = *(DWORD*)(data + 4*index + 10) + data;
sound_size = sound_end - sound_start;

// 4. 保存音效到文件
fwrite(sound_start, 1, sound_size, output_file);
```

### 9.2 Python提取脚本

```python
import struct

def extract_sounds(fdother_dat_path, output_dir):
    with open(fdother_dat_path, 'rb') as f:
        data = f.read()
    
    # 跳过文件头6字节
    offset = 6
    
    # 读取索引表 (假设最多256个音效)
    sounds = []
    while offset + 8 <= len(data):
        start = struct.unpack('<I', data[offset:offset+4])[0]
        end = struct.unpack('<I', data[offset+4:offset+8])[0]
        
        if start == 0 and end == 0:
            break
        
        sounds.append((start, end))
        offset += 8
        
        # 如果下一个偏移超出数据范围，说明索引表结束
        if offset >= len(data):
            break
    
    # 提取每个音效
    for i, (start, end) in enumerate(sounds):
        sound_data = data[start:end]
        output_path = f"{output_dir}/sound_{i:03d}.raw"
        with open(output_path, 'wb') as f:
            f.write(sound_data)
        print(f"Extracted sound {i}: {len(sound_data)} bytes")
```

---

## 10. 关键发现

1. **音效不需要解密** - 数据直接存储在FDOTHER.DAT中，加载后即可使用
2. **使用AIL音频库** - 支持多种音频硬件 (SoundBlaster, AdLib等)
3. **采样率11025Hz** - DOS时代标准的中等质量音效
4. **支持立体声** - 通过声像控制实现左右声道
5. **支持循环播放** - 可设置循环次数
6. **音量控制** - 通过查找表(byte_5360C)进行音量衰减
7. **硬件检测** - 有数字音效和XMIDI硬件检测

---

*分析完成日期: 2026-05-04*
*分析方法: IDA Pro MCP + 汇编代码分析*
