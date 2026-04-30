# FD2 地图数据格式分析

## 概述

本文档记录了通过 IDA MCP 反编译分析得到的《炎龙骑士团2》（FD2）地图数据格式的完整知识。

关键函数：
- `sub_1088D` (0x1088D): 地图加载函数
- `sub_4DF4C` (0x4DF4C): 地形ID处理函数

---

## 一、FDFIELD.DAT 地图文件结构

### 1.1 文件头结构

```
偏移 0-5: 魔数 "LLLLLL" (6 字节)
偏移 6+:  资源偏移表（每个条目 4 字节，小端序）
```

**注意：** FDFIELD.DAT 没有显式的资源计数字段，偏移表直接从偏移 6 开始。

### 1.2 地图资源索引

每个地图使用 **3 个连续资源**：

| 资源索引 | 内容 | 说明 |
|---------|------|------|
| `3 * map_id` | Layout 数据 | 地图瓦片布局 |
| `3 * map_id + 1` | Control 数据 | 地图控制信息（地形集ID等） |
| `3 * map_id + 2` | Spawn 数据 | 角色出生位置 |

### 1.3 Layout 数据结构

```c
// 偏移 0: 地图宽度 (2 字节，小端序)
// 偏移 2: 地图高度 (2 字节，小端序)
// 偏移 4+: 瓦片数据（每个瓦片 4 字节）

struct TileData {
    uint8_t event_id;      // byte[0]: 事件ID
    uint8_t terrain_low;   // byte[1]: 地形ID低2位 (& 3)
    uint8_t terrain_high;  // byte[2]: 地形ID高5位 (& 0x1F)
    uint8_t reserved;      // byte[3]: 固定值 0xFF
};
```

**地形ID计算公式：**
```c
terrain_id = (byte[2] & 0x1F) << 2 | (byte[1] & 3)
```
地形ID范围：0-127（7位）

### 1.4 Control 数据结构

```c
struct ControlData {
    uint8_t terrain_set_id;  // byte[0]: 地形集ID (0-7)
    uint8_t ally_max;        // byte[1]: 己方最大出场人数
    uint8_t enemy_total;     // byte[2]: 敌友出场人物总数
    // ... 后续为事件、宝箱、出场人物等数据
};
```

---

## 二、FDSHAP.DAT 瓦片图像文件结构

### 2.1 文件头结构

```
偏移 0-5: 魔数 "LLLLLL" (6 字节)
偏移 6-9: 资源数量 (4 字节，小端序)
偏移 10+: 资源偏移表（每个条目 4 字节）
```

### 2.2 资源配对

FDSHAP.DAT 中的资源成对出现：

| 资源索引 | 内容 | 大小 |
|---------|------|------|
| `terrain_set_id * 2` | 调色板 | 1200 字节 |
| `terrain_set_id * 2 + 1` | 瓦片图像集 | 可变大小 |

### 2.3 调色板资源结构

```
大小: 1200 字节
- 前 768 字节: 256 色调色板（6-bit RGB，每颜色 3 字节）
- 后 432 字节: 元数据
```

**6-bit 转 8-bit 转换公式：**
```c
r8 = (r6 << 2) | (r6 >> 4)
g8 = (g6 << 2) | (g6 >> 4)
b8 = (b6 << 2) | (b6 >> 4)
```

### 2.4 瓦片图像集结构

```c
struct TileSet {
    uint16_t tile_width;     // 字节 0-1: 瓦片宽度（通常 24）
    uint16_t tile_height;    // 字节 2-3: 瓦片高度（通常 24）
    uint16_t first_offset;   // 字节 4-5: 第一个瓦片数据的偏移
    // 字节 6+: 瓦片偏移表（每 4 字节一个条目）
    // 瓦片数据: RLE 压缩的像素数据
};

// 瓦片偏移表条目格式（从字节 6 开始，每 4 字节）
struct TileOffsetTable {
    uint16_t offset;         // 瓦片数据偏移
    uint16_t zero;           // 固定值 0
};
```

### 2.5 RLE 解压缩算法

```c
void rle_decompress(uint8_t* src, uint8_t* dst, int width, int height) {
    int p = 0;
    for (int row = 0; row < height; row++) {
        int count = width;
        while (count > 0) {
            uint8_t value = src[p++];
            int count_1 = (value & 0x3F) + 1;
            int bit7 = (value >> 7) & 1;
            int bit6 = (value >> 6) & 1;
            
            if (bit7 && bit6) {
                // Skip pixels
                count -= count_1;
            } else if (bit7 && !bit6) {
                // Copy pixels
                for (int i = 0; i < count_1 && count > 0; i++) {
                    dst[row * width + (width - count)] = src[p++];
                    count--;
                }
            } else if (!bit7 && bit6) {
                // Duplicate every other pixel
                uint8_t fill = src[p++];
                for (int i = 0; i < count_1 && count > 0; i++) {
                    dst[row * width + (width - count)] = fill;
                    count -= 2;
                }
            } else {
                // Fill with single pixel
                uint8_t fill = src[p++];
                for (int i = 0; i < count_1 && count > 0; i++) {
                    dst[row * width + (width - count)] = fill;
                    count--;
                }
            }
        }
    }
}
```

---

## 三、IDA 反编译关键函数

### 3.1 sub_1088D - 地图加载函数

```c
int __fastcall sub_1088D(__int32 a1, int a2, int a3, int a4, int n13) {
    // 加载 FDTXT.DAT
    FDTXT_DAT = sub_111BA(n13 + 1, ..., "FDTXT.DAT", ...);
    
    // 计算地图资源索引
    v6 = 3 * n13;
    
    // 加载地图资源
    FDFIELD_DAT = sub_111BA(3 * n13 + 2, ..., "FDFIELD.DAT", ...);
    FDFIELD_DAT__1 = sub_111BA(v6 + 1, ..., "FDFIELD.DAT", ...);   // Control
    FDFIELD_DAT__0 = sub_111BA(v6, ..., "FDFIELD.DAT", ...);      // Layout
    
    // 解析地图尺寸
    v7 = *(__int16 *)FDFIELD_DAT__0;                              // Width
    n40 = *(__int16 *)(FDFIELD_DAT__0 + 2);                       // Height
    
    // 计算地形集资源索引
    v8 = 2 * *(unsigned __int8 *)FDFIELD_DAT__1;                  // terrain_set_id * 2
    
    // 加载 FDSHAP 资源
    FDSHAP_DAT = sub_111BA(v8, ..., "FDSHAP.DAT", ...);           // Palette
    FDSHAP_DAT__0 = sub_111BA(v8 + 1, ..., "FDSHAP.DAT", ...);    // Tiles
    
    // 处理地图数据
    sub_4DF4C((unsigned __int8 *)FDFIELD_DAT__0);
    
    // ... 后续处理
}
```

### 3.2 sub_4DF4C - 地形ID处理函数

```c
char __cdecl sub_4DF4C(unsigned __int8 *a1) {
    int v1;        // 瓦片总数 = width * height
    unsigned __int8 *v2;  // 指向瓦片数据
    
    v1 = (unsigned __int16)(a1[2] * *a1);  // height * width
    v2 = a1 + 4;                            // 跳过 4 字节头 (width + height)
    
    result = -1;
    do {
        v2[3] = -1;      // byte[3] = 0xFF
        v2[2] &= 0x1Fu;  // byte[2] (地形ID高字节) 保留低5位
        v2[1] &= 3u;     // byte[1] (地形ID低字节) 保留低2位
        v2 += 4;         // 下一个瓦片 (4 字节/瓦片)
        --v1;
    } while (v1);
    
    return result;
}
```

**关键说明：**
- 每个瓦片占用 4 字节
- 地形ID使用 7 位（低2位 + 高5位），范围 0-127
- byte[3] 被固定设置为 0xFF

---

## 四、地图生成流程

### 4.1 Python 实现

```python
import struct
from PIL import Image

def parse_fdfield(data: bytes):
    """解析 FDFIELD.DAT"""
    magic = data[:6]
    assert magic == b"LLLLLL"
    
    # 读取资源偏移表
    resource_offsets = []
    pos = 6
    while pos + 4 <= len(data):
        offset = struct.unpack_from("<I", data, pos)[0]
        if offset > pos and offset < len(data):
            resource_offsets.append(offset)
        else:
            break
        pos += 4
    
    return {
        "resource_count": len(resource_offsets),
        "offsets": resource_offsets
    }

def parse_fdshap(data: bytes):
    """解析 FDSHAP.DAT"""
    magic = data[:6]
    assert magic == b"LLLLLL"
    
    resource_count = struct.unpack_from("<I", data, 6)[0]
    resource_offsets = []
    for i in range(resource_count):
        offset = struct.unpack_from("<I", data, 10 + i * 4)[0]
        resource_offsets.append(offset)
    
    return {
        "resource_count": resource_count,
        "offsets": resource_offsets
    }

def load_map(map_id: int, fdfield_data: bytes, fdshap_data: bytes):
    """加载并生成地图"""
    # 解析 FDFIELD.DAT
    fdfield = parse_fdfield(fdfield_data)
    
    # 获取地图资源
    layout_idx = map_id * 3
    control_idx = map_id * 3 + 1
    
    layout_start = fdfield["offsets"][layout_idx]
    control_start = fdfield["offsets"][control_idx]
    
    # 解析地图尺寸
    width = struct.unpack_from("<H", fdfield_data, layout_start)[0]
    height = struct.unpack_from("<H", fdfield_data, layout_start + 2)[0]
    
    # 解析地形集ID
    terrain_set_id = fdfield_data[control_start]
    
    # 加载调色板
    palette_idx = terrain_set_id * 2
    palette_start = fdshap["offsets"][palette_idx]
    palette_6bit = fdshap_data[palette_start:palette_start+768]
    palette = palette_6bit_to_8bit(palette_6bit)
    
    # 加载瓦片图像
    tile_set_idx = terrain_set_id * 2 + 1
    tile_set_start = fdshap["offsets"][tile_set_idx]
    tiles = load_tile_set(fdshap_data, tile_set_start, palette)
    
    # 解析瓦片布局
    tile_data = fdfield_data[layout_start + 4:]
    tiles_grid = []
    pos = 0
    for y in range(height):
        row = []
        for x in range(width):
            b0 = tile_data[pos]
            b1 = tile_data[pos + 1]
            b2 = tile_data[pos + 2]
            b3 = tile_data[pos + 3]
            
            terrain_id = ((b2 & 0x1F) << 2) | (b1 & 3)
            pos += 4
            row.append(terrain_id)
        tiles_grid.append(row)
    
    # 生成地图图像
    return render_map(tiles_grid, tiles, width, height)
```

---

## 五、验证数据

### 5.1 测试地图

| 地图ID | 尺寸 | 地形集ID | 瓦片数量 | 状态 |
|-------|------|---------|---------|------|
| 0 | 24×24 | 0 | 576 | ✓ |
| 1 | 27×21 | 1 | 567 | ✓ |
| 5 | 20×26 | 5 | 520 | ✓ |

### 5.2 FDSHAP 资源统计

| 资源索引 | 内容 | 大小 | 瓦片数 |
|---------|------|------|--------|
| 0 | 调色板 0 | 1200 | - |
| 1 | 瓦片集 0 | 87915 | 148 |
| 2 | 调色板 1 | 1200 | - |
| 3 | 瓦片集 1 | 141101 | 110 |
| ... | ... | ... | ... |

---

## 六、工具使用

### 6.1 map_verify.py

```bash
# 生成指定地图
python tools/map_verify.py --generate-map 0

# 导出瓦片图像
python tools/map_verify.py --export-tiles --max-tiles 100

# 指定源目录和输出目录
python tools/map_verify.py --source game --output output/maps --generate-map 1
```

### 6.2 输出文件

- `map_{id}.png`: 生成的地图图像
- `map_{id}_layout.json`: 地图布局数据（JSON 格式）

---

## 七、注意事项

1. **字节序**: 所有多字节整数均为小端序（Little-Endian）
2. **地形ID范围**: 0-127（7位）
3. **瓦片尺寸**: 通常为 24×24 像素
4. **调色板格式**: 6-bit RGB，需转换为 8-bit
5. **RLE 压缩**: 4 种模式（跳过、复制、交替复制、填充）

---

## 八、相关文件

- `tools/map_verify.py`: 地图验证工具
- `src/fd2_decoder.c`: DAT 文件解码器
- `src/fd2_map.c`: 地图渲染实现
- `include/fd2_decoder.h`: 解码器头文件
- `include/fd2_palette.h`: 调色板相关定义

---

*文档生成日期: 2026-04-29*
*分析方法: IDA MCP 反编译 + Python 验证*
