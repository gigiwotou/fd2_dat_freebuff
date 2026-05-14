# FD2.SAV 存档系统完整分析

> 基于 IDA Pro MCP 反编译代码 1:1 分析
> 分析日期: 2026-05-13
> 源文件: game/FD2.SAV

---

## 一、核心函数索引 (IDA MCP反编译)

| 函数地址 | 函数名 | 功能 | 关键代码行 |
|----------|--------|------|------------|
| 0x10010 | sub_10010 | 加载战场存档(Continue) | [10010.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/10010.c) |
| 0x19DF7 | sub_19DF7 | 营地存档菜单 | [19DF7.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/19DF7.c) |
| 0x25EBB | sub_25EBB | 主菜单处理 | [25EBB.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/25EBB.c) |
| 0x2968D | sub_2968D | 保存战场存档 | [2968D.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/2968D.c) |
| 0x2986F | sub_2986F | 加载营地存档(Load) | [2986F.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/2986F.c) |
| 0x29BCB | sub_29BCB | 存档选择界面 | [29BCB.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/29BCB.c) |
| 0x4DF28 | sub_4DF28 | 解密/加密 | [4DF28.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/4DF28.c) |
| 0x4DF09 | sub_4DF09 | 校验和 | [4DF09.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/4DF09.c) |

---

## 二、存档数量分析

### 2.1 IDA MCP 证据

根据 [sub_29BCB](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/29BCB.c) 的反编译代码：

```c
if ( (_DWORD)n28 != 80 || n4_1 == (unsigned __int8 *)3 )  // line 29d24
```

**n4_1 是存档槽位索引**，当 `n4_1 == 3` 时按下箭头不再增加，说明：

### 2.2 存档槽位数量

**FD2.SAV 有4个存档槽位** (索引 0, 1, 2, 3)

---

## 三、加密/解密算法 (IDA MCP)

### 3.1 sub_4DF28 - 解密/加密函数

**IDA MCP 反编译代码**:

```c
char __cdecl sub_4DF28(char *a1, int a2)
{
  char *v2; // esi
  char *v3; // edi
  __int16 n165; // dx
  char v6; // al
  char result; // al

  v2 = a1; /*0x4df2d*/
  v3 = a1; /*0x4df30*/
  n165 = 165; /*0x4df35*/
  do /*0x4df46*/
  {
    v6 = *v2++; /*0x4df39*/
    n165 = __ROL2__(n165 - 28652, 3); /*0x4df3f*/
    result = n165 ^ v6; /*0x4df43*/
    *v3++ = result; /*0x4df45*/
    --a2; /*0x4df46*/
  }
  while ( a2 ); /*0x4df46*/
  return result; /*0x4df48*/
}
```

### 3.2 算法分析

| 步骤 | 代码 | 说明 |
|------|------|------|
| 初始化 | `n165 = 165` | 初始密钥 0x00A5 |
| 密钥更新 | `n165 = __ROL2__(n165 - 28652, 3)` | 减28652后循环左移3位 |
| XOR解密 | `result = n165 ^ v6` | 与数据XOR |
| 注意 | `n165 - 28652` | 在16位中等价于 `n165 + 0x9014` |

### 3.3 sub_4DF09 - 校验和函数

**IDA MCP 反编译代码**:

```c
int __cdecl sub_4DF09(_BYTE *a1, int n22987)
{
  int v3; // ecx
  int v4; // ebx
  int v5; // eax

  v3 = n22987 - 4; /*0x4df16*/
  v4 = 0; /*0x4df19*/
  v5 = 0; /*0x4df1b*/
  do /*0x4df20*/
  {
    LOBYTE(v5) = *a1++; /*0x4df1d*/
    v4 += v5; /*0x4df1e*/
    --v3; /*0x4df20*/
  }
  while ( v3 ); /*0x4df20*/
  return v4; /*0x4df24*/
}
```

**校验逻辑**:
- 计算范围: `n22987 - 4` 字节 (即前22983字节)
- 算法: 简单累加求和
- 返回: 32位校验和

---

## 四、主菜单逻辑 (sub_25EBB)

### 4.1 IDA MCP 反编译代码

```c
bool __usercall sub_25EBB@<eax>(
    __int32 a1@<eax>, int a2@<edx>, int a3@<ecx>, 
    int n99@<ebx>, unsigned __int8 *a5@<edi>)
{
  // ... 初始化代码 ...
  
  v5 = sub_3702F(a1, a2, n99, a3, 32); /*0x25ec0*/
  sub_1F894(v5, a2, n99, a3); /*0x25ec8*/  // 开场动画
  
  if ( !v6 ) /*0x25ecf*/  // v6 == 0: New Game
  {
    v7 = sub_1F882(); /*0x25ed1*/
    n17 = 0; /*0x25ed6*/
    FDOTHER_DAT = (int)sub_111BA(v7, a2, n99, a3, 
        (int)aFdotherDat, FDOTHER_DAT, 0);  // "FDOTHER.DAT" #0
    n16_1 = 0; /*0x25efa*/
    byte_51AAC = 0; /*0x25f04*/
    ((void (__usercall *)(unsigned __int8 *@<edi>))
        funcs_25E3A[n17])(a5); /*0x25f10*/
    sub_25977((unsigned __int8)byte_51E63[n17], a2, n99, a3, 
        (unsigned __int8)byte_51E63[n17], 0); /*0x25f26*/
    byte_51AAC = 1; /*0x25f2e*/
    sub_4E381(); /*0x25f35*/
    return 0; /*0x2614c*/
  }
  
  if ( v6 != 1 ) /*0x25f42*/  // v6 != 1: Continue
  {
    sub_25977(v6, a2, n99, a3, -1, 0); /*0x26128*/  // 停止音乐
    sub_10010(v18, a2, a3, n99, a5); /*0x26130*/      // 加载战场存档
    sub_25977((unsigned __int8)byte_51E63[n17], a2, n99, a3, 
        (unsigned __int8)byte_51E63[n17], 0); /*0x26144*/  // 播放音乐
    return 0; /*0x26144*/
  }
  
  // v6 == 1: Load
  FDOTHER_DAT__11 = (int)sub_111BA(1, a2, n99, a3, 
      (int)aFdotherDat, FDOTHER_DAT__11, 13);  // "FDOTHER.DAT" #13
  v8 = sub_1F882(); /*0x25f62*/
  FDOTHER_DAT = (int)sub_111BA(v8, a2, n99, a3, 
      (int)aFdotherDat, FDOTHER_DAT, 0);  // "FDOTHER.DAT" #0
  v9 = memset(n99, 655360, 0, 64000); /*0x25f8d*/
  sub_11D40(v9, a2, n99, a3, 0, 255, 0); /*0x25f9e*/
  
  v10 = (unsigned __int8 *)malloc(22987); /*0x25fb0*/
  v11 = v10; /*0x25fb5*/
  v12 = fopen(aFd2Sav_4, &unk_50220);  // "FD2.SAV"
  v13 = v12; /*0x25fc6*/
  if ( (_DWORD)v12 ) /*0x25fcd*/
  {
    sub_373CA(v10, 1u, 22987, v12); /*0x25fd8*/  // 读取
    sub_4DF28((char *)v10, 22987); /*0x25fe6*/    // 解密
    fclose(v13); /*0x25fef*/
  }
  else
  {
    memset((int)v10, (int)v10, 255, 22987); /*0x26004*/  // 填充255
  }
  
  n4_1 = 0; /*0x2600c*/  // 存档槽位索引
  do /*0x260b2*/
  {
    sub_29BCB((int)v11, 0); /*0x26019*/  // 显示存档选择界面
    v15 = v14; /*0x26021*/
    if ( v14 != -1 ) /*0x26026*/  // 用户选择了存档
    {
      v16 = (int)&v11[2600 * (_DWORD)n4_1 + 12587];  // 计算槽位地址
      v12 = memmove(n8_3, v16, 2560); /*0x26056*/
      v10 = (unsigned __int8 *)(v16 + 2560); /*0x2605e*/
      n17 = *v10; /*0x26067*/
      n16_1 = v10[1]; /*0x26070*/
      n999_0 = *(_DWORD *)(v10 + 2); /*0x26078*/
      byte_51AAB = v10[6]; /*0x26080*/
      byte_53AF9 = v10[7]; /*0x26088*/
      n127 = v10[8]; /*0x26090*/
      byte_51E62 = v10[9]; /*0x26098*/
      if ( n17 == 255 ) /*0x260a7*/  // 空槽位
        v15 = 0; /*0x260a9*/
    }
    sub_26996(); /*0x260ab*/
  }
  while ( !v15 ); /*0x260b2*/
  // ... 后续处理 ...
}
```

### 4.2 主菜单三个选项

| 返回值 (v6) | 选项 | 处理逻辑 | 代码行 |
|-------------|------|----------|--------|
| **v6 == 0** | New Game | 开始新游戏 | 0x25ecf |
| **v6 == 1** | Load | 加载营地存档 | 0x25f42 之后 |
| **v6 != 0 && v6 != 1** | Continue | 加载战场存档 | 0x25f42 |

### 4.3 Load选项存档槽位数据加载

```c
v16 = (int)&v11[2600 * (_DWORD)n4_1 + 12587];  // 计算槽位地址
v12 = memmove(n8_3, v16, 2560);  // 复制2560字节地图数据
v10 = (unsigned __int8 *)(v16 + 2560);
n17 = *v10;           // 场景索引
n16_1 = v10[1];       // 选项数量
n999_0 = *(_DWORD *)(v10 + 2);  // 进度数据
byte_51AAB = v10[6];  // 状态标志
byte_53AF9 = v10[7];  // 场景标志
n127 = v10[8];        // 音乐控制
byte_51E62 = v10[9];  // 音乐标志
if ( n17 == 255 )     // 场景索引255 = 空槽位
  v15 = 0;
```

---

## 五、战场存档保存 (sub_2968D)

### 5.1 IDA MCP 反编译代码

```c
int __fastcall sub_2968D(__int32 a1, int a2, int a3, int a4, char n3)
{
  int v5; // ebx
  int v6; // esi
  __int64 v7; // rax
  int v8; // edi
  int v9; // ebp
  int v10; // ebx
  unsigned __int8 *_wb_; // edi

  sub_3702F(a1, a2, a3, a4, 56); /*0x29692*/
  v7 = malloc(22987); /*0x296a0*/
  v5 = v7; /*0x296a5*/
  v6 = v7; /*0x296aa*/
  LODWORD(v7) = fopen((int)aFd2Sav_5, (int)aRb_5);  // "rb"
  v8 = v7; /*0x296bb*/
  if ( (_DWORD)v7 ) /*0x296c2*/
  {
    sub_373CA((_BYTE *)v5, 1u, 22987, v7); /*0x296cd*/  // 读取
    sub_4DF28((char *)v5, 22987); /*0x296db*/            // 解密
    fclose(v8); /*0x296e4*/
  }
  else
  {
    memset(v5, v5, 255, 22987); /*0x296f9*/  // 无存档时填充255
  }
  
  n4_1 = 0; /*0x29701*/  // 存档槽位索引
  do /*0x2985b*/
  {
    sub_29BCB((unsigned __int8)n3, SHIDWORD(v7), v5, a4, v6, 
        (unsigned __int8)n3); /*0x29712*/  // 显示存档选择界面
    v9 = v7; /*0x2971a*/
    if ( (_DWORD)v7 != -1 ) /*0x2971f*/  // 用户确认保存
    {
      v10 = 2600 * (_DWORD)n4_1 + v6 + 12587;  // 计算槽位地址
      v7 = memmove(v10, n8_3, 2560); /*0x2974f*/  // 复制地图数据
      v5 = v10 + 2560; /*0x29757*/
      *(_BYTE *)v5 = n17; /*0x29762*/
      *(_BYTE *)(v5 + 1) = n16_1; /*0x29769*/
      *(_DWORD *)(v5 + 2) = n999_0; /*0x29771*/
      *(_BYTE *)(v5 + 6) = byte_51AAB; /*0x29779*/
      *(_BYTE *)(v5 + 7) = byte_53AF9; /*0x29781*/
      *(_BYTE *)(v5 + 8) = n127; /*0x29789*/
      *(_BYTE *)(v5 + 9) = byte_51E62; /*0x29791*/
      
      _wb_ = (unsigned __int8 *)fopen((int)aFd2Sav_6, (int)aWb_2);  // "wb"
      *(_DWORD *)(v6 + 22983) = sub_4DF09((_BYTE *)v6, 22987); /*0x297b6*/  // 校验和
      sub_4DF28((char *)v6, 22987); /*0x297c2*/  // 加密
      fwrite(v6, 1, 22987, _wb_); /*0x297d3*/    // 写入
      fclose(_wb_); /*0x297dc*/
      sub_4DF28((char *)v6, 22987); /*0x297ea*/  // 再次解密(恢复)
      // ... 后续处理 ...
    }
    sub_26996(v7, SHIDWORD(v7), v5, a4); /*0x29853*/
  }
  while ( v9 != -1 ); /*0x2985b*/
  return free(v6); /*0x2986e*/
}
```

### 5.2 战场存档保存步骤

| 步骤 | 代码行 | 操作 |
|------|--------|------|
| 1 | 0x296a0 | `malloc(22987)` 分配缓冲区 |
| 2 | 0x296b6 | `fopen("FD2.SAV", "rb")` 打开存档 |
| 3 | 0x296cd | `fread(buffer, 1, 22987)` 读取数据 |
| 4 | 0x296db | `sub_4DF28(buffer, 22987)` 解密 |
| 5 | 0x296f9 | 无存档: `memset(buffer, 255, 22987)` |
| 6 | 0x29701 | `n4_1 = 0` 初始化槽位索引 |
| 7 | 0x29712 | `sub_29BCB()` 显示存档选择界面 |
| 8 | 0x29741 | `v10 = 2600 * n4_1 + buffer + 12587` 计算槽位地址 |
| 9 | 0x2974f | `memmove(v10, n8_3, 2560)` 复制地图数据 |
| 10 | 0x29762-0x29791 | 写入状态变量 (n17, n16_1, n999_0, 等) |
| 11 | 0x297a3 | `fopen("FD2.SAV", "wb")` 打开写入 |
| 12 | 0x297b6 | `sub_4DF09(buffer, 22987)` 计算校验和 |
| 13 | 0x297c2 | `sub_4DF28(buffer, 22987)` 加密 |
| 14 | 0x297d3 | `fwrite(buffer, 1, 22987)` 写入文件 |
| 15 | 0x297dc | `fclose()` 关闭文件 |
| 16 | 0x297ea | `sub_4DF28(buffer, 22987)` 再次解密(恢复内存) |

---

## 六、营地存档保存 (sub_19DF7)

### 6.1 IDA MCP 反编译代码 (保存部分)

```c
// case 1: 保存营地存档
v21 = malloc(22987); /*0x19f84*/
_rb__1 = fopen((int)aFd2Sav_0, (int)aRb);  // "rb"
_rb__2 = _rb__1; /*0x19f9a*/
if ( _rb__1 ) /*0x19fa1*/
{
  sub_373CA((_BYTE *)v21, 1u, 22987, _rb__1); /*0x19fac*/
  sub_4DF28((char *)v21, 22987); /*0x19fba*/  // 解密
  fclose(_rb__2); /*0x19fc3*/
}
else
{
  *(_BYTE *)(v21 + 15147) = -1; /*0x19fcd*/  // 槽位0标记为空
  *(_BYTE *)(v21 + 17747) = -1; /*0x19fd4*/  // 槽位1标记为空
  *(_BYTE *)(v21 + 20347) = -1; /*0x19fdb*/  // 槽位2标记为空
  *(_BYTE *)(v21 + 22947) = -1; /*0x19fe2*/  // 槽位3标记为空
}

// 保存所有游戏数据到缓冲区
memmove(v21, FDFIELD_DAT__1, 2211); /*0x19ff5*/  // 营地地图
memmove(v21 + 2211, n8_3, 2560); /*0x1a00f*/      // 临时地图
memmove(v21 + 4771, n8_1, 80 * n6_0); /*0x1a035*/ // 角色数据
memmove(v21 + 12451, n8_0, 32); /*0x1a04c*/       // 角色状态

*(_BYTE *)(v21 + 12483) = n999; /*0x1a060*/
*(_BYTE *)(v21 + 12484) = n6_0; /*0x1a068*/
*(_BYTE *)(v21 + 12485) = n17; /*0x1a071*/
*(_BYTE *)(v21 + 12486) = qword_53AA9; /*0x1a07a*/
*(_BYTE *)(v21 + 12487) = BYTE4(qword_53AA9); /*0x1a083*/
*(_BYTE *)(v21 + 12488) = qword_53AB1; /*0x1a08c*/
*(_BYTE *)(v21 + 12489) = BYTE4(qword_53AB1); /*0x1a095*/
*(_BYTE *)(v21 + 12490) = n10; /*0x1a09e*/
*(_BYTE *)(v21 + 12491) = n2; /*0x1a0a7*/
*(_BYTE *)(v21 + 12492) = n16_1; /*0x1a0b0*/
*(_DWORD *)(v21 + 12493) = n999_0; /*0x1a0b9*/
*(_BYTE *)(v21 + 12497) = byte_53AF9; /*0x1a0c2*/
*(_BYTE *)(v21 + 12498) = byte_51AAB; /*0x1a0cb*/
*(_BYTE *)(v21 + 12499) = n127; /*0x1a0d4*/
*(_BYTE *)(v21 + 12500) = byte_51E62; /*0x1a0dd*/

dst = (int *)fopen((int)aFd2Sav_1, (int)aWb);  // "wb"
*(_DWORD *)(v21 + 22983) = sub_4DF09((_BYTE *)v21, 22987); /*0x1a102*/  // 校验和
sub_4DF28((char *)v21, 22987); /*0x1a10e*/  // 加密
fwrite(v21, 1, 22987, dst); /*0x1a11f*/      // 写入
fclose(dst); /*0x1a128*/
v22 = free(v21); /*0x1a131*/
```

### 6.2 营地存档保存步骤

| 步骤 | 代码行 | 操作 |
|------|--------|------|
| 1 | 0x19f84 | `malloc(22987)` 分配缓冲区 |
| 2 | 0x19f95 | `fopen("FD2.SAV", "rb")` 读取旧存档 |
| 3 | 0x19fac | `fread(buffer, 1, 22987)` 读取数据 |
| 4 | 0x19fba | `sub_4DF28(buffer, 22987)` 解密 |
| 5 | 0x19fcd-0x19fe2 | 无存档: 设置4个槽位场景索引为255(-1) |
| 6 | 0x19ff5 | `memmove(buffer, FDFIELD_DAT__1, 2211)` 保存营地地图 |
| 7 | 0x1a00f | `memmove(buffer+2211, n8_3, 2560)` 保存临时地图 |
| 8 | 0x1a035 | `memmove(buffer+4771, n8_1, 80*n6_0)` 保存角色数据 |
| 9 | 0x1a04c | `memmove(buffer+12451, n8_0, 32)` 保存角色状态 |
| 10 | 0x1a060-0x1a0dd | 保存所有状态变量 (18字节) |
| 11 | 0x1a0ef | `fopen("FD2.SAV", "wb")` 打开写入 |
| 12 | 0x1a102 | `sub_4DF09(buffer, 22987)` 计算校验和 |
| 13 | 0x1a10e | `sub_4DF28(buffer, 22987)` 加密 |
| 14 | 0x1a11f | `fwrite(buffer, 1, 22987)` 写入文件 |
| 15 | 0x1a128 | `fclose()` 关闭文件 |

---

## 七、存档加载 - Continue选项 (sub_10010)

### 7.1 IDA MCP 反编译代码 (关键部分)

```c
void __usercall sub_10010(__int32 a1@<eax>, int a2@<edx>, int a3@<ecx>, 
    int n99@<ebx>, unsigned __int8 *a5@<edi>)
{
  int v5; // ebp
  // ...
  
  sub_3702F(a1, a2, n99, a3, 60); /*0x10015*/
  v5 = malloc(22987); /*0x1002e*/
  if ( v5 ) /*0x10032*/
  {
    _rb_ = fopen(aFd2Sav_2, aRb_0);  // "rb"
    sub_373CA((_BYTE *)v5, 1u, 22987, _rb_); /*0x10074*/
    sub_4DF28((char *)v5, 22987); /*0x10082*/  // 解密
    fclose(_rb_); /*0x1008b*/
    
    if ( sub_4DF09((_BYTE *)v5, 22987) != *(_DWORD *)(v5 + 22983) ) /*0x10099*/
    {
      // 校验失败处理
      sub_1956B(75); /*0x100bf*/
      sub_15F84(a5, FDTXT_DAT__0, 436, 696099, 320, 205, 76, 74, 19, 1); /*0x100e9*/
      sub_16559(0); /*0x100f3*/
      sub_16C57(0); /*0x100fd*/
      sub_196CB(); /*0x10105*/
    }
    
    sub_1F882(); /*0x1010a*/  // 清屏
    
    // 恢复临时地图数据
    v8 = memmove(n8_3, v5 + 2211, 2560); /*0x10121*/
    
    // 加载资源文件
    FDOTHER_DAT = (int)sub_111BA(v8, SHIDWORD(v8), _rb_, a3, 
        (int)aFdotherDat, FDOTHER_DAT, 0);  // "FDOTHER.DAT" #0
    n17 = *(unsigned __int8 *)(v5 + 12485); /*0x1013e*/  // 场景索引
    
    FDFIELD_DAT = (int)sub_111BA(3 * n17 + 2, n17, _rb_, a3, 
        (int)aFdfieldDat, FDFIELD_DAT, 3 * n17 + 2);  // "FDFIELD.DAT" #3*n17+2
    
    // 复制营地地图数据
    if ( FDFIELD_DAT__1 ) /*0x10176*/
      free(FDFIELD_DAT__1); /*0x1017e*/
    FDFIELD_DAT__1 = malloc(2211); /*0x10193*/
    if ( FDFIELD_DAT__1 ) /*0x1019a*/
    {
      v9 = memmove(FDFIELD_DAT__1, v5, 2211); /*0x101cf*/
      sub_10652(v9, SHIDWORD(v9), _rb_, a3); /*0x101d7*/
      
      // 加载文本和地图
      FDTXT_DAT = (int)sub_111BA(n17 + 1, SHIDWORD(v9), _rb_, a3, 
          (int)aFdtxtDat, FDTXT_DAT, n17 + 1);  // "FDTXT.DAT" #n17+1
      FDFIELD_DAT__0 = (int)sub_111BA(3 * n17, n17, _rb_, a3, 
          (int)aFdfieldDat, FDFIELD_DAT__0, 3 * n17);  // "FDFIELD.DAT" #3*n17
      
      // 获取地图尺寸
      HIDWORD(v9) = *(__int16 *)FDFIELD_DAT__0; /*0x10221*/
      dword_53AC1 = HIDWORD(v9); /*0x10224*/
      n40 = *(__int16 *)(FDFIELD_DAT__0 + 2); /*0x1022e*/
      
      // 加载形状数据
      v10 = 2 * *(unsigned __int8 *)FDFIELD_DAT__1; /*0x1023b*/
      FDSHAP_DAT = (int)sub_111BA(FDFIELD_DAT__1, SHIDWORD(v9), v10, a3, 
          (int)aFdshapDat, FDSHAP_DAT, v10);  // "FDSHAP.DAT" #v10
      FDSHAP_DAT__0 = (int)sub_111BA(FDSHAP_DAT, SHIDWORD(v9), v10 + 1, a3, 
          (int)aFdshapDat, FDSHAP_DAT__0, v10 + 1);  // "FDSHAP.DAT" #v10+1
      
      sub_4DF4C((unsigned __int8 *)FDFIELD_DAT__0); /*0x10276*/
      ::n6 = *(unsigned __int8 *)(FDFIELD_DAT__1 + 1); /*0x10287*/
      dword_53BE3 = *(unsigned __int8 *)(FDFIELD_DAT__1 + 2); /*0x10291*/
      
      // 恢复角色数量
      n6_0 = *(unsigned __int8 *)(v5 + 12484); /*0x1029a*/
      
      if ( n8_1 ) /*0x102a6*/
        free(n8_1); /*0x102ae*/
      n8_1 = malloc(7680); /*0x102c3*/
      if ( n8_1 ) /*0x102ca*/
      {
        memmove(n8_1, v5 + 4771, 80 * n6_0); /*0x10311*/
        memmove(n8_0, v5 + 12451, 32); /*0x10328*/
        
        // 加载角色图标
        if ( dword_53A61 ) /*0x10337*/
          free(dword_53A61); /*0x1033f*/
        _rb__1 = fopen(aFdiconB24, aRb_1);  // "rb"
        dword_53BDF = 0; /*0x1035c*/
        for ( n6 = 0; n6 < n6_0; ++n6 ) /*0x10366*/
          *(_BYTE *)(80 * n6 + n8_1 + 2) = 
              sub_11019(*(unsigned __int8 *)(80 * n6 + n8_1 + 7), _rb__1); /*0x10391*/
        fclose(_rb__1); /*0x103a1*/
        
        // 写入临时文件
        _wb_ = fopen(aFd2Tmp, aWb_0);  // "wb"
        _wb__1 = _wb_; /*0x103b8*/
        fwrite(dword_53A61, 1, (char *)&loc_329FE + 2, _wb_); /*0x103cb*/
        fclose(_wb__1); /*0x103d4*/
        
        // 恢复所有状态变量
        n999 = *(unsigned __int8 *)(v5 + 12483); /*0x103df*/
        LODWORD(qword_53AA9) = *(unsigned __int8 *)(v5 + 12486); /*0x103e8*/
        HIDWORD(qword_53AA9) = *(unsigned __int8 *)(v5 + 12487); /*0x103f1*/
        LODWORD(qword_53AB1) = *(unsigned __int8 *)(v5 + 12488); /*0x103fa*/
        HIDWORD(qword_53AB1) = *(unsigned __int8 *)(v5 + 12489); /*0x10403*/
        n10 = *(unsigned __int8 *)(v5 + 12490); /*0x1040c*/
        ::n2 = *(unsigned __int8 *)(v5 + 12491); /*0x10415*/
        n16_1 = *(unsigned __int8 *)(v5 + 12492); /*0x1041e*/
        n999_0 = *(_DWORD *)(v5 + 12493); /*0x10426*/
        byte_53AF9 = *(_BYTE *)(v5 + 12497); /*0x1042e*/
        byte_51AAB = *(_BYTE *)(v5 + 12498); /*0x10436*/
        n127 = *(_BYTE *)(v5 + 12499); /*0x1043e*/
        byte_51E62 = *(_BYTE *)(v5 + 12500); /*0x10446*/
        
        free(v5); /*0x1044c*/
        free(FDFIELD_DAT); /*0x1045a*/
        FDFIELD_DAT = 0; /*0x10462*/
        
        // 播放音乐、显示动画
        sub_25977((unsigned __int8)byte_51E63[n17], SHIDWORD(_wb_), _wb__1, a3, 
            (unsigned __int8)byte_51E63[n17], 0); /*0x1047b*/
        n6_5 = 0; /*0x10483*/
        sub_12263(); /*0x1048d*/
        LODWORD(_wb_) = sub_11CAC(1); /*0x10494*/
        sub_1F525(_wb_, SHIDWORD(_wb_), _wb__1, a3); /*0x1049c*/
        
        // 播放过渡动画...
        // ...
      }
    }
  }
  // ...
}
```

---

## 八、存档选择界面 (sub_29BCB)

### 8.1 IDA MCP 反编译代码

```c
void __fastcall sub_29BCB(__int32 n3, int a2, int a3, int n8, int a5, int n3a)
{
  int v6; // esi
  __int64 n28; // rax
  int n5; // ebx

  sub_3702F(n3, a2, a3, n8, 32); /*0x29bd0*/
  v6 = 0; /*0x29be1*/
  dword_53C5B = malloc(64000); /*0x29bf0*/
  dword_53C5F = malloc(64000); /*0x29c02*/
  n655360_0 = (unsigned __int8 *)malloc(64000); /*0x29c14*/
  memmove(dword_53C5F, 655360, 64000); /*0x29c29*/
  n28 = memmove(n655360_0, dword_53C5F, 64000); /*0x29c42*/
  sub_4EBFF(n655360_0 + 35845, (__int16 *)(*(_DWORD *)(FDOTHER_DAT__11 + 70) + 
      FDOTHER_DAT__11), 320); /*0x29c63*/
  sub_29AB2((int)n4_1, (int)n655360_0, a5); /*0x29c78*/
  sub_25A96(n28, SHIDWORD(n28), a3, n8, FDOTHER_DAT__2, 5, 1); /*0x29c8a*/
  
  for ( n5 = 5; n5 >= 0; --n5 ) /*0x29c92*/
    sub_1974C(13 * n5 + 112, dword_53C5B, (int)n655360_0); /*0x29cac*/
  
  while ( 1 ) /*0x29cb9*/
  {
    if ( n3a ) /*0x29cbb*/  // n3a != 0: Load模式
    {
      sub_16C57(n28, SHIDWORD(n28), n5, n8, 0); /*0x29cbf*/
    }
    else  // 保存模式
    {
      HIBYTE(::n3) = 16; /*0x29cc9*/
      int386(22, &::n3, &::n3); /*0x29cdc*/
      if ( HIBYTE(::n3) == 224 || HIBYTE(::n3) == 82 ) /*0x29cf5*/
        HIBYTE(::n3) = 28; /*0x29cf7*/
      if ( HIBYTE(::n3) == 83 ) /*0x29d08*/
        HIBYTE(::n3) = 1; /*0x29d0a*/
      LODWORD(n28) = HIBYTE(::n3); /*0x29d11*/
    }
    
    // 下箭头 (80) 且 n4_1 == 3 (最大槽位索引)
    if ( (_DWORD)n28 != 80 || n4_1 == (unsigned __int8 *)3 ) /*0x29d24*/
    {
      // 上箭头 (72)
      if ( (_DWORD)n28 == 72 && n4_1 ) /*0x29d60*/
      {
        sub_25A96(72, SHIDWORD(n28), n5, n8, FDOTHER_DAT__2, 7, 1); /*0x29d6c*/
        sub_29AB2((int)--n4_1, 655360, a5); /*0x29d80*/  // 槽位索引-1
      }
      // 确认键 (28) 或 空格 (57)
      else if ( (_DWORD)n28 == 28 || (_DWORD)n28 == 57 ) /*0x29d8a*/
      {
        v6 = 1; /*0x29d8c*/  // 返回确认
      }
      // 取消键 (1)
      else if ( (_DWORD)n28 == 1 ) /*0x29d96*/
      {
        v6 = -1; /*0x29d98*/  // 返回取消
      }
    }
    // 下箭头 (80)
    else
    {
      sub_25A96(80, SHIDWORD(n28), n5, n8, FDOTHER_DAT__2, 7, 1); /*0x29d30*/
      sub_29AB2((int)++n4_1, 655360, a5); /*0x29d4a*/  // 槽位索引+1
    }
    
    if ( v6 ) /*0x29d9f*/
      JUMPOUT(0x26A73); /*0x26a73*/  // 退出循环
  }
}
```

### 8.2 按键映射

| 按键码 | 按键 | 功能 | 代码行 |
|--------|------|------|--------|
| 80 | 下箭头 | 槽位索引+1 | 0x29d24 之后 |
| 72 | 上箭头 | 槽位索引-1 | 0x29d60 |
| 28 | 回车 | 确认选择 | 0x29d8a |
| 57 | 空格 | 确认选择 | 0x29d8a |
| 1 | Esc | 取消 | 0x29d96 |

### 8.3 存档槽位验证

```c
if ( (_DWORD)n28 != 80 || n4_1 == (unsigned __int8 *)3 )  // line 0x29d24
```

**n4_1 最大值为 3**，证明有4个存档槽位 (0, 1, 2, 3)

---

## 九、FD2.SAV 完整文件结构

### 9.1 总体布局

```
FD2.SAV 文件结构 (22987字节)
├── [0x0000 - 0x08A2]     营地地图数据 (2211字节)
├── [0x08A3 - 0x12A2]     临时地图数据 (2560字节)
├── [0x12A3 - 0x30A2]     角色数据 (7680字节, 80字节/角色)
├── [0x30A3 - 0x30C2]     角色状态数据 (32字节)
├── [0x30C3 - 0x30D4]     游戏状态变量 (18字节)
├── [0x30D5 - 0x3172]     预留区域 (86字节)
├── [0x3173 - 0x3B9A]     存档槽位0战场数据 (2600字节)
├── [0x3B9B - 0x45BA]     存档槽位1战场数据 (2600字节)
├── [0x45BB - 0x4FDA]     存档槽位2战场数据 (2600字节)
├── [0x4FDB - 0x59CA]     存档槽位3战场数据 (2596字节)
└── [0x59CB - 0x59CE]     校验和 (4字节)
```

**注意**: 文件总大小 22987 字节

### 9.2 详细偏移表

| 偏移 | 大小 | 字段名 | 全局变量 | IDA代码行 |
|------|------|--------|----------|-----------|
| **0 - 2210** | 2211 | campMapData | FDFIELD_DAT__1 | sub_10010:0x101cf |
| **2211 - 4770** | 2560 | tempMapData | n8_3 | sub_10010:0x10121 |
| **4771 - 12450** | 7680 | charData | n8_1 | sub_10010:0x10311 |
| **12451 - 12482** | 32 | charStateData | n8_0 | sub_10010:0x10328 |
| **12483** | 1 | n999 | n999 | sub_10010:0x103df |
| **12484** | 1 | n6_0 | n6_0 | sub_10010:0x1029a |
| **12485** | 1 | n17 | n17 | sub_10010:0x1013e |
| **12486** | 1 | qword_53AA9_lo | qword_53AA9 | sub_10010:0x103e8 |
| **12487** | 1 | qword_53AA9_hi | qword_53AA9 | sub_10010:0x103f1 |
| **12488** | 1 | qword_53AB1_lo | qword_53AB1 | sub_10010:0x103fa |
| **12489** | 1 | qword_53AB1_hi | qword_53AB1 | sub_10010:0x10403 |
| **12490** | 1 | n10 | n10 | sub_10010:0x1040c |
| **12491** | 1 | n2 | n2 | sub_10010:0x10415 |
| **12492** | 1 | n16_1 | n16_1 | sub_10010:0x1041e |
| **12493 - 12496** | 4 | n999_0 | n999_0 | sub_10010:0x10426 |
| **12497** | 1 | byte_53AF9 | byte_53AF9 | sub_10010:0x1042e |
| **12498** | 1 | byte_51AAB | byte_51AAB | sub_10010:0x10436 |
| **12499** | 1 | n127 | n127 | sub_10010:0x1043e |
| **12500** | 1 | byte_51E62 | byte_51E62 | sub_10010:0x10446 |
| **12501 - 12586** | 86 | reserved | - | - |
| **12587 - 15186** | 2600 | 槽位0战场数据 | - | sub_2968D:0x29741 |
| **15187 - 17786** | 2600 | 槽位1战场数据 | - | sub_2968D:0x29741 |
| **17787 - 20386** | 2600 | 槽位2战场数据 | - | sub_2968D:0x29741 |
| **20387 - 22982** | 2596 | 槽位3战场数据 | - | sub_2968D:0x29741 |
| **22983 - 22986** | 4 | checksum | - | sub_10010:0x10099 |

### 9.3 存档槽位数据结构 (2600字节)

每个存档槽位包含2600字节，结构如下：

| 偏移 (相对槽位) | 大小 | 字段名 | IDA代码行 |
|-----------------|------|--------|-----------|
| +0 - +2559 | 2560 | 临时地图数据 | sub_2968D:0x2974f |
| +2560 | 1 | n17 (场景索引) | sub_2968D:0x29762 |
| +2561 | 1 | n16_1 (选项数量) | sub_2968D:0x29769 |
| +2562 - +2565 | 4 | n999_0 (进度) | sub_2968D:0x29771 |
| +2566 | 1 | byte_51AAB | sub_2968D:0x29779 |
| +2567 | 1 | byte_53AF9 | sub_2968D:0x29781 |
| +2568 | 1 | n127 | sub_2968D:0x29789 |
| +2569 | 1 | byte_51E62 | sub_2968D:0x29791 |
| +2570 - +2599 | 30 | 预留 | - |

### 9.4 槽位索引计算

```c
v10 = 2600 * (_DWORD)n4_1 + v6 + 12587;  // sub_2968D:0x29741
// v6 = buffer地址
// n4_1 = 槽位索引 (0-3)
// 12587 = 第一个槽位的偏移
```

| 槽位索引 | 计算公式 | 起始偏移 |
|----------|----------|----------|
| 0 | 12587 + 2600*0 | 12587 |
| 1 | 12587 + 2600*1 | 15187 |
| 2 | 12587 + 2600*2 | 17787 |
| 3 | 12587 + 2600*3 | 20387 |

**验证**: 槽位3结束位置 = 20387 + 2600 = 22987 (文件末尾)

---

## 十、C语言数据结构定义

```c
#pragma pack(push, 1)

// 单个存档槽位 (2600字节)
typedef struct {
    u8 tempMapData[2560];    // +0: 临时地图数据
    u8 n17;                  // +2560: 场景索引 (255=空)
    u8 n16_1;                // +2561: 选项数量
    u32 n999_0;              // +2562: 进度数据
    u8 byte_51AAB;           // +2566: 状态标志
    u8 byte_53AF9;           // +2567: 场景标志
    u8 n127;                 // +2568: 音乐控制
    u8 byte_51E62;           // +2569: 音乐标志
    u8 reserved[30];         // +2570: 预留
} fd2_save_slot_t;

// 完整存档文件 (22987字节)
typedef struct {
    u8 campMapData[2211];    // +0: 营地地图数据
    u8 tempMapData[2560];    // +2211: 临时地图数据
    u8 charData[7680];       // +4771: 角色数据 (80字节/角色)
    u8 charStateData[32];    // +12451: 角色状态数据
    u8 n999;                 // +12483: 音乐变量
    u8 n6_0;                 // +12484: 角色数量
    u8 n17;                  // +12485: 场景索引
    u8 qword_53AA9_lo;       // +12486
    u8 qword_53AA9_hi;       // +12487
    u8 qword_53AB1_lo;       // +12488
    u8 qword_53AB1_hi;       // +12489
    u8 n10;                  // +12490
    u8 n2;                   // +12491
    u8 n16_1;                // +12492
    u32 n999_0;              // +12493
    u8 byte_53AF9;           // +12497
    u8 byte_51AAB;           // +12498
    u8 n127;                 // +12499
    u8 byte_51E62;           // +12500
    u8 reserved[86];         // +12501: 预留
    fd2_save_slot_t slots[4]; // +12587: 4个存档槽位
    u32 checksum;            // +22983: 校验和
} fd2_sav_t;

#pragma pack(pop)

// 编译时检查
static_assert(sizeof(fd2_save_slot_t) == 2600, "slot size must be 2600");
static_assert(sizeof(fd2_sav_t) == 22987, "fd2_sav_t size must be 22987");
```

---

## 十一、加密与校验

### 11.1 加密算法 (sub_4DF28)

**IDA MCP 反编译代码**:

```c
char __cdecl sub_4DF28(char *a1, int a2)
{
  n165 = 165;  // 初始密钥
  do
  {
    v6 = *v2++;
    n165 = __ROL2__(n165 - 28652, 3);  // 更新密钥
    result = n165 ^ v6;  // XOR
    *v3++ = result;
    --a2;
  }
  while ( a2 );
  return result;
}
```

### 11.2 校验算法 (sub_4DF09)

**IDA MCP 反编译代码**:

```c
int __cdecl sub_4DF09(_BYTE *a1, int n22987)
{
  v3 = n22987 - 4;  // 前22983字节
  v4 = 0;
  v5 = 0;
  do
  {
    LOBYTE(v5) = *a1++;
    v4 += v5;  // 累加
    --v3;
  }
  while ( v3 );
  return v4;
}
```

---

## 十二、全局变量映射表

| 全局变量 | 存档偏移 | 类型 | 说明 | IDA代码行 |
|----------|----------|------|------|-----------|
| FDFIELD_DAT__1 | 0 | u8[2211] | 营地地图 | sub_10010:0x101cf |
| n8_3 | 2211 | u8[2560] | 临时地图 | sub_10010:0x10121 |
| n8_1 | 4771 | u8[7680] | 角色数据 | sub_10010:0x10311 |
| n8_0 | 12451 | u8[32] | 角色状态 | sub_10010:0x10328 |
| n999 | 12483 | u8 | 音乐变量 | sub_10010:0x103df |
| n6_0 | 12484 | u8 | 角色数量 | sub_10010:0x1029a |
| n17 | 12485 | u8 | 场景索引 | sub_10010:0x1013e |
| qword_53AA9 | 12486 | u16 | 状态变量 | sub_10010:0x103e8-0x103f1 |
| qword_53AB1 | 12488 | u16 | 状态变量 | sub_10010:0x103fa-0x10403 |
| n10 | 12490 | u8 | 状态变量 | sub_10010:0x1040c |
| n2 | 12491 | u8 | 状态变量 | sub_10010:0x10415 |
| n16_1 | 12492 | u8 | 选项数量 | sub_10010:0x1041e |
| n999_0 | 12493 | u32 | 进度数据 | sub_10010:0x10426 |
| byte_53AF9 | 12497 | u8 | 场景标志 | sub_10010:0x1042e |
| byte_51AAB | 12498 | u8 | 状态标志 | sub_10010:0x10436 |
| n127 | 12499 | u8 | 音乐控制 | sub_10010:0x1043e |
| byte_51E62 | 12500 | u8 | 音乐标志 | sub_10010:0x10446 |
| n4_1 | - | u8 | 存档槽位索引 | sub_29BCB:0x29d24 |

---

## 十三、存档流程图

### 13.1 主菜单流程

```
sub_25EBB (主菜单)
  ├── v6 == 0: New Game
  │    └── 开始新游戏
  ├── v6 != 0 && v6 != 1: Continue
  │    └── sub_10010() 加载战场存档
  └── v6 == 1: Load
       └── 读取FD2.SAV → 显示存档选择 → 加载选中的槽位
```

### 13.2 保存流程

```
游戏运行中
  └── sub_2968D() 保存战场存档
       ├── 读取FD2.SAV
       ├── 解密
       ├── sub_29BCB() 选择槽位
       ├── memmove(槽位地址, n8_3, 2560)
       ├── 写入状态变量 (10字节)
       ├── 计算校验和
       ├── 加密
       └── 写入FD2.SAV
```

### 13.3 营地存档保存流程

```
营地菜单
  └── sub_19DF7() case 1
       ├── 读取FD2.SAV (如果存在)
       ├── memmove(buffer, FDFIELD_DAT__1, 2211)
       ├── memmove(buffer+2211, n8_3, 2560)
       ├── memmove(buffer+4771, n8_1, 80*n6_0)
       ├── memmove(buffer+12451, n8_0, 32)
       ├── 写入所有状态变量 (18字节)
       ├── 计算校验和
       ├── 加密
       └── 写入FD2.SAV
```

---

## 十四、关键发现 (基于IDA MCP)

1. **4个存档槽位**: 根据 sub_29BCB:0x29d24 代码 `n4_1 == (unsigned __int8 *)3`
2. **槽位地址**: `2600 * n4_1 + buffer + 12587` (sub_2968D:0x29741)
3. **场景索引255**: 表示空槽位 (sub_25EBB:0x260a7, sub_2986F:0x29934)
4. **加密可逆**: sub_4DF28 同一个函数用于加密和解密
5. **校验位置**: 文件末尾4字节 (sub_4DF09:0x4df16)
6. **两种存档**: 战场存档(sub_2968D) 和 营地存档(sub_19DF7 case 1)
7. **主菜单三个选项**: New Game(0), Load(1), Continue(其他)

---

## 十五、IDA Pro 反编译文件索引

| 文件 | 函数地址 | 功能 |
|------|----------|------|
| [10010.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/10010.c) | 0x10010 | 加载战场存档 |
| [19DF7.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/19DF7.c) | 0x19DF7 | 营地存档菜单 |
| [25EBB.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/25EBB.c) | 0x25EBB | 主菜单处理 |
| [2968D.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/2968D.c) | 0x2968D | 保存战场存档 |
| [2986F.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/2986F.c) | 0x2986F | 加载营地存档 |
| [29BCB.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/29BCB.c) | 0x29BCB | 存档选择界面 |
| [4DF28.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/4DF28.c) | 0x4DF28 | 解密/加密 |
| [4DF09.c](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/4DF09.c) | 0x4DF09 | 校验和 |

---

## 相关文档

- [tools/export-for-ai/decompile/](file:///d:/workspace/fd2_dat_freebuff/tools/export-for-ai/decompile/) - IDA反编译代码目录
