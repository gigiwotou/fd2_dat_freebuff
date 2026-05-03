# FD2 战场逻辑研究说明

> 来源: IDA Pro MCP 逆向分析 FD2.EXE
> 日期: 2026-05-03
> 状态: 基于汇编分析，持续完善中

---

## 一、战场整体架构

### 1.1 游戏三层状态机

FD2使用三层状态机管理战场逻辑：

| 层级 | 变量 | 说明 |
|------|------|------|
| 外层状态 | n2_0 | 控制游戏主阶段（0=输入处理, 1=过渡, 2=战斗场景） |
| 内层状态 | n17 | 控制具体场景类型（地图索引0-32） |
| 模式状态 | n44 | 控制输入处理模式（移动/事件/菜单等） |

### 1.2 战场状态流转

```
游戏启动
    ↓
[INTRO] 开场动画 (sub_1F894)
    ↓ (自动)
[MENU] 主菜单 (sub_20421)
    ↓ (选择"开始游戏" + Start)
[BATTLE] 战场状态 ←────────────────┐
    │                               │
    ├── n2_0=0: 主输入处理 (sub_117E7)
    │   ├── 角色移动 (n44=1,44,76)
    │   ├── 事件触发 (n44=57,28)
    │   └── 菜单系统 (n44=59,73)
    │                               │
    ├── n2_0=1: 过渡状态 (sub_22E5C)
    │   └── 加载新资源并渲染
    │                               │
    └── n2_0=2: 战斗场景
        ├── 场景处理 (funcs_25E23)
        ├── 渲染 (sub_26152)
        └── 后续处理 (funcs_25E3A)
```

---

## 二、关键函数地址与功能

### 2.1 核心战场函数

| 函数 | 地址 | 功能 |
|------|------|------|
| sub_1088D | 0x1088D | **地图加载主函数** - 加载FDFIELD.DAT三部分数据 |
| sub_10010 | 0x10010 | **战场存档加载** - 从FD2.SAV恢复战场状态 |
| sub_117E7 | 0x117E7 | **主输入处理** - 处理角色移动、事件触发 |
| sub_18890 | 0x18890 | **战斗执行** - 执行战斗逻辑，返回战斗结果 |
| sub_16F55 | 0x16F55 | **战斗等待** - 等待战斗结束 |
| sub_1B750 | 0x1B750 | **事件位置计算** - 计算事件最终显示位置 |
| sub_22E5C | 0x22E5C | **场景过渡** - 加载新资源并渲染 |
| sub_25EBB | 0x25EBB | **游戏入口** - 主循环入口点 |

### 2.2 资源加载函数

| 函数 | 地址 | 功能 |
|------|------|------|
| sub_111BA | 0x111BA | **DAT资源加载器** - 通用DAT文件资源加载 |
| sub_4DF4C | 0x4DF4C | **瓦片数据处理** - 处理Layout数据中的地形ID |
| sub_11019 | 0x11019 | **图标加载** - 从FDICON.B24加载图标 |
| sub_4E98D | 0x4E98D | **RLE解压缩** - 解压缩RLE图像数据 |
| sub_4E22A | 0x4E22A | **RLE解压缩** - 基础RLE解压缩函数 |

### 2.3 渲染与显示函数

| 函数 | 地址 | 功能 |
|------|------|------|
| sub_1F525 | 0x1F525 | **屏幕刷新** - 刷新显示屏幕 |
| sub_11EB0 | 0x11EB0 | **帧复制** - 复制帧到视频缓冲区 |
| sub_1ACF3 | 0x1ACF3 | **瓦片渲染** - 渲染单个瓦片 |
| sub_12E38 | 0x12E38 | **地形ID提取** - 从Layout数据提取地形ID |
| sub_26152 | 0x26152 | **场景渲染** - 渲染场景画面 |

### 2.4 音效与音乐函数

| 函数 | 地址 | 功能 |
|------|------|------|
| sub_25A96 | 0x25A96 | **音效播放** - 播放数字音效 |
| sub_25977 | 0x25977 | **音乐播放** - 播放XMIDI音乐 |
| sub_25B45 | 0x25B45 | **XMIDI序列** - 播放XMIDI音乐序列 |

### 2.5 工具函数

| 函数 | 地址 | 功能 |
|------|------|------|
| sub_11CAC | 0x11CAC | **淡入淡出** - 调色板淡入淡出效果 |
| sub_1E292 | 0x1E292 | **交互结果处理** |
| sub_13565 | 0x13565 | **返回值处理** |
| sub_12C0D | 0x12C0D | **查找可交互对象** |
| sub_17AED | 0x17AED | **普通交互处理** |

---

## 三、地图加载详细流程 (sub_1088D)

### 3.1 函数签名

```c
int sub_1088D(int map_id);  // n13 = map_id (0-32)
```

### 3.2 资源加载步骤

```c
// 1. 加载FDTXT.DAT（地图文本）
dword_53A79 = sub_111BA("FDTXT.DAT", dword_53A79, map_id + 1);

// 2. 加载FDFIELD.DAT的三个部分（索引 = 3 * map_id + part_index）
dword_53A59 = sub_111BA("FDFIELD.DAT", ..., 3*map_id + 2);  // 角色位置数据
dword_53A55 = sub_111BA("FDFIELD.DAT", ..., 3*map_id + 1);  // 控制数据
dword_53A51 = sub_111BA("FDFIELD.DAT", ..., 3*map_id);      // 布局数据

// 3. 从布局数据读取地图尺寸
dword_53AC1 = *(__int16 *)dword_53A51;        // map_width
dword_53AC5 = *(__int16 *)(dword_53A51 + 2);  // map_height

// 4. 从控制数据读取参数
terrain_set_id = *(uint8_t *)dword_53A55;        // control_data[0]
::n6 = *(uint8_t *)(dword_53A55 + 1);            // control_data[1] = max_friendly
dword_53BE3 = *(uint8_t *)(dword_53A55 + 2);     // control_data[2] = total_units

// 5. 加载FDSHAP.DAT的tileset
v2 = 2 * terrain_set_id;
FDSHAP_DAT = sub_111BA("FDSHAP.DAT", FDSHAP_DAT, v2);        // 调色板
dword_53A69 = sub_111BA("FDSHAP.DAT", dword_53A69, v2 + 1);  // 瓦片集

// 6. 处理布局数据中的瓦片信息
sub_4DF4C(dword_53A51);

// 7. 分配角色数据内存：96 * 80 = 7680字节
dword_53A45 = malloc(7680);

// 8. 打开FDICON.B24图标文件
v9 = fopen("FDICON.B24", "rb");

// 9. 计算角色位置数据指针（跳过敌人位置）
v4 = (_BYTE *)(dword_53A59 + 6 * dword_53BE3 + 2);

// 10. 循环处理每个己方角色
for (n6 = 0; n6 < ::n6; ++n6) {
    if (条件满足) {
        memmove(v3, v5, 80);          // 复制模板数据
        *v3 = *v4;                    // X坐标
        v3[1] = v4[2];                // Y坐标
        v4 += 6;
        v3[2] = sub_11019(v3[7], v9); // 加载图标
        v3[3] = 0;
        v3[4] = 0;
        v3[6] = 2;
        v3[49] = -1;
        memset(v3 + 34, 0, 6);
        sub_1B750(n6);                // 计算位置
        v5 += 80;
        ++v10;
    } else {
        memset(v3, 0, 80);
        v3[5] = 1;                    // 空位标记
    }
    v3 += 80;
}

fclose(v9);
free(dword_53A59);
dword_53A59 = 0;

return sub_10B4E(0);
```

### 3.3 FDFIELD.DAT资源索引

```
索引号 = 3 * map_id + part_index

part_index:
  0 = 布局数据（地图瓦片构成）
  1 = 控制数据（地形集、角色数量等）
  2 = 角色位置数据（敌人+己方角色位置）

文件偏移 = 4 * index + 6
```

### 3.4 数据结构

#### Layout数据（布局）

```c
uint16_t map_width;    // 字节0-1: 地图宽度
uint16_t map_height;   // 字节2-3: 地图高度
// 之后是 width * height 个瓦片数据，每个4字节
```

#### 瓦片4字节格式

```
字节0: terrain_id的低8位
字节1: (terrain_flag << 8) | terrain_id的高2位
       其中terrain_flag = byte[1] & 0x03
字节2: event_type & 0x1F
字节3: 设为0xFF（标记位）

地形ID = byte[0] | ((byte[1] & 3) << 8)  // 范围0-1023
```

#### Control数据（控制）

```c
uint8_t terrain_set_id;  // 字节0: 地形图集ID
uint8_t max_friendly;    // 字节1: 己方最大人数
uint8_t total_units;     // 字节2: 敌人总数
// 之后是回合事件、宝箱、敌人信息等...
```

#### 角色位置数据

```c
uint16_t total_count;    // 字节0-1: 角色总数

// 从字节2开始是每个角色的位置数据，每角色6字节：
struct char_position {
    uint8_t x;          // 字节0: X坐标
    uint8_t unknown1;   // 字节1: 未知（始终为0）
    uint8_t y;          // 字节2: Y坐标
    uint8_t unknown2;   // 字节3: 未知（始终为0）
    uint8_t portrait;   // 字节4: 肖像ID
    uint8_t unknown3;   // 字节5: 未知（始终为0）
};

// 前total_units个位置是敌人/NPC
// 后max_friendly个位置是己方角色
```

---

## 四、角色系统

### 4.1 角色内存结构（80字节）

```c
struct char_data_80 {
    uint8_t x;              // 偏移0: X坐标
    uint8_t y;              // 偏移1: Y坐标
    uint8_t icon_loaded;    // 偏移2: 图标加载结果
    uint8_t field_3;        // 偏移3: 设为0
    uint8_t field_4;        // 偏移4: 设为0
    uint8_t flag;           // 偏移5: 标志位（0=正常，1=空位）
    uint8_t field_6;        // 偏移6: 固定值2
    uint8_t icon_id;        // 偏移7: 原始图标ID
    uint8_t field_8;        // 偏移8: 阵营
    // ...
    uint8_t field_34_39[6]; // 偏移34-39: 清零
    // ...
    uint8_t field_49;       // 偏移49: 0xFF
    // ...总共80字节
    
    // 坐标字段（sub_1B750计算后）
    uint16_t final_x;       // 偏移55-56: 最终X坐标
    uint16_t final_y;       // 偏移57-58: 最终Y坐标
    uint16_t final_h;       // 偏移62-63: 最终高度
    uint16_t calc_x;        // 偏移72-73: 计算后X坐标
    uint16_t calc_y;        // 偏移74-75: 计算后Y坐标
    uint16_t calc_h;        // 偏移76-77: 计算后高度
};
```

### 4.2 角色位置计算 (sub_1B750)

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

### 4.3 全局角色变量

| 变量名 | 地址 | 说明 |
|--------|------|------|
| dword_53A45 | 0x53A45 | 角色数组基址（80字节/角色，最多96个） |
| dword_53AC1 | 0x53AC1 | 地图宽度 |
| dword_53AC5 | 0x53AC5 | 地图高度 |
| dword_53BE3 | 0x53BE3 | 敌人总数 |
| ::n6 | - | 己方最大人数 |
| dword_53BFB | 0x53BFB | 最大角色数量 |
| dword_53BF7 | 0x53BF7 | 角色模板数据指针 |

---

## 五、战斗系统

### 5.1 战斗触发条件

```c
if (n2 == 2 && (char)v16[5] >= 0 && !v16[38]) {
    // n2 == 2: 角色类型为2
    // v16[5] >= 0: 角色状态标志
    // !v16[38]: 未被触发过
    
    // 播放音效
    sub_25A96(dword_53EEC, 7, 1);
    
    // 等待战斗结束
    while (!sub_18890(v13));
}
else {
    sub_17AED(v13, a1);  // 普通交互
}

sub_11CAC(0);           // 淡入淡出
sub_1E292(v13);         // 处理交互结果
v18 = funcs_1197B[n17](v13);  // 调用场景处理函数
sub_13565(v18);         // 处理返回值
```

### 5.2 战斗函数 (sub_18890)

```c
int sub_18890(int char_index);
```

**功能**: 执行战斗逻辑，返回战斗结果

**参数**:
- `char_index`: 角色索引

**返回值**:
- 0: 战斗继续
- 1: 战斗结束
- -1: 战斗失败

### 5.3 战斗等待循环

```c
do {
    v14 = sub_16F55();  // 等待战斗结束
} while (!v14);

if (v14 == 1)
    return 0;  // 战斗胜利，继续
return v15;    // 战斗失败/逃跑，返回状态
```

---

## 六、输入处理 (sub_117E7)

### 6.1 函数签名

```c
int sub_117E7(
    unsigned __int8 *a1@<edi>,
    __int32 a2@<eax>,
    int a3@<edx>,
    int a4@<ecx>
);
```

### 6.2 主输入循环

```c
// 检查事件冷却计时器
if (byte_51A42)
    --byte_51A42;

v12 = sub_12C0D();  // 查找可交互对象
if (v12 != -1) {
    v16 = (_BYTE *)(dword_53A45 + 80 * v12);
    if (v16[7] != 121 && v16[31] != 10) {
        // 检查战斗触发条件
        if (n2 == 2 && (char)v16[5] >= 0 && !v16[38]) {
            // 战斗触发
            sub_25A96(dword_53EEC, 7, 1);
            while (!sub_18890(v13));  // 等待战斗结束
        }
        else {
            sub_17AED(v13, a1);  // 普通交互
        }
        
        sub_11CAC(0);           // 淡入淡出
        sub_1E292(v13);         // 处理交互结果
        v18 = funcs_1197B[n17](v13);  // 调用场景处理函数
        sub_13565(v18);         // 处理返回值
        if (n255 != 255)
            funcs_1199C[n255](v13);  // 调用扩展处理函数
        n255 = 255;
    }
}
```

### 6.3 输入处理模式 (n44)

| 模式值 | 说明 |
|--------|------|
| 1 | 角色移动 |
| 28 | 事件触发 |
| 44 | 角色移动（另一种模式） |
| 57 | 事件触发（另一种模式） |
| 59 | 菜单系统 |
| 72 | 音效处理 |
| 73 | 菜单系统（另一种模式） |
| 75 | 音效处理 |
| 76 | 角色移动（第三种模式） |
| 77 | 音效处理 |
| 80 | 音效处理 |

---

## 七、战场存档系统

### 7.1 存档加载 (sub_10010)

```c
void sub_10010(
    __int32 a1@<eax>,
    int a2@<edx>,
    int a3@<ecx>,
    int n99@<ebx>,
    unsigned __int8 *a5@<edi>
);
```

**功能**: 从FD2.SAV加载战场存档数据

**存档数据结构**:
- 总大小: 22987 字节
- 包含: 地图数据、角色数据、状态变量、校验和

### 7.2 存档恢复流程

```c
// 1. 停止当前音乐
sub_25977(-1, 0);

// 2. 加载战场存档
sub_10010(...);

// 3. 播放场景音乐
sub_25977(byte_51E63[n17], 0);

// 4. 进入主循环
```

---

## 八、场景处理函数表

### 8.1 场景处理函数表 (funcs_1197B)

| 索引 | 场景 | 说明 |
|------|------|------|
| 0-32 | 各地图 | 地图特定的场景处理函数 |

### 8.2 扩展处理函数表 (funcs_1199C)

| 索引 | 说明 |
|------|------|
| 0-255 | 扩展事件处理函数 |

---

## 九、渲染系统

### 9.1 瓦片渲染 (sub_1ACF3)

```c
void sub_1ACF3(
    __int32 a1,
    int a2,
    int a3,
    int a4,
    int a5,        // 目标缓冲区偏移
    int n456       // 目标缓冲区宽度（stride）
);
```

**关键逻辑**:
```c
// 调用sub_12E38提取地形ID和相关数据
sub_12E38(dword_53AB1, dword_53AB5, v12);

// 使用地形ID从FDSHAP_DAT读取瓦片数据
sub_4E22A(
    (char *)(FDSHAP_DAT + *(DWORD *)(FDSHAP_DAT + 4 * v12[0] + 6)),  // src
    (char *)(v6 + 5 * n456 + 6),  // dst
    n456  // stride
);
```

### 9.2 地形ID提取 (sub_12E38)

```c
char sub_12E38(
    __int32 a1,
    int a2,
    int a3,
    int a4,
    int a5,   // x坐标
    int a6,   // y坐标
    int a7    // 输出缓冲区指针
);
```

**关键逻辑**:
```c
// 计算瓦片在layout中的偏移
v7 = *(WORD *)(dword_53A51 + 4 * (x + dword_53AC1 * y) + 4);
HIBYTE(v7) &= 3u;  // 高字节 & 3

v8 = *(BYTE *)(dword_53A51 + 4 * (x + dword_53AC1 * y) + 6) & 0x1F;
*(WORD *)a7 = v7;       // 存储地形ID到a7[0-1]
*(WORD *)(a7 + 2) = v8; // 存储byte[2]&0x1F到a7[2-3]

// 从dword_53A69（瓦片集资源）读取4字节
v9 = (BYTE *)(4 * v7 + dword_53A69);
a7[4] = v9[0];
a7[5] = v9[1];
a7[6] = v9[2];
a7[7] = v9[3];
```

---

## 十、RLE解压缩系统

### 10.1 基础RLE解压缩 (sub_4E22A)

```c
char sub_4E22A(
    char *src,    // RLE压缩数据源
    char *dst,    // 解压缩目标缓冲区
    int stride    // 目标行宽度
);
```

**RLE编码格式**:
```
操作码字节 (opcode):
- Bit7=1, Bit6=1: SKIP (跳过count像素)
- Bit7=1, Bit6=0: COPY (复制count字节)
- Bit7=0, Bit6=0: FILL (填充count字节)
- Bit7=0, Bit6=1: ALTERNATE (每隔一个像素写入)

count = (opcode & 0x3F) + 1  (范围1-64)
```

**四种操作模式**:

| 模式 | Bit7 | Bit6 | 说明 |
|------|------|------|------|
| SKIP | 1 | 1 | 跳过count像素（透明区域） |
| COPY | 1 | 0 | 复制count字节原始数据 |
| FILL | 0 | 0 | 用单色填充count像素 |
| ALTERNATE | 0 | 1 | 每隔一个像素写入相同值 |

### 10.2 高级RLE解压缩 (sub_4E98D)

```c
char sub_4E98D(
    __int16 *a1,      // RLE压缩数据（包含头部）
    int a2,           // 目标基址
    int a3,           // 起始行
    int a4,           // 起始列
    int a5,           // 目标宽度（stride）
    int value_1       // 填充值
);
```

**三种value_1模式**:

| 模式 | value_1 | 说明 |
|------|---------|------|
| 直接模式 | -1 | 原始像素数据 |
| 重映射模式 | >255 | 使用调色板重映射 |
| 单色模式 | <=255 | 固定颜色填充 |

---

## 十一、音效系统

### 11.1 音效播放 (sub_25A96)

```c
void sub_25A96(
    int a1,
    int sample_index,  // FDOTHER.DAT资源索引
    int a3
);
```

**常用音效索引**:
- 索引2: 全局音效
- 索引7: 特殊音效
- 索引-1: 停止所有音效

### 11.2 音乐播放 (sub_25977)

```c
void sub_25977(
    int midi_index,  // XMIDI序列索引
    int a2
);
```

**常用音乐索引**:
- 索引1: 战斗BGM
- 索引2: 菜单BGM/场景音乐
- 索引3: 停止音乐
- 索引7: 胜利音乐
- 索引12: 胜利/升级
- 索引36: 剧情对话

---

## 十二、关键全局变量

### 12.1 地图相关

| 变量名 | 地址 | 说明 |
|--------|------|------|
| dword_53A45 | 0x53A45 | 角色数组基址（80字节/角色） |
| dword_53A51 | 0x53A51 | Layout数据指针 |
| dword_53A55 | 0x53A55 | Control数据指针 |
| dword_53A59 | 0x53A59 | 角色位置数据指针 |
| dword_53AC1 | 0x53AC1 | 地图宽度 |
| dword_53AC5 | 0x53AC5 | 地图高度 |
| dword_53BE3 | 0x53BE3 | 敌人总数 |
| dword_53BDF | 0x53BDF | 事件计数器 |
| dword_53BFB | 0x53BFB | 最大角色数量 |
| dword_53BF7 | 0x53BF7 | 角色模板数据指针 |

### 12.2 场景相关

| 变量名 | 地址 | 说明 |
|--------|------|------|
| dword_53AFF | 0x53AFF | 场景背景缓冲区 |
| dword_53B03 | 0x53B03 | FDOTHER.DAT资源指针 |
| n17 | - | 当前场景索引 |
| n2_0 | - | 外层状态 |
| n44 | - | 输入处理模式 |

### 12.3 视频/图形

| 变量名 | 地址 | 说明 |
|--------|------|------|
| 0x655360 | 0xA0000 | 视频缓冲区（64000字节，mode 13h） |
| dword_53BF7 | - | 调色板缓冲区（2560字节） |
| dword_53AD5 | - | 调色板数据（32字节） |

### 12.4 DAT指针

| 变量名 | 地址 | 说明 |
|--------|------|------|
| dword_53E00 | 0x53E00 | FDOTHER.DAT指针 |
| dword_53A59 | 0x53A59 | FDFIELD.DAT指针 |
| dword_53A79 | 0x53A79 | FDTXT.DAT指针 |
| dword_53A5D | 0x53A5D | FDSHAP.DAT指针 |
| dword_53AC1 | 0x53AC1 | FDMUS.DAT指针 |

---

## 十三、战场状态机详细流程

### 13.1 主循环 (sub_25EBB)

```c
int sub_25EBB() {
    // 根据n2_0进入不同状态
    switch (n2_0) {
        case 0:
            // 主输入处理
            return sub_117E7(...);
        case 1:
            // 过渡/加载状态
            return sub_22E5C(...);
        case 2:
            // 战斗场景处理
            v = funcs_25E23[n17](...);
            sub_26152(...);
            return funcs_25E3A[n17](...);
    }
}
```

### 13.2 场景处理循环

```c
// 输入处理循环
while (1) {
    keys = sub_10620();  // 键盘检测
    update_action_state(keys);
    
    // 处理角色移动
    // 处理事件触发
    // 处理菜单
    
    // 检查是否触发战斗
    if (战斗条件) {
        while (!sub_18890(char_index));  // 等待战斗结束
    }
}

// 战斗等待循环
do {
    v = sub_16F55();
} while (!v);

if (v == 1)
    return 0;  // 战斗胜利
return v15;    // 战斗失败
```

---

## 十四、函数指针表

### 14.1 场景处理函数表 (funcs_1197B)

```c
int (*funcs_1197B[33])(int char_index);
```

每个地图有特定的场景处理函数。

### 14.2 扩展处理函数表 (funcs_1199C)

```c
int (*funcs_1199C[256])(int char_index);
```

扩展事件处理函数。

### 14.3 场景入口函数表 (funcs_25E23)

```c
int (*funcs_25E23[33])(...);
```

场景进入时调用的函数。

### 14.4 场景退出函数表 (funcs_25E3A)

```c
int (*funcs_25E3A[33])(...);
```

场景退出时调用的函数。

---

## 十五、待深入分析的领域

### 15.1 高优先级

1. **伤害计算函数** - 需要进一步IDA分析sub_18890内部逻辑
2. **AI决策逻辑** - 敌方角色移动和攻击选择
3. **回合处理** - 回合切换、回合事件触发
4. **技能系统** - 技能选择、MP消耗、效果计算
5. **经验值与升级** - 升级条件、属性增长

### 15.2 中优先级

6. **物品系统** - 道具使用、装备管理
7. **商店系统** - 买卖逻辑、价格计算
8. **转职系统** - 职业转换、条件判断
9. **魔法系统** - 魔法学习、效果计算
10. **地形效果** - 地形对战斗的影响

### 15.3 低优先级

11. **隐藏要素** - 隐藏角色、隐藏物品
12. **多结局** - 结局条件、分支判断
13. **难度系统** - 难度对游戏的影响

---

## 十六、下一步行动计划

### 16.1 短期计划

1. 使用IDA MCP深入分析sub_18890战斗函数
2. 分析AI决策逻辑相关函数
3. 分析回合处理相关函数
4. 分析伤害计算相关函数

### 16.2 中期计划

5. 实现C代码版本的战场逻辑
6. 测试验证战场逻辑的正确性
7. 完善角色系统、战斗系统
8. 实现AI逻辑

### 16.3 长期计划

9. 实现完整的回合制战斗系统
10. 实现角色成长系统
11. 实现物品、商店、转职系统
12. 实现多结局系统

---

## 十七、参考资料

- [游戏状态机分析](game_state_machine_analysis.md)
- [FDFIELD.DAT解析](fdfield_ida_analysis.md)
- [地图事件数据分析](map_event_data_analysis.md)
- [Continue战场存档恢复](continue-battle-save-restore-analysis.md)
- [游戏循环状态机分析](game-loop-states-analysis.md)
- [核心函数调用分析](core-functions-usage-analysis.md)
- [逆向工程指南](reverse-engineering.md)
- [FD2逆向工程与移植指南](FD2_REVERSE_ENGINEERING.md)

---

*分析完成时间: 2026-05-03*
*分析师: IDA Pro MCP + Qwen3.6-Plus*
*状态: 基于汇编分析，持续完善中*
