# FDOTHER.DAT 完整解析报告

## 概述

FDOTHER.DAT是FD2游戏的主要资源文件，包含422个索引的资源。本文档记录了所有资源的解析结果。

## 文件格式

### DAT文件结构
```
[0-5字节]    "LLLLLL" 文件头 (6字节)
[6字节开始]  索引表 (每项4字节，仅包含偏移值)
[索引表后]   资源数据块
```

### 资源读取方式
根据IDA Pro MCP分析 `sub_111BA` 函数：
1. 定位索引表：`fseek(file, 4 * index + 6, SEEK_SET)`
2. 读取2个DWORD（8字节）：当前资源偏移和下一个资源偏移
3. 计算大小：`size = offset[index+1] - offset[index]`
4. 读取资源：定位到 `offset[index]`，读取 `size` 字节

## 调色板

FDOTHER.DAT包含多个调色板资源：

| 索引 | 大小 | 说明 |
|------|------|
| 0 | 768字节 | 主调色板（256色） |
| 8 | 768字节 | 调色板副本 |
| 57 | 768字节 | 调色板副本 |
| 76 | 768字节 | 调色板副本 |
| 99 | 768字节 | 调色板副本 |
| 101 | 768字节 | 调色板副本 |
| 102 | 768字节 | 调色板副本 |

### 调色板格式
```
[0-2字节]   颜色0 (R, G, B) - 6位颜色值
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

## Tile数据结构

### 直接索引Tile格式
```
[0-1字节]  宽度 (2字节，小端序)
[2-3字节]  高度 (2字节，小端序)
[4字节起]  RLE压缩的像素数据
```

### 嵌套DAT Tile格式
```
[0-1字节]  宽度 (2字节，小端序)
[2-3字节]  高度 (2字节，小端序)
[4字节]    调色板窗口偏移值 (1字节)
[5字节起]  RLE压缩的像素数据
```

## RLE解压缩算法

根据IDA Pro MCP分析 `sub_4E98D` 函数：

### 控制字节格式

| Bit 7 | Bit 6 | 模式 | 说明 |
|-------|-------|------|------|
| 0 | X | 填充 | 用指定颜色填充 `((value & 0x3F) + 1)` 个像素 |
| 1 | 0 | 复制 | 从源数据复制 `((value & 0x3F) + 1)` 个字节 |
| 1 | 1 | 跳过 | 跳过 `((value & 0x3F) + 1)` 个像素位置 |

## sub_2EB9F函数行为

根据IDA Pro MCP分析，`sub_2EB9F` 函数的第三个参数（value）用于调色板窗口偏移：
- 当处理嵌套DAT中的tile时，该参数值等于tile数据中offset+4处的字节值
- 在渲染时，将像素值映射到调色板的特定窗口：`displayed_color = palette[(window_offset + pixel_value) % 256]`
- 这样实现了使用调色板的不同部分来渲染同一组像素数据（调色板窗口技术）

## 直接索引资源

### 主要Tile图像（320x200）

| 索引 | 尺寸 | 说明 |
|------|------|------|
| 11 | 320x200 | 全屏图像 |
| 15 | 320x200 | 全屏图像 |
| 55 | 320x200 | 全屏图像 |
| 56 | 320x200 | 全屏图像 |
| 61 | 320x200 | 全屏图像 |
| 62 | 320x200 | 全屏图像 |
| 74 | 320x200 | 全屏图像 |
| 75 | 320x200 | 全屏图像 |
| 97 | 320x200 | 全屏图像 |
| 100 | 320x200 | 全屏图像 |

### 中等尺寸图像（320x147）

| 索引 | 尺寸 | 说明 |
|------|------|------|
| 69 | 320x147 | 中等图像 |
| 70 | 320x147 | 中等图像 |
| 71 | 320x147 | 中等图像 |
| 72 | 320x147 | 中等图像 |
| 73 | 320x147 | 中等图像 |

### 其他Tile图像

| 索引 | 尺寸 | 非零像素 | 说明 |
|------|------|---------|------|
| 1 | 24x24 | 248/576 | 小图标 |
| 10 | 62x26 | 551/1612 | 小图标 |
| 18 | 16x16 | 77/256 | 小图标 |
| 19 | 30x30 | 197/900 | 小图标 |
| 20 | 16x16 | 86/256 | 小图标 |
| 21 | 30x30 | 217/900 | 小图标 |
| 22 | 14x14 | 39/196 | 小图标 |
| 23 | 14x14 | 39/196 | 小图标 |
| 24 | 12x12 | 22/144 | 小图标 |
| 25 | 12x12 | 24/144 | 小图标 |
| 26 | 18x18 | 119/324 | 小图标 |
| 27 | 18x18 | 99/324 | 小图标 |
| 28 | 32x32 | 341/1024 | 小图标 |
| 30 | 32x32 | 191/1024 | 小图标 |
| 32 | 10x10 | 32/100 | 小图标 |
| 33 | 10x10 | 7/100 | 小图标 |
| 34 | 101x101 | 7413/10201 | 中等图标 |
| 37 | 5x5 | 4/25 | 微小图标 |
| 38 | 5x5 | 4/25 | 微小图标 |
| 39 | 33x33 | 338/1089 | 小图标 |
| 42 | 312x192 | 59904/59904 | 大图像 |
| 43 | 33x33 | 383/1089 | 小图标 |
| 44 | 31x31 | 342/961 | 小图标 |
| 45 | 59x59 | 2803/3481 | 中等图标 |
| 54 | 111x111 | 11970/12321 | 中等图标 |
| 58 | 20x20 | 234/400 | 小图标 |
| 65 | 5x5 | 2/25 | 微小图标 |
| 66 | 14x14 | 89/196 | 小图标 |
| 67 | 9x9 | 20/81 | 小图标 |
| 68 | 9x9 | 40/81 | 小图标 |
| 96 | 24x24 | 32/576 | 小图标 |
| 98 | 155x30 | 4650/4650 | 长条图像 |

## 嵌套DAT资源

FDOTHER.DAT包含29个嵌套DAT资源：

### 嵌套DAT格式
嵌套DAT同样使用 "LLLLLL" 魔数，具有与主DAT相同的结构。

### 索引7（嵌套DAT）
- 包含多个tile图像
- tile[0]: 320x200（全屏图像）
- tile[1-6]: 61x7到62x8的小图标
- tile[1] 使用调色板窗口偏移 0x01
- tile[2] 使用调色板窗口偏移 0x11
- tile[3] 使用调色板窗口偏移 0x01
- tile[4] 使用调色板窗口偏移 0x08
- tile[5] 使用调色板窗口偏移 0x01

### 索引12（嵌套DAT）
- 包含122个资源
- tile[1] 使用调色板窗口偏移 0x49 (73)
- tile[15] 使用调色板窗口偏移 0x60 (96)
- tile[16-22] 使用各种调色板窗口偏移（0x49, 0xC3, 0xFF等）

### 索引63（嵌套DAT）
- 包含130个资源
- tile[1] 使用调色板窗口偏移 0x49 (73)
- tile[15] 使用调色板窗口偏移 0x60 (96)
- tile[16-22] 使用各种调色板窗口偏移（0x49, 0xC3, 0xFF等）

### 嵌套DAT中tile的处理方法
嵌套DAT中的tile需要使用调色板窗口技术来正确显示：
1. 解压RLE数据获得原始像素索引
2. 将每个像素索引映射到调色板的特定窗口：`displayed_color = palette[(window_offset + pixel_value) % 256]`
3. 其中window_offset是tile数据中offset+4处的字节值（sub_2EB9F函数的value参数）

## 正确的渲染算法

对于嵌套DAT中的tile，正确的渲染步骤如下：

```python
def render_nested_tile(tile_data, base_palette):
    # 解析tile数据
    width = struct.unpack_from('<H', tile_data, 0)[0]
    height = struct.unpack_from('<H', tile_data, 2)[0]
    window_offset = tile_data[4]  # sub_2EB9F函数的value参数
    rle_data = tile_data[5:]
    
    # RLE解压缩
    pixels = decompress_rle(rle_data, width, height)
    
    # 应用调色板窗口技术
    image = Image.new('RGB', (width, height))
    for i, pixel_value in enumerate(pixels):
        # 将像素值映射到调色板窗口
        palette_index = (window_offset + pixel_value) % 256
        image.putpixel((i % width, i // width), base_palette[palette_index])
    
    return image
```

## 尝试过的方法及最终解决方案

### 早期尝试的方法（均不正确）
1. **像素索引偏移**：`new_pixel = (original_pixel + color_shift) % 256`
2. **调色板旋转**：`rotated_palette[i] = original_palette[(i - color_shift) % 256]`
3. **调色板移位**：调整颜色值的亮度
4. **调色板内容移位**：`shifted_palette[i] = original_palette[(color_shift + i) % 256]`

### 正确的方法：调色板窗口技术
- 将sub_2EB9F函数的value参数作为调色板窗口的起始偏移量
- 公式：`displayed_color = palette[(window_offset + pixel_value) % 256]`
- 这种方法允许使用相同的像素数据，但通过改变窗口偏移量来显示不同的颜色主题

## 工具脚本

| 脚本 | 功能 |
|------|------|
| `extract_all_fdother_complete.py` | 提取所有tile图像（直接+嵌套） |
| `apply_palette_v2.py` | 应用调色板到图像 |
| `final_fdother_parser.py` | 完整解析器（包含颜色索引偏移处理） |
| `systematic_test.py` | 系统性测试多种处理方法 |
| `palette_transform_test.py` | 测试调色板变换方法 |
| `palette_window_approach.py` | 使用调色板窗口技术的正确方法 |

## 输出目录

| 目录 | 内容 |
|------|------|
| `output/fdother_all_tiles/` | 第一次提取的tile图像 |
| `output/fdother_all_tiles_v2/` | 完整提取的tile图像（114个） |
| `output/nested_dat_tiles_v4/` | 嵌套DAT索引63的tile图像 |
| `output/nested_dat_tiles_v4_colored_v2/` | 应用调色板后的彩色图像 |
| `output/nested_dat_tiles_v5_rle/` | 使用RLE解压缩的tile图像 |
| `output/nested_dat_tiles_v5_rle_colored_v2/` | RLE解压缩+调色板的彩色图像 |
| `output/final_extracted_tiles/` | 最终提取的tile图像（包含颜色索引偏移） |
| `output/systematic_test/` | 多种处理方法的测试图像 |
| `output/palette_window_approach/` | 使用调色板窗口技术的正确渲染结果 |

## 关键发现

1. **直接索引tile**：使用`[w:2][h:2][rle_data...]`结构，直接用调色板0正确显示
2. **嵌套DAT**：使用`'LLLLLL'`魔数，内部包含多个资源
3. **嵌套DAT tile**：使用`[w:2][h:2][window_offset:1][rle_data...]`结构，其中第5个字节（offset+4）是调色板窗口偏移值
4. **sub_2EB9F函数行为**：其value参数用于调色板窗口偏移，实现调色板窗口技术
5. **最终解决方案**：使用调色板窗口技术 `palette[(window_offset + pixel_value) % 256]`

## 参考

- IDA Pro MCP分析：`sub_111BA` (DAT加载函数)
- IDA Pro MCP分析：`sub_4E98D` (RLE解压缩函数)
- IDA Pro MCP分析：`sub_2EB9F` (渲染函数，处理调色板窗口偏移)
- FD2游戏DAT文件：`bin/FDOTHER.DAT`