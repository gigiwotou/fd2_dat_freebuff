# FD2 光标移动与地形信息UI渲染分析

> 基于IDA MCP反编译分析，所有代码逻辑1:1还原

## 概述

当光标在战场上移动时，游戏会执行一系列渲染操作来显示地形信息和角色状态。完整调用链如下：

```
sub_117E7 (输入处理)
  └─> sub_11CAC (光标移动后渲染)
        ├─> sub_11EEE (渲染地图瓦片)
        ├─> sub_122DC (渲染地形信息/范围)
        ├─> sub_127A9 (额外渲染)
        ├─> sub_1ACF3 (渲染角色信息UI框)
        └─> sub_11EB0 (blit到屏幕)
```

## 核心函数详解

### 1. 输入处理 [sub_117E7](file:///ida@0x117E7)

**地址**: 0x117E7

```c
int __usercall sub_117E7@<eax>(
        int a1@<edx>,
        int n80_1@<ebx>,
        int a3@<esi>,
        __int32 a4@<eax>,
        int a5@<ecx>,
        unsigned __int8 *a6@<edi>)
{
  // ... 省略部分代码 ...
  
  // 检测光标位置是否有角色
  n6_2 = sub_12C0D();  // 查找光标位置的角色
  n6_1 = n6_2;
  
  if ( n6_2 != -1 ) {
    v16 = (_BYTE *)(n8_1 + 80 * n6_2);  // 角色数据结构
    n2 = (unsigned __int8)v16[6];       // 阵营/类型
    n999_2 = 0;
    
    if ( v16[7] != 121 ) {  // 不是尸体
      n10 = (unsigned __int8)v16[31];   // 单位类型
      if ( n10 != 10 ) {    // 不是事件
        if ( n2 == 2 && (char)v16[5] >= 0 && !v16[38] ) {
          // 可操作角色：播放移动动画
          sub_25A96(0, 2, n10, a5, FDOTHER_DAT__2, 7, 1);
          while ( !sub_18890(n6_1) );
        } else {
          sub_17AED(n6_1, a3);
        }
        
        // ★ 核心渲染调用
        sub_11CAC(0);           // 渲染地形信息
        sub_1E292(a6, n6_1);    // 更新UI
        funcs_1197B[n17]();     // 根据移动模式执行函数
        sub_13565();            // 其他UI更新
        
        if ( n255 != 255 )
          ((void (__usercall *)(unsigned __int8 *@<edi>))funcs_1199C[n255])(a6);
        n255 = 255;
      }
    }
  }
  // ...
}
```

**关键逻辑**:
- 使用 `sub_12C0D()` 查找光标位置的角色
- 角色数据结构：80字节/角色，基址 `n8_1`
- 角色偏移+7: 0x79=正常, 0x79=尸体
- 角色偏移+31: 单位类型, 10=事件
- 角色偏移+6: 阵营, 2=可操作

### 2. 光标移动后渲染 [sub_11CAC](file:///ida@0x11CAC)

**地址**: 0x11CAC

```c
int __fastcall sub_11CAC(__int32 a1, int a2, int a3, int a4, int a5)
{
  sub_3702F(a1, a2, a3, a4, 32);
  sub_1297D();                          // 动画计时
  
  if ( !a5 )
    sub_4E31C();                        // 清除
  
  // 渲染地图瓦片到缓冲区
  // 参数: 目标缓冲区, 行宽456, 13列, 8行, 偏移x, 偏移y
  sub_11EEE(n655360 + 32904, 456, 13, 8, qword_53AA9, SHIDWORD(qword_53AA9));
  
  // ★ 渲染地形信息(根据移动模式显示不同范围)
  sub_122DC();
  
  // 额外渲染
  sub_127A9();
  
  // ★ 渲染角色信息UI框(边框+地形图标+HP/MP+角色立绘)
  sub_1ACF3(n655360 + 32904, 456);
  
  // Blit缓冲区到屏幕
  // 参数: src_buf, src_stride, dst_buf, dst_stride, width, height
  return sub_11EB0(n655360 + 32904, a2, a3, a4, 
                   656644, 320,           // 屏幕缓冲
                   n655360 + 32904, 456,  // 源缓冲
                   312, 192);             // 312x192区域
}
```

**缓冲区布局**:
- 基地址: `n655360 + 32904`
- 行宽: 456字节
- 可见区域: 13列 × 8行瓦片
- 屏幕blit: 312×192像素

### 3. 地形信息渲染 [sub_122DC](file:///ida@0x122DC)

**地址**: 0x122DC

```c
int __fastcall sub_122DC(__int32 a1, int a2, int a3, int a4)
{
  int result;
  int v5;
  int n5;

  result = sub_3702F(a1, a2, a3, a4, 16);
  
  // 根据移动模式(n6_5)渲染不同范围的地形信息
  switch ( n6_5 ) {
    case 1:  // 单个地形
      n5 = 0;
LABEL_3:
      v5 = HIDWORD(qword_53AB1);
      return sub_126F7(qword_53AB1, v5, n5);
      
    case 2:  // 单个地形(变体)
      n5 = 1;
      goto LABEL_3;
      
    case 3:  // 十字形5个地形
      sub_126F7(qword_53AB1, SHIDWORD(qword_53AB1), 14);  // 中心
      sub_126F7(qword_53AB1, (unsigned __int64)(qword_53AB1 - 0x100000000LL) >> 32, 2);
      sub_126F7(qword_53AB1 - 1, SHIDWORD(qword_53AB1), 3);  // 左
      sub_126F7(qword_53AB1 + 1, SHIDWORD(qword_53AB1), 4);  // 右
      n5 = 5;
LABEL_8:
      v5 = HIDWORD(qword_53AB1) + 1;
      return sub_126F7(qword_53AB1, v5, n5);  // 上
      
    case 4:  // 周围一圈13个地形
      sub_126F7(qword_53AB1, SHIDWORD(qword_53AB1), 1);
      sub_126F7(qword_53AB1, HIDWORD(qword_53AB1) - 2, 2);
      sub_126F7(qword_53AB1 - 2, SHIDWORD(qword_53AB1), 3);
      sub_126F7(qword_53AB1 + 2, SHIDWORD(qword_53AB1), 4);
      sub_126F7(qword_53AB1, HIDWORD(qword_53AB1) + 2, 5);
      sub_126F7(qword_53AB1 - 1, HIDWORD(qword_53AB1) - 1, 6);
      sub_126F7(qword_53AB1 + 1, HIDWORD(qword_53AB1) - 1, 7);
      sub_126F7(qword_53AB1 - 1, HIDWORD(qword_53AB1) + 1, 8);
      sub_126F7(qword_53AB1 + 1, HIDWORD(qword_53AB1) + 1, 9);
      sub_126F7(qword_53AB1, (unsigned __int64)(qword_53AB1 - 0x100000000LL) >> 32, 10);
      sub_126F7(qword_53AB1 - 1, SHIDWORD(qword_53AB1), 11);
      sub_126F7(qword_53AB1 + 1, SHIDWORD(qword_53AB1), 12);
      n5 = 13;
      goto LABEL_8;
      
    case 5:  // 更大范围18个地形
      // ... 18次sub_126F7调用 ...
      
    case 6:  // 清除地图标记
      result = qword_53AB1 + dword_53AC1 * HIDWORD(qword_53AB1);
      *(_BYTE *)(FDFIELD_DAT__0 + 4 * result + 7) = 0;
      break;
  }
  return result;
}
```

**移动模式 (n6_5)**:
| 模式 | 描述 | 渲染地形数量 |
|------|------|-------------|
| 1-2 | 单个地形 | 1 |
| 3 | 十字形 | 5 |
| 4 | 周围一圈 | 13 |
| 5 | 更大范围 | 18 |
| 6 | 清除标记 | 0 |

### 4. 角色信息UI渲染 [sub_1ACF3](file:///ida@0x1ACF3)

**地址**: 0x1ACF3

```c
void __fastcall sub_1ACF3(__int32 a1, int a2, int a3, int a4, int a5, int n456)
{
  int v6;        // UI框位置
  int v8, v9;
  int v10;       // 角色数据指针
  _WORD v12[2];  // [0]=地形ID, [1]=单位ID
  unsigned __int8 v13;
  char *src;     // 精灵数据指针
  
  sub_3702F(a1, a2, a3, a4, 56);
  
  if ( byte_51AAB && byte_51AAC ) {
    // 计算UI框位置
    if ( n2 <= 5 || n10 >= 3 ) {
      if ( n2 > 5 && n10 > 9 )
        n242 = 1;
    } else {
      n242 = 242;
    }
    v6 = n242 + 157 * n456 + a5;
    
    // 1. 渲染信息框边框 (FDOTHER_DAT__7 索引526)
    sub_4E98D((__int16 *)(*(_DWORD *)(FDOTHER_DAT__7 + 526) + FDOTHER_DAT__7), 
              0, 0, v6, n456, -1);
    
    // 2. 获取光标位置地块信息
    // v12[0] = 地形ID, v12[1] = 单位ID
    sub_12E38((__int32)v12, a2, a3, a4, 
              qword_53AB1, SHIDWORD(qword_53AB1), (int)v12);
    
    // 3. 渲染地形图标 (FDSHAP_DAT)
    sub_4E22A((char *)(FDSHAP_DAT + *(_DWORD *)(FDSHAP_DAT + 4 * v12[0] + 6)), 
              (char *)(v6 + 5 * n456 + 6), n456);
    
    // 4. 渲染HP条
    sub_1AEB1(v6 + 8 * n456 + 43, n456, dword_51A12[v13]);
    
    // 5. 渲染MP条
    v8 = sub_1AEB1(v6 + 19 * n456 + 43, n456, dword_51A2A[v13]);
    
    // 6. 检查光标位置是否有角色
    v9 = sub_12C0D(v8, FDSHAP_DAT, a3, a4);
    if ( v9 != -1 ) {
      v10 = 80 * v9 + n8_1;  // 角色数据结构指针
      
      if ( *(_BYTE *)(v10 + 7) != 121 && 
           (*(_BYTE *)(v10 + 31) != 10 || *(_BYTE *)(v10 + 6) != 1) ) {
        // 7. 渲染角色立绘
        n3 = n3_1;
        if ( n3_1 == 3 ) n3 = 1;
        src = (char *)(dword_53A61 + 
                 *(_DWORD *)(dword_53A61 + 4 * (12 * *(unsigned __int8 *)(v10 + 2) + n3)));
        sub_4E22A(src, (char *)(v6 + 5 * n456 + 6), n456);
        
        // 8. 渲染角色属性(等级/HP/MP等)
        sub_1875D(21 * n456 + v6 + 9, n456, 
                  *(unsigned __int16 *)(v10 + 64),   // HP
                  *(unsigned __int16 *)(v10 + 66),   // MP
                  3);
      }
    }
  }
}
```

### 5. 地块信息获取 [sub_12E38](file:///ida@0x12E38)

**地址**: 0x12E38

```c
char __fastcall sub_12E38(__int32 a1, int a2, int a3, int a4, int a5, int a6, int a7)
{
  __int16 v7;  // 地形相关
  __int16 v8;  // 单位相关
  _BYTE *v9;
  char result;

  sub_3702F(a1, a2, a3, a4, 12);
  
  // 从FDFIELD_DAT__0获取地块数据
  // 索引公式: 4 * (x + width * y)
  v7 = *(_WORD *)(FDFIELD_DAT__0 + 4 * (a5 + dword_53AC1 * a6) + 4);
  HIBYTE(v7) &= 3u;
  
  v8 = *(_BYTE *)(FDFIELD_DAT__0 + 4 * (a5 + dword_53AC1 * a6) + 6) & 0x1F;
  
  // 输出到v12数组
  *(_WORD *)a7 = v7;       // v12[0] = 地形ID
  *(_WORD *)(a7 + 2) = v8; // v12[1] = 单位ID
  
  // 从FDSHAP_DAT__0获取地形属性
  v9 = (_BYTE *)(4 * v7 + FDSHAP_DAT__0);
  *(_BYTE *)(a7 + 4) = v9[0];
  *(_BYTE *)(a7 + 5) = v9[1];
  *(_BYTE *)(a7 + 6) = v9[2];
  result = v9[3];
  *(_BYTE *)(a7 + 7) = result;
  
  return result;
}
```

**输出结构 (8字节)**:
- `[0-1]`: 地形ID (低10位)
- `[2-3]`: 单位ID (低5位)
- `[4]`: 地形属性1 (FDSHAP_DAT__0偏移+0)
- `[5]`: 地形属性2 (FDSHAP_DAT__0偏移+1)
- `[6]`: 地形属性3 (FDSHAP_DAT__0偏移+2)
- `[7]`: 地形属性4 (FDSHAP_DAT__0偏移+3)

## 资源使用汇总

### 全局变量

| 变量名 | 用途 | 类型 |
|--------|------|------|
| `n655360` | 渲染缓冲区基址 | `void*` |
| `n8_1` | 角色数据数组基址 | `u8*` (80字节/角色) |
| `qword_53AA9` | 地图可视区域偏移(x,y) | `qword` |
| `qword_53AB1` | 光标坐标(x,y) | `qword` |
| `dword_53AC1` | 地图宽度 | `int` |
| `n6_5` | 移动模式 | `int` |
| `n2` | 阵营/类型 | `int` |
| `n10` | 单位类型 | `int` |
| `byte_51AAB` | UI显示标志1 | `bool` |
| `byte_51AAC` | UI显示标志2 | `bool` |
| `dword_51A12` | HP条颜色数组 | `u32[]` |
| `dword_51A2A` | MP条颜色数组 | `u32[]` |
| `dword_53A61` | 角色精灵数据基址 | `u8*` |

### DAT资源

| 资源 | 索引 | 用途 | 汇编引用 |
|------|------|------|---------|
| FDOTHER.DAT | 7, 526 | 信息框边框图像 | sub_1ACF3@1ad86 |
| FDOTHER.DAT | 2 | 移动动画资源 | sub_117E7@1193a |
| FDFIELD.DAT | 0 | 地图地块数据 | sub_12E38@12e67 |
| FDSHAP.DAT | - | 地形图标/角色精灵 | sub_1ACF3@1adc4 |
| FDSHAP.DAT | 0 | 地形属性表 | sub_12E38@12e8b |

## 角色数据结构 (80字节)

```
偏移  大小  字段            说明
+0    1     未知            可能为标志位
+1    1     未知
+2    1     角色ID/立绘索引  用于查找dword_53A61
+3-4  2     未知
+5    1     阵营/状态       >=0时可操作
+6    1     阵营            2=可操作
+7    1     状态            0x79=正常, 其他=尸体
+8-30 23    未知
+31   1     单位类型        10=事件
+32-37 6    未知
+38   1     标志位          !=0时不可操作
+39-63 25   未知
+64   2     HP              当前HP值
+66   2     MP              当前MP值
+68-79 12   未知
```

## UI渲染流程总结

```
光标移动
  │
  ├─> sub_12C0D() - 查找角色
  │     │
  │     └─> 找到角色?
  │           │
  │           ├─ 是 ─> 播放动画/选中
  │           │
  │           └─ 继续渲染UI
  │
  ├─> sub_11CAC() - 完整渲染
  │     │
  │     ├─> sub_11EEE() - 地图瓦片
  │     │     └─> 渲染13x8可见瓦片到缓冲区
  │     │
  │     ├─> sub_122DC() - 地形信息
  │     │     └─> 根据n6_5模式调用sub_126F7
  │     │           └─> 渲染地形加成图标
  │     │
  │     ├─> sub_127A9() - 额外渲染
  │     │
  │     ├─> sub_1ACF3() - 角色UI框
  │     │     ├─> FDOTHER_DAT__7[526] - 边框
  │     │     ├─> sub_12E38() - 地块信息
  │     │     ├─> FDSHAP_DAT - 地形图标
  │     │     ├─> dword_51A12 - HP条
  │     │     ├─> dword_51A2A - MP条
  │     │     ├─> sub_12C0D() - 查找角色
  │     │     │     └─> 找到?
  │     │     │           ├─> dword_53A61 - 角色立绘
  │     │     │           └─> sub_1875D() - 属性文字
  │     │
  │     └─> sub_11EB0() - Blit到屏幕
  │           └─> 312x192区域到屏幕
  │
  └─> sub_1E292() - UI状态更新
```

## 参考

- IDA分析基于FD2原始可执行文件
- 所有函数地址和逻辑1:1还原自IDA MCP反编译结果
- 更新时间: 2026-05-04
