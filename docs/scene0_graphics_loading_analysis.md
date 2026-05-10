# 场景0图形加载完整分析

## 1. sub_4E809(n17) 分析

### 函数原型
```c
char *__cdecl sub_4E809(int a1)
{
  return (char *)&unk_6238D + 31 * a1 - 31;
}
```

### 功能说明
- **地址**: 0x4E809
- **大小**: 0x16 (22字节)
- **功能**: 场景元数据表读取函数
- **返回值**: 指向场景元数据表的指针，每个场景元数据占31字节

### 元数据表结构
```c
typedef struct fd2_scene_metadata {
    u8 field_0;       /* +0 - 场景类型标识 */
    u8 field_1;       /* +1 - FDOTHER.DAT资源索引 */
    u16 field_2_3;    /* +2 */
    u16 field_4_5;    /* +4 */
    u8 field_6;       /* +6 */
    u8 field_7;       /* +7 */
    u8 field_8;       /* +8 */
    u16 field_9_A;    /* +9 */
    u16 field_B_C;    /* +11 */
    u16 field_D_E;    /* +13 */
    u8 field_F;       /* +15 */
    u8 field_10;      /* +16 */
    u8 field_11_1F[15]; /* +17 ~ +31 */
} fd2_scene_metadata_t;
```

### 当n17=0时的返回值
- **调用**: `sub_4E809(0)`
- **返回**: `&unk_6238D + 31 * 0 - 31 = &unk_6238D - 31`
- **注意**: 这个返回值指向场景元数据表之前的区域，可能用于特殊场景或错误处理

---

## 2. 场景0战场地图加载流程

### 主调用函数: sub_26152
- **地址**: 0x26152
- **调用者**: 0x25bf4, 0x25ebb
- **关键流程**:

```c
// 1. 检查是否为特殊场景
if (byte_523E7[n17]) {
    // 特殊场景处理 (场景0可能属于此类)
    memset(655360, 0, 64000);
    // ... 标题画面渲染
} else {
    // 普通场景处理
    n7 = malloc(153216);  // 分配场景数据缓冲区
    v16 = sub_4E809(n17); // 获取场景元数据
    dword_53F56 = v16;    // 保存元数据指针
    LOBYTE(i) = *(_BYTE *)v16;  // 获取场景类型标识
    
    // 加载FDOTHER.DAT资源
    v17 = sub_111BA(..., FDOTHER_DAT, ..., i);
    sub_4E98D(v17, 0, 0, n7 + 32904, 456, -1);  // 解压场景图形
    free(v17);
    
    // 加载另一个资源
    dword_53F5A = sub_111BA(..., FDOTHER_DAT, ..., 10);
}
```

### 关键变量
- `n7`: 场景数据缓冲区 (153216字节)
- `n7 + 32904`: 解压后的场景图形数据存储位置
- `dword_53F56`: 场景元数据指针
- `byte_523E7[n17]`: 特殊场景标志

---

## 3. FDOTHER.DAT索引分析

### 场景0使用的索引
从sub_26152分析：
```c
// 第一个资源加载
v17 = sub_111BA(..., FDOTHER_DAT, ..., i);  // i = *(_BYTE *)sub_4E809(n17)
sub_4E98D(v17, 0, 0, n7 + 32904, 456, -1);

// 第二个资源加载  
dword_53F5A = sub_111BA(..., FDOTHER_DAT, ..., 10);
```

### 场景0背景资源
- **主背景索引**: 由`*(_BYTE *)sub_4E809(n17)`决定，即场景元数据的第一个字节
- **辅助资源索引**: 10 (固定)

### 渲染时使用的资源
```c
// sub_265EC中的渲染
sub_15F84(..., n5 + 495, ...);  // 文本渲染
sub_4E22A(..., dst, 456);       // 光标复制
sub_11EB0(...);                 // 屏幕区域更新
```

---

## 4. sub_4E98D解压分析

### 函数原型
```c
char __cdecl sub_4E98D(__int16 *arg0, int arg4, int arg8, int argC, int arg10, int value_1)
```

### 参数说明
- `arg0`: 压缩数据源指针 (前2字节包含宽高信息)
- `arg4`: 目标缓冲区基础地址
- `arg8`: 额外偏移
- `argC`: 列偏移
- `arg10`: 行宽 (456字节)
- `value_1`: 颜色值模式 (-1=原始颜色, 其他=基于value_1的偏移)

### 解压算法
这是**RLE变体解压算法**，支持三种模式：

#### 模式1: value_1 == -1 (原始颜色)
```c
// 控制字节分析
value = *src++;
v12 = 2 * value;

if (__CFSHL__(value, 1)) {  // 最高位为1
    if (__CFSHL__(v12, 1)) {  // 次高位为1
        // 跳过模式: 跳过 (value >> 2) + 1 个字节
        count_1 = ((value * 4) >> 2) + 1;
        dst += count_1;
        count -= count_1;
    } else {  // 次高位为0
        // 复制模式: 复制 (value >> 2) + 1 个字节
        count_1 = ((value * 4) >> 2) + 1;
        qmemcpy(dst, src, count_1);
        src += count_1;
        dst += count_1;
    }
} else {  // 最高位为0
    // 填充模式: 用指定值填充
    count_1 = ((value * 4) >> 2) + 1;
    value = *src++;
    memset(dst, value, count_1);
    dst += count_1;
}
```

#### 模式2: value_1 > 0xFF (调色板偏移模式)
- 使用`value_1 + ((BYTE1(value_1) + v23) & 7)`计算颜色值
- 支持8种颜色偏移

#### 模式3: value_1 <= 0xFF (单色模式)
- 所有非跳过操作都使用`value_1`作为颜色值

### 关键特性
1. **按行处理**: 使用`word_627B6`作为行数计数器
2. **行间距处理**: 每行结束后`dst += v8` (v8 = arg10 - count)
3. **压缩效率**: 控制字节高2位决定操作类型，低6位决定长度

---

## 5. 场景0完整加载和渲染流程

### 阶段1: 初始化
```
sub_26152() 被调用
  ↓
检查 byte_523E7[n17] (特殊场景标志)
  ↓
如果是特殊场景: 走标题画面流程
如果不是: 走战场地图流程
```

### 阶段2: 资源加载 (战场地图)
```
1. n7 = malloc(153216)                    // 分配场景数据缓冲区
2. v16 = sub_4E809(n17)                   // 获取场景元数据
3. i = *(_BYTE *)v16                      // 读取场景类型
4. v17 = sub_111BA(..., FDOTHER_DAT, i)   // 加载FDOTHER.DAT资源i
5. sub_4E98D(v17, 0, 0, n7+32904, 456, -1) // 解压到FDSHAP_DAT+32904
6. free(v17)                              // 释放临时资源
7. dword_53F5A = sub_111BA(..., 10)       // 加载辅助资源10
```

### 阶段3: 渲染循环
```
while (!退出条件) {
    sub_265EC()                           // 渲染场景
      ↓
    sub_4E809(n17)                        // 获取场景元数据
    memmove(目标, n7, 153216)             // 复制场景数据
    sub_4EBFF(目标+dword_53F5A, 456)      // 复制屏幕区域
    sub_15F84(...)                        // 渲染文本
    sub_4E22A(光标, 目标, 456)            // 绘制光标
    sub_11EB0(...)                        // 更新屏幕
    
    处理输入:
      - 上下左右键: 移动光标
      - 确认键: 选择
      - 取消键: 退出
}
```

### 阶段4: 退出条件
- 按下ESC键 (扫描码28)
- 按下ENTER键 (扫描码32)
- 选择特定菜单项 (n5 == 2)

### 关键数据流
```
FDOTHER.DAT 资源i
     ↓
sub_111BA() 加载
     ↓
sub_4E98D() 解压
     ↓
n7 + 32904 (153216字节缓冲区)
     ↓
sub_265EC() 渲染
     ↓
屏幕缓冲区 (655360)
     ↓
显示
```

---

## 总结

1. **sub_4E809(n17)**: 返回场景元数据指针，每个场景31字节
2. **场景0地图加载**: 通过sub_26152调用sub_111BA加载FDOTHER.DAT资源，然后sub_4E98D解压
3. **FDOTHER.DAT索引**: 由场景元数据的第一个字节决定，辅助资源固定为索引10
4. **sub_4E98D解压**: RLE变体算法，支持跳过/复制/填充三种模式，按行处理
5. **完整流程**: 初始化→资源加载→RLE解压→渲染循环→输入处理→退出

## 代码位置参考
- `sub_4E809`: [tools/export-for-ai/decompile/4E809.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/4E809.c)
- `sub_4E98D`: [tools/export-for-ai/decompile/4E98D.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/4E98D.c)
- `sub_26152`: [tools/export-for-ai/decompile/26152.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/26152.c)
- `sub_265EC`: [tools/export-for-ai/decompile/265EC.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/265EC.c)
- `sub_2670E`: [tools/export-for-ai/decompile/2670E.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/2670E.c)
- 场景实现: [src/fd2_scenes.c](file:///d:/workspace/fd2_dat_freebuff/src/fd2_scenes.c)
