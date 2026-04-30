# FDFIELD.DAT 解析 - IDA反编译分析

## 概述

本文档基于IDA MCP对FD2.EXE的反编译分析，1:1复原游戏实际的FDFIELD.DAT解析逻辑。

**重要：不要使用猜测的逻辑，必须完全遵循IDA反编译的代码。**

---

## 核心函数：sub_111BA（数据加载器）

### 函数签名
```c
void* sub_111BA(const char* filename, void* old_data, int index);
```

### IDA反编译代码
```c
int __cdecl sub_111BA(int a1, int a2, int a3)
{
    // a1 = filename (char*)
    // a2 = old_data (void*)
    // a3 = index (int)
    
    // 1. 释放旧数据
    if (a2)
        free(a2);
    
    // 2. 打开文件
    v3 = fopen(a1, "rb");
    if (!v3) {
        printf("\n\n File not found %s!!! \n\n", a1);
        goto LABEL_8;
    }
    
    // 3. 分配8字节缓冲区
    v4 = (int *)malloc(8);
    
    // 4. 关键：计算索引偏移
    //    offset = 4 * a3 + 6
    fseek(v3, 4 * a3 + 6, 0);
    
    // 5. 读取8字节（2个DWORD）
    sub_373CA(v4, 1, 8, v3);
    
    // 6. 解析数据范围
    v5 = *v4;                      // start_offset
    dword_53BFF = v4[1] - *v4;    // data_size = end_offset - start_offset
    
    free(v4);
    
    // 7. 分配数据缓冲区并读取
    v6 = malloc(dword_53BFF);
    if (!v6) {
        printf("Out of Memory at Load %s Number:%d!!\n", a1, a3);
        LABEL_8:
        JUMPOUT(0x1005E);
    }
    
    fseek(v3, v5, 0);
    sub_373CA(v6, 1, dword_53BFF, v3);
    fclose(v3);
    
    return v6;
}
```

### 关键发现

**索引偏移计算公式：**
```c
file_offset = 4 * index + 6
```

**重要**：
- 每个索引项占用**4字节**（1个DWORD）
- 索引表从文件偏移6开始
- 函数读取**2个DWORD**：start_offset和end_offset
- 数据大小 = end_offset - start_offset

---

## 核心函数：sub_1088D（地图加载）

### 函数签名
```c
int sub_1088D(int map_id);  // n13 = map_id
```

### IDA反编译代码（关键部分）

```c
int __cdecl sub_1088D(int n13)
{
    // 1. 加载FDTXT.DAT（地图文本）
    //    index = map_id + 1
    dword_53A79 = sub_111BA("FDTXT.DAT", dword_53A79, n13 + 1);
    
    // 2. 加载FDFIELD.DAT的三个部分
    //    索引计算：index = 3 * map_id + part_index
    
    // Part 3: 角色位置数据（索引 = 3*map_id + 2）
    dword_53A59 = sub_111BA("FDFIELD.DAT", dword_53A59, 3 * n13 + 2);
    
    // Part 2: 控制数据（索引 = 3*map_id + 1）
    dword_53A55 = sub_111BA("FDFIELD.DAT", dword_53A55, 3 * n13 + 1);
    
    // Part 1: 布局数据（索引 = 3*map_id）
    dword_53A51 = sub_111BA("FDFIELD.DAT", dword_53A51, 3 * n13);
    
    // 3. 从布局数据读取地图尺寸
    dword_53AC1 = *(__int16 *)dword_53A51;        // map_width
    dword_53AC5 = *(__int16 *)(dword_53A51 + 2);  // map_height
    
    // 4. 从控制数据读取参数
    terrain_set_id = *(uint8_t *)dword_53A55;        // control_data[0]
    ::n6 = *(uint8_t *)(dword_53A55 + 1);            // control_data[1] = max_friendly
    dword_53BE3 = *(uint8_t *)(dword_53A55 + 2);     // control_data[2] = total_units
    
    // 5. 加载FDSHAP.DAT的tileset
    v2 = 2 * terrain_set_id;
    FDSHAP_DAT = sub_111BA("FDSHAP.DAT", FDSHAP_DAT, v2);
    dword_53A69 = sub_111BA("FDSHAP.DAT", dword_53A69, v2 + 1);
    
    // 6. 处理布局数据中的瓦片信息
    sub_4DF4C(dword_53A51);
    
    // 7. 分配角色数据内存：96 * 80 = 7680字节
    dword_53A45 = malloc(7680);
    
    // 8. 打开FDICON.B24
    v9 = fopen("FDICON.B24", "rb");
    
    // 9. 计算角色位置数据指针
    //    v4指向第total_units个角色的位置（跳过前total_units个敌人位置）
    v4 = (_BYTE *)(dword_53A59 + 6 * dword_53BE3 + 2);
    
    // 10. 角色信息源数据
    v5 = dword_53BF7;
    
    // 11. 循环处理每个己方角色（循环max_friendly次）
    for (n6 = 0; n6 < ::n6; ++n6) {
        if (条件满足 && v10 < dword_53BFB) {
            // 从源数据复制80字节
            memmove(v3, v5, 80);
            
            // 设置角色位置（从角色位置数据）
            v7 = v4[2];
            *v3 = *v4;        // X坐标（byte[0]）
            v3[1] = v7;       // Y坐标（byte[2]）
            
            // 步进到下一个角色位置
            v4 += 6;
            
            // 加载图标
            v3[2] = sub_11019((uint8_t)v3[7], v9);
            
            // 设置其他字段
            v3[3] = 0;
            v3[4] = 0;
            v3[6] = 2;
            v3[49] = -1;
            memset(v3 + 34, 0, 6);
            
            // 调用初始化函数
            sub_1B750(n6);
            
            v5 += 80;  // 步进到下一个源角色
            ++v10;
        } else {
            // 空位处理
            memset(v3, 0, 80);
            v3[5] = 1;
        }
        v3 += 80;  // 步进到下一个目标位置
    }
    
    fclose(v9);
    free(dword_53A59);
    dword_53A59 = 0;
    
    return sub_10B4E(0);
}
```

---

## 关键数据结构

### 索引表组织方式

**重要发现：索引表是按索引号顺序排列的，不是按地图号！**

```
索引号 0: 地图0-布局数据偏移   (偏移6)
索引号 1: 地图0-控制数据偏移   (偏移10)
索引号 2: 地图0-角色位置偏移   (偏移14)
索引号 3: 地图1-布局数据偏移   (偏移18)
索引号 4: 地图1-控制数据偏移   (偏移22)
索引号 5: 地图1-角色位置偏移   (偏移26)
...
索引号 96: 地图32-布局数据偏移  (偏移390)
索引号 97: 地图32-控制数据偏移  (偏移394)
索引号 98: 地图32-角色位置偏移  (偏移398)
```

**计算公式：**
```c
// 地图map_id的某部分数据的索引号
index = 3 * map_id + part_index

// part_index:
//   0 = 布局数据（地图构成）
//   1 = 控制数据
//   2 = 角色位置数据

// 文件偏移计算
file_offset = 4 * index + 6
```

### 布局数据（dword_53A51）

```c
// 从文件加载后，layout_data指向的数据：
uint16_t map_width  = *(uint16_t*)layout_data;        // 字节0-1
uint16_t map_height = *(uint16_t*)(layout_data + 2);  // 字节2-3

// 之后是width * height个瓦片数据，每个4字节
```

### 控制数据（dword_53A55）

```c
// 从文件加载后，control_data指向的数据：
uint8_t terrain_set_id = control_data[0];    // 地形图集ID
uint8_t max_friendly   = control_data[1];    // ::n6 = 己方最大人数
uint8_t total_units    = control_data[2];    // dword_53BE3 = 敌人总数

// 之后是回合事件、宝箱、敌人信息等...
```

### 角色位置数据（dword_53A59）

```c
// 从文件加载后，char_pos_data指向的数据：
uint16_t total_count = *(uint16_t*)char_pos_data;  // 字节0-1：角色总数

// 从字节2开始是每个角色的位置数据，每角色6字节：
struct char_position {
    uint8_t x;          // 字节0：X坐标
    uint8_t unknown1;   // 字节1：未知（始终为0）
    uint8_t y;          // 字节2：Y坐标
    uint8_t unknown2;   // 字节3：未知（始终为0）
    uint8_t portrait;   // 字节4：肖像ID（如0x30=48, 0x42=66, 0x44=68, 0x45=69）
    uint8_t unknown3;   // 字节5：未知（始终为0）
};

// IDA读取己方角色位置的方式：
// v4 = char_pos_data + 6 * total_units + 2;
// 循环max_friendly次，每次步进6字节
```

**注意**：IDA反编译显示`v3[7] = v4[3]`，但实际数据验证显示portrait在byte[4]。
这可能是因为IDA中v3指向的角色结构体有特殊的内存布局。

**关键逻辑解释：**
- 角色位置数据中，前`total_units`个位置是敌人/NPC的位置
- 后`max_friendly`个位置是己方角色的位置
- IDA通过 `6 * total_units + 2` 跳过敌人位置，直接定位到己方角色
- 然后循环`max_friendly`次读取己方角色位置

### 瓦片数据处理（sub_4DF4C）

```c
char __cdecl sub_4DF4C(uint8_t *layout_data)
{
    // 计算瓦片总数
    int tile_count = (uint16_t)(layout_data[2] * layout_data[0]);
    //                    height * width
    
    uint8_t *v2 = layout_data + 4;  // 跳过width和height
    
    // 处理每个瓦片的4字节数据
    do {
        v2[3] = -1;           // byte[3] = 0xFF
        v2[2] &= 0x1F;        // byte[2] &= 0x1F（事件类型）
        v2[1] &= 3;           // byte[1] &= 0x03（地形标志）
        v2 += 4;              // 步进4字节
        --tile_count;
    } while (tile_count);
    
    return -1;
}
```

**瓦片4字节格式：**
```
字节0: terrain_id的低8位
字节1: (terrain_flag << 8) | terrain_id的高2位
       其中terrain_flag = byte[1] & 0x03
字节2: event_type & 0x1F
字节3: 设为0xFF（可能是标记位）
```

### 角色信息（内存中80字节结构）

根据IDA sub_1088D，角色在内存中使用80字节结构：

```c
struct char_data_80 {
    uint8_t x;              // 偏移0：X坐标（从角色位置数据）
    uint8_t y;              // 偏移1：Y坐标（从角色位置数据）
    uint8_t icon_loaded;    // 偏移2：图标加载结果（从sub_11019）
    uint8_t field_3;        // 偏移3：设为0
    uint8_t field_4;        // 偏移4：设为0
    uint8_t flag;           // 偏移5：标志位（0=正常，1=空位）
    uint8_t field_6;        // 偏移6：固定值2
    uint8_t icon_id;        // 偏移7：原始图标ID（用于加载图标）
    uint8_t field_8;        // 偏移8：阵营（用于条件判断）
    // ...
    uint8_t field_34_39[6]; // 偏移34-39：清零
    // ...
    uint8_t field_49;       // 偏移49：0xFF
    // ...总共80字节
};
```

---

## 完整解析流程

### 步骤1：加载三部分数据

```c
int map_id = 32;  // 例如加载地图32

// 计算索引号
int layout_idx  = 3 * map_id;      // 96
int control_idx = 3 * map_id + 1;  // 97
int charpos_idx = 3 * map_id + 2;  // 98

// 加载数据
void* layout_data  = sub_111BA("FDFIELD.DAT", NULL, layout_idx);
void* control_data = sub_111BA("FDFIELD.DAT", NULL, control_idx);
void* charpos_data = sub_111BA("FDFIELD.DAT", NULL, charpos_idx);
```

### 步骤2：解析地图参数

```c
// 从布局数据读取地图尺寸
uint16_t map_width  = *(uint16_t*)layout_data;
uint16_t map_height = *(uint16_t*)((uint8_t*)layout_data + 2);

// 从控制数据读取参数
uint8_t terrain_set_id = ((uint8_t*)control_data)[0];
uint8_t max_friendly   = ((uint8_t*)control_data)[1];
uint8_t total_units    = ((uint8_t*)control_data)[2];

// 处理瓦片数据
sub_4DF4C((uint8_t*)layout_data);
```

### 步骤3：解析己方角色位置

```c
// 计算己方角色位置起始偏移
uint8_t* charpos = (uint8_t*)charpos_data;
uint16_t total_count = *(uint16_t*)charpos;

// IDA逻辑：跳过前total_units个敌人位置
uint8_t* friendly_pos = charpos + 6 * total_units + 2;

// 读取max_friendly个己方角色
for (int i = 0; i < max_friendly; i++) {
    uint8_t x = friendly_pos[i * 6];         // byte[0]
    uint8_t y = friendly_pos[i * 6 + 2];     // byte[2]
    uint8_t portrait = friendly_pos[i * 6 + 3]; // byte[3]
    
    printf("Friendly char %d: (%d, %d), portrait=%d\n", i, x, y, portrait);
}
```

### 步骤4：解析敌人信息（从控制数据）

```c
// 敌人信息从控制数据的偏移0x83（131字节）开始
uint8_t* enemy_info = (uint8_t*)control_data + 0x83;

// 每个敌人26字节
for (int i = 0; i < total_units; i++) {
    uint8_t* unit = enemy_info + i * 26;
    
    uint8_t faction = unit[0];
    uint8_t portrait = unit[1];
    uint8_t race = unit[2];
    uint8_t job = unit[3];
    uint8_t level = unit[4];
    // ... 共26字节
}
```

---

## 验证结果

### 地图0验证

```
索引计算：
  layout:  3*0+0 = 0,  file_offset = 4*0+6  = 6
  control: 3*0+1 = 1,  file_offset = 4*1+6  = 10
  charpos: 3*0+2 = 2,  file_offset = 4*2+6  = 14

控制数据解析：
  terrain_set_id = 0
  max_friendly (::n6) = 4
  total_units (dword_53BE3) = 30

角色位置数据：
  总数 = 34
  敌人位置：前30个（索引0-29）
  己方位置：后4个（索引30-33）
  
IDA计算v4偏移：
  v4 = charpos_data + 6 * 30 + 2 = 182
  
读取4个己方角色：
  Char 0: X=7, Y=20, Portrait=0
  Char 1: X=10, Y=21, Portrait=0
  Char 2: X=8, Y=22, Portrait=0
  Char 3: X=11, Y=23, Portrait=0
```

### 地图32验证

```
索引计算：
  layout:  3*32+0 = 96,  file_offset = 4*96+6  = 390
  control: 3*32+1 = 97,  file_offset = 4*97+6  = 394
  charpos: 3*32+2 = 98,  file_offset = 4*98+6  = 398

读取的偏移：
  layout  offset: 0x03A23C (238140)
  control offset: 0x03B098 (241816)
  charpos offset: 0x03B52B (242987)

地图尺寸：18x51瓦片
控制数据：
  terrain_set_id = 32
  max_friendly = 0
  total_units = 30
```

---

## C代码实现要点

### 关键修正

1. **角色位置是uint8_t（1字节），不是uint16_t（2字节）**
   ```c
   typedef struct {
       uint8_t  x;           // 1 byte
       uint8_t  y;           // 1 byte
       uint8_t  portrait_id; // 1 byte
   } fd2_map_char_pos_t;
   ```

2. **索引计算使用IDA公式**
   ```c
   int index = 3 * map_id + part_index;
   int file_offset = 4 * index + 6;
   ```

3. **己方角色位置从敌人位置之后读取**
   ```c
   uint8_t* friendly_pos = charpos_data + 6 * total_units + 2;
   for (int i = 0; i < max_friendly; i++) {
       x = friendly_pos[i * 6];
       y = friendly_pos[i * 6 + 2];
       portrait = friendly_pos[i * 6 + 3];
   }
   ```

4. **瓦片数据处理遵循sub_4DF4C**
   ```c
   byte[1] &= 0x03;  // terrain_flag
   byte[2] &= 0x1F;  // event_type
   byte[3] = 0xFF;   // 标记位
   ```

---

## 参考资料

- IDA函数：sub_111BA（0x111BA）- 数据加载器
- IDA函数：sub_1088D（0x1088D）- 地图加载主函数
- IDA函数：sub_4DF4C（0x4DF4C）- 瓦片数据处理
- IDA函数：sub_11019（0x11019）- 图标加载
