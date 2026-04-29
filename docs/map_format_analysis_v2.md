# FD2 地图数据格式分析（更新版）

## 概述

基于IDA MCP反编译和用户提供的文档，记录《富甲天下2》（FD2）地图数据格式的完整知识。

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

### 3.1 地形编号到瓦片索引

**结论**：地形编号直接用作瓦片索引，**没有额外的映射或模运算**。

- 地图0有192个瓦片（tile_count=192）
- 地形ID范围 8-286
- 地形ID >= 192 的瓦片**无法渲染**（原始工具也是如此）
- 地图0有44/576个瓦片的地形ID超出192范围

**这可能是因为**：
1. 游戏使用多个瓦片集（不同terrain_set_id）
2. 超出范围的瓦片在游戏中显示为空白/特殊处理
3. 运行时有额外的重映射逻辑

### 3.2 IDA 分析验证

已验证的IDA函数：
- `sub_1088D`: 地图加载，计算资源索引 `3*map_id` 和 `2*terrain_set_id`
- `sub_4DF4C`: 地形ID处理（就地修改数据）
- `sub_12E38`: 地形ID提取，使用 `4 * terrain_id + dword_53A69` 查找偏移表
- `sub_1ACF3`: 瓦片渲染
- `sub_4E98D`: RLE解压缩
- `sub_4E22A`: RLE解压缩（简化版）

### 3.3 瓦片集统计

| 地形集ID | 调色板资源 | 瓦片集资源 | 瓦片数量 |
|---------|-----------|-----------|---------|
| 0 | 0 | 1 | 192 |
| 1 | 2 | 3 | 110 |
| 2 | 4 | 5 | ? |
| ... | ... | ... | ... |

---

## 四、工具

### 4.1 test_map_ida_verified.py

基于IDA分析验证的测试工具，使用：
- 正确的地形ID计算：`byte[0] | (byte[1] << 8)`
- 正确的瓦片偏移表解析：byte 6开始，DWORD条目
- 正确的RLE解压缩：4种模式
- 输出：`output/map_{id}_ida_verified.png`

### 4.2 map_verify.py

主要地图验证工具，支持：
- `--generate-map N`: 生成地图
- `--export-tiles`: 导出瓦片
- 输出：`output/maps/map_{id}.png`

---

## 五、待解决问题

1. **地形ID超出范围**：地形ID >= tile_count 时游戏如何处理？
2. **调色板后432字节**：地形控制资料的完整结构
3. **多瓦片集映射**：不同地图的terrain_set_id如何选择瓦片集
4. **变体地形**：byte[1]=1 的地形（272-286）是否使用不同的瓦片

---

*更新日期: 2026-04-29*
*来源: IDA MCP反编译 + 用户文档 + Python验证*
