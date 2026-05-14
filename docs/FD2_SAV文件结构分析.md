# FD2.SAV 存档文件结构完整分析

> 基于 IDA Pro MCP 反编译代码 1:1 分析
> 分析日期: 2026-05-13
> 源文件: game/FD2.SAV (22987字节)

---

## 一、核心函数索引

| 函数地址 | 函数名 | 功能 | 调用者 |
|----------|--------|------|--------|
| 0x10010 | sub_10010 | 加载FD2.SAV存档 | 0x19DF7, 0x25EBB |
| 0x4DF28 | sub_4DF28 | 解密存档数据 | 0x10010, 0x19DF7, 0x1F894, 0x25EBB, 0x2968D, 0x2986F |
| 0x4DF09 | sub_4DF09 | 计算校验和 | 0x10010, 0x19DF7, 0x1F894, 0x2968D |

---

## 二、解密算法 (sub_4DF28)

### 2.1 IDA原始反编译代码

```c
char __cdecl sub_4DF28(char *a1, int a2)
{
  char *v2; // esi
  char *v3; // edi
  __int16 n165; // dx
  char v6; // al
  char result; // al

  v2 = a1;
  v3 = a1;
  n165 = 165;
  do
  {
    v6 = *v2++;
    n165 = __ROL2__(n165 - 28652, 3);
    result = n165 ^ v6;
    *v3++ = result;
    --a2;
  }
  while ( a2 );
  return result;
}
```

### 2.2 算法分析

**关键点**:
- 初始密钥: `n165 = 165` (0x00A5)
- 每次迭代: `n165 = __ROL2__(n165 - 28652, 3)`
- XOR操作: `result = n165 ^ v6`

**注意**: `n165 - 28652` 等价于 `n165 + 0x9014` (因为 -28652 = 0x9014 在16位补码中)

### 2.3 等价C代码

```c
void fd2_sav_decrypt(unsigned char* data, int size) {
    unsigned short n165 = 165;
    
    for (int i = 0; i < size; i++) {
        n165 = __ROL2__(n165 + 0x9014, 3);  // 循环左移3位
        data[i] ^= (n165 & 0xFF);           // XOR低字节
    }
}
```

### 2.4 循环左移实现

```c
unsigned short __ROL2__(unsigned short value, int shift) {
    return (value << shift) | (value >> (16 - shift));
}
```

---

## 三、校验和算法 (sub_4DF09)

### 3.1 IDA原始反编译代码

```c
int __cdecl sub_4DF09(_BYTE *a1, int n22987)
{
  int v3; // ecx
  int v4; // ebx
  int v5; // eax

  v3 = n22987 - 4;
  v4 = 0;
  v5 = 0;
  do
  {
    LOBYTE(v5) = *a1++;
    v4 += v5;
    --v3;
  }
  while ( v3 );
  return v4;
}
```

### 3.2 算法分析

- 计算范围: 前 `size - 4` 字节
- 算法: 简单累加求和
- 返回: 32位整数校验和

### 3.3 等价C代码

```c
unsigned int fd2_sav_verify(const unsigned char* data, int size) {
    unsigned int checksum = 0;
    int count = size - 4;
    
    for (int i = 0; i < count; i++) {
        checksum += data[i];
    }
    
    return checksum;
}
```

---

## 四、存档加载流程 (sub_10010)

### 4.1 IDA原始反编译代码

```c
void sub_10010()
{
  int v0; // ebp - 存档缓冲区
  int v1; // eax
  int v2; // ebx
  __int64 v3; // rax
  int v4; // eax
  int v5; // ebx
  int i; // ebx
  __int64 v7; // rax
  int v8; // ebx
  int n6; // ebx
  int v10; // esi
  int n2; // ebx
  int v12; // edi
  int v13; // eax
  int v14; // [esp+0h] [ebp-14h]

  sub_3702F(60);
  v0 = malloc(22987);
  if ( v0 )
  {
    v3 = fopen("FD2.SAV", "rb");
    v2 = v3;
    sub_373CA(v0, 1, 22987, v3);
    fclose(v2);
    sub_4DF28(v0, 22987);
    LODWORD(v3) = sub_4DF09(v0, 22987);
    if ( (_DWORD)v3 != *(_DWORD *)(v0 + 22983) )
    {
      sub_1956B(75);
      sub_15F84(dword_53A7D, 436, 696099, 320, 205, 76, 74, 19, 1);
      sub_16559(0);
      LODWORD(v3) = sub_16C57(0);
      LODWORD(v3) = sub_196CB(v3, HIDWORD(v3));
    }
    sub_1F882(v3, HIDWORD(v3));
    memmove(dword_53BF7, v0 + 2211, 2560);
    FDOTHER_DAT = sub_111BA("FDOTHER.DAT", FDOTHER_DAT, 0);
    n17 = *(unsigned __int8 *)(v0 + 12485);
    dword_53A59 = sub_111BA("FDFIELD.DAT", dword_53A59, 3 * n17 + 2);
    if ( dword_53A55 )
      free(dword_53A55);
    dword_53A55 = malloc(2211);
    if ( dword_53A55 )
    {
      v4 = memmove(dword_53A55, v0, 2211);
      sub_10652(v4);
      dword_53A79 = sub_111BA("FDTXT.DAT", dword_53A79, n17 + 1);
      dword_53A51 = sub_111BA("FDFIELD.DAT", dword_53A51, 3 * n17);
      dword_53AC1 = *(__int16 *)dword_53A51;
      dword_53AC5 = *(__int16 *)(dword_53A51 + 2);
      v5 = 2 * *(unsigned __int8 *)dword_53A55;
      dword_53A5D = sub_111BA("FDSHAP.DAT", dword_53A5D, v5);
      dword_53A69 = sub_111BA("FDSHAP.DAT", dword_53A69, v5 + 1);
      sub_4DF4C(dword_53A51);
      ::n6 = *(unsigned __int8 *)(dword_53A55 + 1);
      dword_53BE3 = *(unsigned __int8 *)(dword_53A55 + 2);
      n6_0 = *(unsigned __int8 *)(v0 + 12484);
      if ( dword_53A45 )
        free(dword_53A45);
      dword_53A45 = malloc(7680);
      if ( dword_53A45 )
      {
        memmove(dword_53A45, v0 + 4771, 80 * n6_0);
        memmove(dword_53AD5, v0 + 12451, 32);
        if ( dword_53A61 )
          free(dword_53A61);
        v14 = fopen("fdicon.b24", "rb");
        dword_53BDF = 0;
        for ( i = 0; i < n6_0; ++i )
          *(_BYTE *)(80 * i + dword_53A45 + 2) = sub_11019(*(unsigned __int8 *)(80 * i + dword_53A45 + 7), v14);
        fclose(v14);
        v7 = fopen("FD2.TMP", "wb");
        v8 = v7;
        fwrite(dword_53A61, 1, (char *)&loc_329FE + 2, v7);
        fclose(v8);
        dword_53BEF = *(unsigned __int8 *)(v0 + 12483);
        dword_53AA9 = *(unsigned __int8 *)(v0 + 12486);
        dword_53AAD = *(unsigned __int8 *)(v0 + 12487);
        dword_53AB1 = *(unsigned __int8 *)(v0 + 12488);
        dword_53AB5 = *(unsigned __int8 *)(v0 + 12489);
        dword_53AB9 = *(unsigned __int8 *)(v0 + 12490);
        n2_1 = *(unsigned __int8 *)(v0 + 12491);
        dword_53BFB = *(unsigned __int8 *)(v0 + 12492);
        dword_53BF3 = *(_DWORD *)(v0 + 12493);
        byte_53AF9 = *(_BYTE *)(v0 + 12497);
        byte_51AAB = *(_BYTE *)(v0 + 12498);
        byte_51E61 = *(_BYTE *)(v0 + 12499);
        byte_51E62 = *(_BYTE *)(v0 + 12500);
        free(v0);
        free(dword_53A59);
        dword_53A59 = 0;
        LODWORD(v7) = sub_25977((unsigned __int8)byte_51E63[n17], 0);
        dword_51A83 = 0;
        sub_12263(v7, HIDWORD(v7));
        LODWORD(v7) = sub_11CAC(1);
        sub_1F525(v7);
        for ( n6 = 0; n6 < 9; ++n6 )
        {
          v10 = sub_15F0E(dword_53A81, 655360, 320, 120, 84, n6 + 83);
          if ( n6 > 6 )
            sub_187D6(684651, 320, dword_53BEF, 42, 3);
          j___delay(70);
          if ( n6 == 8 )
            j___delay(500);
          sub_15E71(v10, 655360, 320);
        }
        for ( n2 = 2; n2 < 6; ++n2 )
        {
          if ( n2 == 5 )
            n2 = 9;
          v12 = sub_15F0E(dword_53A81, dword_53A49 + 32904, 456, 116, n2 * n2 + 84, 91);
          sub_187D6(456 * (n2 * n2 + 90) + dword_53A49 + 33071, 456, dword_53BEF, 42, 3);
          sub_11EB0(656644, 320, dword_53A49 + 32904, 456, 312, 192);
          sub_17AA9(1);
          sub_15E71(v12, dword_53A49 + 32904, 456);
        }
        sub_11CAC(0);
        v13 = j___delay(200);
        dword_53AE9 = 0;
        dword_51A83 = 1;
        sub_4E381(v13);
        JUMPOUT(0x22BBE);
      }
      n3 = 3;
      int386(16, &n3, &n3);
      v1 = printf(" Out of Memory !!!\n");
    }
    else
    {
      n3 = 3;
      int386(16, &n3, &n3);
      v1 = printf(" Out of Memory !!!\n");
    }
  }
  else
  {
    n3 = 3;
    int386(16, &n3, &n3);
    v1 = printf(" Out of Memory !!!\n");
  }
  exit(v1);
}
```

### 4.2 加载步骤详解

| 步骤 | 地址偏移 | 操作 | 说明 |
|------|----------|------|------|
| 1 | - | `malloc(22987)` | 分配存档缓冲区 |
| 2 | - | `fopen("FD2.SAV", "rb")` | 打开存档文件 |
| 3 | - | `fread(buffer, 1, 22987, file)` | 读取22987字节 |
| 4 | - | `fclose(file)` | 关闭文件 |
| 5 | - | `sub_4DF28(buffer, 22987)` | 解密存档数据 |
| 6 | - | `sub_4DF09(buffer, 22987)` | 计算校验和 |
| 7 | - | 校验: `checksum == buffer[22983]` | 验证校验和 |
| 8 | - | `sub_1F882()` | 清屏 |
| 9 | - | `memmove(dword_53BF7, buffer+2211, 2560)` | 复制临时地图数据 |
| 10 | - | `sub_111BA("FDOTHER.DAT", 0)` | 加载FDOTHER#0 |
| 11 | - | `n17 = buffer[12485]` | 恢复场景索引 |
| 12 | - | `sub_111BA("FDFIELD.DAT", 3*n17+2)` | 加载地图数据 |
| 13 | - | `malloc(2211)` + `memmove(..., buffer, 2211)` | 复制营地地图数据 |
| 14 | - | `sub_10652()` | 处理地图数据 |
| 15 | - | `sub_111BA("FDTXT.DAT", n17+1)` | 加载文本数据 |
| 16 | - | `sub_111BA("FDFIELD.DAT", 3*n17)` | 加载主地图数据 |
| 17 | - | 获取地图尺寸 `width/height` | 从FDFIELD.DAT读取 |
| 18 | - | `sub_111BA("FDSHAP.DAT", v5)` | 加载形状数据 |
| 19 | - | `sub_111BA("FDSHAP.DAT", v5+1)` | 加载形状数据 |
| 20 | - | `sub_4DF4C()` | 处理地图 |
| 21 | - | 恢复角色数据 `80*n6_0` | 从偏移4771读取 |
| 22 | - | 恢复角色状态数据 32字节 | 从偏移12451读取 |
| 23 | - | `fopen("fdicon.b24")` + 加载图标 | 加载角色图标 |
| 24 | - | `fwrite(..., "FD2.TMP")` | 写入临时文件 |
| 25 | - | 恢复所有状态变量 | 从偏移12483开始 |
| 26 | - | `free(buffer)` | 释放临时缓冲区 |
| 27 | - | `sub_25977(byte_51E63[n17], 0)` | 播放场景音乐 |
| 28 | - | `sub_12263()` | 处理地图状态 |
| 29 | - | `sub_11CAC(1)` + `sub_1F525()` | 淡入效果 |
| 30 | - | 播放对话动画 83-91 | 过渡动画 |
| 31 | - | 播放战斗动画 (n2=2,3,4,9) | 战斗动画 |
| 32 | - | `sub_11CAC(0)` + `delay(200)` | 淡出效果 |
| 33 | - | `dword_53AE9 = 0; dword_51A83 = 1` | 设置战斗状态 |
| 34 | - | `sub_4E381()` | 刷新屏幕 |

---

## 五、FD2.SAV 文件结构详解

### 5.1 总体布局

```
FD2.SAV 文件结构 (22987字节)
├── [0x0000 - 0x08A2]     营地地图数据 (2211字节)
├── [0x08A3 - 0x12A2]     临时地图数据 (2560字节)
├── [0x12A3 - 0x30A2]     角色数据 (7680字节)
├── [0x30A3 - 0x30C2]     角色状态数据 (32字节)
├── [0x30C3 - 0x30D4]     游戏状态变量 (18字节)
├── [0x30D5 - 0x59C6]     其他数据 (10483字节)
└── [0x59C7 - 0x59CA]     校验和 (4字节)
```

### 5.2 详细偏移表

| 偏移 | 大小 | 字段名 | 全局变量 | 说明 |
|------|------|--------|----------|------|
| **0 - 2210** | 2211 | campMapData | dword_53A55 | 营地地图数据 |
| **2211 - 4770** | 2560 | tempMapData | dword_53BF7 | 临时地图数据缓冲区 |
| **4771 - 12450** | 7680 | charData | dword_53A45 | 角色数据 (80字节/角色) |
| **12451 - 12482** | 32 | charStateData | dword_53AD5 | 角色状态数据 (n8_0) |
| **12483** | 1 | n999 | dword_53BEF | 音乐相关变量 |
| **12484** | 1 | n6_0 | - | 角色数量 |
| **12485** | 1 | n17 | - | 场景索引 |
| **12486** | 1 | qword_53AA9_lo | dword_53AA9 | qword_53AA9 低字节 |
| **12487** | 1 | qword_53AA9_hi | dword_53AAD | qword_53AA9 高字节 |
| **12488** | 1 | qword_53AB1_lo | dword_53AB1 | qword_53AB1 低字节 |
| **12489** | 1 | qword_53AB1_hi | dword_53AB5 | qword_53AB1 高字节 |
| **12490** | 1 | n10 | dword_53AB9 | 游戏状态变量 |
| **12491** | 1 | n2 | n2_1 | 游戏状态变量 |
| **12492** | 1 | n16_1 | dword_53BFB | 选项数量 |
| **12493 - 12496** | 4 | n999_0 | dword_53BF3 | 进度数据 (32位) |
| **12497** | 1 | byte_53AF9 | byte_53AF9 | 场景标志 |
| **12498** | 1 | byte_51AAB | byte_51AAB | 状态标志 |
| **12499** | 1 | n127 | byte_51E61 | 音乐控制 |
| **12500** | 1 | byte_51E62 | byte_51E62 | 音乐标志 |
| **12501 - 22982** | 10483 | otherData | - | 其他数据 |
| **22983 - 22986** | 4 | checksum | - | 校验和 (小端序) |

### 5.3 角色数据结构 (80字节/角色)

| 偏移 (相对角色数据) | 大小 | 字段名 | 说明 |
|---------------------|------|--------|------|
| +0 | 1 | - | 未知 |
| +1 | 1 | - | 未知 |
| +2 | 1 | cache_index | 图标缓存索引 (sub_11019填充) |
| +3 - +6 | 4 | - | 未知 |
| +7 | 1 | icon_id | FDICON.B24 图标索引 |
| +8 - +79 | 72 | - | 未知 |

**角色数据加载代码**:
```c
for ( i = 0; i < n6_0; ++i )
  *(_BYTE *)(80 * i + dword_53A45 + 2) = 
      sub_11019(*(unsigned __int8 *)(80 * i + dword_53A45 + 7), v14);
```

---

## 六、十六进制结构图

```
00000000  ┌─────────────────────────────────────┐
          │  营地地图数据 (2211 字节)              │
          │  → memmove(dword_53A55, buffer, 2211) │
000008A2  ├─────────────────────────────────────┤
          │  临时地图数据 (2560 字节)              │
          │  → memmove(dword_53BF7, buffer+2211)  │
000012A2  ├─────────────────────────────────────┤
          │                                     │
          │  角色数据 (7680 字节)                 │
          │  - 每个角色 80 字节                   │
          │  → memmove(dword_53A45, buffer+4771)  │
          │                                     │
000030A2  ├─────────────────────────────────────┤
          │  角色状态数据 (32 字节)               │
          │  → memmove(dword_53AD5, buffer+12451) │
000030C2  ├─────────────────────────────────────┤
          │  n999         (1 字节) @12483        │
          │  n6_0         (1 字节) @12484        │
          │  n17          (1 字节) @12485        │
          │  qword_53AA9  (2 字节) @12486        │
          │  qword_53AB1  (2 字节) @12488        │
          │  n10          (1 字节) @12490        │
          │  n2           (1 字节) @12491        │
          │  n16_1        (1 字节) @12492        │
          │  n999_0       (4 字节) @12493        │
          │  byte_53AF9   (1 字节) @12497        │
          │  byte_51AAB   (1 字节) @12498        │
          │  n127         (1 字节) @12499        │
          │  byte_51E62   (1 字节) @12500        │
000030D4  ├─────────────────────────────────────┤
          │                                     │
          │  其他数据 (10483 字节)                │
          │                                     │
000059C6  ├─────────────────────────────────────┤
          │  校验和 (4 字节, 小端序)              │
          │  → buffer[22983]                     │
000059CA  └─────────────────────────────────────┘
```

---

## 七、C语言数据结构定义

```c
#pragma pack(push, 1)
typedef struct {
    /* 地图数据 (偏移 0) */
    u8 campMapData[2211];          /* 营地地图数据 */
    
    /* 临时地图数据 (偏移 2211) */
    u8 tempMapData[2560];          /* 临时地图数据缓冲区 */
    
    /* 角色数据 (偏移 4771) */
    u8 charData[7680];             /* 角色数据 (80字节/角色) */
    
    /* 角色状态数据 (偏移 12451) */
    u8 charStateData[32];          /* 角色状态数据 (n8_0) */
    
    /* 游戏状态变量 (偏移 12483) */
    u8 n999;                       /* @12483: 音乐变量 → dword_53BEF */
    u8 n6_0;                       /* @12484: 角色数量 */
    u8 n17;                        /* @12485: 场景索引 */
    u8 qword_53AA9_lo;             /* @12486 → dword_53AA9 */
    u8 qword_53AA9_hi;             /* @12487 → dword_53AAD */
    u8 qword_53AB1_lo;             /* @12488 → dword_53AB1 */
    u8 qword_53AB1_hi;             /* @12489 → dword_53AB5 */
    u8 n10;                        /* @12490 → dword_53AB9 */
    u8 n2;                         /* @12491 → n2_1 */
    u8 n16_1;                      /* @12492 → dword_53BFB */
    u32 n999_0;                    /* @12493 → dword_53BF3 */
    u8 byte_53AF9;                 /* @12497 */
    u8 byte_51AAB;                 /* @12498 */
    u8 n127;                       /* @12499 → byte_51E61 */
    u8 byte_51E62;                 /* @12500 */
    
    /* 其他数据 (偏移 12501) */
    u8 otherData[10483];           /* 其他数据 */
    
    /* 校验和 (偏移 22983) */
    u32 checksum;                  /* @22983: 校验和 */
} fd2_sav_t;
#pragma pack(pop)

/* 编译时检查结构体大小 */
static_assert(sizeof(fd2_sav_t) == 22987, "fd2_sav_t size must be 22987");
```

---

## 八、全局变量映射表

| 全局变量 | 存档偏移 | 类型 | 说明 |
|----------|----------|------|------|
| dword_53A55 | 0 | u8[2211] | 营地地图数据 |
| dword_53BF7 | 2211 | u8[2560] | 临时地图数据 |
| dword_53A45 | 4771 | u8[7680] | 角色数据 |
| dword_53AD5 | 12451 | u8[32] | 角色状态数据 |
| dword_53BEF | 12483 | u8 | n999 (音乐变量) |
| - | 12484 | u8 | n6_0 (角色数量) |
| - | 12485 | u8 | n17 (场景索引) |
| dword_53AA9 | 12486 | u8 | qword_53AA9 低字节 |
| dword_53AAD | 12487 | u8 | qword_53AA9 高字节 |
| dword_53AB1 | 12488 | u8 | qword_53AB1 低字节 |
| dword_53AB5 | 12489 | u8 | qword_53AB1 高字节 |
| dword_53AB9 | 12490 | u8 | n10 |
| n2_1 | 12491 | u8 | n2 |
| dword_53BFB | 12492 | u8 | n16_1 (选项数量) |
| dword_53BF3 | 12493 | u32 | n999_0 (进度数据) |
| byte_53AF9 | 12497 | u8 | 场景标志 |
| byte_51AAB | 12498 | u8 | 状态标志 |
| byte_51E61 | 12499 | u8 | n127 (音乐控制) |
| byte_51E62 | 12500 | u8 | 音乐标志 |

---

## 九、校验失败处理

当 `sub_4DF09(buffer, 22987) != buffer[22983]` 时:

```c
sub_1956B(75);  // 显示错误画面
sub_15F84(dword_53A7D, 436, 696099, 320, 205, 76, 74, 19, 1);  // 显示错误文本
sub_16559(0);
sub_16C57(0);
sub_196CB();
```

---

## 十、相关资源文件

| 文件名 | 用途 | 加载索引 |
|--------|------|----------|
| FD2.SAV | 存档文件 | - |
| FDOTHER.DAT | 其他资源 | #0 |
| FDFIELD.DAT | 地图数据 | #3*n17, #3*n17+2 |
| FDTXT.DAT | 文本数据 | #n17+1 |
| FDSHAP.DAT | 形状数据 | #v5, #v5+1 |
| fdicon.b24 | 图标文件 | - |
| FD2.TMP | 临时文件 | - |

---

## 十一、验证清单

- [x] 文件大小: 22987 字节
- [x] 解密算法: XOR 滚动密钥 (n165 = __ROL2__(n165 - 28652, 3))
- [x] 校验算法: 简单求和 (前 size-4 字节)
- [x] 校验和位置: 偏移 22983-22986
- [x] 营地地图数据: 偏移 0, 大小 2211
- [x] 临时地图数据: 偏移 2211, 大小 2560
- [x] 角色数据: 偏移 4771, 大小 7680 (80字节/角色)
- [x] 角色状态数据: 偏移 12451, 大小 32
- [x] 游戏状态变量: 偏移 12483-12500 (18字节)
- [x] 角色图标加载: offset+7 为图标索引, offset+2 为缓存索引

---

## 十二、关键发现

1. **解密算法**: 使用 16 位滚动密钥, 初始值 165, 每次加 0x9014 后循环左移 3 位
2. **校验和**: 简单累加求和, 存储在文件末尾 4 字节
3. **角色数据**: 每个角色 80 字节, 图标索引在偏移 +7, 缓存索引在偏移 +2
4. **场景索引**: n17 决定加载哪些 DAT 文件资源
5. **临时文件**: 加载存档时会写入 FD2.TMP 文件

---

## 相关文档

- [tools/export-for-ai/decompile/10010.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/10010.c) - sub_10010 完整反编译
- [tools/export-for-ai/decompile/4DF28.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/4DF28.c) - sub_4DF28 完整反编译
- [tools/export-for-ai/decompile/4DF09.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/4DF09.c) - sub_4DF09 完整反编译
- [docs/continue-battle-save-restore-analysis.md](file:///d:/workspace/fd2_dat_freebuff/docs/continue-battle-save-restore-analysis.md) - 存档恢复分析
- [src/fd2_save_load.c](file:///d:/workspace/fd2_dat_freebuff/src/fd2_save_load.c) - 存档系统实现
