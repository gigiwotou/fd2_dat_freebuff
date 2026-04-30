# FD2 地图事件数据分析

## 概述

基于IDA MCP反编译分析，记录《炎龙骑士团2》（FD2）地图事件数据的完整结构和使用方式。

**关键函数**：`sub_1088D`（地图加载）、`sub_10652`（场景初始化）、`sub_1B750`（事件位置计算）、`sub_4DF4C`（瓦片数据处理）

---

## 一、事件数据加载

### 1.1 资源索引

事件数据（Spawn/Event数据）在FDFIELD.DAT中的索引：

```c
// sub_1088D中加载三个资源
dword_53A51 = sub_111BA("FDFIELD.DAT", ..., 3 * n13);      // Layout数据
dword_53A55 = sub_111BA("FDFIELD.DAT", ..., 3 * n13 + 1);  // Control数据
dword_53A59 = sub_111BA("FDFIELD.DAT", ..., 3 * n13 + 2);  // 事件数据
```

### 1.2 事件数据格式

从IDA分析看，事件数据的格式如下：

```c
struct EventData {
    uint16_t event_count;         // 事件/单位数量（从control数据byte[2]获取）
    
    struct EventEntry {
        uint8_t  type;            // byte[0]: 类型标识
        uint8_t  field_1;         // byte[1]: 字段1
        uint8_t  field_2;         // byte[2]: 字段2
        uint8_t  terrain_ref;     // byte[3]: 地形引用（用于加载图标）
        uint8_t  field_4;         // byte[4]: 字段4
        uint8_t  field_5;         // byte[5]: 字段5
        uint16_t spawn_x;         // byte[6-7]: X坐标（从control派生）
        uint16_t spawn_y;         // byte[8-9]: Y坐标（从control派生）
        uint8_t  portrait_id;     // byte[10-11]: 肖像/角色ID
        uint8_t  field_12;        // byte[12-13]: 字段12
        uint8_t  field_14;        // byte[14-15]: 字段14
        uint8_t  field_16;        // byte[16-17]: 字段16
        uint8_t  field_18;        // byte[18-19]: 字段18
        uint8_t  field_20;        // byte[20-21]: 字段20
        uint8_t  field_22;        // byte[22-23]: 字段22
        uint8_t  field_24;        // byte[24-25]: 字段24
        uint8_t  field_26;        // byte[26-27]: 字段26
        uint8_t  field_28;        // byte[28-29]: 字段28
        uint8_t  field_30;        // byte[30-31]: 字段30
        uint8_t  field_32;        // byte[32-33]: 字段32
        // ... 更多字段，总共约80字节
    } events[event_count];
};
```

### 1.3 事件数据处理流程

```c
// sub_1088D中的事件数据处理
// 1. 分配80字节/条目的缓冲区
dword_53A45 = malloc(event_count * 80);

// 2. 打开FDICON.B24图标文件
v9 = fopen("FDICON.B24", "rb");

// 3. 初始化事件指针
v4 = event_data + 6 * dword_53BE3 + 2;  // 事件数据起始位置
v5 = dword_53BF7;  // 初始模板数据指针

// 4. 循环处理每个事件
for (n6 = 0; n6 < event_count; n6++) {
    if (condition_met) {
        // 复制模板数据（80字节）
        memmove(v3, v5, 80);
        
        // 从事件数据中提取坐标信息
        v7 = v4[2];
        *v3 = *v4;
        v3[1] = v7;
        v4 += 6;  // 每条事件数据占6字节
        
        // 加载图标
        v3[2] = sub_11019(v3[7], v9);  // 从FDICON.B24加载图标
        v3[3] = 0;
        v3[4] = 0;
        v3[6] = 2;
        v3[49] = -1;
        memset(v3 + 34, 0, 6);
        
        // 调用事件初始化函数
        sub_1B750(n6);
        
        v5 += 80;
        v10++;
    } else {
        // 清空事件条目
        memset(v3, 0, 80);
        v3[5] = 1;
    }
    v3 += 80;
}

fclose(v9);
free(dword_53A59);  // 释放事件数据
dword_53A59 = 0;
```

---

## 二、关键全局变量

### 2.1 地图相关变量

| 变量名 | 地址 | 说明 |
|--------|------|------|
| dword_53A45 | 0x53A45 | 事件条目数组（80字节/条目） |
| dword_53A51 | 0x53A51 | Layout数据指针 |
| dword_53A55 | 0x53A55 | Control数据指针 |
| dword_53A59 | 0x53A59 | 事件数据指针（加载后释放） |
| dword_53AC1 | 0x53AC1 | 地图宽度（从Layout byte[0-1]） |
| dword_53AC5 | 0x53AC5 | 地图高度（从Layout byte[2-3]） |
| dword_53BE3 | 0x53BE3 | 事件数量（从Control byte[2]） |
| dword_53BDF | 0x53BDF | 事件计数器 |
| dword_53BFB | 0x53BFB | 最大事件数量 |
| dword_53BF7 | 0x53BF7 | 事件模板数据指针 |

### 2.2 场景相关变量

| 变量名 | 地址 | 说明 |
|--------|------|------|
| dword_53AFF | 0x53AFF | 场景背景缓冲区 |
| dword_53B03 | 0x53B03 | FDOTHER.DAT资源指针 |

---

## 三、事件条目结构（80字节）

根据IDA分析，每个事件条目是80字节：

```c
struct EventEntry80 {
    // 从事件数据复制的字段
    uint8_t  byte_0;          // byte[0]: 类型/标志
    uint8_t  byte_1;          // byte[1]: 坐标相关
    uint8_t  byte_2;          // byte[2]: FDICON.B24索引（从sub_11019返回）
    uint8_t  byte_3;          // byte[3]: 清零
    uint8_t  byte_4;          // byte[4]: 清零
    uint8_t  byte_5;          // byte[5]: 标志位（1=空，2=已加载）
    uint8_t  byte_6;          // byte[6]: 固定值2
    
    // 从模板数据复制的字段
    uint8_t  byte_7;          // byte[7]: terrain_ref（用于加载图标）
    uint8_t  bytes_8_9[2];    // byte[8-9]: 肖像/角色ID
    uint8_t  byte_10;         // byte[10]: 字段10
    uint8_t  byte_11;         // byte[11]: 字段11
    
    // ... 更多字段 ...
    
    // sub_1B750计算的坐标字段
    uint16_t final_x;         // byte[55-56]: 最终X坐标
    uint16_t final_y;         // byte[57-58]: 最终Y坐标
    uint16_t final_height;    // byte[62-63]: 最终高度/其他
    uint16_t calc_x;          // byte[72-73]: 计算后X坐标
    uint16_t calc_y;          // byte[74-75]: 计算后Y坐标
    uint16_t calc_h;          // byte[76-77]: 计算后高度
};
```

---

## 四、sub_1B750 - 事件位置计算

这个函数负责计算事件的最终显示位置：

```c
void sub_1B750(int event_index) {
    int entry_ptr = 80 * event_index + dword_53A45;
    
    // 读取基础坐标
    int16_t base_x = *(int16_t*)(entry_ptr + 55);
    int16_t base_y = *(int16_t*)(entry_ptr + 57);
    int16_t base_h = *(int16_t*)(entry_ptr + 62);
    
    // 条件调整
    if (*(uint8_t*)(entry_ptr + 36)) {
        base_h += 15;
    }
    
    // 累加8个偏移量（每个2字节）
    for (int i = 0; i < 8; i++) {
        if ((*(uint8_t*)(entry_ptr + 2*i + 10) & 0x40) != 0) {
            // 从某个表中获取偏移量并累加
            char* offset_data = sub_4E8BC(*(uint8_t*)(entry_ptr + 2*i + 11));
            base_x += *(int16_t*)(offset_data + 1);
            base_y += *(int16_t*)(offset_data + 5);
            base_h += *(int16_t*)(offset_data + 3);
        }
    }
    
    // 可能的缩放处理
    if (*(uint8_t*)(entry_ptr + 34)) {
        base_x = (int)(base_x * dbl_5018D);
    }
    if (*(uint8_t*)(entry_ptr + 35)) {
        base_y = (int)(base_y * dbl_5018D);
    }
    
    // 存储计算结果
    *(uint16_t*)(entry_ptr + 72) = base_x;
    *(uint16_t*)(entry_ptr + 74) = base_y;
    *(uint16_t*)(entry_ptr + 76) = base_h;
}
```

---

## 五、sub_4DF4C - 瓦片数据处理

这个函数处理Layout数据，就地修改每个瓦片条目：

```c
void sub_4DF4C(uint8_t* layout_data) {
    int tile_count = (uint16_t)(layout_data[2] * layout_data[0]);  // width * height
    uint8_t* tile_ptr = layout_data + 4;
    
    do {
        tile_ptr[3] = -1;           // byte[3]固定为0xFF
        tile_ptr[2] &= 0x1F;        // byte[2]保留低5位（事件ID）
        tile_ptr[1] &= 3;           // byte[1]保留低2位（地形标志）
        tile_ptr += 4;
        --tile_count;
    } while (tile_count);
}
```

**说明**：
- 清理每个瓦片的4字节数据
- byte[3]设为0xFF（可能作为结束标志或默认值）
- byte[2]保留低5位（0-31，事件ID）
- byte[1]保留低2位（0-3，地形标志）

---

## 六、sub_10652 - 场景初始化

这个函数根据`n17`（地图状态索引）加载不同的场景资源：

```c
void sub_10652() {
    switch (n17) {
        case 9, 24, 25:
            // 加载FDOTHER.DAT资源15
            dword_53AFF = sub_111BA("FDOTHER.DAT", ..., 15);
            dword_53B03 = malloc(64000);
            break;
            
        case 17, 21, 22, 27:
            // 根据不同地图设置不同的尺寸
            switch (n17) {
                case 21: width=408, height=276, res_idx=35; break;
                case 22: width=408, height=256, res_idx=40; break;
                case 27: height=244, res_idx=46; break;
            }
            dword_53AFF = malloc(width * height);
            dword_53B03 = sub_111BA("FDOTHER.DAT", ..., res_idx);
            sub_4E98D(dword_53B03, 0, 0, dword_53AFF, width, -1);
            // 加载下半部分
            dword_53B03 = sub_111BA("FDOTHER.DAT", ..., res_idx + 1);
            sub_4E98D(dword_53B03, 0, height/2, dword_53AFF, width, -1);
            break;
            
        case 23:
            // 特殊场景
            dword_53AFF = malloc(59904);
            dword_53B03 = sub_111BA("FDOTHER.DAT", ..., 42);
            sub_4E98D(dword_53B03, 0, 0, dword_53AFF, 312, -1);
            break;
            
        case 28, 29:
            dword_53AFF = sub_111BA("FDOTHER.DAT", ..., 55);
            dword_53B03 = malloc(64000);
            break;
    }
}
```

---

## 七、事件数据使用示例

### 7.1 完整加载流程

```c
// 1. 分配场景缓冲区（40个条目 × 未知大小）
v1 = sub_3702F(40);
sub_10652(v1);  // 根据n17加载场景资源

// 2. 加载文本数据
dword_53A79 = sub_111BA("FDTXT.DAT", ..., n13 + 1);

// 3. 加载地图资源
dword_53A59 = sub_111BA("FDFIELD.DAT", ..., 3*n13 + 2);  // 事件数据
dword_53A55 = sub_111BA("FDFIELD.DAT", ..., 3*n13 + 1);  // Control数据
dword_53A51 = sub_111BA("FDFIELD.DAT", ..., 3*n13);      // Layout数据

// 4. 提取地图尺寸
dword_53AC1 = *(int16_t*)dword_53A51;           // 宽度
dword_53AC5 = *(int16_t*)(dword_53A51 + 2);     // 高度

// 5. 加载瓦片集
v2 = 2 * *(uint8_t*)dword_53A55;                // terrain_set_id * 2
FDSHAP_DAT = sub_111BA("FDSHAP.DAT", ..., v2);
dword_53A69 = sub_111BA("FDSHAP.DAT", ..., v2 + 1);

// 6. 处理瓦片数据
sub_4DF4C(dword_53A51);

// 7. 提取控制信息
n6 = *(uint8_t*)(dword_53A55 + 1);              // ally_max
dword_53BE3 = *(uint8_t*)(dword_53A55 + 2);     // enemy_total

// 8. 分配事件缓冲区
dword_53A45 = malloc(7680);  // 96个事件 × 80字节 = 7680

// 9. 打开图标文件并处理事件
v9 = fopen("FDICON.B24", "rb");
v4 = event_data + 6 * dword_53BE3 + 2;
v5 = dword_53BF7;
for (n6 = 0; n6 < enemy_total; n6++) {
    // ... 处理每个事件 ...
}
fclose(v9);

// 10. 释放事件数据
free(dword_53A59);
dword_53A59 = 0;
```

---

## 八、关键发现

### 8.1 事件数据格式

事件数据使用**6字节/条目**的紧凑格式：
```
byte[0]: 类型标志
byte[1]: X坐标相关
byte[2]: Y坐标相关
byte[3]: terrain_ref
byte[4]: 字段4
byte[5]: 字段5
```

### 8.2 事件条目结构

每个事件在内存中扩展为**80字节**的完整结构：
- 包含从事件数据提取的信息
- 包含从模板数据复制的信息
- 包含计算后的坐标信息
- 包含图标引用

### 8.3 图标加载

事件图标从**FDICON.B24**文件加载：
- 使用`sub_11019`函数
- 参数是事件条目中的`byte[7]`（terrain_ref）
- 返回图标在内存中的位置

### 8.4 坐标计算

事件坐标通过`sub_1B750`函数计算：
1. 从事件数据读取基础坐标
2. 累加8个可能的偏移量（每个由标志位控制）
3. 可能的缩放处理（使用`dbl_5018D`常量）
4. 存储计算结果到事件条目

---

## 九、C代码实现建议

### 9.1 事件数据结构定义

```c
#define FD2_MAX_EVENTS 96
#define FD2_EVENT_ENTRY_SIZE 80

typedef struct {
    uint8_t type;           // 类型标志
    uint8_t coord_x;        // X坐标（原始）
    uint8_t coord_y;        // Y坐标（原始）
    uint8_t terrain_ref;    // 地形引用（用于加载图标）
    uint8_t field_4;
    uint8_t field_5;
} fd2_event_data_t;  // 6字节/条目

typedef struct {
    uint8_t data[FD2_EVENT_ENTRY_SIZE];  // 80字节完整条目
} fd2_event_entry_t;

typedef struct {
    uint16_t event_count;
    fd2_event_data_t* events;
    fd2_event_entry_t entries[FD2_MAX_EVENTS];
} fd2_map_events_t;
```

### 9.2 事件加载函数

```c
int fd2_map_events_load(fd2_map_events_t* events, 
                        const char* fdfield_path, int map_id,
                        const uint8_t* control_data) {
    // 1. 加载FDFIELD.DAT
    // 2. 提取事件数据（3*map_id + 2）
    // 3. 解析6字节/条目的事件数据
    // 4. 初始化80字节/条目的完整结构
    // 5. 加载FDICON.B24图标
    // 6. 调用sub_1B750计算坐标
}
```

---

*分析日期: 2026-04-30*
*来源: IDA MCP反编译 sub_1088D, sub_10652, sub_1B750, sub_4DF4C, sub_10B4E*
*验证状态: 待C代码实现验证*
