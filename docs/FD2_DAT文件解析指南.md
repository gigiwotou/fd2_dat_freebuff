# FD2游戏DAT文件解析完整指南

## 概述

本文档记录FD2游戏DAT文件的完整解析过程，包括索引表读取、嵌套DAT处理、RLE解压缩算法和调色板应用。

## DAT文件标准格式

### 文件结构

```
[0-5字节]    "LLLLLL" 文件头 (6字节)
[6字节开始]  索引表 (每项4字节，仅包含偏移值)
[索引表后]   资源数据块
```

### 索引表读取方式

根据IDA Pro MCP分析 `sub_111BA` 函数，DAT文件的读取方式是：

1. **定位索引表**：`fseek(file, 4 * index + 6, SEEK_SET)`
2. **读取2个DWORD**（8字节）：当前资源偏移和下一个资源偏移
3. **计算大小**：`size = offset[index+1] - offset[index]`
4. **读取资源**：定位到 `offset[index]`，读取 `size` 字节

### Python实现

```python
def read_dat_resource(file_data, base_offset, index):
    """读取DAT文件中的资源"""
    index_offset = base_offset + 4 * index + 6
    offset0 = struct.unpack_from('<I', file_data, index_offset)[0]
    offset1 = struct.unpack_from('<I', file_data, index_offset + 4)[0]
    size = offset1 - offset0
    if size <= 0 or offset0 >= len(file_data):
        return None, 0, 0
    resource_data = file_data[offset0:offset0 + size]
    return resource_data, offset0, size
```

## 嵌套DAT结构

某些资源（如索引63）本身也是DAT格式，称为嵌套DAT。

### 嵌套DAT解析

1. 先读取外部DAT的资源数据
2. 将资源数据作为新的DAT文件解析
3. 嵌套DAT同样使用标准DAT读取方式

```python
# 读取嵌套DAT的资源
nested_data, _, _ = read_dat_resource(external_dat_data, 0, nested_index)

# 如果嵌套数据也是DAT格式，继续解析
if nested_data[:6] == b"LLLLLL":
    nested_count = struct.unpack_from('<I', nested_data, 6)[0]
    # 读取嵌套DAT的资源
    tile_data, _, _ = read_dat_resource(nested_data, 0, tile_index)
```

## RLE解压缩算法

### sub_4E98D 函数分析

根据IDA Pro MCP分析，`sub_4E98D` 是RLE解压缩函数。

#### 控制字节格式

| Bit 7 | Bit 6 | 模式 | 说明 |
|-------|-------|------|------|
| 0 | X | 填充 | 用指定颜色填充 `((value & 0x3F) + 1)` 个像素 |
| 1 | 0 | 复制 | 从源数据复制 `((value & 0x3F) + 1)` 个字节 |
| 1 | 1 | 跳过 | 跳过 `((value & 0x3F) + 1)` 个像素位置 |

#### Python实现

```python
def decompress_sub_4E98D(src_data, width, height, stride, value_1=-1):
    """
    RLE解压缩函数
    
    参数:
    - src_data: RLE压缩数据 (不包含w,h头)
    - width: 图像宽度
    - height: 图像高度  
    - stride: 行宽 (通常等于width)
    - value_1: 颜色模式 (-1=原始颜色, 0-255=固定颜色, >255=调色板偏移)
    """
    output_size = stride * height
    output = bytearray(output_size)
    
    src_pos = 0
    src_len = len(src_data)
    
    row_start = 0  # 当前行起始位置
    col_pos = 0    # 当前行已写入的像素数
    current_row = 0
    
    while current_row < height and src_pos < src_len:
        ctrl = src_data[src_pos]
        src_pos += 1
        
        count = (ctrl & 0x3F) + 1
        
        if ctrl & 0x80:  # Bit 7 = 1
            if ctrl & 0x40:  # Bit 6 = 1: 跳过
                col_pos += count
            else:  # Bit 6 = 0: 复制
                for i in range(count):
                    if src_pos < src_len and col_pos < width:
                        pixel = src_data[src_pos]
                        src_pos += 1
                        out_pos = row_start + col_pos
                        if value_1 == -1:
                            output[out_pos] = pixel
                        col_pos += 1
        else:  # Bit 7 = 0: 填充
            if src_pos < src_len:
                fill_value = src_data[src_pos]
                src_pos += 1
                for i in range(count):
                    if col_pos < width:
                        out_pos = row_start + col_pos
                        output[out_pos] = fill_value
                        col_pos += 1
        
        if col_pos >= width:
            current_row += 1
            row_start += stride
            col_pos = 0
    
    return bytes(output)
```

## Tile数据结构

### 格式

```
[0-1字节]  宽度 (2字节，小端序)
[2-3字节]  高度 (2字节，小端序)
[4字节起]  RLE压缩的像素数据
```

### 解析流程

1. 读取宽度和高度
2. 读取RLE压缩数据（从偏移4开始）
3. 使用 `sub_4E98D` 解压缩
4. 应用调色板

## 调色板处理

### 调色板位置

FDOTHER.DAT 索引0 是主要的256色调色板（768字节）。

### 调色板格式

```
[0-2字节]   颜色0 (R, G, B)
[3-5字节]   颜色1 (R, G, B)
...
[765-767]   颜色255 (R, G, B)
```

### 颜色值转换

FD2使用6位颜色值（0-63），需要扩展到8位（0-255）：

```python
def convert_6bit_to_8bit(value):
    return (value << 2) | (value >> 4)
```

### 应用调色板

```python
# 读取调色板
palette_data, _, _ = read_dat_resource(dat_data, 0, 0)

# 解析调色板
palette_rgb = []
for i in range(256):
    r = palette_data[i * 3]
    g = palette_data[i * 3 + 1]
    b = palette_data[i * 3 + 2]
    r = (r << 2) | (r >> 4)
    g = (g << 2) | (g >> 4)
    b = (b << 2) | (b >> 4)
    palette_rgb.append((r, g, b))

# 应用调色板到图像
img_rgb = Image.new('RGB', (w, h))
for y in range(h):
    for x in range(w):
        pal_idx = decompressed[y * w + x]
        img_rgb.putpixel((x, y), palette_rgb[pal_idx])
```

## 完整提取流程

### 提取嵌套DAT中的Tile图像

```python
import struct
from PIL import Image

# 1. 读取主DAT
with open('FDOTHER.DAT', 'rb') as f:
    dat_data = f.read()

# 2. 读取索引63（嵌套DAT）
nested_data, _, _ = read_dat_resource(dat_data, 0, 63)

# 3. 读取调色板
palette_data, _, _ = read_dat_resource(dat_data, 0, 0)
palette_rgb = parse_palette(palette_data)

# 4. 提取tile图像
for i in range(20):
    tile_data, _, _ = read_dat_resource(nested_data, 0, i)
    
    w = struct.unpack_from('<H', tile_data, 0)[0]
    h = struct.unpack_from('<H', tile_data, 2)[0]
    
    rle_data = tile_data[4:]
    decompressed = decompress_sub_4E98D(rle_data, w, h, w, -1)
    
    # 创建图像并应用调色板
    img = Image.new('RGB', (w, h))
    for y in range(h):
        for x in range(w):
            pal_idx = decompressed[y * w + x]
            img.putpixel((x, y), palette_rgb[pal_idx])
    
    img.save(f'tile_{i}.png')
```

## 工具脚本

| 脚本 | 功能 |
|------|------|
| `extract_nested_dat_correct.py` | 正确读取DAT文件并提取资源 |
| `extract_with_correct_rle.py` | 实现RLE解压缩并提取tile图像 |
| `apply_palette_v2.py` | 应用调色板到灰度图像 |

## 输出目录

| 目录 | 内容 |
|------|------|
| `output/nested_dat_tiles_v4/` | 灰度tile图像 |
| `output/nested_dat_tiles_v4_colored_v2/` | 应用调色板后的彩色图像 |

## 参考

- IDA Pro MCP分析：`sub_111BA` (DAT加载函数)
- IDA Pro MCP分析：`sub_4E98D` (RLE解压缩函数)
- FD2游戏DAT文件：`bin/FDOTHER.DAT`
