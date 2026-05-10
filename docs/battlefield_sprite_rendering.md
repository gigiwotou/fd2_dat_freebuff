# FD2 战场精灵渲染与死亡角色过滤分析

> 来源: IDA Pro MCP 逆向分析 FD2.EXE  
> 日期: 2026-05-07  
> 状态: 基于汇编分析，已验证

---

## 一、死亡角色过滤逻辑

### 1.1 核心函数: sub_14818

**函数地址**: 0x14818

**功能**: 构建可显示角色索引列表，过滤死亡角色

**IDA反编译代码**:
```c
for ( n6 = 0; n6 < n6_0; ++n6 ) {
    v19 = (unsigned __int8 *)(80 * n6 + dword_53A45);  // 角色数据结构(80字节)
    
    if ( (v19[5] & 1) == 0  // ← 关键：offset+5 的 bit0 必须为 0 才显示
      && *(unsigned __int8 *)(4 * (n9_3 * v19[1] + *v19) + dword_53A51 + 7) != 255
      && (!n2 && !v19[6] || n2 == 1 && v19[6] || n2 == 2 && v19[6] == 1 || n2 == 3 && v19[6] == 2) )
    {
      if ( a7 )
        *(_BYTE *)(v22 + a7) = n6;  // 将角色索引加入显示列表
      ++v22;
    }
}
```

### 1.2 过滤规则

| 条件 | 说明 |
|------|------|
| `(offset+5 & 1) == 0` | **bit0 == 0** = 存活显示，**bit0 == 1** = 死亡隐藏 |
| 地图位置标记 != 255 | 角色必须在有效地图位置 |
| 阵营匹配 (n2参数) | `n2=0`: 无阵营, `n2=1`: 阵营0, `n2=2`: 阵营1, `n2=3`: 阵营2 |

### 1.3 角色数据结构 (offset+5详解)

```c
struct char_data_80 {
    uint8_t x;              // 偏移0: X坐标
    uint8_t y;              // 偏移1: Y坐标
    uint8_t icon_loaded;    // 偏移2: 图标加载结果
    uint8_t field_3;        // 偏移3: 未知
    uint8_t portrait_id;    // 偏移4: 肖像ID
    uint8_t active_byte;    // 偏移5: bit0=死亡标志 (0=存活, 1=死亡)
    uint8_t field_6;        // 偏移6: 阵营/类型
    uint8_t icon_id;        // 偏移7: 原始图标ID
    // ... 共80字节
};
```

---

## 二、战场精灵渲染调用链

### 2.1 完整调用链

```
sub_15055 (战斗入口)
  └─> sub_14818 (构建可显示角色索引列表)
       └─> 过滤条件: (offset+5 & 1) == 0
  └─> sub_20C6F (处理战斗逻辑)
       └─> sub_1C4CC (渲染装饰背景图层)
            └─> sub_4EBAB (在地图缓冲区绘制装饰)
            └─> sub_11EB0 + sub_17AA9 (渲染到屏幕)
       └─> sub_1C2DA (渲染地图精灵)
            └─> 遍历活跃角色索引数组
            └─> 绘制角色精灵到地图
```

### 2.2 调用关系表

| 函数 | 地址 | 功能 | 调用者 |
|------|------|------|--------|
| sub_14818 | 0x14818 | 构建可显示角色列表 | sub_15055, sub_1CFF0 |
| sub_1C4CC | 0x1C4CC | 渲染装饰背景图层 | sub_20C6F |
| sub_1C2DA | 0x1C2DA | 渲染地图精灵 | sub_20C6F |
| sub_20C6F | 0x20C6F | 战斗逻辑处理 | sub_15055 |
| sub_15055 | 0x15055 | 战斗入口 | sub_14EF0 |

---

## 三、装饰图层渲染 (sub_1C4CC)

### 3.1 函数原型

```c
int __fastcall sub_1C4CC(
    __int32 a1,
    int a2,
    int a3,
    int a4,
    int a5,
    int n9,        // 装饰图层类型ID
    int a7,        // 角色数量
    int a8         // 角色索引数组指针
);
```

### 3.2 功能说明

在角色所在tiles上绘制背景装饰元素：
- 地面装饰（草丛、花朵等）
- 障碍物遮挡层
- 特殊地形效果

### 3.3 核心逻辑

```c
// 1. 初始化临时地图缓冲区
v10 = malloc(153217);  // 分配地图数据缓冲区
memmove(v17, dword_53A49, 153217);  // 复制原始地图数据

// 2. 遍历装饰图层
for ( n3 = 0; n3 < (unsigned __int8)dst__1[n9]; ++n3 ) {
    // 获取装饰数据指针
    v18 = (__int16 *)(dword_53AD1 + *(dword_53AD1 + 4 * (n3 + dst_[n9]) + 6));
    
    // 恢复原始地图数据
    memmove(dword_53A49, v17, 153217);
    
    // 3. 对每个角色位置绘制装饰
    for ( i = 0; i < a7; ++i ) {
        // 获取角色坐标: offset+0=x, offset+1=y
        v10 = dword_53A45 + 80 * *(i + a8);
        tile_x = *(v10);
        tile_y = *(v10 + 1);
        
        // 检查角色是否在屏幕范围内
        if ( tile_x >= n9-1 && tile_x <= dword_51A87+n9 &&
             tile_y >= n34-1 && tile_y <= dword_51A8B+n34+1 ) {
            // 计算地图缓冲区偏移
            v9 = dword_53A49 + 32904 + 24 * (tile_x - n9);
            offset = 10944 * (tile_y - n34) - 2736;
            
            // 调用sub_4EBAB在地图上绘制装饰元素
            sub_4EBAB((_BYTE *)(v9 + offset), v18, 456);
        }
    }
    
    // 4. 渲染装饰图层到屏幕
    sub_11EB0(656644, 320, dword_53A49 + 32904, 456, 312, 192);
    sub_17AA9(v10, ..., 1);  // 执行实际渲染
    
    // 5. 特殊音效触发
    if ( n9 == 22 && n3 == 7 )
        sub_25A96(dword_53B13, 3, 1);
    else if ( n9 == 25 && (n3 == 3 || n3 == 6) )
        sub_25A96(dword_53B13, 5, 1);
    else if ( n9 == 18 && n3 == 4 )
        sub_25A96(dword_53B13, 7, 1);
    // ... 更多条件
}

free(v17);
```

### 3.4 装饰图层类型

| n9值 | 说明 | 特殊音效触发条件 |
|------|------|------------------|
| 18 | 地形装饰A | n3 == 4 时播放音效7 |
| 19 | 地形装饰B | n3 == 3或6 时播放音效8 |
| 22 | 地形装饰C | n3 == 7 时播放音效3 |
| 25 | 地形装饰D | n3 == 3或6 时播放音效5 |
| 8 | 地形装饰E | n3 == 3或6 时播放音效10 |
| 9 | 地形装饰F | n3 == 15或19 时播放音效15 |

### 3.5 与精灵渲染的关系

- `sub_1C4CC` 在角色精灵渲染**之前**被调用
- 负责在地图tiles上绘制背景装饰
- `sub_1C2DA` 将角色精灵**叠加**在这些装饰之上
- **与死亡过滤无关**，死亡过滤在`sub_14818`中完成

---

## 四、实现位置

### 4.1 代码位置

**死亡过滤实现**: [fd2_battle.c L160-L167](file:///d:/testworkspace/fd2_dat_freebuff/src/fd2_battle.c#L160-L167)

```c
/* IDA sub_14818: 检查 offset+5 的 bit0
   (v19[5] & 1) == 0 才显示在战场上
   bit0 == 1 表示死亡角色，不显示 */
if ((data->char_data[i].active_byte & 1) != 0) {
    printf("  char[%d]: SKIP (dead, offset+5=0x%02X bit0=1)\n", i, data->char_data[i].active_byte);
    continue;
}
```

**数据结构定义**: [fd2_battle.h L34](file:///d:/testworkspace/fd2_dat_freebuff/include/fd2_battle.h#L34)

```c
uint8_t active_byte;    /* offset+5: bit0=death flag (0=alive/show, 1=dead/hidden) */
```

---

## 五、关键全局变量

| 变量名 | 地址 | 说明 |
|--------|------|------|
| dword_53A45 | 0x53A45 | 角色数组基址（80字节/角色） |
| dword_53A49 | 0x53A49 | 地图数据缓冲区 |
| dword_53A51 | 0x53A51 | Layout数据指针 |
| dword_53AD1 | 0x53AD1 | 装饰数据索引表 |
| dword_53B13 | 0x53B13 | FDOTHER.DAT资源指针（音效） |
| n9_3 | - | 地图可见区域起始X |
| n34 | - | 地图可见区域起始Y |
| dword_51A87 | 0x51A87 | 地图可见宽度 |
| dword_51A8B | 0x51A8B | 地图可见高度 |

---

## 六、测试验证

### 6.1 验证方法

1. 加载包含死亡角色的存档
2. 检查输出日志中是否有 `SKIP (dead, offset+5=0xXX bit0=1)` 信息
3. 确认死亡角色未显示在战场上

### 6.2 预期结果

- 死亡角色的 `offset+5` 字段 bit0 应为 1
- 这些角色应被过滤，不加入精灵渲染列表
- 战场上只显示存活角色

---

## 七、参考资料

- [战场逻辑分析](battlefield_logic_analysis.md)
- [战场光标逻辑](battlefield_cursor_logic.md)
- [FD2.SAV存档格式](continue-battle-save-restore-analysis.md)

---

*分析完成时间: 2026-05-07*  
*分析师: IDA Pro MCP + Qwen3.6-Plus*  
*状态: 已验证实现*
