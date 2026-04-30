# FDFIELD.DAT 地图数据格式详解

## 概述

FDFIELD.DAT是炎龙骑士团2（FD2）的地图数据文件，包含所有33个地图的基础信息。

## 文件结构

### 文件头（6字节）
```
Offset 0x000000: 4C 4C 4C 4C 4C 4C  (连续6个0x4C，即'LLLLLL')
```

### 地图索引表（33个地图 × 12字节 = 396字节）

每个地图占用12字节（3个DWORD），从文件偏移6开始：

| 偏移 | 内容 | 说明 |
|------|------|------|
| +0 (4字节) | 地图构成数据偏移 | Part 1起始位置 |
| +4 (4字节) | 地图控制信息偏移 | Part 2起始位置 |
| +8 (4字节) | 人物出场位置偏移 | Part 3起始位置 |

**索引计算公式：**
```c
index_offset = 6 + map_id * 12
```

**示例 - 地图0的索引表：**
```
0x00000000: 4C 4C 4C 4C 4C 4C 96 01 00 00 9A 0A 00 00 43 0E
0x00000010: 00 00 11 0F 00 00 F1 17 00 00 84 1C 00 00 94 1D

地图0索引：
  DWORD[0] (字节6-9):   0x00000196 = 406 (地图构成数据偏移)
  DWORD[1] (字节10-13): 0x00000A9A = 2714 (地图控制信息偏移)
  DWORD[2] (字节14-17): 0x00000E43 = 3651 (人物出场位置偏移)
```

---

## 第一部分：地图构成数据

### 数据结构

```
起始：2字节地图宽度（little-endian WORD）
      2字节地图高度（little-endian WORD）
之后：width × height 个瓦片数据，每个4字节
```

### 瓦片数据格式（4字节/瓦片）

每个瓦片包含2个WORD（little-endian）：

| 字节 | 内容 | 说明 |
|------|------|------|
| +0~1 | 地形编号（terrain_id） | 16位整数，从FDSHAP.DAT获取地形控制数据 |
| +2~3 | 事件编号（event_id） | #0以上表示宝箱编号，#1以上表示触发事件编号 |

**数据排列顺序：** 先水平（X）后垂直（Y），即按行扫描

### 示例 - 地图0

```
地图尺寸：24 × 24 瓦片
布局数据偏移：0x0196
数据大小：4 + 24×24×4 = 2308字节 (0x904)
数据范围：0x0196 ~ 0x0A99
```

**十六进制示例：**
```
00000190: 03 00 E1 B5 03 00 18 00 18 00 31 00 00 00 31 00
                    ↑宽度=24 ↑高度=24

之后每4字节一个瓦片：
  31 00 00 00  → terrain=49, event=0
  31 00 00 00  → terrain=49, event=0
  ...
```

### 瓦片尺寸

**重要：** 地图瓦片是**24×24像素**（不是64或128）

- 地图0：24瓦片 × 24像素 = 576像素（宽度和高度）
- 地图32：18瓦片 × 24像素 = 432像素（宽度），51瓦片 × 24像素 = 1224像素（高度）

---

## 第二部分：地图控制信息

### 数据结构

```
偏移0x00 (3字节)：地图信息
  字节0：地图编号
  字节1：己方最多可出场人数
  字节2：敌友出场人物总数

偏移0x03 (48字节)：回合事件信息（16组 × 3字节）
  每组：回合(1字节) + 事件编号(2字节, little-endian)
  FF FF 00 表示没有事件

偏移0x33 (32字节)：保留数据（16组 × 2字节）
  一律为 FF 00

偏移0x53 (48字节)：宝箱数据（16组 × 3字节）
  每组：类型(1字节) + 内容(2字节, little-endian)
  类型：00=物品，01=金钱
  内容：物品编号 / 金钱数目

偏移0x83：出场人物信息（敌友单位，每人26字节）
```

### 前缀总大小

```
3 (地图信息) + 48 (回合事件) + 32 (保留) + 48 (宝箱) = 131字节 (0x83)
```

### 出场人物信息（26字节/单位）

**重要：** 这是敌人和NPC的信息，**不是**己方人物的位置信息。

| 偏移 | 大小 | 字段 | 说明 |
|------|------|------|------|
| +0 | 1 | faction | 阵营：00=敌军，01=NPC，02=友军 |
| +1 | 1 | portrait_id | 肖像编号 |
| +2 | 1 | race_id | 种族编号 |
| +3 | 1 | job_id | 职业编号 |
| +4 | 1 | level | 等级 |
| +5~12 | 8 | items[8] | 物品编号（前2个为武器和防具，FF表示没有） |
| +13~16 | 4 | spells[4] | 法术编号 |
| +17 | 1 | spawn_turn | 出场回合（FF表示增援） |
| +18 | 1 | drop_type | 死亡掉落类型：00=物品，01=金钱 |
| +19~21 | 3 | drop_content[3] | 掉落内容：物品编号(2字节)或金钱数目(3字节) |
| +22~25 | 4 | reserved[4] | 保留字节 |

**总计：** 1+1+1+1+1+8+4+1+1+3+4 = 26字节

### 示例 - 地图0控制数据

```
地图控制信息偏移：0x0A9A
数据大小：937字节 (0x3A9)
数据范围：0x0A9A ~ 0x0E42

地图信息（0x0A9A）：
  00 = 地图编号0
  04 = 最大友军数4
  1E = 敌人总数30

回合事件（0x0A9D~0x0ACC，48字节）：
  03 00 01 = 第3回合结束后显示事件0x0001
  ...

宝箱数据（0x0AED~0x0B1C，48字节）：
  01 B8 = 类型01(金钱)，内容0x00B8(184)
  0B 88 = 类型0B(未知)，内容0x0088
  13 00 = 类型13(未知)，内容0x0000
  ...

人物信息（0x0B1D开始，30单位 × 26字节 = 780字节）：
  Char 0: faction=0(敌军), portrait=96, level=2, items=[00,80,FF,...]
  Char 1: faction=0(敌军), portrait=96, level=2, ...
  ...
```

---

## 第三部分：人物出场位置

### 数据结构

```
偏移0x00 (2字节)：人物总数（little-endian WORD）
                  = 己方最多可出场人数 + 敌友出场人物总数

偏移0x02：出场位置信息（每人6字节 = 3个WORD）
  每组：X坐标(2字节) + Y坐标(2字节) + 肖像编号(2字节)
        均为little-endian WORD
        
  肖像编号：
  - 0000：表示己方人物
  - 非0：敌军或NPC的头像ID
```

### 示例 - 地图0

```
人物出场位置偏移：0x0E43
数据大小：206字节 (0xCE)
数据范围：0x0E43 ~ 0x0F10

总数：0x0022 = 34个角色

位置数据（前10个）：
  Char  0: X=1,  Y=3,  Portrait=96  (敌军/NPC)
  Char  1: X=2,  Y=1,  Portrait=96  (敌军/NPC)
  Char  2: X=4,  Y=1,  Portrait=96  (敌军/NPC)
  Char  3: X=6,  Y=1,  Portrait=96  (敌军/NPC)
  Char  4: X=9,  Y=1,  Portrait=96  (敌军/NPC)
  Char  5: X=13, Y=1,  Portrait=96  (敌军/NPC)
  Char  6: X=14, Y=2,  Portrait=96  (敌军/NPC)
  Char  7: X=2,  Y=16, Portrait=6   (敌军/NPC)
  Char  8: X=2,  Y=16, Portrait=3   (敌军/NPC)
  Char  9: X=2,  Y=16, Portrait=4   (敌军/NPC)
  ...
  Char 30: X=13, Y=15, Portrait=0   (己方人物)
  Char 31: X=13, Y=15, Portrait=0   (己方人物)
  Char 32: X=15, Y=8,  Portrait=0   (己方人物)
  Char 33: X=15, Y=8,  Portrait=0   (己方人物)
```

### 示例 - 地图32

```
人物出场位置偏移：0x03B52B
总数：30个角色
有效角色：21个（其余9个为X=0, Y=0的空位）

部分角色位置：
  Char  0: X=7,  Y=5,  Portrait=48
  Char  1: X=10, Y=5,  Portrait=66
  Char  2: X=8,  Y=42, Portrait=0   (己方)
  Char  3: X=4,  Y=46, Portrait=0   (己方)
  Char  4: X=13, Y=47, Portrait=4
  Char  5~20: 各种位置，Portrait=68或69
  Char 21~29: X=0, Y=0 (空位)
```

---

## 坐标系统

### 地图瓦片坐标

- 坐标原点(0,0)在地图左上角
- X轴向右递增，Y轴向下递增
- 坐标单位为**瓦片**（不是像素）

### 屏幕坐标转换

```c
// 地图瓦片 → 屏幕像素
screen_x = tile_x * MAP_TILE_SIZE - camera_x;
screen_y = tile_y * MAP_TILE_SIZE - camera_y;

// MAP_TILE_SIZE = 24（像素）
```

### 摄像机系统

- 摄像机偏移（camera_x, camera_y）控制地图滚动
- 角色位置相对于地图坐标，不随摄像机移动而改变
- 屏幕显示区域：320×200像素

---

## C代码实现

### 数据结构定义

```c
/* 地图瓦片尺寸 */
#define MAP_TILE_SIZE 24

/* 角色位置数据（6字节/角色） */
typedef struct {
    uint16_t x;           /* X坐标（地图瓦片） */
    uint16_t y;           /* Y坐标（地图瓦片） */
    uint16_t portrait_id; /* 肖像ID（0=己方人物） */
} fd2_map_char_pos_t;

/* 角色信息数据（26字节/单位） */
typedef struct {
    uint8_t  faction;         /* 阵营：0=敌军，1=NPC，2=友军 */
    uint8_t  portrait_id;     /* 肖像编号 */
    uint8_t  race_id;         /* 种族编号 */
    uint8_t  job_id;          /* 职业编号 */
    uint8_t  level;           /* 等级 */
    uint8_t  items[8];        /* 物品ID（前2个为武器/防具） */
    uint8_t  spells[4];       /* 法术ID（4个） */
    uint8_t  spawn_turn;      /* 出场回合 */
    uint8_t  drop_type;       /* 掉落类型：0=物品，1=金钱 */
    uint8_t  drop_content[3]; /* 掉落内容 */
    uint8_t  reserved[4];     /* 保留字节 */
} fd2_map_char_info_t;

/* 地图场景数据 */
typedef struct {
    uint8_t  map_number;      /* 地图编号 */
    uint8_t  max_friendly;    /* 最大友军数 */
    uint8_t  total_units;     /* 敌人总数 */
    uint8_t  total_chars;     /* 总人物数 = max_friendly + total_units */
    
    int char_pos_count;
    fd2_map_char_pos_t char_positions[FD2_MAX_MAP_CHARS];
    
    int char_info_count;
    fd2_map_char_info_t char_info[FD2_MAX_MAP_CHARS];
    
    bool loaded;
} fd2_map_scene_t;
```

### 解析代码

```c
/* 从FDFIELD.DAT解析地图数据 */
int fd2_map_load_from_dat(fd2_map_t* map, int map_id,
                          const char* fdfield_path,
                          const char* fdshap_path,
                          const char* fdother_path) {
    // ...
    
    /* 计算索引偏移 */
    int layout_idx = map_id * 3;      /* 第1部分索引 */
    int control_idx = map_id * 3 + 1; /* 第2部分索引 */
    int char_pos_idx = map_id * 3 + 2;/* 第3部分索引 */
    
    /* 解析角色位置数据 */
    if (char_pos_data && char_pos_size >= 2) {
        uint16_t total_chars = char_pos_data[0] | (char_pos_data[1] << 8);
        
        for (int i = 0; i < char_count; i++) {
            u32 offset = 2 + i * 6;
            char_pos->x = char_pos_data[offset] | (char_pos_data[offset+1] << 8);
            char_pos->y = char_pos_data[offset+2] | (char_pos_data[offset+3] << 8);
            char_pos->portrait_id = char_pos_data[offset+4] | (char_pos_data[offset+5] << 8);
        }
    }
    
    /* 解析角色信息数据 */
    u32 char_info_offset = 3 + (16 * 3) + (16 * 2) + (16 * 3); /* 131字节 */
    
    for (int i = 0; i < char_info_count; i++) {
        u32 offset = char_info_offset + i * 26;
        
        char_info->faction = control_data[offset];
        char_info->portrait_id = control_data[offset + 1];
        char_info->race_id = control_data[offset + 2];
        char_info->job_id = control_data[offset + 3];
        char_info->level = control_data[offset + 4];
        memcpy(char_info->items, &control_data[offset + 5], 8);
        memcpy(char_info->spells, &control_data[offset + 13], 4);
        char_info->spawn_turn = control_data[offset + 17];
        char_info->drop_type = control_data[offset + 18];
        memcpy(char_info->drop_content, &control_data[offset + 19], 3);
        memcpy(char_info->reserved, &control_data[offset + 22], 4);
    }
    
    // ...
}
```

---

## 验证工具

使用Python验证FDFIELD.DAT结构：

```python
import struct

with open('FDFIELD.DAT', 'rb') as f:
    data = f.read()

# 验证文件头
assert data[0:6] == b'LLLLLL'

# 解析地图0索引
map_id = 0
idx_offset = 6 + map_id * 12
layout_off, control_off, charpos_off = struct.unpack_from('<III', data, idx_offset)

print(f"地图{map_id}:")
print(f"  布局数据偏移: 0x{layout_off:06X}")
print(f"  控制数据偏移: 0x{control_off:06X}")
print(f"  角色位置偏移: 0x{charpos_off:06X}")

# 验证地图尺寸
width = struct.unpack_from('<H', data, layout_off)[0]
height = struct.unpack_from('<H', data, layout_off + 2)[0]
print(f"  地图尺寸: {width} × {height} 瓦片")

# 解析角色位置
total_chars = struct.unpack_from('<H', data, charpos_off)[0]
print(f"  角色总数: {total_chars}")

for i in range(min(10, total_chars)):
    pos = charpos_off + 2 + i * 6
    x, y, portrait = struct.unpack_from('<HHH', data, pos)
    print(f"  Char {i}: X={x}, Y={y}, Portrait={portrait}")
```

---

## 参考资料

- IDA MCP分析函数：sub_1088D（地图加载），sub_111BA（数据加载）
- 相关数据文件：FDSHAP.DAT（瓦片图集），FDICON.B24（角色精灵）
- 游戏版本：炎龙骑士团2（FD2）
