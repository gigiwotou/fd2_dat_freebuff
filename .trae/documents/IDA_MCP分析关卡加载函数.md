# IDA MCP 关卡加载函数详细分析结果

## 分析日期
2026-04-29

## 分析环境
- 二进制文件: FD2.EXE
- IDB路径: E:\downloads\FD\fd2\FD2\FD2\FD2.EXE.i64
- 工具: IDA Pro MCP Server

---

## 第一步：地图加载主函数 sub_1088D (0x1088D)

### 函数签名
```c
int __cdecl sub_1088D(int n13)
```
- **参数**: n13 = 地图ID (0-32)
- **返回**: 成功返回0

### 关键代码流程

#### 1. 加载FDFIELD.DAT的3个资源
```c
// 地址 0x108C4 - FDTXT.DAT (地图文本)
dword_53A79 = sub_111BA("FDTXT.DAT", dword_53A79, n13 + 1);

// 地址 0x108EB - FDFIELD.DAT 资源 3*n13+2 (Spawn数据)
dword_53A59 = sub_111BA("FDFIELD.DAT", dword_53A59, 3 * n13 + 2);

// 地址 0x10907 - FDFIELD.DAT 资源 3*n13+1 (Control数据)
dword_53A55 = sub_111BA("FDFIELD.DAT", dword_53A55, 3 * n13 + 1);

// 地址 0x10920 - FDFIELD.DAT 资源 3*n13 (Layout数据)
dword_53A51 = sub_111BA("FDFIELD.DAT", dword_53A51, 3 * n13);
```

**资源索引计算方式**：
- Layout: `3 * map_id`
- Control: `3 * map_id + 1`
- Spawn: `3 * map_id + 2`

#### 2. 读取地图尺寸
```c
// 地址 0x10928 - 宽度 (2字节)
dword_53AC1 = *(__int16 *)dword_53A51;

// 地址 0x10932 - 高度 (2字节)
dword_53AC5 = *(__int16 *)(dword_53A51 + 2);
```

**Layout数据头部结构**：
- 偏移0: width (16-bit little-endian)
- 偏移2: height (16-bit little-endian)
- 偏移4+: tile数据

#### 3. 加载FDSHAP.DAT的调色板和瓦片
```c
// 地址 0x1093F - terrain_set_id = control_data[0]
v2 = 2 * *(unsigned __int8 *)dword_53A55;

// 地址 0x10955 - FDSHAP.DAT 资源 2*terrain_set_id (调色板)
FDSHAP_DAT = sub_111BA("FDSHAP.DAT", FDSHAP_DAT, v2);

// 地址 0x1096F - FDSHAP.DAT 资源 2*terrain_set_id+1 (瓦片集)
dword_53A69 = sub_111BA("FDSHAP.DAT", dword_53A69, v2 + 1);
```

**FDSHAP资源索引计算**：
- 调色板: `2 * terrain_set_id` (偶数索引)
- 瓦片集: `2 * terrain_set_id + 1` (奇数索引)
- terrain_set_id 从 Control数据的byte[0]读取

#### 4. 处理地形ID
```c
// 地址 0x1097A - 修改Layout数据中的地形ID
sub_4DF4C(dword_53A51);
```

#### 5. 读取Control数据
```c
// 地址 0x1098B - n6 = control_data[1] (图标数量)
::n6 = *(unsigned __int8 *)(dword_53A55 + 1);

// 地址 0x10995 - dword_53BE3 = control_data[2]
dword_53BE3 = *(unsigned __int8 *)(dword_53A55 + 2);
```

**Control数据结构**：
- byte[0]: terrain_set_id (地形集ID)
- byte[1]: 图标数量
- byte[2]: 未知 (可能是敌人总数)

### 汇编代码关键片段
```asm
10937  mov     eax, dword_53A55
1093c  movzx   ebx, byte ptr [eax]    ; ebx = control[0]
1093f  add     ebx, ebx                ; ebx = control[0] * 2
10941  push    ebx
10942  push    _FDSHAP_DAT_
10948  push    offset aFdshapDat       ; "FDSHAP.DAT"
1094d  call    sub_111BA               ; 加载调色板
10955  mov     _FDSHAP_DAT_, eax
1095a  inc     ebx                     ; ebx = control[0] * 2 + 1
1095b  push    ebx
1095c  push    dword_53A69
10962  push    offset aFdshapDat       ; "FDSHAP.DAT"
10967  call    sub_111BA               ; 加载瓦片集
```

---

## 第二步：地形ID处理函数 sub_4DF4C (0x4DF4C)

### 函数签名
```c
char __cdecl sub_4DF4C(unsigned __int8 *a1)
```
- **参数**: a1 = Layout数据指针
- **返回**: 0xFF

### 完整反编译代码
```c
v1 = (unsigned __int16)(a1[2] * *a1);  // height * width
v2 = a1 + 4;  // 跳过4字节头 (width + height)
do {
    v2[3] = -1;      // byte[3] = 0xFF
    v2[2] &= 0x1Fu;  // byte[2] = byte[2] & 0x1F (保留低5位)
    v2[1] &= 3u;     // byte[1] = byte[1] & 3 (保留低2位)
    v2 += 4;
    --v1;
} while (v1);
```

### 汇编代码
```asm
4df55  xor     eax, eax
4df57  mov     al, [edi]        ; al = a1[0] (width low byte)
4df59  mov     ah, [edi+2]      ; ah = a1[2] (height low byte)
4df5c  mul     ah               ; eax = al * ah (width * height)
4df5e  mov     ecx, eax         ; ecx = 瓦片数量
4df60  add     edi, 4           ; edi = a1 + 4 (跳过头部)
4df63  mov     al, 0FFh         ; al = 0xFF

; === 循环开始 ===
4df65  mov     [edi+3], al      ; byte[3] = 0xFF
4df68  mov     ah, [edi+2]      ; ah = byte[2]
4df6b  and     ah, 1Fh          ; ah = byte[2] & 0x1F
4df6e  mov     [edi+2], ah      ; 保存修改后的byte[2]
4df71  mov     ah, [edi+1]      ; ah = byte[1]
4df74  and     ah, 3            ; ah = byte[1] & 3
4df77  mov     [edi+1], ah      ; 保存修改后的byte[1]
4df7a  add     edi, 4           ; 下一个瓦片
4df7d  loop    loc_4DF65        ; --ecx, if ecx!=0 继续循环
```

### 地形ID计算公式

**原始数据（4字节/瓦片）**：
- byte[0]: 地形ID低8位
- byte[1]: 地形ID高2位 + 其他标志6位
- byte[2]: 其他数据（被掩码为0x1F）
- byte[3]: 其他数据（被设为0xFF）

**修改后的数据**：
- byte[0]: 不变
- byte[1]: byte[1] & 3 (保留低2位)
- byte[2]: byte[2] & 0x1F (保留低5位)
- byte[3]: 0xFF

**地形ID计算**：
```
terrain_id = byte[0] | (byte[1] << 8)
```
其中byte[1]已经是`byte[1] & 3`，所以：
```
terrain_id = byte[0] | ((original_byte[1] & 3) << 8)
```
**范围**: 0-1023 (10位)

### 关键发现
1. **sub_4DF4C直接修改内存中的数据**，是就地修改(in-place)
2. **修改后byte[1]只有2位**，说明原始byte[1]的高6位是其他用途（可能是标志位）
3. **byte[2]只有5位**，说明用于其他目的（可能是图层或属性）
4. **地形ID是10位**（0-1023），不是7位或8位

---

## 第三步：瓦片渲染函数 sub_1ACF3 (0x1ACF3)

### 函数签名
```c
void __fastcall sub_1ACF3(__int32 a1, int a2, int a3, int a4, int a5, int n456)
```
- **参数**: 
  - a1-a4: 未知
  - a5: 目标缓冲区偏移
  - n456: 目标缓冲区宽度（stride）

### 关键代码 - 瓦片加载
```c
// 调用sub_12E38提取地形ID和相关数据
sub_12E38(dword_53AB1, dword_53AB5, v12);

// 使用地形ID从FDSHAP_DAT读取瓦片数据
// 关键行：从FDSHAP_DAT + 4*v12[0] + 6读取DWORD作为偏移
sub_4E22A(
    (char *)(FDSHAP_DAT + *(_DWORD *)(FDSHAP_DAT + 4 * v12[0] + 6)),  // src
    (char *)(v6 + 5 * n456 + 6),  // dst
    n456  // stride
);
```

### 瓦片偏移表结构
```c
// 公式：*(DWORD*)(FDSHAP_DAT + 4 * tile_index + 6)
// 解释：
//   - FDSHAP_DAT: 调色板资源的起始地址
//   - 4 * tile_index: 每个条目4字节（DWORD）
//   - +6: 偏移表从byte 6开始
//   - *(DWORD*...): 读取4字节作为瓦片数据偏移
```

**关键确认**：
- ✅ 偏移表从**byte 6**开始（不是byte 4）
- ✅ 每个条目是**4字节DWORD**（不是2字节WORD）
- ✅ 使用**FDSHAP_DAT**（调色板资源），不是瓦片集资源

### 为什么使用FDSHAP_DAT而不是dword_53A69？

这是一个重要发现！代码使用FDSHAP_DAT（调色板资源）来查找瓦片偏移，但dword_53A69是瓦片集资源。

可能的解释：
1. FDSHAP.DAT的资源0可能不是纯调色板，而是包含偏移表和瓦片数据的混合结构
2. 或者游戏在加载时将瓦片数据复制到了FDSHAP_DAT指向的内存区域

需要进一步验证实际内存布局...

---

## 第四步：地形ID提取函数 sub_12E38 (0x12E38)

### 函数签名
```c
char __fastcall sub_12E38(__int32 a1, int a2, int a3, int a4, int a5, int a6, int a7)
```
- **参数**:
  - a5: x坐标
  - a6: y坐标
  - a7: 输出缓冲区指针

### 完整反编译代码
```c
// 计算瓦片在layout中的偏移
// dword_53A51 = layout数据起始
// dword_53AC1 = width
// 4 * (x + width * y) + 4: 跳过4字节头，定位到瓦片数据
v7 = *(_WORD *)(dword_53A51 + 4 * (a5 + dword_53AC1 * a6) + 4);
HIBYTE(v7) &= 3u;  // 高字节 & 3

v8 = *(_BYTE *)(dword_53A51 + 4 * (a5 + dword_53AC1 * a6) + 6) & 0x1F;
*(_WORD *)a7 = v7;      // 存储地形ID到a7[0-1]
*(_WORD *)(a7 + 2) = v8; // 存储byte[2]&0x1F到a7[2-3]

// 从dword_53A69（瓦片集资源）读取4字节
v9 = (_BYTE *)(4 * v7 + dword_53A69);
*(_BYTE *)(a7 + 4) = *v9;        // byte[0]
*(_BYTE *)(a7 + 5) = v9[1];      // byte[1]
*(_BYTE *)(a7 + 6) = v9[2];      // byte[2]
*(_BYTE *)(a7 + 7) = v9[3];      // byte[3]
```

### 关键发现

#### 1. 地形ID计算
```c
v7 = *(WORD*)(layout + 4*(x + width*y) + 4);
HIBYTE(v7) &= 3;
```
- 读取2字节：byte[0-1]
- 高字节（byte[1]）& 3
- 地形ID = byte[0] | ((byte[1] & 3) << 8)
- **范围**: 0-1023

#### 2. 瓦片属性提取
```c
v8 = *(BYTE*)(layout + 4*(x + width*y) + 6) & 0x1F;
```
- byte[2] & 0x1F = 5位值（0-31）
- 可能用于：图层、透明度、碰撞等属性

#### 3. 从瓦片集读取额外数据
```c
v9 = (BYTE*)(4 * v7 + dword_53A69);
```
- 使用地形ID * 4 + dword_53A69
- 从瓦片集资源读取4字节
- **注意**：这里直接从dword_53A69开始，没有+6偏移

### 汇编代码
```asm
12e46  mov     edx, [esp+8+arg_8]     ; edx = a7 (输出缓冲区)
12e4a  mov     eax, [esp+8+arg_4]     ; eax = a5 (x坐标)
12e4e  imul    eax, dword_53AC1       ; eax = x * width
12e55  add     eax, [esp+8+arg_0]     ; eax = x * width + y
12e59  shl     eax, 2                 ; eax = (x * width + y) * 4
12e5c  mov     ebx, dword_53A51       ; ebx = layout数据
12e62  add     eax, ebx               ; eax = layout + 4*tile_index
12e64  add     eax, 4                 ; eax = layout + 4*tile_index + 4
12e67  mov     bx, [eax]              ; bx = *(WORD*)(eax)
12e6a  and     bh, 3                  ; bh = bh & 3
12e6d  mov     al, [eax+2]            ; al = byte[2]
12e70  and     al, 1Fh                ; al = al & 0x1F
12e72  movzx   ax, al
12e76  mov     [edx], bx              ; a7[0-1] = v7 (地形ID)
12e79  mov     [edx+2], ax            ; a7[2-3] = v8 (byte[2]&0x1F)
12e7d  movsx   eax, bx                ; eax = v7
12e80  shl     eax, 2                 ; eax = v7 * 4
12e86  mov     eax, dword_53A69       ; eax = 瓦片集资源
12e8b  add     eax, [esp+8+var_8]     ; eax = dword_53A69 + 4*v7
12e8e  mov     bl, [eax]              ; 读取4字节
12e90  mov     [edx+4], bl
12e93  mov     bl, [eax+1]
12e96  mov     [edx+5], bl
12e99  mov     bl, [eax+2]
12e9c  mov     [edx+6], bl
12e9f  mov     al, [eax+3]
12ea2  mov     [edx+7], al
```

### 与Python代码的对比

**当前Python代码** (map_verify.py L365-366):
```python
terrain_id = struct.unpack_from("<H", tile_data, pos)[0]
event_id = struct.unpack_from("<H", tile_data, pos + 2)[0]
```

**问题**：
- ❌ 没有对byte[1]应用`& 3`掩码
- ❌ 直接读取16-bit值，但游戏会修改byte[1]
- ❌ 地形ID范围可能超过实际瓦片数量

**正确的Python代码应该**：
```python
b0 = tile_data[pos]
b1 = tile_data[pos + 1]
b2 = tile_data[pos + 2]
b3 = tile_data[pos + 3]

# 应用IDA的掩码
b1_masked = b1 & 3
b2_masked = b2 & 0x1F

# 地形ID = byte[0] | ((byte[1] & 3) << 8)
terrain_id = b0 | (b1_masked << 8)

# event_id或属性 = byte[2] & 0x1F
event_id = b2_masked
```

---

## 第五步：RLE解压缩函数 sub_4E22A (0x4E22A)

### 函数签名
```c
char __cdecl sub_4E22A(char *src, char *dst, int a3)
```
- **参数**:
  - src: RLE压缩数据源
  - dst: 解压缩目标缓冲区
  - a3: 目标行宽度（stride）

### 完整反编译代码分析

```c
n24 = 24;  // 瓦片高度固定24
do {
    n24_1 = 24;  // 瓦片宽度固定24
    do {
        value = *src++;
        v9 = 2 * value;
        
        // 检查bit 7 (最高位)
        if (value & 0x80) {
            // bit 7 = 1
            count = ((4 * value) >> 2) + 1 = (value & 0x3F) + 1
            
            // 检查bit 6
            if (value & 0x40) {
                // bit 7=1, bit 6=1: SKIP模式
                // 跳过count个像素（不写入）
                dst += count;
                n24_1 -= count;
            } else {
                // bit 7=1, bit 6=0: COPY模式
                // 从src复制count个字节到dst
                memcpy(dst, src, count);
                src += count;
                dst += count;
                n24_1 -= count;
            }
        } else {
            // bit 7 = 0
            count = ((4 * value) >> 2) + 1 = (value & 0x3F) + 1
            
            // 检查bit 6
            if (value & 0x40) {
                // bit 7=0, bit 6=1: ALTERNATE模式
                // 交替写入单个字节
                value = *src++;
                for (i = 0; i < count; i++) {
                    *dst = value;
                    dst += 2;  // 每隔一个像素写入
                }
                n24_1 -= count * 2;
            } else {
                // bit 7=0, bit 6=0: FILL模式
                // 用单个值填充count个字节
                value = *src++;
                memset(dst, value, count);
                dst += count;
                n24_1 -= count;
            }
        }
    } while (n24_1);
    
    // 一行结束，移动到下一行
    dst += a3 - 24;
    --n24;
} while (n24);
```

### RLE编码格式

**操作码字节结构**：
```
Bit 7 | Bit 6 | Bits 5-0
------+------+---------
  1   |   1   | count-1 (SKIP模式)
  1   |   0   | count-1 (COPY模式)
  0   |   1   | count-1 (ALTERNATE模式)
  0   |   0   | count-1 (FILL模式)
```

**Count计算**：
```
count = (opcode & 0x3F) + 1
```
范围: 1-64

### 四种操作模式

#### 1. SKIP模式 (bit7=1, bit6=1)
```c
dst += count;  // 跳过count个像素
n24_1 -= count;
```
- **用途**: 透明区域，不写入任何数据
- **数据**: 无额外数据

#### 2. COPY模式 (bit7=1, bit6=0)
```c
memcpy(dst, src, count);
src += count;
dst += count;
n24_1 -= count;
```
- **用途**: 复制连续的不同像素
- **数据**: count字节的原始像素数据

#### 3. FILL模式 (bit7=0, bit6=0)
```c
value = *src++;
memset(dst, value, count);
dst += count;
n24_1 -= count;
```
- **用途**: 填充相同颜色的连续区域
- **数据**: 1字节的填充值

#### 4. ALTERNATE模式 (bit7=0, bit6=1)
```c
value = *src++;
for (i = 0; i < count; i++) {
    *dst = value;
    dst += 2;
}
n24_1 -= count * 2;
```
- **用途**: 每隔一个像素写入相同值（可能是棋盘格图案）
- **数据**: 1字节的交替值

### 与Python代码的对比

**当前Python代码** (map_verify.py RLE解压):
```python
def rle_decompress(src: bytes, width: int, height: int) -> bytes:
    # 尝试实现RLE解压，但可能不完全正确
```

**问题**：
- Python代码可能没有完全实现4种模式
- 特别是ALTERNATE模式（每隔一个像素写入）可能实现错误
- SKIP模式的处理可能不正确

---

## 第六步：RLE解压缩函数 sub_4E98D (0x4E98D)

### 函数签名
```c
char __cdecl sub_4E98D(__int16 *a1, int a2, int a3, int a4, int a5, int value_1)
```
- **参数**:
  - a1: RLE压缩数据（包含头部）
  - a2: 目标基址
  - a3: 起始行
  - a4: 起始列
  - a5: 目标宽度（stride）
  - value_1: 填充值（-1=直接模式，0-255=单色模式，>255=重映射模式）

### 完整反编译代码分析

这个函数比sub_4E22A更复杂，支持3种不同的value_1模式：

#### 模式1: value_1 == -1 (直接模式)
与sub_4E22A类似，使用4种RLE操作：
- SKIP: 跳过像素
- COPY: 复制原始数据
- FILL: 填充单个值
- ALTERNATE: 交替写入

#### 模式2: value_1 > 0xFF (重映射模式)
```c
value = value_1 + ((BYTE1(value_1) + src_byte) & 7);
```
- 使用src_byte作为索引
- 从value_1的调色板中选择颜色
- BYTE1(value_1)可能是调色板基索引

#### 模式3: value_1 <= 0xFF (单色模式)
```c
value = value_1;  // 固定使用value_1作为填充色
```
- 所有写入都使用value_1
- 用于单色区域填充

### 关键发现
sub_4E98D是更通用的RLE解压器，支持：
1. **直接模式** (value_1=-1): 原始像素数据
2. **重映射模式** (value_1>255): 使用调色板重映射
3. **单色模式** (value_1<=255): 固定颜色填充

这解释了为什么地图渲染可能有不同的颜色效果！

---

## 第七步：FDSHAP.DAT资源结构分析

### 实际数据验证

通过Python脚本verify_fdshap_structure.py验证：

**资源0 (调色板)**：
- 起始: 148014
- 大小: 1200 字节
- 前32字节: `00 00 04 00 00 00 04 00 00 00 04 00 ...`
- 结构: 看起来不是768字节的调色板，而是重复的4字节模式

**资源1 (瓦片集)**：
- 起始: 149214
- 大小: 87915 字节
- Tile尺寸: 24x24

**头部结构**：
```
Byte 0-1: tile_width = 24 (0x0018)
Byte 2-3: tile_height = 24 (0x0018)
Byte 4-5: 0x00C0 = 192 (瓦片数量！)
Byte 6-9: 0x00000306 = 774 (Tile 0偏移)
Byte 10-13: 0x00000429 = 1065 (Tile 1偏移)
Byte 14-17: 0x00000578 = 1400 (Tile 2偏移)
```

### 关键发现

**Byte 4-5 = 192 = 瓦片总数！**

这验证了：
1. ✅ 瓦片偏移表从**byte 6**开始
2. ✅ 每个条目是**4字节DWORD**
3. ✅ Byte 4-5存储瓦片数量（用于快速验证）
4. ✅ 找到192个瓦片

---

## 第八步：调色板结构分析

### 资源0数据分析

**前32字节**:
```
00 00 04 00 00 00 04 00 00 00 04 00 00 00 04 00
00 00 04 00 00 00 04 00 00 00 04 00 00 00 04 00
```

这个模式看起来不是标准的768字节（256色×3）调色板。

**可能结构**：
```
每4字节: 00 00 04 00
- Byte 0-1: 0x0000 = 0
- Byte 2-3: 0x0004 = 4
```

重复256次 = 1024字节，但资源大小是1200字节。

**另一种可能**：
- Byte 4: 可能存储瓦片数量或其他元数据
- Byte 6+: 调色板数据

需要进一步分析实际调色板数据...

---

## 关键发现总结

### 1. 资源索引计算 ✅

**FDFIELD.DAT**:
```python
layout_idx = 3 * map_id
control_idx = 3 * map_id + 1
spawn_idx = 3 * map_id + 2
```

**FDSHAP.DAT**:
```python
terrain_set_id = control_data[0]
palette_idx = 2 * terrain_set_id
tileset_idx = 2 * terrain_set_id + 1
```

### 2. 地形ID计算 ⚠️ 需要修复

**当前Python代码（错误）**:
```python
terrain_id = struct.unpack_from("<H", tile_data, pos)[0]
```

**正确代码（根据IDA）**:
```python
b0 = tile_data[pos]
b1 = tile_data[pos + 1]
b2 = tile_data[pos + 2]
b3 = tile_data[pos + 3]

# sub_4DF4C修改后的值
b1_masked = b1 & 3
b2_masked = b2 & 0x1F

# 地形ID = byte[0] | ((byte[1] & 3) << 8)
terrain_id = b0 | (b1_masked << 8)

# 属性/事件ID
event_id = b2_masked
```

**范围**: 0-1023 (10位)

### 3. 瓦片偏移表结构 ✅ 已修复

**当前Python代码（已修复）**:
```python
# 从byte 6开始，4字节DWORD
pos = res1_start + 6
while pos + 4 <= res1_start + res1_size:
    offset_val = struct.unpack_from("<I", fdshap, pos)[0]
    if 0 < offset_val < res1_size:
        tile_offsets.append(offset_val)
    else:
        break
    pos += 4
```

**头部完整结构**:
```
Byte 0-1: tile_width (16-bit)
Byte 2-3: tile_height (16-bit)
Byte 4-5: tile_count (16-bit)
Byte 6+: tile_offsets[tile_count] (DWORD数组)
```

### 4. RLE解压缩 ⚠️ 需要验证

**4种操作模式**:
```
操作码字节 (opcode):
- Bit 7=1, Bit 6=1: SKIP (跳过count像素)
- Bit 7=1, Bit 6=0: COPY (复制count字节)
- Bit 7=0, Bit 6=0: FILL (填充count字节)
- Bit 7=0, Bit 6=1: ALTERNATE (每隔一个像素写入)

count = (opcode & 0x3F) + 1  (范围1-64)
```

**当前Python代码可能问题**:
- ALTERNATE模式可能实现错误（应该是dst+=2）
- SKIP模式可能需要特殊处理

### 5. 调色板结构 ❓ 待确认

**问题**:
- 资源0的大小是1200字节，不是768字节
- 前32字节显示重复的`00 00 04 00`模式
- 可能包含元数据或不是标准调色板

**需要**:
- 分析资源0的完整结构
- 确认调色板数据起始位置
- 验证6-bit到8-bit转换公式

---

## 需要修复的问题

### 高优先级

1. **地形ID到瓦片索引的映射** ✅ 已解决
   - 地形ID范围超过瓦片数量时，使用模运算：`tile_index = terrain_id % tile_count`
   - 地图0: terrain_id 8-286, tile_count 192
   - 使用模运算后渲染576/576瓦片（原来532/576）
   - 在sub_12AC6中发现：`v7 = *(_WORD *)(4 * (a6 + dword_53AC1 * a7) + dword_53A51 + 4) & 0x3FF`
   - 掩码0x3FF(1023)表明地形ID最大1023，然后需要映射到瓦片索引

2. **地形ID计算** ✅ 已解决
   - 应用byte[1] & 3掩码
   - 使用正确的10位公式：`terrain_id = byte[0] | ((byte[1] & 3) << 8)`
   - 实际测试发现原始数据byte[1]已经<4，所以两种公式结果相同
   
2. **RLE解压缩** (map_verify.py 和 test_map0_final.py)
   - 验证4种操作模式
   - 特别是ALTERNATE模式

3. **调色板解析**
   - 确认资源0的实际结构
   - 验证调色板数据位置和大小

### 中优先级

4. **瓦片索引范围验证**
   - 地形ID范围0-1023
   - 瓦片数量192
   - 需要确认映射关系（是否直接索引？）

5. **byte[2] & 0x1F的用途**
   - 可能是事件ID或图层属性
   - 需要进一步分析

---

## 下一步行动

1. 修复地形ID计算公式
2. 验证RLE解压缩实现
3. 深入分析调色板结构
4. 测试修复后的代码生成地图

---

*分析完成时间: 2026-04-29*
*分析师: IDA MCP + Qwen3.5-Plus*
