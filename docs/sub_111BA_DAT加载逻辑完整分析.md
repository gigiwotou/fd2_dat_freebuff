# sub_111BA 函数 DAT文件加载逻辑完整分析

> 基于 IDA Pro MCP 反汇编代码 1:1 分析
> 分析日期: 2026-05-26
> 源地址: FD2.EXE 0x111BA

---

## 一、函数签名

```c
_BYTE *__fastcall sub_111BA(
    __int32 a1,           // 寄存器传递参数(上下文)
    int a2,               // 寄存器传递参数
    int a3,               // 寄存器传递参数
    int a4,               // 寄存器传递参数
    int a5,               // DAT文件名 (const char*)
    int a6,               // 旧内存指针 (用于释放，可为NULL)
    int a7                // 资源索引号 (从0开始)
);
```

**返回值**: 指向加载数据的指针，失败时程序退出

---

## 二、DAT文件格式

```
[偏移 0-5]    文件头 "LLLLLL" (0x4C4C4C4C4C4C) - 6字节，程序直接跳过
[偏移 6开始]  索引表 - 每个条目4字节（32位小端整数）
              - 索引N的值 = 数据块N在文件中的起始偏移
              - 数据块N的大小 = 索引[N+1] - 索引[N]
[索引表之后]  数据块区域
```

### 关键点
1. **没有资源数量字段** - 程序不读取资源总数
2. **索引表起始于偏移6** - 跳过6字节文件头
3. **资源大小通过差值计算** - 不需要单独存储每个资源的大小

---

## 三、完整加载流程（基于IDA汇编代码）

### 3.1 汇编代码逐行分析

```asm
; === 函数入口 - 初始化栈帧 ===
111ba  push    20h                    ; 栈帧大小32字节
111bf  call    sub_3702F              ; 初始化栈帧
111c4  push    ebx                    ; 保存寄存器
111c5  push    esi
111c6  push    edi

; === 释放旧内存 ===
111c7  mov     ebx, [esp+0Ch+arg_4]   ; ebx = 旧内存指针 (a6)
111cb  test    ebx, ebx               ; 检查是否为NULL
111cd  jz      short loc_111D8        ; 如果为NULL，跳过释放
111cf  push    ebx
111d0  call    free                   ; 释放旧内存
111d5  add     esp, 4

; === 打开DAT文件 ===
loc_111D8:
111d8  push    offset aRb_12          ; 压入"rb"模式字符串
111dd  push    [esp+10h+arg_0]        ; 压入文件名 (a5)
111e1  call    fopen                  ; 以二进制只读模式打开文件
111e6  add     esp, 8
111e9  mov     esi, eax               ; esi = 文件句柄
111eb  test    eax, eax               ; 检查文件是否打开成功
111ed  jnz     short loc_11205        ; 成功则继续

; === 文件打开失败处理 ===
111ef  push    [esp+0Ch+arg_0]        ; 压入文件名
111f3  push    offset aFileNotFoundS  ; "\n\n File not found %s!!! \n\n"
111f8  call    printf                 ; 打印错误信息
111fd  add     esp, 8
11200  jmp     loc_1005E              ; 跳转到退出

; === 分配临时缓冲区 ===
loc_11205:
11205  push    8                      ; 分配8字节
11207  call    malloc
1120c  mov     ebx, eax               ; ebx = 临时缓冲区指针
1120e  add     esp, 4

; === 计算索引表位置并定位 ===
11211  push    0                      ; SEEK_SET = 0
11213  mov     eax, [esp+10h+arg_8]   ; eax = 索引号 (a7)
11217  shl     eax, 2                 ; eax = 索引号 * 4 (每个索引4字节)
1121a  add     eax, 6                 ; eax = 索引号 * 4 + 6 (跳过6字节文件头)
1121d  push    eax                    ; 压入偏移量
1121e  push    esi                    ; 压入文件句柄
1121f  call    fseek                  ; 定位到索引表位置

; === 读取索引数据（8字节 = 2个DWORD）===
11224  add     esp, 0Ch
11227  push    esi                    ; 文件句柄
11228  push    8                      ; 读取8字节
1122a  push    1                      ; 每次读取1字节
1122c  push    ebx                    ; 目标缓冲区
1122d  call    sub_373CA              ; 读取8字节（两个32位索引值）

; === 解析索引数据 ===
11232  add     esp, 10h
11235  mov     edi, [ebx]             ; edi = 起始偏移 (索引值1)
11237  mov     eax, [ebx+4]           ; eax = 结束偏移 (索引值2)
1123a  sub     eax, edi               ; eax = 数据块大小 = 结束偏移 - 起始偏移
1123c  mov     dword_53BFF, eax       ; 保存数据块大小到全局变量

; === 释放临时缓冲区 ===
11241  push    ebx
11242  call    free                   ; 释放8字节临时缓冲区

; === 分配数据缓冲区 ===
1124a  push    dword_53BFF            ; 数据块大小
11250  call    malloc                 ; 分配数据缓冲区
11255  add     esp, 4
11258  mov     ebx, eax               ; ebx = 数据缓冲区指针
1125a  test    eax, eax               ; 检查分配是否成功
1125c  jnz     short loc_11278        ; 成功则继续

; === 内存分配失败处理 ===
1125e  push    [esp+0Ch+arg_8]        ; 索引号
11262  push    [esp+10h+arg_0]        ; 文件名
11266  push    offset aOutOfMemoryAtL ; "Out of Memory at Load %s Number:%d!!\n"
1126b  call    printf                 ; 打印错误信息

; === 定位并读取数据块 ===
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

; === 关闭文件并返回 ===
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

### 3.2 C代码实现（1:1对应汇编）

```c
_BYTE *__fastcall sub_111BA(
    __int32 a1, int a2, int a3, int a4, 
    int filename, int old_ptr, int resource_index)
{
    int file_handle;        // esi - 文件句柄
    int *temp_buffer;       // ebx - 临时8字节缓冲区
    int data_offset;        // edi - 数据块起始偏移
    _BYTE *data_buffer;     // ebx/返回值 - 数据缓冲区指针

    // 1. 初始化栈帧 (32字节)
    sub_3702F(a1, a2, a3, a4, 32);
    
    // 2. 如果之前有分配的内存，先释放
    if (old_ptr)
        free(old_ptr);
    
    // 3. 以二进制只读模式打开DAT文件
    file_handle = fopen((const char *)filename, "rb");
    if (!file_handle) {
        printf("\n\n File not found %s!!! \n\n", (const char *)filename);
        goto ERROR_EXIT;
    }
    
    // 4. 分配8字节临时缓冲区
    temp_buffer = (int *)malloc(8);
    
    // 5. 定位到索引表位置
    // 公式: offset = resource_index * 4 + 6
    // 其中6是跳过文件头"LLLLLL"
    fseek(file_handle, 4 * resource_index + 6, SEEK_SET);
    
    // 6. 读取8字节 (两个32位整数)
    // temp_buffer[0] = 当前资源块的起始偏移
    // temp_buffer[1] = 下一个资源块的起始偏移
    sub_373CA((unsigned char *)temp_buffer, 1, 8, file_handle);
    
    // 7. 解析索引数据
    data_offset = temp_buffer[0];                    // 数据块起始偏移
    dword_53BFF = temp_buffer[1] - temp_buffer[0];   // 资源大小 = 下一个偏移 - 当前偏移
    
    // 8. 释放临时缓冲区
    free(temp_buffer);
    
    // 9. 根据资源大小分配内存
    data_buffer = (_BYTE *)malloc(dword_53BFF);
    if (!data_buffer) {
        printf("Out of Memory at Load %s Number:%d!!\n", 
               (const char *)filename, resource_index);
        goto ERROR_EXIT;
    }
    
    // 10. 定位到数据块起始位置
    fseek(file_handle, data_offset, SEEK_SET);
    
    // 11. 读取整个数据块到缓冲区
    sub_373CA(data_buffer, 1, dword_53BFF, file_handle);
    
    // 12. 关闭文件
    fclose(file_handle);
    
    // 13. 返回数据缓冲区指针
    return data_buffer;

ERROR_EXIT:
    exit(1);
}
```

---

## 四、资源大小计算方法

### 4.1 核心公式

```
资源N的大小 = 索引表[N+1] - 索引表[N]
```

### 4.2 具体步骤

1. **定位索引表**: `fseek(file, 4 * N + 6, SEEK_SET)`
2. **读取2个DWORD**: 
   - `offsets[0]` = 资源N的起始偏移
   - `offsets[1]` = 资源N+1的起始偏移
3. **计算大小**: `size = offsets[1] - offsets[0]`

### 4.3 示例

以FDOTHER.DAT为例：

```
文件头 (6字节): 4C 4C 4C 4C 4C 4C ("LLLLLL")

索引表 (从偏移6开始):
  偏移 6:  0x000001A6 (422)   <- 索引0: 资源0从偏移422开始
  偏移 10: 0x000004A6 (1190)  <- 索引1: 资源1从偏移1190开始
  偏移 14: 0x00000D61 (3425)  <- 索引2: 资源2从偏移3425开始

资源0的大小 = 1190 - 422 = 768 字节 (调色板)
资源1的大小 = 3425 - 1190 = 2235 字节 (RLE图片)
```

---

## 五、关键发现

### 5.1 与原游戏1:1对照

| 项目 | 原游戏逻辑 | 说明 |
|------|------------|------|
| 文件头 | 6字节"LLLLLL" | 直接跳过，不验证 |
| 资源数量 | **不读取** | 直接访问索引表 |
| 索引表起始 | 偏移6 | `fseek(4*index + 6)` |
| 读取范围 | 只读8字节 | 当前索引和下一个索引 |
| 大小计算 | 差值法 | `next_offset - current_offset` |
| 全局变量 | `dword_53BFF` | 保存最后加载的资源大小 |

### 5.2 与原实现的差异

我们的`fd2_dat.c`当前实现存在以下问题：

```c
// ❌ 错误：读取了不存在的资源数量字段
dword resource_count;
fread(&resource_count, 4, 1, f);

// ❌ 错误：索引表起始位置错误
fseek(f, 10, SEEK_SET);  // 应该是6，不是10

// ✅ 正确：只读取需要的2个索引值
fseek(f, 4 * resource_idx + 6, SEEK_SET);
fread(offsets, 4, 2, f);  // 只读2个DWORD
size = offsets[1] - offsets[0];
```

---

## 六、调用统计

根据IDA Pro分析，`sub_111BA`在程序中被调用**134次**，涉及40个文件：

| 调用文件 | 调用次数 | 用途 |
|----------|---------|------|
| main (0x25BF4) | 8 | 初始资源加载 |
| sub_10010 (0x10010) | 6 | 存档恢复加载 |
| sub_25EBB (0x25EBB) | 2 | 游戏状态切换 |
| sub_1F894 (0x1F894) | 14 | 启动画面动画 |
| 其他函数 | 104 | 各种资源加载 |

---

## 七、DAT文件列表

| 文件名 | 大小 | 主要用途 |
|--------|------|----------|
| FDOTHER.DAT | 3.30MB | 标题、菜单、杂项图形 + 调色板 |
| FDTXT.DAT | 117KB | 文本/字体字形 |
| FDMUS.DAT | - | MIDI音乐数据 |
| FDSHAP.DAT | 3.39MB | 战斗角色精灵 + 调色板 |
| FDFIELD.DAT | 237KB | 舞台/背景字段数据 |
| BG.DAT | 610KB | 背景图像 |
| FIGANI.DAT | 14.60MB | 角色动画帧 |
| TAI.DAT | 92KB | 角色头像 |
| DATO.DAT | - | 游戏逻辑常量/数据 |
| ANI.DAT | 2.38MB | AFM动画序列 |
| FDICON.B24 | - | 图标数据(B24格式) |

---

## 八、全局变量

| 变量名 | 地址 | 类型 | 说明 |
|--------|------|------|------|
| dword_53BFF | 0x53BFF | int | 最后加载的资源大小 |

---

## 九、总结

1. **DAT文件格式**: 6字节文件头 + 索引表 + 数据块
2. **索引表**: 从偏移6开始，每项4字节
3. **资源大小**: 通过相邻索引差值计算，无需单独存储
4. **加载策略**: 只读取需要的2个索引值，不读取整个索引表
5. **内存管理**: 每次调用先释放旧内存，避免泄漏
6. **错误处理**: 文件不存在或内存不足时打印错误并退出

---

**分析工具**: IDA Pro MCP Server  
**源文件**: D:\workspace\fd2ida\FD2\FD2.EXE  
**函数地址**: 0x111BA  
**分析完成日期**: 2026-05-26
