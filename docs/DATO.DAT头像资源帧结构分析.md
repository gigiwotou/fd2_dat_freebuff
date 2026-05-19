# DATO.DAT 头像资源帧结构分析

## 概述

DATO.DAT 文件包含游戏头像资源，共 **554个资源**，文件大小 **1.89MB**。每个头像是 **80x80像素** 的动画序列。

## 文件结构

```
DATO.DAT 文件:
  [0-5]    文件头 "LLLLLL" (6字节)
  [6-9]    资源数量 DWORD (554)
  [10...]  偏移表 (每项4字节，N+1项)
  [偏移表后] 资源数据块
```

## 资源内部结构

每个资源包含 **3帧动画**（通过头部大小=16确定）：

```
资源格式:
  [0-3]    DWORD: 头部大小 (通常是16)
  [4-7]    DWORD: 帧0相对偏移
  [8-11]   DWORD: 帧1相对偏移
  [12-15]  DWORD: 帧2相对偏移
  [16-17]  WORD:  宽度 (80)
  [18-19]  WORD:  高度 (80)
  [字节20开始] 像素数据
```

## 帧数据格式

每帧数据从偏移位置开始：

```
帧格式:
  [0-1]   WORD: 宽度 (80)
  [2-3]   WORD: 高度 (80)
  [4...]  RLE压缩的像素数据
```

## RLE压缩算法

使用 **0xC0-0xFF** 作为RLE转义标记：

```
解码规则:
  - 如果字节 < 0xC0: 字面量像素值
  - 如果字节 >= 0xC0: RLE序列
      count = byte & 0x3F
      if count == 0: count = 64
      pixel = 下一个字节
      输出 count 个 pixel 值
```

### 示例

```
压缩数据: C5 4A C1 FE 3E D1 3F 3E
解码:
  C5 -> RLE: count=5, pixel=0x4A(74) -> [74,74,74,74,74]
  C1 -> RLE: count=1, pixel=0xFE(254) -> [254]
  3E -> 字面量: 62
  D1 -> RLE: count=17, pixel=0x3F(63) -> [63,63,...,63] (17个)
  3E -> 字面量: 62
```

### 压缩统计

- 压缩比: ~50% (3150字节压缩 -> 6400像素)
- 高频RLE count值: 1, 2, 3, 4
- 常见像素值范围: 58-63, 193-197

## 解码示例代码

```python
import struct

def decode_portrait_frame(compressed_data):
    """解码一帧RLE压缩的头像数据"""
    decoded = []
    i = 0
    while i < len(compressed_data):
        byte = compressed_data[i]
        if byte >= 0xC0:
            if i + 1 < len(compressed_data):
                count = byte & 0x3F
                if count == 0:
                    count = 64
                pixel = compressed_data[i + 1]
                decoded.extend([pixel] * count)
                i += 2
            else:
                break
        else:
            decoded.append(byte)
            i += 1
    return decoded

def load_portrait(dato_data, index):
    """加载头像资源"""
    # 解析文件头
    count = struct.unpack('<I', dato_data[6:10])[0]
    if index >= count - 1:
        return None
    
    # 获取资源偏移
    off_start = struct.unpack('<I', dato_data[10 + index * 4: 14 + index * 4])[0]
    off_end = struct.unpack('<I', dato_data[10 + (index + 1) * 4: 14 + (index + 1) * 4])[0]
    
    res_data = dato_data[off_start:off_end]
    
    # 解析资源头部
    header_size = struct.unpack('<I', res_data[0:4])[0]
    frame_offsets = []
    for i in range(3):
        offset = struct.unpack('<I', res_data[4 + i*4: 8 + i*4])[0]
        frame_offsets.append(offset)
    
    width = struct.unpack('<H', res_data[16:18])[0]
    height = struct.unpack('<H', res_data[18:20])[0]
    
    # 解码所有帧
    frames = []
    for i, offset in enumerate(frame_offsets):
        # 跳过帧内部的宽高4字节
        next_offset = frame_offsets[i+1] if i < 2 else len(res_data)
        compressed = res_data[offset+4:next_offset]
        pixels = decode_portrait_frame(compressed)
        frames.append(pixels)
    
    return {
        'width': width,
        'height': height,
        'frames': frames,
        'num_frames': len(frames)
    }
```

## 重要发现

1. **帧数**: 所有资源都是 **3帧** 动画（头部大小=16）
2. **像素尺寸**: 80x80 像素
3. **解码后大小**: 每帧 6400 字节
4. **压缩数据大小**: 约 3150 字节/帧
5. **调色板**: 使用8位索引颜色（0-254）
6. **帧关系**: 3帧通常是不同的动画序列

## 资源0示例

```
资源0:
  头部大小: 16
  帧0偏移: 3165, 大小: 3163字节 -> 解码6400像素
  帧1偏移: 6328, 大小: 3184字节 -> 解码6400像素
  帧2偏移: 9512, 大小: 3153字节 -> 解码6400像素
  宽高: 80x80
```

## 可视化输出

解码后的头像可以用ASCII字符可视化：

```
行 0: |+++++#+++++++++++++++++++++-#+++++++++++#-----++#+--+##++-------++#++++++++-----|
行 1: |++++#-+++++######+++++++++-#+++++++++++++#----+++#+--++#++-------++##++++++-----|
行 2: |+++#---++##++++++##++++++--#++++++++++++++#----++#++-+++##+-------+++#++++++----|
...
```

## 调色板

头像使用FDOTHER.DAT索引75的调色板（256色）。

## 注意事项

- 字节20之后的数据是帧0的像素数据（不是额外的帧偏移）
- 所有检查的资源头部大小都是16，确认只有3帧
- 如果用户需要4帧循环，可能需要在游戏逻辑层面实现（如重复最后一帧）

## 工具脚本

分析工具位于 `tools/` 目录：
- `analyze_dato_frames.py` - 基本帧结构分析
- `analyze_dato_final.py` - RLE解码验证
- `verify_structure.py` - 结构一致性验证
- `check_4th_frame.py` - 第4帧检查

## 更新日期

2026-05-19
