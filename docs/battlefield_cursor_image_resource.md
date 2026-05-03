# FD2 战场地图光标图像资源分析

> 来源: IDA Pro MCP 逆向分析 FD2.EXE
> 日期: 2026-05-03
> 分析状态: 基于汇编反编译，1:1还原

---

## 一、概述

战场地图中的光标不是简单的几何图形，而是从 **FDOTHER.DAT** 资源文件加载的 **RLE格式图像**。光标有动画效果，会在不同帧之间切换。

---

## 二、光标图像资源

### 2.1 图像数据来源

| 变量 | 地址 | 说明 |
|------|------|------|
| dword_53A81 | 0x53A81 | 光标图像数据源指针（来自FDOTHER.DAT） |
| n242 | - | 光标图像帧ID（242或1） |

### 2.2 图像帧切换逻辑

根据IDA sub_1ACF3函数：

```c
if (byte_51AAB && byte_51AAC) {
    if (n2_1 <= 5 || n10 >= 3) {
        if (n2_1 > 5 && n10 > 9)
            n242 = 1;        // 移动到右下角时：帧1
    }
    else {
        n242 = 242;          // 移动到左上角时：帧242
    }
    
    v6 = n242 + 157 * n456 + a5;
    sub_4E98D((__int16 *)(*(_DWORD *)(dword_53A81 + 526) + dword_53A81), 0, 0, v6, n456, -1);
}
```

**光标帧ID**：
- **n242 = 242**: 光标在左上角区域（n2_1 <= 5 || n10 < 3）
- **n242 = 1**: 光标在右下角区域（n2_1 > 5 && n10 > 9）

### 2.3 图像绘制函数

**sub_4E98D** - RLE图像绘制核心函数

```c
char sub_4E98D(
    __int16 *arg0,      // 图像数据指针（包含头部）
    int arg4,           // 目标X坐标
    int arg8,           // 目标Y坐标
    int argC,           // 额外偏移
    int arg10,          // 目标宽度（stride）
    int value_1         // 绘制模式（-1=直接模式）
);
```

**调用参数**（来自sub_1ACF3）：
```c
sub_4E98D(
    (__int16 *)(*(_DWORD *)(dword_53A81 + 526) + dword_53A81),  // 图像数据
    0,    // X坐标
    0,    // Y坐标
    v6,   // 偏移量 (n242 + 157 * n456 + a5)
    n456, // stride
    -1    // 直接模式
);
```

---

## 三、图像数据结构

### 3.1 dword_53A81 数据结构

```c
// dword_53A81 指向 FDOTHER.DAT 加载的图像数据
struct fdother_image_data {
    // 头部...
    uint32_t image_offset;   // 偏移526 (0x20E)：图像数据偏移
    // ...
};

// 图像数据访问：
uint16_t* image_data = (uint16_t*)(*(uint32_t*)(dword_53A81 + 526) + dword_53A81);
```

### 3.2 sub_4E98D 图像头部格式

```c
struct rle_image_header {
    uint16_t width;    // arg0[0]: 图像宽度（像素）
    uint16_t height;   // arg0[1]: 图像高度（像素）
    uint8_t  rle_data[];  // arg0[2]: RLE压缩数据
};
```

### 3.3 RLE编码格式

根据sub_4E98D分析，RLE编码使用操作码字节：

| Bit7 | Bit6 | 模式 | 说明 |
|------|------|------|------|
| 0 | 0 | SKIP | 跳过count像素（透明区域） |
| 0 | 1 | FILL | 填充count像素为单一颜色 |
| 1 | 0 | COPY | 复制count字节原始数据 |
| 1 | 1 | ALTERNATE | 每隔一个像素写入相同值 |

**count = (opcode & 0x3F) + 1**（范围1-64）

---

## 四、光标渲染完整流程

### 4.1 sub_1ACF3 函数完整逻辑

**地址**: 0x1ACF3

**函数签名**:
```c
void sub_1ACF3(
    __int32 a1,
    int a2,
    int a3,
    int a4,
    int a5,       // 额外参数
    int n456      // 目标宽度（stride）
);
```

**完整逻辑**:
```c
void sub_1ACF3(__int32 a1, int a2, int a3, int a4, int a5, int n456) {
    sub_3702F(56);  // 分配栈空间
    
    // 检查是否显示光标
    if (byte_51AAB && byte_51AAC) {
        // 根据移动计数器决定光标帧
        if (n2_1 <= 5 || n10 >= 3) {
            if (n2_1 > 5 && n10 > 9)
                n242 = 1;        // 右下角区域：帧1
        } else {
            n242 = 242;          // 左上角区域：帧242
        }
        
        // 计算光标图像偏移
        v6 = n242 + 157 * n456 + a5;
        
        // 绘制光标图像
        sub_4E98D(
            (__int16 *)(*(_DWORD *)(dword_53A81 + 526) + dword_53A81),
            0, 0, v6, n456, -1
        );
        
        // 提取地形ID
        sub_12E38(v12, a2, a3, a4, dword_53AB1, dword_53AB5, (int)v12);
        
        // 绘制地形瓦片
        sub_4E22A(
            (char *)(dword_53A5D + *(_DWORD *)(dword_53A5D + 4 * v12[0] + 6)),
            (char *)(v6 + 5 * n456 + 6),
            n456
        );
        
        // 绘制其他元素...
        sub_1AEB1(v6 + 8 * n456 + 43, n456, dword_51A12[v13]);
        sub_1AEB1(v6 + 19 * n456 + 43, n456, dword_51A2A[v13]);
        
        // 查找光标位置的角色
        v9 = sub_12C0D(...);
        if (v9 != -1) {
            v10 = 80 * v9 + dword_53A45;
            if (*(_BYTE *)(v10 + 7) != 121 && 
                (*(_BYTE *)(v10 + 31) != 10 || *(_BYTE *)(v10 + 6) != 1)) {
                // 绘制角色图标
                src = (char *)(dword_53A61 + *(_DWORD *)(dword_53A61 + 4 * (12 * *(unsigned __int8 *)(v10 + 2) + n3)));
                sub_4E22A(src, (char *)(v6 + 5 * n456 + 6), n456);
                sub_1875D(...);
            }
        }
    }
}
```

---

## 五、控制变量

### 5.1 光标显示控制

| 变量 | 地址 | 说明 |
|------|------|------|
| byte_51AAB | 0x51AAB | 光标显示标志1 |
| byte_51AAC | 0x51AAC | 光标显示标志2 |

**条件**: `byte_51AAB && byte_51AAC` 为真时才绘制光标

### 5.2 移动计数器

| 变量 | 说明 |
|------|------|
| n2_1 | 垂直移动计数器（控制上下移动） |
| n10 | 水平移动计数器（控制左右移动） |

---

## 六、光标帧切换规则

### 6.1 帧ID计算

```
if (n2_1 <= 5 || n10 >= 3):
    if (n2_1 > 5 && n10 > 9):
        n242 = 1    # 帧1
    else:
        n242 = n242 # 保持当前帧
else:
    n242 = 242      # 帧242
```

### 6.2 触发条件

| 区域 | 条件 | 帧ID |
|------|------|------|
| 左上角 | n2_1 <= 5 || n10 < 3 | 242 |
| 右下角 | n2_1 > 5 && n10 > 9 | 1 |
| 其他 | - | 保持当前帧 |

---

## 七、图像加载流程

### 7.1 FDOTHER.DAT 加载

```c
// 战场初始化 (sub_205DA)
fd2_resources_load_dat(&game->resources, FD2_DAT_FDOTHER);

// 获取FDOTHER数据指针
dword_53A81 = fd2_resources_get(&game->resources, FD2_DAT_FDOTHER, 0, &size);
```

### 7.2 图像数据访问

```c
// 从dword_53A81获取图像数据
uint32_t image_offset = *(uint32_t*)(dword_53A81 + 526);
uint16_t* image_data = (uint16_t*)(image_offset + dword_53A81);

// 图像头部
uint16_t width = image_data[0];
uint16_t height = image_data[1];
uint8_t* rle_data = (uint8_t*)(image_data + 2);
```

---

## 八、sub_4E98D 绘制模式

### 8.1 三种绘制模式

| value_1 | 模式 | 说明 |
|---------|------|------|
| -1 | 直接模式 | 直接写入像素数据 |
| >255 | 重映射模式 | 使用调色板重映射 |
| <=255 | 单色模式 | 固定颜色填充 |

### 8.2 直接模式（value_1 = -1）

光标绘制使用此模式：
- 直接读取RLE数据并写入目标缓冲区
- 不进行颜色重映射
- 支持SKIP、COPY、FILL、ALTERNATE四种操作

---

## 九、完整渲染流程

```
战场渲染循环
    ↓
sub_1ACF3 (光标渲染主函数)
    ↓
1. 检查 byte_51AAB && byte_51AAC
    ↓
2. 根据 n2_1, n10 决定 n242 (242 或 1)
    ↓
3. 计算图像偏移 v6 = n242 + 157 * n456 + a5
    ↓
4. sub_4E98D(...) 绘制光标图像
    ↓
5. sub_12E38(...) 提取地形ID
    ↓
6. sub_4E22A(...) 绘制地形瓦片
    ↓
7. sub_1AEB1(...) 绘制其他元素
    ↓
8. sub_12C0D() 查找光标位置角色
    ↓
9. 如果找到角色:
    ├── sub_4E22A(...) 绘制角色图标
    └── sub_1875D(...) 绘制角色信息
```

---

## 十、关键发现

### 10.1 光标不是几何图形

- 光标是从 **FDOTHER.DAT** 加载的 **RLE格式图像**
- 有**两种帧**（242和1），根据位置切换
- 使用 **sub_4E98D** 函数绘制

### 10.2 图像资源索引

- **dword_53A81**: FDOTHER.DAT 加载的基址指针
- **偏移526**: 图像数据偏移量存储位置
- **图像数据**: *(uint32_t*)(dword_53A81 + 526) + dword_53A81

### 10.3 光标帧切换

- **帧242**: 光标在左上角区域
- **帧1**: 光标在右下角区域
- 切换条件基于移动计数器 n2_1 和 n10

---

## 十一、C代码实现要点

### 11.1 光标图像结构

```c
typedef struct {
    uint16_t width;
    uint16_t height;
    uint8_t  rle_data[];  // RLE压缩数据
} fd2_cursor_image_t;
```

### 11.2 图像加载

```c
// 从FDOTHER.DAT加载光标图像
const u8* fdother_data = fd2_resources_get(&resources, FD2_DAT_FDOTHER, 0, &size);
uint32_t image_offset = *(uint32_t*)(fdother_data + 526);
uint16_t* image_data = (uint16_t*)(image_offset + fdother_data);

// 保存光标图像指针
cursor_image = (fd2_cursor_image_t*)image_data;
```

### 11.3 帧选择

```c
int cursor_frame_id;
if (move_counter_y <= 5 || move_counter_x >= 3) {
    if (move_counter_y > 5 && move_counter_x > 9)
        cursor_frame_id = 1;
} else {
    cursor_frame_id = 242;
}
```

---

*分析完成时间: 2026-05-03*
*分析师: IDA Pro MCP + Qwen3.6-Plus*
*分析状态: 基于汇编反编译，1:1还原*
