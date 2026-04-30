# FDICON.B24 图标格式分析

**更新日期**: 2026-04-30
**基于**: IDA MCP sub_11019 (0x11019) + 实际文件分析

---

## 一、文件结构

```
FDICON.B24 (624010 bytes)
├─ 字节 0-5: 头部
│   └─ 18 00 18 00 90 06
├─ 字节 6-6725: 偏移表
│   ├─ 6720字节 = 1680 DWORDs
│   └─ 140图标 × 12段 + 4额外DWORD
└─ 字节 6730+: 图标数据区
    ├─ 图标0: 5251字节 (偏移6730-11981)
    ├─ 图标1: 4862字节 (偏移11981-16843)
    ├─ ...
    └─ 图标139: 24字节
```

## 二、图标分段结构

每个图标有**12段**，对应**4方向×3帧**：

| 段索引 | 方向 | 帧 |
|--------|------|-----|
| 0 | 正面 (Front) | 帧0 |
| 1 | 正面 (Front) | 帧1 |
| 2 | 正面 (Front) | 帧2 |
| 3 | 左面 (Left) | 帧0 |
| 4 | 左面 (Left) | 帧1 |
| 5 | 左面 (Left) | 帧2 |
| 6 | 背面 (Back) | 帧0 |
| 7 | 背面 (Back) | 帧1 |
| 8 | 背面 (Back) | 帧2 |
| 9 | 右面 (Right) | 帧0 |
| 10 | 右面 (Right) | 帧1 |
| 11 | 右面 (Right) | 帧2 |

## 三、段数据格式

### 3.1 数据大小

段大小范围：24-500字节（压缩后）
平均大小：~400字节

### 3.2 压缩编码

段数据使用**RLE变体压缩**（Run-Length Encoding）。

从实际数据分析：

```
示例：Icon 0, Segment 0 (449 bytes)
First 20 bytes: c5 04 6f c1 04 6f c5 c4 80 6f 03 f3 81 6f 68 02 f3 81 6f 6f

模式推测：
- c5 04 6f: 可能表示 (count=0xc5, value=0x04, palette_index=0x6f)
- 或: (command=0xc5, count=0x04, color=0x6f)
```

### 3.3 编码特征

1. **没有0x00或0xFF字节** - 所有字节都是有效的颜色索引或命令
2. **字节值范围0x01-0xD7** - 说明使用了特殊编码
3. **重复模式** - 如c5 04 6f反复出现，表明是RLE类编码
4. **段间相似性** - 相邻段的数据高度相似（同一方向的不同帧）

## 四、sub_11019 函数

### 4.1 函数签名

```c
int sub_11019(int icon_id, FILE* fd);
```

### 4.2 功能

1. 读取FDICON.B24偏移表（从字节6开始，6720字节）
2. 提取指定图标的13个偏移量（12段 + 1用于计算大小）
3. 计算数据大小：`data_size = offsets[12] - offsets[0]`
4. 检查缓存：如果图标已加载，返回缓存索引
5. 首次加载：
   - 分配207362字节缓冲区（dword_53A61）
   - 从文件读取数据到`缓冲区 + 1920`
   - 存储调整后的偏移量到缓冲区头部
6. 后续加载：追加到缓冲区末尾

### 4.3 调用者

```c
// sub_1088D (地图加载)
v3[2] = sub_11019((unsigned __int8)v3[7], v9);
// v3[7]是事件条目中的图标ID
// v3[2]存储缓存索引
// v9是FDICON.B24文件句柄
```

## 五、全局变量

| 变量 | 地址 | 说明 |
|------|------|------|
| dword_53A61 | 0x53A61 | 图标缓冲区指针 |
| dword_53BDF | 0x53BDF | 已缓存图标计数 |
| dword_53B17 | 0x53B17 | 已缓存图标ID数组 |
| buf | N/A | 缓冲区写入指针 |

## 六、事件条目中的图标引用

事件条目（80字节）结构：

```c
struct EventEntry {
    uint8_t  byte_0;      // 类型
    uint8_t  byte_1;      // 坐标
    uint8_t  byte_2;      // 图标缓存索引（sub_11019返回值）
    uint8_t  byte_3;      // 清零
    uint8_t  byte_4;      // 清零
    uint8_t  byte_5;      // 标志
    uint8_t  byte_6;      // 固定值2
    uint8_t  byte_7;      // 图标ID（传递给sub_11019）
    // ... 更多字段
};
```

## 七、解码实现建议

### 7.1 段数据解码

```c
// 伪代码 - 需要进一步IDA分析确认
int decode_segment(const uint8_t* compressed, int size, 
                   uint8_t* output, int max_output) {
    int in_pos = 0;
    int out_pos = 0;
    
    while (in_pos < size && out_pos < max_output) {
        uint8_t cmd = compressed[in_pos++];
        
        if (cmd & 0x80) {
            // 可能是重复命令
            int count = cmd & 0x7F;
            uint8_t value = compressed[in_pos++];
            for (int i = 0; i < count; i++) {
                output[out_pos++] = value;
            }
        } else {
            // 可能是直接复制
            int count = cmd;
            for (int i = 0; i < count; i++) {
                output[out_pos++] = compressed[in_pos++];
            }
        }
    }
    
    return out_pos;
}
```

### 7.2 图像尺寸

可能的尺寸（基于段大小分析）：
- 16×16 = 256字节（未压缩）
- 24×24 = 576字节（未压缩）
- 压缩后：200-500字节

---

*分析基于: IDA MCP + 实际FDICON.B24文件（624010字节，140图标）*
*验证状态: 段数据格式待确认*
