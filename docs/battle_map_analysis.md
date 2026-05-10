# 战场地图逻辑分析

> 基于IDA Pro MCP反编译分析，1:1还原原始游戏战场地图逻辑

## 核心文件依赖

| 文件名 | 用途 | 加载位置 |
|--------|------|----------|
| FD2.SAV | 存档文件，包含游戏状态和地图数据 | sub_10010 |
| FDFIELD.DAT | 战场地图布局数据 | sub_10010, sub_1088D |
| FDSHAP.DAT | 地形瓦片形状数据 | sub_10010, sub_1088D |
| FDOTHER.DAT | 其他地图资源（背景、特效等） | sub_10010, sub_10652 |
| FDTXT.DAT | 文本数据 | sub_10010, sub_1088D |
| FDICON.B24 | 图标数据 | sub_10010, sub_10B4E |
| BG.DAT | 背景数据 | sub_2D80D |
| TAI.DAT | 地形数据 | sub_2D80D |
| FIGANI.DAT | 角色动画数据 | sub_2D80D |

## 核心函数分析

### 1. sub_10010 - 游戏初始化函数

**功能**: 从存档加载游戏数据，初始化所有地图资源

**流程**:
```
1. 读取FD2.SAV存档文件(22987字节)
2. 验证存档校验和
3. 加载FDOTHER.DAT (索引: 3*n17+2)
4. 分配2211字节内存存储地图配置
5. 加载FDTXT.DAT (索引: n17+1)
6. 加载FDFIELD.DAT (索引: 3*n17)
7. 解析地图尺寸 (word_53AC1, word_53AC5)
8. 加载FDSHAP.DAT (索引: 2*地形集ID)
9. 加载FDSHAP.DAT+1 (索引: 2*地形集ID+1)
10. 处理图标数据(FDICON.B24)
11. 写入临时文件FD2.TMP
12. 初始化战场场景
13. 播放开场动画(9帧，每帧70ms延迟)
14. 显示标题画面
```

**关键全局变量**:
- `dword_53BF7` - 地图布局数据指针(2560字节)
- `dword_53A59` - FDOTHER.DAT数据指针
- `dword_53A55` - 地图配置数据指针(2211字节)
- `dword_53A51` - FDFIELD.DAT数据指针
- `dword_53AC1` - 地图宽度
- `dword_53AC5` - 地图高度
- `dword_53A45` - 图标数据指针(7680字节)
- `n6` - 瓦片集ID
- `dword_53BE3` - 地形集ID
- `dword_53BEF` - 调色板相关

### 2. sub_1088D - 地图场景加载函数

**原型**: `int __cdecl sub_1088D(int map_id)`

**功能**: 根据地图ID加载对应的场景数据

**流程**:
```
1. 加载FDTXT.DAT (索引: map_id+1)
2. 加载FDFIELD.DAT (索引: 3*map_id+2) - 地图布局
3. 加载FDFIELD.DAT (索引: 3*map_id+1) - 地形配置
4. 加载FDFIELD.DAT (索引: 3*map_id)   - 地图头信息
5. 解析地图尺寸
6. 加载FDSHAP.DAT (索引: 2*地形集ID)
7. 加载FDSHAP.DAT (索引: 2*地形集ID+1)
8. 分配7680字节图标内存
9. 遍历地图单元(n6次循环):
   - 检查条件: (map_id>=13 || 单元!=6 || 特殊标志==2) && 计数器<n7
   - 复制80字节单元数据
   - 设置瓦片属性
   - 调用sub_11019处理图标
   - 调用sub_1B750初始化单元
10. 清理FDOTHER.DAT
11. 返回sub_10B4E(0)
```

### 3. sub_10652 - 地图数据解析函数

**功能**: 根据不同的地图类型(n17)加载对应的地图资源

**地图类型处理**:
```c
switch (n17) {
    case 9, 24, 25:
        // 标准战场
        加载FDOTHER.DAT(索引15)
        分配64000字节战场缓冲区
        break;
    
    case 17, 21, 22, 27:
        // 特殊地形战场
        switch (n17) {
            case 21: 宽度=408, 高度=276, 索引=35; break;
            case 22: 宽度=408, 高度=256, 索引=40; break;
            case 27: 高度=244, 索引=46; break;
        }
        分配(宽度*高度)字节
        加载FDOTHER.DAT(索引)
        解压上半部分到缓冲区
        加载FDOTHER.DAT(索引+1)
        解压下半部分到缓冲区
        break;
    
    case 23:
        // 室内场景
        分配59904字节
        加载FDOTHER.DAT(索引42)
        解压(312宽度)
        break;
    
    case 28, 29:
        // 其他战场
        加载FDOTHER.DAT(索引55)
        分配64000字节
        break;
}
```

### 4. sub_4E98D - RLE解压缩函数

**原型**: `char __cdecl sub_4E98D(__int16 *compressed_data, int dst_base, int y_offset, int dst, int stride, int value)`

**功能**: 解压RLE压缩的地图瓦片数据

**压缩格式**:
- 每个字节的高2位表示类型，低6位表示长度
- 类型0: 复制数据 (src复制到dst)
- 类型1: 填充相同值 (memset)
- 类型2: 重复单字节 (交替写入)
- 类型3: 跳过 (dst前进，不写入)

**三种解压模式**:
1. `value == -1`: 直接复制模式
2. `value > 0xFF`: 调色板偏移模式，使用value + ((value>>8) + data) & 7
3. `value <= 0xFF`: 固定值填充模式，全部填充value

**关键变量**:
- `count` - 当前行已处理像素数
- `word_627B6` - 剩余行数

### 5. sub_2EB9F - 地图渲染封装函数

**原型**: `char __cdecl sub_2EB9F(int data_file, int index, int dst, int stride, int value)`

**功能**: 封装sub_4E98D调用，从数据文件中提取并解压瓦片

**流程**:
```
1. 计算数据偏移: data_file + 4*index + 8
2. 获取压缩数据指针: *(data_ptr) + data_file + 9
3. 调用sub_4E98D解压到目标缓冲区
```

### 6. sub_11EB0 - 内存复制辅助函数

**原型**: `int __cdecl sub_11EB0(int dst, int dst_stride, int src, int src_stride, int size, int rows)`

**功能**: 按行复制内存，支持不同跨距

**流程**:
```c
for (i = 0; i < rows; i++) {
    memmove(dst, src, size);
    dst += dst_stride;
    src += src_stride;
}
```

### 7. sub_2D80D - 战场场景渲染主函数

**原型**: `int __fastcall sub_2D80D(__int32 a1, int a2, int a3, int n2_1, int unit_idx, int scene_type, int n30, unsigned __int8 *a8)`

**功能**: 完整的战场场景渲染，包括背景、地形、单位、特效

**渲染流程**:
```
1. 获取单元数据(80*n2_1 + dword_53A45)
2. 调用sub_12E38解析单元信息
3. 加载TAI.DAT(地形数据)
4. 加载BG.DAT(背景数据)
5. 分配64000字节主缓冲区
6. 分配128000字节辅助缓冲区
7. 初始化主缓冲区为0
8. 调用sub_4E98D解压背景
9. 调用sub_2FACD处理地形
10. 调用sub_1F882后处理
11. 加载FIGANI.DAT(角色动画)
12. 加载FDOTHER.DAT(其他资源)
13. 调用sub_2E9A8初始化单位
14. 调用sub_30E9D处理单位渲染

15. 渲染角色动画(8层):
    for (i = 0; i < 8; i++) {
        sub_11EB0(复制缓冲区)
        sub_2EB9F(渲染FIGANI.DAT第i层)
        sub_11EB0(上传到屏幕655360)
        sub_17AA9(翻转显示, 延迟)
    }

16. 渲染特效层(8到0):
    for (i = 8; i >= 0; i--) {
        sub_11EB0(复制缓冲区)
        sub_2EB9F(渲染FDOTHER.DAT第i层)
        sub_11EB0(上传到屏幕)
        sub_17AA9(翻转显示, 延迟)
    }

17. 根据scene_type渲染特殊效果:
    case 32: 调用sub_2111A
    case 33: 调用sub_211A4
    case 34: 调用sub_22721, sub_22866, sub_22997
    case 35: 调用sub_22D1B (3次不同参数)

18. 淡入动画:
    for (i = 0; i <= 40; i++) {
        sub_2DF01(调色板淡入)
        delay(6ms)
    }

19. 根据scene_type调用后续处理:
    case 32: sub_2111A(unit_idx, n30, a8, 32)
    case 33: sub_211A4(unit_idx, n30, a8, 950)
    case 34: sub_22997(unit_idx, n30, a8)
    case 35: sub_22D1B(unit_idx, 27, n30, a8, 38)
```

### 8. sub_24754 - 过场场景函数

**功能**: 战场过渡动画和场景切换

**流程**:
```
1. 显示对话框
2. 根据sub_24B14(100)结果选择对话分支
3. 播放多段对话动画
4. 调用sub_2189A显示单位
5. 调用sub_24B4D延迟
6. 淡出动画(64步, 每步4ms)
7. 加载新地图数据:
   - FDFIELD.DAT(索引69)
   - FDSHAP.DAT(索引46)
   - FDSHAP.DAT(索引47)
8. 调用sub_10652解析地图
9. 调用sub_135DD设置场景
10. 淡入动画
11. 调用sub_1366A(73)显示新场景
```

## 数据结构

### 地图单元结构 (80字节)

```c
struct MapUnit {
    BYTE tile_type;      // +0: 瓦片类型
    BYTE terrain_type;   // +1: 地形类型
    BYTE icon_index;     // +2: 图标索引
    BYTE unknown_3;      // +3: 未知
    BYTE unknown_4;      // +4: 未知
    BYTE flag;           // +5: 标志位
    BYTE unknown_6;      // +6: 未知
    BYTE unit_id;        // +7: 单位ID
    // ... 其他字段
    BYTE unknown_34[6];  // +34: 未知
    BYTE npc_id;         // +49: NPC ID (-1表示无)
};
```

### 地图头信息

```c
struct MapHeader {
    WORD width;          // +0: 地图宽度
    WORD height;         // +2: 地图高度
    // ... 其他字段
};
```

### 地形配置

```c
struct TerrainConfig {
    BYTE terrain_set_id;  // +0: 地形集ID
    BYTE tile_set_id;     // +1: 瓦片集ID
    BYTE other_id;        // +2: FDOTHER索引
};
```

## 渲染管线

```
┌─────────────────────────────────────────────────────────────────┐
│                        战场渲染管线                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 数据加载阶段:                                                 │
│     FD2.SAV → FDFIELD.DAT → FDSHAP.DAT → FDOTHER.DAT            │
│                                                                 │
│  2. 解析阶段:                                                     │
│     sub_10652() 解析地图配置                                      │
│     sub_1088D() 加载场景数据                                      │
│                                                                 │
│  3. 解压阶段:                                                     │
│     sub_4E98D() RLE解压瓦片数据                                   │
│     sub_2EB9F() 封装解压调用                                      │
│                                                                 │
│  4. 渲染阶段:                                                     │
│     背景层: sub_4E98D(BG.DAT)                                    │
│     地形层: sub_2FACD() + sub_1F882()                            │
│     单位层: sub_2E9A8() + sub_30E9D()                            │
│                                                                 │
│  5. 合成阶段:                                                     │
│     角色动画: FIGANI.DAT (8层, 从下到上)                          │
│     特效层: FDOTHER.DAT (9层, 从上到下)                           │
│                                                                 │
│  6. 显示阶段:                                                     │
│     sub_11EB0() → 屏幕缓冲区(655360)                              │
│     sub_17AA9() → 翻转显示                                        │
│                                                                 │
│  7. 后处理:                                                       │
│     sub_2DF01() → 调色板淡入/淡出                                 │
│     sub_25A96/sub_25B45() → 特效处理                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 关键地址和常量

| 常量 | 值 | 说明 |
|------|-----|------|
| 屏幕缓冲区 | 655360 (0xA0000) | 320x200 256色模式 |
| 战场缓冲区 | 64000 (0xFA00) | 320x200 战场渲染缓冲 |
| 辅助缓冲区 | 128000 (0x1F400) | 双缓冲或特效缓冲 |
| 图标数据 | 7680 (0x1E00) | 96个图标x80字节 |
| 地图配置 | 2211 (0x8A3) | 地图配置数据大小 |
| 存档大小 | 22987 (0x59CB) | FD2.SAV文件大小 |
| 地图单元 | 80 (0x50) | 每个单元数据大小 |
| 最大单元数 | 96 | 地图最大单元数量 |

## 坐标系统

- 屏幕分辨率: 320x200
- 颜色模式: 256色(8位)
- 瓦片大小: 可变(根据地形集)
- 地图单元: 80字节/单元

## 战场逻辑架构

### 核心发现：函数表驱动的场景逻辑

原游戏**不是**每个场景都有独立的逻辑函数，而是采用**函数表驱动**的设计：

- `funcs_30469` (地址0x524C6) 是一个包含10个函数指针的数组
- 每个场景类型(n28)对应函数表中的一个索引
- 所有场景共享同一个主渲染函数 `sub_2FF01`，通过函数表调用场景特定的渲染逻辑

### 场景逻辑函数表 (funcs_30469)

| 索引 | 函数地址 | 函数名 | 适用场景类型 | 说明 |
|------|----------|--------|-------------|------|
| 0 | 0x2B996 | sub_2B996 | n28=0 | 标准室内场景 |
| 1 | 0x2BB33 | sub_2BB33 | n28=1 | 标准室外场景 |
| 2 | 0x2BD6C | sub_2BD6C | n28=2 | 特殊过渡场景 |
| 3 | 0x2BFD9 | sub_2BFD9 | n28=3 | 战斗场景 |
| 4 | 0x2C217 | sub_2C217 | n28=4 | 剧情场景 |
| 5 | 0x2C441 | sub_2C441 | n28=5 | 对话场景 |
| 6 | 0x2C67D | sub_2C67D | n28=6 | 菜单场景 |
| 7 | 0x2C9FC | sub_2C9FC | n28=7 | 特殊效果场景 |
| 8 | 0x2CCF4 | sub_2CCF4 | n28=8 | 商店场景 |
| 9 | 0x2CE1A | sub_2CE1A | n28=9 | 过场动画场景 |

### sub_2FF01 - 战场渲染主调度函数

**原型**: `int __fastcall sub_2FF01(__int32 a1, int a2, int n11, int a4, int arg0, int n28, int n30, unsigned __int8 *p_n6)`

**功能**: 统一的战场渲染调度器，根据n28场景类型调用对应的场景逻辑函数

**渲染阶段**:

```
1. 初始化阶段 (0x2FF01-0x300A8):
   - 释放旧的地图资源
   - 解析当前单元数据(80*arg0 + dword_53A45)
   - 调用sub_12E38解析单元信息
   - 加载BG.DAT和TAI.DAT

2. 场景分支阶段 (0x2FFFA-0x3003F):
   if (n28 >= 32)
     return sub_2D80D(...);  // 特殊场景(32-35)
   if (n28 == 24 || n28 > 27)
     return sub_2CF30(...);  // 其他特殊场景
   // 否则继续标准渲染流程

3. 渲染循环阶段:
   - 初始化: v67 = funcs_30469[n28](arg0, _FDOTHER.DAT_, v18, 320, 0)
   - 主循环: for (i = 0; i < v67; ++i)
     - 复制缓冲区
     - funcs_30469[n28](arg0, _FDOTHER.DAT_, v28, 640, 1)
     - 渲染角色动画
     - funcs_30469[n28](arg0, _FDOTHER.DAT_, _FIGANI.DAT__1, 640, 2)
     - 上传到屏幕并显示

4. 多单位渲染阶段:
   for (n30_3 = 0; n30_3 < n30; ++n30_3)
     v67 = funcs_30469[n28](arg0, _FDOTHER.DAT_, v18, 320, 3)
     for (j = 0; j < v67; ++j)
       funcs_30469[n28](..., 4)
       funcs_30469[n28](..., 5)
     单位间过渡: sub_31266(...)

5. 最终渲染阶段:
   v67 = funcs_30469[n28](arg0, _FDOTHER.DAT_, v18, 320, 6)
   for (k = 0; k < v67; ++k)
     funcs_30469[n28](..., 7)
     funcs_30469[n28](..., 8)
```

**场景逻辑函数接口**:
```c
int scene_logic_func(
    int unit_idx,      // 当前单元索引
    int fdother_data,  // FDOTHER.DAT数据指针
    int buffer,        // 渲染缓冲区
    int stride,        // 缓冲区跨距
    int phase          // 渲染阶段 (0-8)
);
```

**渲染阶段(phase)说明**:
- phase 0: 初始化，返回渲染帧数
- phase 1: 角色动画层渲染
- phase 2: 特效层渲染
- phase 3: 多单位场景初始化
- phase 4: 单位特效层1
- phase 5: 单位特效层2
- phase 6: 最终场景初始化
- phase 7: 最终特效层1
- phase 8: 最终特效层2

### 特殊场景处理

**n28 >= 32**: 调用 sub_2D80D
- case 32: 室内对话场景
- case 33: 剧情过场场景
- case 34: 多选项对话场景
- case 35: 特殊战斗场景

**n28 == 24 || n28 > 27**: 调用 sub_2CF30
- 其他特殊场景类型

## 注意事项

1. 所有数据加载都通过sub_111BA函数，该函数负责从DAT文件中提取数据
2. RLE压缩使用自定义格式，需要正确解析高2位类型和低6位长度
3. 渲染采用分层合成，角色动画和特效层需要按正确顺序渲染
4. 调色板动画通过sub_2DF01实现淡入淡出效果
5. 不同地图类型(n17)对应不同的资源加载逻辑
