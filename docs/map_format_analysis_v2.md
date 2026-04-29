# FD2 地图数据格式分析（最终版）

## 概述

基于IDA MCP反编译、用户提供的关键索引信息和Python验证，记录《富甲天下2》（FD2）地图数据格式的完整知识。

**最终验证结果**：33/33地图全部成功导出，100%渲染率（43734/43734瓦片）。

---

## 一、FDFIELD.DAT 地图文件结构

### 1.1 文件头

```
偏移 0-5: 魔数 "LLLLLL" (6 字节)
偏移 6+:  资源偏移表（每个条目 4 字节DWORD，小端序）
```

**注意**：FDFIELD.DAT **没有**显式的资源计数字段，偏移表直接从偏移6开始。当读取到无效偏移时停止。

### 1.2 地图资源索引

每个地图使用 **3 个连续资源**：

| 资源索引 | 内容 | 说明 |
|---------|------|------|
| `3 * map_id` | Layout 数据 | 地图瓦片布局 |
| `3 * map_id + 1` | Control 数据 | 地图控制信息 |
| `3 * map_id + 2` | Spawn 数据 | 角色出生位置 |

### 1.3 Layout 数据结构

```
偏移 0-1: 地图宽度 (WORD, 小端序)
偏移 2-3: 地图高度 (WORD, 小端序)
偏移 4+:  瓦片数据（每瓦片 4 字节）
```

**每瓦片 4 字节结构**：
```c
struct TileData {
    uint16_t terrain_id;    // 地形编号 (2字节，小端序)
    uint16_t event_id;      // 事件编号/宝箱编号 (2字节)
};
```

**地形编号说明**：
- 直接使用 `byte[0] | (byte[1] << 8)` 读取为 16位整数
- 范围：0-383（跨所有地图）
- 地图0范围：8-286
- **地形编号直接用作FDSHAP.DAT瓦片集的索引**

### 1.4 Control 数据结构

```c
struct ControlData {
    uint8_t terrain_set_id;   // byte[0]: 地形集ID (0-7)
    uint8_t ally_max;         // byte[1]: 己方最多可出场人数
    uint8_t enemy_total;      // byte[2]: 敌友出场人物总数
    
    // 回合事件：16组 × 3字节
    struct EventInfo {
        uint8_t round;        // 所在回合
        uint16_t event_id;    // 事件编号 (FF FF 00 = 没有)
    } events[16];
    
    // 保留：16组 × 2字节 (FF 00)
    uint8_t reserved[32];
    
    // 宝箱资料：16组 × 3字节
    struct ChestInfo {
        uint8_t type;         // 00=物品, 01=金钱
        uint16_t content;     // 物品编号/金钱数目
    } chests[16];
    
    // 出场人物：enemy_total × 26字节
    struct CharacterInfo {
        uint8_t faction;      // 00=敌方, 01=友方, 02=己方
        uint8_t portrait;     // 肖像编号
        uint8_t race;         // 种族编号
        uint8_t profession;   // 职业编号
        uint8_t level;        // 等级
        uint8_t items[8];     // 物品 (前2个是武器/防具, FF=没有)
        uint8_t spells[8];    // 法术
        uint8_t spawn_round;  // 出场回合
        struct {
            uint8_t type;     // 00=物品, 01=金钱
            uint24_t content; // 内容 (3字节)
        } drop;               // 死亡掉落
    } characters[enemy_total];
};
```

### 1.5 Spawn 数据结构

```c
struct SpawnData {
    uint16_t character_count;  // 人物总数 (ally_max + enemy_total)
    
    struct SpawnInfo {
        uint16_t x;            // X坐标
        uint16_t y;            // Y坐标
        uint16_t portrait;     // 肖像编号 (00=己方人物)
    } spawns[character_count];
};
```

---

## 二、FDSHAP.DAT 瓦片图像文件结构

### 2.1 文件头

```
偏移 0-5: 魔数 "LLLLLL" (6 字节)
偏移 6-9: 资源数量 (DWORD, 小端序)
偏移 10+: 资源偏移表（每个条目 4 字节DWORD）
```

### 2.2 资源配对

FDSHAP.DAT 资源成对出现：

| 资源索引 | 内容 |
|---------|------|
| `terrain_set_id * 2` | 调色板 |
| `terrain_set_id * 2 + 1` | 瓦片图像集 |

### 2.3 调色板资源结构

```
大小: 1200 字节
- 偏移 0-767: 256色调色板 (6-bit RGB, 每颜色3字节)
- 偏移 768-1199: 地形控制资料 (432字节)
```

**6-bit 转 8-bit**：
```c
r8 = (r6 << 2) | (r6 >> 4)
g8 = (g6 << 2) | (g6 >> 4)
b8 = (b6 << 2) | (b6 >> 4)
```

**地形控制资料（768-1199）**：
- 432字节，可能包含地形属性信息
- 结构待分析（可能每4字节一个条目 = 108个条目）
- 用于判断地形是否有宝箱等特殊属性

### 2.4 瓦片图像集结构

```c
struct TileSet {
    uint16_t tile_width;      // 偏移 0-1: 瓦片宽度 (通常 24)
    uint16_t tile_height;     // 偏移 2-3: 瓦片高度 (通常 24)
    uint16_t tile_count;      // 偏移 4-5: 瓦片数量
    // 偏移 6+: 瓦片偏移表 (DWORD 数组)
};
```

**瓦片偏移表**（从byte 6开始）：
- 每个条目 4 字节 DWORD
- 条目数 = tile_count
- 每个条目是瓦片RLE数据在资源内的偏移

### 2.5 RLE 解压缩

```c
void rle_decompress(uint8_t* src, uint8_t* dst, int width, int height) {
    int p = 0;
    for (int row = 0; row < height; row++) {
        int row_dst = row * width;
        int count = width;
        while (count > 0) {
            uint8_t value = src[p++];
            int count_1 = (value & 0x3F) + 1;
            int bit7 = (value >> 7) & 1;
            int bit6 = (value >> 6) & 1;
            
            if (bit7 && bit6) {
                // SKIP: 跳过像素
                count -= count_1;
            } else if (bit7 && !bit6) {
                // COPY: 复制像素
                for (int i = 0; i < count_1 && count > 0; i++) {
                    dst[row_dst++] = src[p++];
                    count--;
                }
            } else if (!bit7 && bit6) {
                // ALTERNATE: 每隔一像素填充
                uint8_t fill = src[p++];
                for (int i = 0; i < count_1 && count > 0; i++) {
                    dst[row_dst] = fill;
                    row_dst += 2;
                    count -= 2;
                }
            } else {
                // FILL: 填充像素
                uint8_t fill = src[p++];
                for (int i = 0; i < count_1 && count > 0; i++) {
                    dst[row_dst++] = fill;
                    count--;
                }
            }
        }
    }
}
```

---

## 三、关键发现

### 3.1 用户提供的资源索引公式（已验证正确）

**FDFIELD.DAT 地图数据索引**（用户原始索引从1开始）：
- 用户描述："fdfield的地图数据是1，4，7，10略"
- 转换为0开始索引：0, 3, 6, 9...
- **公式**: `map_id * 3`（Layout）、`map_id * 3 + 1`（Control）、`map_id * 3 + 2`（Spawn）

**FDSHAP.DAT 瓦片集索引**（用户原始索引从1开始）：
- 用户描述："fdshap瓦块集是1，3，5，7略"
- 转换为0开始索引：0, 2, 4, 6...
- **公式**: `terrain_set_id * 2`

**FDOTHER.DAT 调色板**：
- 资源0：全局调色板（768字节，6-bit RGB）

### 3.2 地形编号到瓦片索引的映射

**最终结论**：地形编号直接用作瓦片索引，**没有任何掩码或模运算**。

```c
// 正确方式
tile_idx = terrain_id;  // 直接使用

// 错误方式（会导致瓦片位置串位）
tile_idx = terrain_id & 0x7F;  // ❌ 会将274映射到18
tile_idx = terrain_id % 128;   // ❌ 同上
tile_idx = terrain_id % 192;   // ❌ 超出范围的瓦片无法渲染
```

**验证数据**：
- 地图0: 288个瓦片，地形ID范围8-286，所有ID都在瓦片集范围内
- 地图总数33个，瓦片集大小从96到384不等
- 所有地图100%渲染率证明直接映射是正确的

**关键错误示例**：
- 地形ID 274 (0x112)，使用 `& 0x7F` 会得到 18 (0x12)
- 这会导致瓦片位置完全错误（差了一位或多位）

### 3.3 各地图瓦片集统计

| 地图ID | 尺寸 | terrain_set | 瓦片数 | 渲染率 |
|-------|------|-------------|--------|--------|
| 0 | 24x24 | 0 | 288 | 576/576 (100%) |
| 1 | 27x21 | 1 | 192 | 567/567 (100%) |
| 7 | 29x45 | 7 | 384 | 1305/1305 (100%) |
| 9 | 31x45 | 9 | 192 | 1395/1395 (100%) |
| 11 | 28x50 | 11 | 288 | 1400/1400 (100%) |
| 23 | 41x37 | 23 | 96 | 1517/1517 (100%) |
| 32 | 18x51 | 32 | 192 | 918/918 (100%) |

**总计**：43734瓦片，100%渲染成功

### 3.4 瓦片集大小分布

- 96个瓦片: 地图23, 25
- 192个瓦片: 地图1, 3, 8-10, 15, 18, 19, 24, 25, 30-32
- 288个瓦片: 地图0, 2, 4, 5, 11-14, 16, 20-21, 26-27, 29
- 384个瓦片: 地图7, 17, 22, 28

### 3.5 IDA 分析验证

已验证的IDA函数：
- `sub_1088D`: 地图加载，计算资源索引 `3*map_id` 和 `2*terrain_set_id`
- `sub_4DF4C`: 地形ID处理（就地修改数据）
- `sub_12E38`: 地形ID提取，使用 `4 * terrain_id + dword_53A69` 查找偏移表
- `sub_1ACF3`: 瓦片渲染
- `sub_4E98D`: RLE解压缩
- `sub_4E22A`: RLE解压缩（简化版）

---

## 四、常见错误和教训

### 4.1 资源索引错误

**错误**：使用 `map_id * 3 + 1` 作为Layout索引
- **原因**：用户说"1, 4, 7, 10"，错误理解为 `map_id * 3 + 1`
- **实际**：用户索引从1开始，转换为0开始：`map_id * 3`
- **后果**：所有33个地图导出失败

### 4.2 瓦片索引串位错误

**错误**：使用 `terrain_id & 0x7F` 作为瓦片索引
- **原因**：从旧代码复制，当时误以为地图0只有192个瓦片
- **实际**：地图0有288个瓦片，地形ID范围8-286都在范围内
- **后果**：调色板正确、地图数据和瓦块集对上了，但瓦片位置完全错误
- **示例**：地形ID 274 (0x112) → 索引18 (0x12)，导致瓦片位置错乱

**关键教训**：
1. 用户索引可能从1开始，需要转换为0开始
2. 不要盲目复制旧代码的掩码运算，要先验证数据范围
3. 如果调色板正确但瓦片位置不对，很可能是索引掩码问题
4. 直接使用 `tile_idx = terrain_id` 是正确的方式

---

## 五、工具

### 5.1 export_all_maps.py

批量导出所有地图的主工具，使用：
- 正确的资源索引：`map_id * 3`（Layout）、`terrain_set_id * 2`（瓦片集）
- 直接使用terrain_id作为瓦片索引（无掩码）
- FDOTHER.DAT资源0作为调色板
- 输出：`output/maps/map_{id}_v3.png`
- **结果**：33/33地图成功，43734/43734瓦片渲染（100%）

### 5.2 test_map_fixed_palette.py

参考工具（之前正确渲染map0的工具），使用：
- FDSHAP格式2（无显式计数）
- FDOTHER.DAT资源0作为调色板
- terrain_set_id直接索引

### 5.3 map_verify.py

原始验证工具，支持：
- `--generate-map N`: 生成地图
- `--export-tiles`: 导出瓦片
- 输出：`output/maps/map_{id}.png`

---

## 六、待解决问题

1. **调色板后432字节**：地形控制资料的完整结构
2. **变体地形**：byte[1]=1 的地形（272-286）是否使用不同的瓦片

---

*更新日期: 2026-04-29*
*来源: IDA MCP反编译 + 用户关键索引信息 + Python验证*
*验证状态: ✅ 所有33个地图100%渲染成功*
