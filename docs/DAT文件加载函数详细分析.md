# FD2.EXE DAT文件加载函数详细分析

## 一、sub_111BA - 核心DAT文件加载函数 (地址: 0x111BA)

### 1.1 功能描述
这是整个程序中加载DAT文件的核心函数。它根据文件名和索引号，从DAT文件中读取对应的数据块到内存。

### 1.2 参数分析

```
调用约定: __fastcall (部分参数通过寄存器传递)
寄存器参数:
  eax -> a1: __int32 (未知用途，可能是上下文指针)
  edx -> a2: int (未知用途)
  ecx -> a3: int (未知用途)
  ebx -> n99: int (未知用途)
栈参数:
  [esp+4]  -> arg_0: int (DAT文件名指针，如"FDOTHER.DAT")
  [esp+8]  -> arg_4: int (之前分配的内存指针，用于释放旧数据)
  [esp+12] -> arg_8: int (数据块索引号)
返回值:
  eax: 指向加载数据的指针 (_BYTE *)
```

### 1.3 反汇编逐行分析

```asm
; 函数入口 - 初始化栈帧
111ba  push    20h                    ; 栈帧大小32字节
111bf  call    sub_3702F              ; 初始化栈帧
111c4  push    ebx                    ; 保存寄存器
111c5  push    esi
111c6  push    edi

; 获取参数并释放旧内存
111c7  mov     ebx, [esp+0Ch+arg_4]   ; ebx = 旧内存指针
111cb  test    ebx, ebx               ; 检查是否为NULL
111cd  jz      short loc_111D8        ; 如果为NULL，跳过释放
111cf  push    ebx
111d0  call    free                   ; 释放旧内存
111d5  add     esp, 4

; 打开DAT文件
loc_111D8:
111d8  push    offset aRb_12          ; 压入"rb"模式字符串
111dd  push    [esp+10h+arg_0]        ; 压入文件名
111e1  call    fopen                  ; 以二进制只读模式打开文件
111e6  add     esp, 8
111e9  mov     esi, eax               ; esi = 文件句柄
111eb  test    eax, eax               ; 检查文件是否打开成功
111ed  jnz     short loc_11205        ; 成功则继续

; 文件打开失败处理
111ef  push    [esp+0Ch+arg_0]        ; 压入文件名用于错误信息
111f3  push    offset aFileNotFoundS  ; "\n\n File not found %s!!! \n\n"
111f8  call    printf                 ; 打印错误信息
111fd  add     esp, 8
11200  jmp     loc_1005E              ; 跳转到退出

; 分配临时缓冲区
loc_11205:
11205  push    8                      ; 分配8字节
11207  call    malloc
1120c  mov     ebx, eax               ; ebx = 临时缓冲区指针
1120e  add     esp, 4

; 计算索引表位置并定位
11211  push    0                      ; SEEK_SET = 0
11213  mov     eax, [esp+10h+arg_8]   ; eax = 索引号
11217  shl     eax, 2                 ; eax = 索引号 * 4 (每个索引4字节)
1121a  add     eax, 6                 ; eax = 索引号 * 4 + 6 (跳过6字节文件头)
1121d  push    eax                    ; 压入偏移量
1121e  push    esi                    ; 压入文件句柄
1121f  call    fseek                  ; 定位到索引表位置

; 读取索引数据
11224  add     esp, 0Ch
11227  push    esi                    ; 文件句柄
11228  push    8                      ; 读取8字节
1122a  push    1                      ; 每次读取1字节
1122c  push    ebx                    ; 目标缓冲区
1122d  call    sub_373CA              ; 读取8字节（两个32位索引值）

; 解析索引数据
11232  add     esp, 10h
11235  mov     edi, [ebx]             ; edi = 起始偏移 (索引值1)
11237  mov     eax, [ebx+4]           ; eax = 结束偏移 (索引值2)
1123a  sub     eax, edi               ; eax = 数据块大小 = 结束偏移 - 起始偏移
1123c  mov     dword_53BFF, eax       ; 保存数据块大小到全局变量

; 释放临时缓冲区
11241  push    ebx
11242  call    free                   ; 释放8字节临时缓冲区

; 分配数据缓冲区
1124a  push    dword_53BFF            ; 数据块大小
11250  call    malloc                 ; 分配数据缓冲区
11255  add     esp, 4
11258  mov     ebx, eax               ; ebx = 数据缓冲区指针
1125a  test    eax, eax               ; 检查分配是否成功
1125c  jnz     short loc_11278        ; 成功则继续

; 内存分配失败处理
1125e  push    [esp+0Ch+arg_8]        ; 索引号
11262  push    [esp+10h+arg_0]        ; 文件名
11266  push    offset aOutOfMemoryAtL ; "Out of Memory at Load %s Number:%d!!\n"
1126b  call    printf                 ; 打印错误信息

; 定位并读取数据块
loc_11278:
11278  push    0                      ; SEEK_SET = 0
1127a  push    edi                    ; 起始偏移
1127b  push    esi                    ; 文件句柄
1127c  call    fseek                  ; 定位到数据块起始位置
11281  add     esp, 0Ch
11284  push    esi                    ; 文件句柄
11285  push    dword_53BFF            ; 数据块大小
1128b  push    1                      ; 每次读取1字节
1128d  push    ebx                    ; 数据缓冲区
1128e  call    sub_373CA              ; 读取整个数据块

; 关闭文件并返回
11293  add     esp, 10h
11296  push    esi                    ; 文件句柄
11297  call    fclose                 ; 关闭文件
1129c  add     esp, 4
1129f  mov     eax, ebx               ; eax = 数据缓冲区指针 (返回值)
112a1  pop     edi                    ; 恢复寄存器
112a2  pop     esi
112a3  pop     ebx
112a4  retn                          ; 返回
```

### 1.4 C代码实现

```c
/**
 * 函数名: sub_111BA
 * 地址: 0x111BA
 * 功能: 从DAT文件加载指定索引的数据块到内存
 * 
 * 参数说明:
 *   @param a1 (__int32) - 未知用途，可能是上下文指针
 *   @param a2 (int) - 未知用途
 *   @param a3 (int) - 未知用途
 *   @param a4 (int) - 未知用途
 *   @param a5 (int) - DAT文件名字符串指针 (如 "FDOTHER.DAT")
 *   @param a6 (int) - 之前分配的内存指针 (如果非NULL则先释放)
 *   @param a7 (int) - 数据块索引号 (从0开始)
 * 
 * 返回值:
 *   @return (_BYTE *) - 指向加载的数据块的指针，失败时程序退出
 * 
 * DAT文件格式:
 *   [文件头 6字节] [索引表(每项4字节)] [数据块0] [数据块1] ...
 *   
 *   索引表结构:
 *   - 索引N的值 = 数据块N在文件中的起始偏移
 *   - 数据块N的大小 = 索引[N+1] - 索引[N]
 *   - 文件头固定6字节，索引表从偏移6开始
 */
_BYTE *__fastcall sub_111BA(__int32 a1, int a2, int a3, int a4, int a5, int a6, int a7)
{
  int file_handle;      // 文件句柄 (esi)
  int *temp_buffer;     // 临时8字节缓冲区 (ebx)
  int data_offset;      // 数据块起始偏移 (edi)
  _BYTE *data_buffer;   // 数据缓冲区指针 (ebx/返回值)

  // 初始化栈帧 (32字节)
  sub_3702F(a1, a2, a3, a4, 32);
  
  // 如果之前有分配的内存，先释放
  if (a6)
    free(a6);
  
  // 以二进制只读模式打开DAT文件
  file_handle = fopen((const char *)a5, "rb");
  if (!file_handle)
  {
    // 文件未找到，打印错误信息
    printf("\n\n File not found %s!!! \n\n", (const char *)a5);
    goto ERROR_EXIT;
  }
  
  // 分配8字节临时缓冲区，用于存储两个索引值
  temp_buffer = (int *)malloc(8);
  if (!temp_buffer)
  {
    fclose(file_handle);
    goto ERROR_EXIT;
  }
  
  // 计算索引表位置: offset = index * 4 + 6
  // 每个索引项占4字节，文件头有6字节
  fseek(file_handle, 4 * a7 + 6, SEEK_SET);
  
  // 读取8字节 (两个32位整数)
  // temp_buffer[0] = 当前数据块的起始偏移
  // temp_buffer[1] = 下一个数据块的起始偏移
  sub_373CA((unsigned char *)temp_buffer, 1, 8, file_handle);
  
  // 解析索引数据
  data_offset = temp_buffer[0];           // 数据块起始偏移
  dword_53BFF = temp_buffer[1] - temp_buffer[0];  // 数据块大小 = 结束偏移 - 起始偏移
  
  // 释放临时缓冲区
  free(temp_buffer);
  
  // 根据数据块大小分配内存
  data_buffer = (_BYTE *)malloc(dword_53BFF);
  if (!data_buffer)
  {
    // 内存分配失败，打印错误信息
    printf("Out of Memory at Load %s Number:%d!!\n", 
           (const char *)a5, a7);
    goto ERROR_EXIT;
  }
  
  // 定位到数据块起始位置
  fseek(file_handle, data_offset, SEEK_SET);
  
  // 读取整个数据块到缓冲区
  sub_373CA(data_buffer, 1, dword_53BFF, file_handle);
  
  // 关闭文件
  fclose(file_handle);
  
  // 返回数据缓冲区指针
  return data_buffer;

ERROR_EXIT:
  // 错误处理 - 退出程序
  exit(1);
}
```

### 1.5 关键全局变量

| 变量名 | 地址 | 类型 | 说明 |
|--------|------|------|------|
| dword_53BFF | 0x53BFF | int | 最后一次加载的数据块大小 |

---

## 二、sub_10010 - 存档加载函数 (地址: 0x10010)

### 2.1 功能描述
此函数负责从FD2.SAV存档文件加载游戏状态，并根据存档数据加载相关的DAT文件资源。

### 2.2 参数分析

```
调用约定: __usercall (多个寄存器参数)
寄存器参数:
  eax -> a1: __int32 (未知用途)
  edx -> a2: int (未知用途)
  ecx -> a3: int (未知用途)
  ebx -> n99: int (未知用途)
  edi -> a5: unsigned __int8 * (未知用途)
局部变量:
  [ebp-0x14]: int (文件句柄)
返回值:
  void (无返回值，错误时直接退出)
```

### 2.3 执行流程

1. **分配22987字节缓冲区** (0x59CB)
2. **打开并读取FD2.SAV存档文件**
3. **校验存档数据完整性**
4. **从存档中提取各种游戏数据**
5. **加载相关DAT文件资源**:
   - FDOTHER.DAT (索引0)
   - FDFIELD.DAT (索引 3*n17+2)
   - FDTXT.DAT (索引 n17+1)
   - FDFIELD.DAT (索引 3*n17)
   - FDSHAP.DAT (索引 2*byte)
   - FDSHAP.DAT (索引 2*byte+1)
   - FDICON.B24 (图标文件)
6. **初始化游戏地图和单元数据**
7. **显示加载动画**

### 2.4 C代码实现

```c
/**
 * 函数名: sub_10010
 * 地址: 0x10010
 * 功能: 从FD2.SAV加载存档并初始化游戏资源
 * 
 * 参数说明:
 *   @param a1 (__int32) - 未知用途
 *   @param a2 (int) - 未知用途
 *   @param a3 (int) - 未知用途
 *   @param n99 (int) - 未知用途
 *   @param a5 (unsigned __int8 *) - 未知用途
 * 
 * 存档文件格式 (FD2.SAV):
 *   总大小: 22987字节 (0x59CB)
 *   [0x0000 - 0x08A2]: 地图数据 (2211字节)
 *   [0x08A3 - 0x12A2]: 地图单元数据 (2560字节)
 *   [0x12A3 - 0x30A2]: 其他游戏数据
 *   [0x30A3 - 0x30C2]: 配置数据 (32字节)
 *   [0x30C3 - 0x30CA]: 游戏状态字节 (8字节)
 *   [0x30CB - 0x59C6]: 其他数据
 *   [0x59C7 - 0x59CA]: 校验码 (4字节)
 */
void __usercall sub_10010(__int32 a1, int a2, int a3, int n99, unsigned __int8 *a5)
{
  int save_buffer;      // 存档数据缓冲区 (ebp)
  int file_handle;      // 文件句柄 (ebx)
  int map_index;        // 地图索引 (eax/n17)
  int data_ptr;         // 数据指针 (esi)
  int i;                // 循环变量
  int temp_handle;      // 临时文件句柄 (var_14)

  // 初始化栈帧 (60字节)
  sub_3702F(a1, a2, n99, a3, 60);
  
  // 分配22987字节缓冲区用于存档数据
  save_buffer = malloc(22987);
  if (!save_buffer)
  {
    // 内存不足，切换到图形模式并退出
    n3 = 3;
    int386(0x10, &n3, &n3);
    printf(" Out of Memory !!!\n");
    exit(1);
  }
  
  // 打开存档文件
  file_handle = fopen("FD2.SAV", "rb");
  
  // 读取整个存档文件
  sub_373CA((unsigned char *)save_buffer, 1, 22987, file_handle);
  fclose(file_handle);
  
  // 处理/解密存档数据
  sub_4DF28((char *)save_buffer, 22987);
  
  // 校验存档数据
  // sub_4DF09计算校验码，与存档末尾的校验码比较
  if (sub_4DF09((unsigned char *)save_buffer, 22987) != 
      *(int *)(save_buffer + 22983))
  {
    // 校验失败，显示错误
    sub_1956B(75);
    sub_15F84(a5, "FDTXT.DAT", 436, 696099, 320, 205, 76, 74, 19, 1);
    sub_16559(0);
    sub_16C57(0);
    sub_196CB();
  }
  
  // 获取游戏状态
  sub_1F882();
  
  // 复制地图单元数据到n8_3 (2560字节)
  memmove(n8_3, (void *)(save_buffer + 2211), 2560);
  
  // === 加载DAT文件资源 ===
  
  // 1. 加载FDOTHER.DAT 索引0
  FDOTHER_DAT = (int)sub_111BA(a1, a2, n99, a3, 
                                (int)"FDOTHER.DAT", FDOTHER_DAT, 0);
  
  // 2. 获取地图索引 (偏移12485 = 0x30C5)
  n17 = *(unsigned char *)(save_buffer + 12485);
  
  // 3. 加载FDFIELD.DAT 索引(3*n17+2)
  FDFIELD_DAT = (int)sub_111BA(3 * n17 + 2, n17, n99, a3,
                                (int)"FDFIELD.DAT", FDFIELD_DAT, 3 * n17 + 2);
  
  // 4. 分配2211字节缓冲区存储地图数据
  if (FDFIELD_DAT__1)
    free(FDFIELD_DAT__1);
  FDFIELD_DAT__1 = malloc(2211);
  if (!FDFIELD_DAT__1)
  {
    // 内存不足处理
    goto OUT_OF_MEMORY;
  }
  
  // 5. 从存档复制地图数据
  memmove(FDFIELD_DAT__1, (void *)save_buffer, 2211);
  sub_10652(...);  // 处理地图数据
  
  // 6. 加载FDTXT.DAT 索引(n17+1)
  FDTXT_DAT = (int)sub_111BA(n17 + 1, ... , (int)"FDTXT.DAT", FDTXT_DAT, n17 + 1);
  
  // 7. 加载FDFIELD.DAT 索引(3*n17)
  FDFIELD_DAT__0 = (int)sub_111BA(3 * n17, n17, n99, a3,
                                   (int)"FDFIELD.DAT", FDFIELD_DAT__0, 3 * n17);
  
  // 8. 解析地图尺寸
  dword_53AC1 = *(short *)FDFIELD_DAT__0;      // 地图宽度
  n40 = *(short *)(FDFIELD_DAT__0 + 2);        // 地图高度
  
  // 9. 计算形状索引
  int shape_index = 2 * *(unsigned char *)FDFIELD_DAT__1;
  
  // 10. 加载FDSHAP.DAT
  FDSHAP_DAT = (int)sub_111BA(FDFIELD_DAT__1, ... , (int)"FDSHAP.DAT", 
                               FDSHAP_DAT, shape_index);
  FDSHAP_DAT__0 = (int)sub_111BA(FDSHAP_DAT, ... , (int)"FDSHAP.DAT", 
                                  FDSHAP_DAT__0, shape_index + 1);
  
  // 11. 处理地图数据
  sub_4DF4C((unsigned char *)FDFIELD_DAT__0);
  
  // 12. 获取地图单元数量和其他参数
  n6 = *(unsigned char *)(FDFIELD_DAT__1 + 1);
  dword_53BE3 = *(unsigned char *)(FDFIELD_DAT__1 + 2);
  n6_0 = *(unsigned char *)(save_buffer + 12484);
  
  // 13. 分配地图单元数据缓冲区 (7680字节 = 80 * n6_0)
  if (n8_1)
    free(n8_1);
  n8_1 = malloc(7680);
  if (!n8_1)
  {
    goto OUT_OF_MEMORY;
  }
  
  // 14. 复制地图单元数据 (从偏移4771开始)
  memmove(n8_1, (void *)(save_buffer + 4771), 80 * n6_0);
  
  // 15. 复制配置数据 (32字节，从偏移12451开始)
  memmove(n8_0, (void *)(save_buffer + 12451), 32);
  
  // 16. 加载图标文件
  if (dword_53A61)
    free(dword_53A61);
  temp_handle = fopen("FDICON.B24", "rb");
  dword_53BDF = 0;
  
  // 为每个地图单元加载图标
  for (i = 0; i < n6_0; ++i)
  {
    // 获取图标索引 (从地图单元数据偏移7处)
    int icon_index = *(unsigned char *)(80 * i + n8_1 + 7);
    // 加载图标并存储到偏移2处
    *(unsigned char *)(80 * i + n8_1 + 2) = sub_11019(icon_index, temp_handle);
  }
  fclose(temp_handle);
  
  // 17. 创建临时文件
  temp_handle = fopen("FD2.TMP", "wb");
  fwrite(dword_53A61, 1, (int)&loc_329FE + 2, temp_handle);
  fclose(temp_handle);
  
  // 18. 从存档恢复游戏状态
  n999 = *(unsigned char *)(save_buffer + 12483);
  qword_53AA9 = *(unsigned char *)(save_buffer + 12486);
  qword_53AA9+4 = *(unsigned char *)(save_buffer + 12487);
  qword_53AB1 = *(unsigned char *)(save_buffer + 12488);
  qword_53AB1+4 = *(unsigned char *)(save_buffer + 12489);
  n10 = *(unsigned char *)(save_buffer + 12490);
  n2 = *(unsigned char *)(save_buffer + 12491);
  n16_1 = *(unsigned char *)(save_buffer + 12492);
  n999_0 = *(int *)(save_buffer + 12493);
  byte_53AF9 = *(unsigned char *)(save_buffer + 12497);
  byte_51AAB = *(unsigned char *)(save_buffer + 12498);
  n127 = *(unsigned char *)(save_buffer + 12499);
  byte_51E62 = *(unsigned char *)(save_buffer + 12500);
  
  // 19. 释放临时缓冲区
  free(save_buffer);
  free(FDFIELD_DAT);
  FDFIELD_DAT = 0;
  
  // 20. 初始化游戏场景
  sub_25977(..., (unsigned char)byte_51E63[n17], 0);
  n6_5 = 0;
  sub_12263();
  sub_11CAC(1);
  sub_1F525();
  
  // 21. 显示加载动画 (9帧)
  for (i = 0; i < 9; ++i)
  {
    sub_15F0E(FDOTHER_DAT__7, 655360, 320, 120, 84, i + 83);
    int screen_ptr = sub_187D6(684651, 320, n999, 42, 3);
    delay(70);
    if (i == 8)
      delay(500);
    sub_15E71(screen_ptr, 655360, 320);
  }
  
  // 22. 显示其他动画 (5帧)
  for (int j = 2; j < 6; ++j)
  {
    if (j == 5)
      j = 9;
    sub_15F0E(FDOTHER_DAT__7, n655360 + 32904, 456, 116, j*j + 84, 91);
    int screen_ptr2 = ...;
    sub_187D6(...);
    sub_11EB0(...);
    sub_17AA9(1);
    sub_15E71(screen_ptr2, n655360 + 32904, 456);
  }
  
  // 23. 完成加载
  sub_11CAC(0);
  delay(200);
  dword_53AE9 = 0;
  n6_5 = 1;
  sub_4E381();
  goto loc_22BBE;

OUT_OF_MEMORY:
  n3 = 3;
  int386(0x10, &n3, &n3);
  printf(" Out of Memory !!!\n");
  exit(1);
}
```

### 2.5 关键全局变量

| 变量名 | 说明 |
|--------|------|
| FDOTHER_DAT | FDOTHER.DAT索引0的数据指针 |
| FDFIELD_DAT | FDFIELD.DAT数据指针 |
| FDFIELD_DAT__0 | FDFIELD.DAT数据指针 (地图数据) |
| FDFIELD_DAT__1 | FDFIELD.DAT数据指针 (地图信息) |
| FDTXT_DAT | FDTXT.DAT数据指针 |
| FDSHAP_DAT | FDSHAP.DAT数据指针 |
| FDSHAP_DAT__0 | FDSHAP.DAT数据指针 |
| dword_53AC1 | 地图宽度 |
| n40 | 地图高度 |
| n6_0 | 地图单元数量 |
| n8_1 | 地图单元数据指针 (每个单元80字节) |
| n8_0 | 配置数据指针 (32字节) |
| dword_53A61 | 图标数据缓冲区指针 |
| dword_53BDF | 图标数量 |
| n17 | 当前地图索引 |

---

## 三、sub_25EBB - 游戏状态加载函数 (地址: 0x25EBB)

### 3.1 功能描述
此函数处理游戏状态的加载和切换，包括启动画面、存档加载和游戏初始化。

### 3.2 C代码实现

```c
/**
 * 函数名: sub_25EBB
 * 地址: 0x25EBB
 * 功能: 加载游戏状态并初始化游戏场景
 * 
 * 参数说明:
 *   @param a1 (__int32) - 未知用途
 *   @param a2 (int) - 未知用途
 *   @param a3 (int) - 未知用途
 *   @param n99 (int) - 未知用途
 *   @param a5 (unsigned __int8 *) - 未知用途
 * 
 * 返回值:
 *   @return (bool) - 加载是否成功
 */
bool __usercall sub_25EBB(__int32 a1, int a2, int a3, int n99, unsigned __int8 *a5)
{
  int result;         // 返回值 (eax)
  int save_buffer;    // 存档缓冲区 (edi/ebx)
  int file_handle;    // 文件句柄 (esi)
  int loop_result;    // 循环结果 (esi)
  int i;              // 循环变量 (n4_1)

  // 初始化栈帧 (32字节)
  sub_3702F(a1, a2, n99, a3, 32);
  
  // 调用启动画面函数
  result = sub_1F894(a1, a2, n99, a3);
  
  // 根据启动画面返回值进行不同处理
  if (result == 0)
  {
    // 首次启动，初始化游戏
    sub_1F882();
    n17 = 0;
    
    // 加载FDOTHER.DAT索引0
    FDOTHER_DAT = (int)sub_111BA(a1, a2, n99, a3,
                                  (int)"FDOTHER.DAT", FDOTHER_DAT, 0);
    n16_1 = 0;
    byte_51AAC = 0;
    
    // 调用场景初始化函数
    funcs_25E3A[n17](a5);
    sub_25977(..., (unsigned char)byte_51E63[n17], 0);
    byte_51AAC = 1;
    sub_4E381();
    return 0;
  }
  
  if (result != 1)
  {
    // 其他情况，调用sub_10010加载存档
    sub_25977(..., -1, 0);
    sub_10010(a1, a2, a3, n99, a5);
    sub_25977(..., (unsigned char)byte_51E63[n17], 0);
    return 0;
  }
  
  // result == 1，从存档恢复游戏状态
  
  // 1. 加载FDOTHER.DAT索引13
  FDOTHER_DAT__11 = (int)sub_111BA(1, a2, n99, a3,
                                    (int)"FDOTHER.DAT", FDOTHER_DAT__11, 13);
  
  // 2. 加载FDOTHER.DAT索引0
  sub_1F882();
  FDOTHER_DAT = (int)sub_111BA(sub_1F882(), a2, n99, a3,
                                (int)"FDOTHER.DAT", FDOTHER_DAT, 0);
  
  // 3. 清空屏幕缓冲区
  memset(655360, 0, 64000);
  sub_11D40(0, 255, 0);
  
  // 4. 分配存档缓冲区
  save_buffer = malloc(22987);
  file_handle = (int)fopen("FD2.SAV", &unk_50220);
  
  if (file_handle)
  {
    // 读取存档
    sub_373CA((unsigned char *)save_buffer, 1, 22987, file_handle);
    sub_4DF28((char *)save_buffer, 22987);  // 解密
    fclose(file_handle);
  }
  else
  {
    // 无存档文件，填充0xFF
    memset(save_buffer, 255, 22987);
  }
  
  // 5. 处理存档数据
  i = 0;
  do
  {
    // 处理存档数据块
    loop_result = sub_29BCB((int)save_buffer, 0);
    
    if (loop_result != -1)
    {
      // 复制数据到n8_3
      int data_ptr = (int)&save_buffer[2600 * i + 12587];
      memmove(n8_3, (void *)data_ptr, 2560);
      
      // 解析游戏状态
      unsigned char *state_ptr = (unsigned char *)(data_ptr + 2560);
      n17 = state_ptr[0];
      n16_1 = state_ptr[1];
      n999_0 = *(int *)(state_ptr + 2);
      byte_51AAB = state_ptr[6];
      byte_53AF9 = state_ptr[7];
      n127 = state_ptr[8];
      byte_51E62 = state_ptr[9];
      
      // 检查结束条件
      if (n17 == 255)
        loop_result = 0;
    }
    
    sub_26996();
  } while (!loop_result);
  
  // 6. 释放缓冲区
  free(save_buffer);
  free(FDOTHER_DAT__11);
  FDOTHER_DAT__11 = 0;
  
  // 7. 初始化游戏场景
  if (loop_result)
  {
    byte_51AAC = 0;
    loop_result = sub_26152();
    
    if (!loop_result)
    {
      funcs_25E3A[n17](save_buffer);
      sub_25977(..., (unsigned char)byte_51E63[n17], 0);
    }
    byte_51AAC = 1;
  }
  
  sub_4E381();
  return loop_result;
}
```

---

## 四、sub_11019 - 图标加载函数 (地址: 0x11019)

### 4.1 功能描述
此函数从FDICON.B24文件中加载图标数据到内存缓冲区，并维护一个图标缓存表。

### 4.2 C代码实现

```c
/**
 * 函数名: sub_11019
 * 地址: 0x11019
 * 功能: 从FDICON.B24加载图标数据并缓存
 * 
 * 参数说明:
 *   @param a1 (__int32) - 未知用途
 *   @param a2 (int) - 未知用途
 *   @param a3 (int) - 未知用途
 *   @param a4 (int) - 未知用途
 *   @param a5 (int) - 图标索引
 *   @param a6 (int) - 文件句柄 (FDICON.B24)
 * 
 * 返回值:
 *   @return (int) - 图标在缓存中的索引
 * 
 * FDICON.B24文件格式:
 *   [文件头 6字节] [索引表(每项4字节，13个)] [图标数据0] [图标数据1] ...
 *   每个图标有13个索引值，可能是不同格式/分辨率的偏移
 */
int __fastcall sub_11019(__int32 a1, int a2, int a3, int a4, int a5, int a6)
{
  unsigned char *header_buffer;  // 6720字节头缓冲区 (ebp)
  int offsets[13];               // 13个偏移值
  int data_size;                 // 数据大小
  int i;                         // 循环变量
  int cache_index;               // 缓存索引

  // 初始化栈帧 (92字节)
  sub_3702F(a1, a2, a3, a4, 92);
  
  // 定位到文件头 (偏移6)
  fseek(a6, 6, SEEK_SET);
  
  // 分配6720字节缓冲区 (用于存储13个索引项 * 若干图标)
  header_buffer = (unsigned char *)malloc(6720);
  sub_373CA(header_buffer, 1, 6720, a6);
  
  // 提取指定图标的13个偏移值
  // 每个图标占用48字节 (13 * 4 = 52? 需要确认)
  for (int n13 = 0; n13 < 13; ++n13)
  {
    offsets[n13] = *(int *)&header_buffer[48 * a5 + 4 * n13];
  }
  
  // 计算数据大小
  data_size = offsets[12] - offsets[0];
  
  // 释放头缓冲区
  free(header_buffer);
  
  // 检查图标缓存是否已初始化
  if (dword_53BDF)  // 缓存中已有图标
  {
    // 查找是否已缓存该图标
    for (i = 0; i < dword_53BDF; ++i)
    {
      if (a5 == dword_53B17[i])
        return i;  // 返回缓存索引
    }
    
    // 未缓存，添加到缓存
    dword_53B17[i] = a5;  // 记录图标索引
    
    // 定位到图标数据
    fseek(a6, offsets[0], SEEK_SET);
    
    // 读取图标数据
    sub_373CA((unsigned char *)(buf__3 + dword_53A61), 1, data_size, a6);
    
    // 存储12个相对偏移
    for (int n12 = 0; n12 < 12; ++n12)
    {
      *(int *)(dword_53A61 + 4 * (n12 + 12 * dword_53BDF)) = 
          offsets[n12] - offsets[0] + buf__3;
    }
    
    // 更新缓冲区指针
    buf__3 += data_size;
    
    // 返回新缓存索引并增加计数
    return dword_53BDF++;
  }
  else  // 首次加载，初始化缓存
  {
    // 记录第一个图标索引
    dword_53B17[0] = a5;
    
    // 分配图标数据缓冲区 ((char *)&loc_329FE + 2 字节)
    dword_53A61 = malloc((int)&loc_329FE + 2);
    
    // 定位到图标数据
    fseek(a6, offsets[0], SEEK_SET);
    
    // 读取图标数据 (偏移1920处开始)
    sub_373CA((unsigned char *)(dword_53A61 + 1920), 1, data_size, a6);
    
    // 存储12个相对偏移
    for (int n12_1 = 0; n12_1 < 12; ++n12_1)
    {
      *(int *)(dword_53A61 + 4 * n12_1) = 
          offsets[n12_1] - offsets[0] + 1920;
    }
    
    // 增加缓存计数
    ++dword_53BDF;
    
    // 更新缓冲区指针
    buf__3 = data_size + 1920;
    
    return 0;  // 返回第一个缓存索引
  }
}
```

### 4.3 关键全局变量

| 变量名 | 说明 |
|--------|------|
| dword_53A61 | 图标数据缓冲区指针 |
| dword_53BDF | 已缓存的图标数量 |
| dword_53B17 | 图标索引缓存表 (记录已加载的图标原始索引) |
| buf__3 | 图标数据缓冲区当前写入位置 |

---

## 五、sub_1F894 - 启动画面加载函数 (地址: 0x1F894)

### 5.1 功能描述
此函数在游戏启动时显示启动动画，加载大量FDOTHER.DAT资源文件，并根据是否有存档文件决定进入新游戏还是加载存档。

### 5.2 C代码实现

```c
/**
 * 函数名: sub_1F894
 * 地址: 0x1F894
 * 功能: 显示启动画面并加载初始资源
 * 
 * 参数说明:
 *   @param a1 (__int32) - 未知用途
 *   @param a2 (int) - 未知用途
 *   @param n99_1 (int) - 未知用途
 *   @param a3 (int) - 未知用途
 * 
 * 返回值:
 *   0 - 首次启动，应初始化新游戏
 *   1 - 有存档，应加载存档
 *   其他值 - 其他状态
 * 
 * 加载的FDOTHER.DAT索引:
 *   索引77 - var_18
 *   索引76 - FDOTHER_DAT
 *   索引74 - var_28
 *   索引99 - FDOTHER_DAT
 *   索引101 - FDOTHER_DAT
 *   索引69-73 - var_28 (循环5次)
 *   索引7 - var_24
 *   索引8 - FDOTHER_DAT
 *   索引102 - FDOTHER_DAT (循环中)
 *   索引101 - FDOTHER_DAT (循环中)
 */
void __fastcall sub_1F894(__int32 a1, int a2, int n99_1, int a3)
{
  int var_18;         // 局部变量，存储临时数据指针
  int var_28;         // 局部变量，存储数据指针 (short*)
  int var_24;         // 局部变量，存储数据指针 (BYTE*)
  int var_2C;         // 局部变量，标志位
  int var_1C;         // 局部变量，计数器
  BYTE var_14;        // 局部变量，索引计数器
  int dst_[15];       // 本地数组，存储关键帧索引
  int screen_buffer;  // 屏幕缓冲区指针 (edi)
  int i, j;           // 循环变量

  // 初始化栈帧 (136字节)
  sub_3702F(a1, a2, n99_1, a3, 136);
  
  // 初始化局部变量
  var_1C = 1;
  var_2C = 0;
  var_24 = 0;
  var_20 = 12;
  var_14 = 0;
  
  // 复制15个值到dst_数组
  qmemcpy(dst_, &src__14, sizeof(dst_));
  
  // === 加载初始资源 ===
  
  // 1. 加载FDOTHER.DAT索引77
  var_18 = (int)sub_111BA(a1, a2, n99_1, 0,
                          (int)"FDOTHER.DAT", 0, 77);
  
  // 2. 清空屏幕缓冲区 (64000字节)
  memset(655360, 0, 64000);
  
  // 3. 加载FDOTHER.DAT索引76
  FDOTHER_DAT = (int)sub_111BA(..., "FDOTHER.DAT", FDOTHER_DAT, 76);
  
  // 4. 初始化调色板
  sub_11D40(0, 255, 64);
  
  // 5. 加载FDOTHER.DAT索引74 (short*类型数据)
  var_28 = (short *)sub_111BA(..., "FDOTHER.DAT", 0, 74);
  
  // 6. 显示图像
  sub_4E98D(var_28, 0, 0, 655360, 320, -1);
  sub_1F525();
  sub_17AA9(1);
  sub_17AA9(30);
  
  // 7. 加载FDOTHER.DAT索引99
  sub_1F882();
  FDOTHER_DAT = (int)sub_111BA(..., "FDOTHER.DAT", FDOTHER_DAT, 99);
  memset(655360, 0, 64000);
  sub_11D40(0, 255, 0);
  sub_20421(3, 90, 1);
  
  // 8. 加载FDOTHER.DAT索引101
  sub_1F882();
  memset(655360, 0, 64000);
  FDOTHER_DAT = (int)sub_111BA(..., "FDOTHER.DAT", FDOTHER_DAT, 101);
  sub_11D40(0, 255, 64);
  
  // 9. 分配屏幕缓冲区并清空
  screen_buffer = malloc(&loc_396C0);
  memset(screen_buffer, 0, &loc_396C0);
  
  // 10. 循环加载FDOTHER.DAT索引69-73 (5个动画帧)
  for (i = 0; i < 5; ++i)
  {
    var_28 = (short *)sub_111BA(i + 69, ..., "FDOTHER.DAT", var_28, i + 69);
    int offset = 147 * i;
    sub_4E98D(var_28, 0, offset, screen_buffer, 320, -1);
  }
  
  // 11. 刷新屏幕
  sub_4E381();
  
  // 12. 重新分配地图单元缓冲区
  if (n8_1)
    free(n8_1);
  n8_1 = malloc(160);
  
  // === 启动动画序列 ===
  
  // 13. 向下滚动动画 (从y=535到y=0)
  for (int y = 535; ; --y)
  {
    if (y < 0)
    {
      // 滚动完成，进入菜单选择
      goto MENU_SELECTION;
    }
    
    // 渲染当前帧
    sub_11EB0(655360, 320, screen_buffer + 320 * y, 320, 320, 200);
    
    if (y == 535)
      sub_1F525();  // 首次刷新
    
    // 特殊帧处理
    if (y == 25)
    {
      sub_1F81E(0, 15, 0);  // 设置调色板
      // 渲染当前帧
      sub_11EB0(655360, 320, screen_buffer + 320 * y, 320, 320, 200);
      FDOTHER_DAT = (int)sub_111BA(..., "FDOTHER.DAT", FDOTHER_DAT, 101);
      sub_1F525();
    }
    
    switch (y)
    {
      case 450:
        sub_1F73F(100, 99, screen_buffer, 450);
        break;
      case 330:
        sub_1F882();
        sub_1F81E(4, 90, 99);
        sub_1F81E(5, 50, 0);
        break;
      case 210:
        sub_1F882();
        sub_1F81E(6, 90, 99);
        sub_1F81E(7, 50, 0);
        break;
      case 110:
        sub_1F882();
        sub_1F81E(8, 90, 99);
        break;
      case 10:
        sub_1F73F(75, 76, screen_buffer, 10);
        break;
    }
    
    // 检查是否到达关键帧
    if (y == dst_[var_14])
    {
      var_20 = 0;
      sub_25A96((int)var_24, 0, 1);
      FDOTHER_DAT = (int)sub_111BA(..., "FDOTHER.DAT", FDOTHER_DAT, 102);
      sub_11D40(0, 255, 0);
      ++var_14;
    }
    
    if (var_20 == 11)
    {
      FDOTHER_DAT = (int)sub_111BA(..., "FDOTHER.DAT", FDOTHER_DAT, 101);
      sub_11D40(0, 255, 0);
    }
    ++var_20;
    
    delay(30);
    if (!y)
      delay(1000);
    
    // 检查是否跳过动画
    if (sub_10620())
      goto MENU_SELECTION;
  }

MENU_SELECTION:
  // 14. 加载菜单资源
  for (int k = 40; k >= 0; --k)
  {
    sub_2DF01(0, 255, k, 0x3F, 0, 0);
    delay(8);
  }
  delay(100);
  sub_4E381();
  free(screen_buffer);
  free(var_28);
  
  // 15. 加载菜单选项资源
  var_24 = sub_111BA(..., "FDOTHER.DAT", var_24, 7);
  FDOTHER_DAT = (int)sub_111BA(..., "FDOTHER.DAT", FDOTHER_DAT, 8);
  memset(655360, 0, 64000);
  sub_11D40(0, 255, 0);
  sub_20421(1, 15, 1);
  sub_25B45((int)var_18, 3, 1);
  sub_11DF2(0, 255, 64);
  sub_16886(655360, 320, (int)var_24, 0);
  
  // 淡入效果
  for (int m = 0; m <= 40; ++m)
  {
    sub_2DF01(0, 255, m, 0x38, 0x3C, 0x3F);
    delay(8);
  }
  sub_4E381();
  
  // 16. 检查存档文件
  int file_handle = fopen("FD2.SAV", "rb");
  if (file_handle)
  {
    int *save_data = malloc(22987);
    sub_373CA((BYTE *)save_data, 1, 22987, file_handle);
    fclose(file_handle);
    sub_4DF28((char *)save_data, 22987);
    
    // 校验存档
    if (sub_4DF09((BYTE *)save_data, 22987) == *(int *)(save_data + 22983))
    {
      var_1C = 2;  // 有有效存档
      if (*(BYTE *)(save_data + 12485) != 255)
        var_1C = 3;  // 存档有游戏进度
    }
    free(save_data);
  }
  
  // 17. 显示菜单并等待用户选择
  sub_1FF79((int)var_24, 0, var_1C);
  while (!var_2C)
  {
    sub_1FF79((int)var_24, var_2C, var_1C);
    HIBYTE(n3) = 16;
    int386(22, &n3, &n3);  // 读取键盘输入
    
    // 上箭头 (72) - 向上移动选择
    if (HIBYTE(n3) == 72)
    {
      sub_25A96((int)var_24, 2, 1);
      if (var_2C)
        --var_2C;
      else
        var_2C = var_1C - 1;
    }
    // 下箭头 (80) - 向下移动选择
    else if (HIBYTE(n3) == 80)
    {
      sub_25A96((int)var_24, 2, 1);
      if (var_2C == var_1C - 1)
        var_2C ^= var_1C - 1;
      else
        ++var_2C;
    }
    // 回车/空格/Insert/Delete - 确认选择
    else if ((BYTE)n3 == 13 || (BYTE)n3 == 32 || 
             HIBYTE(n3) == 224 || HIBYTE(n3) == 82)
    {
      sub_25A96((int)var_24, 1, 1);
      var_2C = 1;
    }
  }
  
  // 18. 闪烁效果
  for (int n = 0; n < 4; ++n)
  {
    sub_1FF79((int)var_24, -1, var_1C);
    delay(80);
    sub_1FF79((int)var_24, var_2C, var_1C);
    delay(80);
  }
  
  // 19. 清理并返回
  sub_1F882();
  memset(655360, 0, 64000);
  free(var_24);
  sub_25A96((int)var_24, -1, 1);
  free(var_18);
  return var_1C;  // 返回选择结果
}
```

---

## 六、sub_373CA - 文件读取函数 (地址: 0x373CA)

### 6.1 功能描述
这是类似标准C库fread函数的文件读取实现，支持带缓冲区的读取和文本模式下的行结束符处理。

### 6.2 C代码实现

```c
/**
 * 函数名: sub_373CA
 * 地址: 0x373CA
 * 功能: 从文件流读取数据 (类似fread)
 * 
 * 参数说明:
 *   @param a1 (_BYTE *) - 目标缓冲区指针
 *   @param a2 (unsigned int) - 单个元素大小 (字节)
 *   @param a3 (int) - 元素个数
 *   @param a4 (int) - FILE结构体指针
 * 
 * 返回值:
 *   @return (int) - 成功读取的元素个数
 * 
 * 说明:
 *   - 支持文本模式和二进制模式
 *   - 文本模式下处理CR/LF转换
 *   - 处理EOF标记 (0x1A)
 *   - 内部使用缓冲区优化读取性能
 */
int __cdecl sub_373CA(_BYTE *a1, unsigned int a2, int a3, int a4)
{
  unsigned int total_bytes;  // 总字节数 = a2 * a3
  unsigned int bytes_read;   // 已读取字节数
  unsigned int buffer_size;  // 缓冲区中的剩余字节数
  
  // 检查文件是否为读取模式 (bit0 of flag byte)
  if ((*(_BYTE *)(a4 + 12) & 1) == 0)
  {
    // 不是读取模式，设置错误
    *(_DWORD *)sub_3DB46() = 4;
    *(_BYTE *)(a4 + 12) |= 0x20;
    return 0;
  }
  
  // 计算总读取字节数
  total_bytes = a2 * a3;
  if (!total_bytes)
    return 0;
  
  // 如果缓冲区未初始化，则分配
  if (!*(_DWORD *)(a4 + 8))
    _ioalloc(a4);
  
  bytes_read = 0;
  
  // 检查是否为二进制模式 (bit6 of flag byte)
  if ((*(_BYTE *)(a4 + 12) & 0x40) != 0)
  {
    // 二进制模式读取
    unsigned int remaining = total_bytes;
    
    while (1)
    {
      // 如果缓冲区有数据
      if (*(_DWORD *)(a4 + 4))
      {
        unsigned int copy_size = *(_DWORD *)(a4 + 4);
        if (copy_size > remaining)
          copy_size = remaining;
        
        // 从缓冲区复制数据
        memcpy(a1, *(_DWORD *)a4, copy_size);
        *(_DWORD *)a4 += copy_size;
        bytes_read += copy_size;
        *(_DWORD *)(a4 + 4) -= copy_size;
        remaining -= copy_size;
        a1 += copy_size;
        
        // 检查是否需要从文件填充缓冲区
        if (*(_DWORD *)(a4 + 20) + *(_DWORD *)(a4 + 8) != *(_DWORD *)a4)
          break;
      }
      
      // 如果已读取所有数据
      if (!remaining)
        break;
      
      // 直接从文件读取
      unsigned int read_size = remaining;
      if ((*(_BYTE *)(a4 + 13) & 4) == 0 && remaining > 0x200)
        read_size = remaining & 0xFE00;  // 对齐到512字节边界
      
      int result = _qread(*(_DWORD *)(a4 + 16), a1, read_size);
      if (result == -1)
      {
        // 读取错误
        *(_BYTE *)(a4 + 12) |= 0x20;
        return bytes_read / a2;
      }
      if (!result)
        break;  // EOF
      
      a1 += result;
      bytes_read += result;
      remaining -= result;
      
      if (result != read_size)
        return bytes_read / a2;
    }
  }
  else
  {
    // 文本模式读取
    bool at_buffer_end = true;
    _BYTE *dest = a1;
    
    while (1)
    {
      // 如果缓冲区为空，填充缓冲区
      if (!*(_DWORD *)(a4 + 4))
      {
        if (!at_buffer_end || !_fill_buffer(a4))
          return bytes_read / a2;
        if (*(_DWORD *)(a4 + 20) + *(_DWORD *)(a4 + 8) != *(_DWORD *)a4)
          at_buffer_end = false;
      }
      
      // 从缓冲区读取一个字节
      --*(_DWORD *)(a4 + 4);
      unsigned char *src = (unsigned char *)(*(_DWORD *)a4)++;
      int ch = *src;
      
      // 处理CR/LF转换
      if (ch == 13)  // CR
      {
        if (!*(_DWORD *)(a4 + 4))
        {
          if (!at_buffer_end || !_fill_buffer(a4))
            return bytes_read / a2;
          if (*(_DWORD *)(a4 + 20) + *(_DWORD *)(a4 + 8) != *(_DWORD *)a4)
            at_buffer_end = false;
        }
        --*(_DWORD *)(a4 + 4);
        unsigned char *src2 = (unsigned char *)(*(_DWORD *)a4)++;
        ch = *src2;
      }
      
      // 检查EOF标记
      if (ch == 26)  // 0x1A (DOS EOF)
        break;
      
      // 存储字符
      *dest = ch;
      
      // 检查是否读取完成
      if ((*(_BYTE *)(a4 + 12) & 0x30) == 0)
      {
        ++dest;
        ++bytes_read;
        if (dest != &a1[total_bytes])
          continue;
      }
      return bytes_read / a2;
    }
    
    // 遇到EOF，设置EOF标志
    *(_BYTE *)(a4 + 12) |= 0x10;
  }
  
  return bytes_read / a2;
}
```

### 6.3 FILE结构体分析

根据代码推断，FILE结构体可能如下：

```c
struct FILE {
  unsigned char *buffer;       // +0: 缓冲区指针
  unsigned int buffer_remaining; // +4: 缓冲区剩余字节数
  void *buffer_base;           // +8: 缓冲区基地址
  unsigned char flags;         // +12: 标志位
                               //   bit0: 读取模式
                               //   bit4,bit5: 未知
                               //   bit6: 二进制模式
                               //   bit2: 未知
  unsigned char flags2;        // +13: 标志位2
  int file_handle;             // +16: 文件句柄
  unsigned int buffer_size;    // +20: 缓冲区大小
};
```

---

## 七、sub_2B996 - DAT数据处理函数 (地址: 0x2B996)

### 7.1 功能描述
此函数处理已加载的DAT数据，特别是FDOTHER.DAT的内容，根据类型进行不同的图形处理操作。

### 7.2 C代码实现

```c
/**
 * 函数名: sub_2B996
 * 地址: 0x2B996
 * 功能: 处理DAT数据并执行图形操作
 * 
 * 参数说明:
 *   @param a1-a8 - 各种参数 (用途待分析)
 *   @param a9 (unsigned __int8) - 处理类型
 *      3 - 初始化dword_53F76数组
 *      4 - 处理类型4的图形操作
 *      5 - 处理类型5的图形操作
 */
void __fastcall sub_2B996(__int32 a1, int a2, int a3, int a4, 
                           int a5, int a6, int a7, int a8, unsigned __int8 a9)
{
  int dst_[7];       // 本地数组1
  int dst__1[7];     // 本地数组2
  int v21;           // 标志位
  int v22;           // 参数保存

  // 初始化栈帧 (108字节)
  sub_3702F(a1, a2, a3, a4, 108);
  v22 = a3;
  v21 = 0;
  
  // 复制数据到本地数组
  qmemcpy(dst_, &src__38, sizeof(dst_));
  qmemcpy(dst__1, &src__39, sizeof(dst__1));
  
  // 根据条件调整数组值
  int n8 = n8_1;
  if (!*(_BYTE *)(n8_1 + 80 * a5 + 6))
  {
    for (int n7 = 0; n7 < 7; ++n7)
      dst_[n7] += 148;
  }
  
  // 根据类型进行处理
  switch (a9)
  {
    case 3:
      // 类型3: 初始化dword_53F76数组
      for (int n8_1 = 0; n8_1 < 8; ++n8_1)
        dword_53F76[n8_1] = -2 * n8_1;
      // 跳转到后续处理
      goto LABEL_28;
      
    case 4:
      // 类型4: 处理图形显示
      for (int n7_1 = 0; n7_1 < 7; ++n7_1)
      {
        // 检查条件并调用显示函数
        if (dword_53F76[n7_1] == 3)
          sub_25A96(a9, n8, n7_1, 0, dword_54153, 1, 1);
        
        int v12 = 4 * n7_1;
        if ((unsigned int)dword_53F76[n7_1] < 0x10)
        {
          n8 = *((unsigned char *)&off_524EE + n7_1);
          if (n8 == 1)
          {
            int v9 = dst_[n7_1] + a7;
            n8 = v9 + a8 * dst__1[n7_1];
            // 调用图形处理函数
            v12 = sub_2EB9F(a6, dword_53F76[n7_1], n8, a8, -1);
          }
        }
      }
      break;
      
    case 5:
      // 类型5: 处理图形显示并递增计数器
      for (int n7_2 = 0; n7_2 < 7; ++n7_2)
      {
        if ((unsigned int)dword_53F76[n7_2] < 0x10 && 
            !*((char *)&off_524EE + n7_2))
        {
          // 调用图形处理函数
          sub_2EB9F(a6, dword_53F76[n7_2], 
                    dst_[n7_2] + a7 + a8 * dst__1[n7_2], a8, -1);
        }
        
        // 递增计数器，达到9时设置标志
        if (++dword_53F76[n7_2] == 9)
          v21 = 1;
      }
      
LABEL_28:
      // 跳转到后续处理
      goto loc_2C93D;
  }
  
  // 继续处理
  goto loc_2C93B;
}
```

### 7.3 关键全局变量

| 变量名 | 说明 |
|--------|------|
| dword_53F76 | 图形处理计数器数组 (8项) |
| dword_54153 | 图形处理参数 |
| off_524EE | 图形处理配置表 |

---

## 八、其他辅助函数

### 8.1 sub_11D40 - 调色板设置函数

```c
// 功能: 设置VGA调色板
// 参数:
//   start_color: 起始颜色索引
//   end_color: 结束颜色索引
//   palette_index: 调色板索引
void __cdecl sub_11D40(int start_color, int end_color, int palette_index);
```

### 8.2 sub_4E98D - 图像显示函数

```c
// 功能: 将图像数据渲染到屏幕缓冲区
// 参数:
//   data: 图像数据指针
//   x, y: 目标坐标
//   screen_buffer: 屏幕缓冲区指针
//   width: 图像宽度
//   flag: 标志位
void __cdecl sub_4E98D(void *data, int x, int y, 
                        void *screen_buffer, int width, int flag);
```

### 8.3 sub_11EB0 - 图像块复制函数

```c
// 功能: 将图像块复制到屏幕缓冲区
// 参数:
//   dest_buffer: 目标缓冲区
//   dest_pitch: 目标行距
//   src_buffer: 源缓冲区
//   src_pitch: 源行距
//   width, height: 宽高
void __cdecl sub_11EB0(void *dest_buffer, int dest_pitch,
                        void *src_buffer, int src_pitch,
                        int width, int height);
```

### 8.4 sub_15F0E - 图像渲染函数

```c
// 功能: 渲染图像到屏幕
// 参数:
//   data: 图像数据
//   buffer: 屏幕缓冲区
//   pitch: 行距
//   x, y: 坐标
//   index: 图像索引
int __cdecl sub_15F0E(void *data, void *buffer, int pitch,
                       int x, int y, int index);
```

### 8.5 sub_187D6 - 调色板动画函数

```c
// 功能: 执行调色板淡入/淡出效果
// 参数:
//   color_value: 颜色值
//   pitch: 行距
//   state: 状态值
//   start, end: 颜色范围
int __cdecl sub_187D6(int color_value, int pitch, int state,
                       int start, int end);
```

### 8.6 sub_25A96 - 场景切换函数

```c
// 功能: 切换游戏场景
// 参数:
//   data: 场景数据
//   type: 切换类型
//   flag: 标志位
int __cdecl sub_25A96(int data, int type, int flag);
```

### 8.7 sub_4DF28 - 存档解密函数

```c
// 功能: 解密/处理存档数据
// 参数:
//   buffer: 存档数据缓冲区
//   size: 数据大小
void __cdecl sub_4DF28(char *buffer, int size);
```

### 8.8 sub_4DF09 - 存档校验函数

```c
// 功能: 计算存档校验码
// 参数:
//   buffer: 存档数据缓冲区
//   size: 数据大小
// 返回值: 校验码
int __cdecl sub_4DF09(unsigned char *buffer, int size);
```

### 8.9 sub_29BCB - 存档数据处理函数

```c
// 功能: 处理存档数据块
// 参数:
//   buffer: 存档数据
//   index: 数据块索引
// 返回值: 处理结果 (-1表示错误)
int __cdecl sub_29BCB(int buffer, int index);
```

---

## 九、调用关系总结

```
main (0x25BF4)
├── sub_3702F - 栈帧初始化
├── sub_3AA72 - 未知初始化
├── sub_111BA - 加载DAT文件 (多次调用)
│   ├── fopen - 打开文件
│   ├── fseek - 定位文件
│   ├── sub_373CA - 读取数据
│   └── fclose - 关闭文件
├── sub_25EBB - 游戏状态加载
│   ├── sub_1F894 - 启动画面
│   │   ├── sub_111BA - 加载DAT文件 (索引77,76,74,99,101,69-73,7,8,102)
│   │   ├── sub_4E98D - 显示图像
│   │   ├── sub_11EB0 - 图像块复制
│   │   ├── sub_11D40 - 设置调色板
│   │   ├── sub_1FF79 - 显示菜单
│   │   └── fopen("FD2.SAV") - 检查存档
│   ├── sub_10010 - 存档加载
│   │   ├── fopen("FD2.SAV") - 打开存档
│   │   ├── sub_373CA - 读取存档
│   │   ├── sub_4DF28 - 解密存档
│   │   ├── sub_4DF09 - 校验存档
│   │   ├── sub_111BA - 加载DAT文件
│   │   ├── fopen("FDICON.B24") - 打开图标文件
│   │   └── sub_11019 - 加载图标 (循环)
│   └── sub_29BCB - 处理存档数据
└── sub_117E7 - 输入处理
    └── sub_11019 - 加载图标
    └── sub_17AED - 处理输入
    └── sub_25A96 - 场景切换

sub_2B996 - DAT数据处理
└── sub_25A96 - 场景切换
└── sub_2EB9F - 图形处理
```

---

## 十、文件格式总结

### 10.1 DAT文件格式 (通用)

```
偏移0-5:     文件头 (6字节，具体含义未知)
偏移6开始:   索引表
            - 每个索引项4字节 (32位有符号整数)
            - 索引N表示数据块N的起始文件偏移
索引表之后:  数据块
            - 数据块N的大小 = 索引[N+1] - 索引[N]
            - 数据块N的起始位置 = 索引[N]
```

### 10.2 FD2.SAV存档文件格式

```
总大小: 22987字节 (0x59CB)

[0x0000 - 0x08A2]   地图数据 (2211字节)
[0x08A3 - 0x12A2]   地图单元数据 (2560字节)  
[0x12A3 - 0x30A2]   其他游戏数据
[0x30A3 - 0x30C2]   配置数据 (32字节)
[0x30C3]            未知字节 (n999)
[0x30C4]            地图索引 (n17)
[0x30C5 - 0x30CA]   游戏状态字节 (6字节)
[0x30CB - 0x59C6]   其他数据
[0x59C7 - 0x59CA]   校验码 (4字节)
```

### 10.3 FDICON.B24图标文件格式

```
偏移0-5:     文件头 (6字节)
偏移6开始:   索引表
            - 每个图标13个索引值 (每个4字节)
            - 每个图标占用48字节
索引表之后:  图标数据
            - 图标数据格式未知 (可能是位图)
```

---

## 十一、关键数据结构

### 11.1 地图单元结构 (80字节/单元)

```c
struct MapUnit {
  unsigned char field_0;    // 偏移0: 未知
  unsigned char field_1;    // 偏移1: 未知
  unsigned char icon_index; // 偏移2: 图标索引 (由sub_11019返回)
  // ... 填充 ...
  unsigned char field_5;    // 偏移5: 状态标志 (bit7, bit2, bit0有特殊含义)
  unsigned char field_6;    // 偏移6: 类型 (2表示某种特殊类型)
  unsigned char field_7;    // 偏移7: 原始图标索引 (用于从FDICON.B24加载)
  // ... 填充 ...
  unsigned char field_31;   // 偏移31: 类型 (10表示某种特殊类型)
  unsigned char field_38;   // 偏移38: 未知标志
};
```

### 11.2 地图信息结构 (从FDFIELD_DAT__1)

```c
struct MapInfo {
  unsigned char field_0;    // 偏移0: 形状相关值
  unsigned char field_1;    // 偏移1: n6值
  unsigned char field_2;    // 偏移2: dword_53BE3值
};
```

---

## 十二、全局变量汇总

### 12.1 DAT文件数据指针

| 变量名 | 类型 | 说明 |
|--------|------|------|
| FDOTHER_DAT | int | FDOTHER.DAT索引0 |
| FDOTHER_DAT__2 | int | FDOTHER.DAT索引31 |
| FDOTHER_DAT__3 | int | FDOTHER.DAT索引1 |
| FDOTHER_DAT__4 | int | FDOTHER.DAT索引2 |
| FDOTHER_DAT__5 | int | FDOTHER.DAT索引3 |
| FDOTHER_DAT__6 | int | FDOTHER.DAT索引4 |
| FDOTHER_DAT__7 | int | FDOTHER.DAT索引5 |
| FDOTHER_DAT__8 | int | FDOTHER.DAT索引6 |
| FDOTHER_DAT__11 | int | FDOTHER.DAT索引13 |
| FDTXT_DAT | int | FDTXT.DAT数据指针 |
| FDTXT_DAT__0 | int | FDTXT.DAT数据指针 |
| FDFIELD_DAT | int | FDFIELD.DAT数据指针 |
| FDFIELD_DAT__0 | int | FDFIELD.DAT地图数据 |
| FDFIELD_DAT__1 | int | FDFIELD.DAT地图信息 |
| FDSHAP_DAT | int | FDSHAP.DAT数据指针 |
| FDSHAP_DAT__0 | int | FDSHAP.DAT数据指针 |

### 12.2 游戏状态变量

| 变量名 | 类型 | 说明 |
|--------|------|------|
| dword_53BFF | int | 最后加载的数据块大小 |
| dword_53AC1 | int | 地图宽度 |
| n40 | int | 地图高度 |
| n6_0 | int | 地图单元数量 |
| n8_1 | int | 地图单元数据指针 (80字节/单元) |
| n8_0 | int | 配置数据指针 (32字节) |
| n17 | int | 当前地图索引 |
| n16_1 | int | 游戏状态值 |
| n999 | int | 游戏状态值 |
| n999_0 | int | 游戏状态值 |
| n127 | int | 游戏状态值 |
| n10 | int | 游戏状态值 |
| n2 | int | 游戏状态值 |
| n6 | int | 游戏状态值 |
| n6_5 | int | 游戏状态值 |
| dword_53A61 | int | 图标数据缓冲区指针 |
| dword_53BDF | int | 已缓存图标数量 |
| dword_53BE3 | int | 地图相关值 |
| byte_53AF9 | char | 游戏状态字节 |
| byte_51AAB | char | 游戏状态字节 |
| byte_51E62 | char | 游戏状态字节 |
| byte_51AAC | char | 场景标志 (0=切换中, 1=正常) |
| dword_53AE9 | int | 地图单元遍历索引 |
| qword_53AA9 | __int64 | 游戏状态值 |
| qword_53AB1 | __int64 | 游戏状态值 |
| dword_53F76 | int[8] | 图形处理计数器数组 |
| dword_54153 | int | 图形处理参数 |
| off_524EE | 指针 | 图形处理配置表 |
| byte_51E63 | char[] | 场景配置表 |
| buf__3 | int | 图标数据缓冲区当前写入位置 |
| dword_53B17 | int[] | 图标索引缓存表 |

### 12.3 函数表

| 变量名 | 说明 |
|--------|------|
| funcs_25E3A | 场景初始化函数表 |
| funcs_25E23 | 场景处理函数表 |
| funcs_1197B | 场景动作函数表 |
| funcs_1199C | 场景特殊处理函数表 |

