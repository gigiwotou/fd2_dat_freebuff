# FD2 Continue战场存档恢复与战场循环逻辑

> 来源: IDA Pro MCP 逆向分析 FD2.EXE
> 日期: 2026-05-02

---

## 一、选项2 Continue 执行流程

### 1.1 sub_25EBB 中的处理

当菜单返回值 != 0 且 != 1 时 (Continue 选项)：

**地址**: 0x26124 - 0x26151

```asm
26124  push    0                          ; a7 (loops)
26126  push    0FFFFFFFFh                 ; a6 (index = -1, stop)
26128  call    sub_25977                  ; 停止当前音乐
2612d  add     esp, 8
26130  call    sub_10010                  ; 加载战场存档
26135  push    0                          ; a7 (loops)
26137  mov     eax, n17                   ; 场景索引
2613c  movzx   eax, byte_51E63[eax]       ; 音乐索引
26143  push    eax
26144  call    sub_25977                  ; 播放场景音乐
26149  add     esp, 8
2614c  xor     eax, eax                   ; 返回 0
2614e  pop     edi
2614f  pop     esi
26150  pop     ebx
26151  retn
```

**逻辑**:
1. 停止当前音乐 (`sub_25977(-1, 0)`)
2. 调用 `sub_10010` 加载战场存档
3. 播放场景音乐 (`sub_25977(byte_51E63[n17], 0)`)
4. 返回 0，进入 main 主循环

---

## 二、sub_10010 战场存档加载函数

### 2.1 函数签名

```c
void sub_10010(
    __int32 a1@<eax>,
    int a2@<edx>,
    int a3@<ecx>,
    int n99@<ebx>,
    unsigned __int8 *a5@<edi>
);
```

### 2.2 存档校验

```c
int v5 = malloc(22987);
if (v5) {
    int _rb_ = fopen("FD2.SAV", "rb");
    sub_373CA((char *)v5, 1, 22987, _rb_);  // 读取存档
    fclose(_rb_);
    sub_4DF28((char *)v5, 22987);           // 解密
    
    // 校验存档完整性
    if (sub_4DF09((unsigned __int8 *)v5, 22987) != *(DWORD *)(v5 + 22983)) {
        sub_1956B(75);                      // 显示错误画面
        sub_15F84(a5, FDTXT_DAT, 436, 655360, 320, 205, 76, 74, 19, 1);
        sub_16559(0);
        sub_16C57(0);
        sub_196CB();
    }
}
```

**关键数据位置**:
| 偏移 | 大小 | 内容 |
|------|------|------|
| 0-2210 | 2211 | 营地地图数据 |
| 2211-4770 | 2560 | 临时地图数据 |
| 4771-4770+80*n6_0 | 80*n6_0 | 角色数据 |
| 12451-12482 | 32 | n8_0 数据 |
| 12483 | 1 | n999 |
| 12484 | 1 | n6_0 (角色数量) |
| 12485 | 1 | n17 (场景索引) |
| 12486 | 1 | qword_53AA9 低字节 |
| 12487 | 1 | qword_53AA9 高字节 |
| 12488 | 1 | qword_53AB1 低字节 |
| 12489 | 1 | qword_53AB1 高字节 |
| 12490 | 1 | n10 |
| 12491 | 1 | n2 |
| 12492 | 1 | n16_1 |
| 12493-12496 | 4 | n999_0 |
| 12497 | 1 | byte_53AF9 |
| 12498 | 1 | byte_51AAB |
| 12499 | 1 | n127 |
| 12500 | 1 | byte_51E62 |
| 22983-22986 | 4 | 校验和 |

### 2.3 数据加载

```c
// 清屏
sub_1F882();

// 复制临时地图数据
memmove(dword_53BF7, v5 + 2211, 2560);

// 加载 FDOTHER#0
FDOTHER_DAT = sub_111BA(..., "FDOTHER.DAT", 0);

// 恢复场景索引
n17 = *(unsigned __int8 *)(v5 + 12485);

// 加载 FDFIELD.DAT[3*n17+2]
FDFIELD_DAT = sub_111BA(..., "FDFIELD.DAT", 3 * n17 + 2);

// 释放旧地图数据，分配新空间
if (FDFIELD_DAT__1)
    free(FDFIELD_DAT__1);
FDFIELD_DAT__1 = malloc(2211);
memmove(FDFIELD_DAT__1, v5, 2211);

// 处理地图数据
sub_10652(FDFIELD_DAT__1);

// 加载 FDTXT.DAT[n17+1]
FDTXT_DAT = sub_111BA(..., "FDTXT.DAT", n17 + 1);

// 加载 FDFIELD.DAT[3*n17]
FDFIELD_DAT__0 = sub_111BA(..., "FDFIELD.DAT", 3 * n17);

// 获取地图尺寸
dword_53AC1 = *(short *)FDFIELD_DAT__0;      // 地图宽度
n40 = *(short *)(FDFIELD_DAT__0 + 2);        // 地图高度

// 计算形状索引
int v10 = 2 * *(unsigned __int8 *)FDFIELD_DAT__1;

// 加载 FDSHAP.DAT[v10]
FDSHAP_DAT = sub_111BA(..., "FDSHAP.DAT", v10);

// 加载 FDSHAP.DAT[v10+1]
FDSHAP_DAT__0 = sub_111BA(..., "FDSHAP.DAT", v10 + 1);

// 处理地图
sub_4DF4C(FDFIELD_DAT__0);
```

### 2.4 角色数据恢复

```c
// 恢复角色相关变量
n6 = *(unsigned __int8 *)(FDFIELD_DAT__1 + 1);       // 角色类型
dword_53BE3 = *(unsigned __int8 *)(FDFIELD_DAT__1 + 2);  // 角色数量
n6_0 = *(unsigned __int8 *)(v5 + 12484);             // 角色数量

// 分配角色数据空间
if (n8_1)
    free(n8_1);
n8_1 = malloc(7680);

// 恢复角色数据
memmove(n8_1, v5 + 4771, 80 * n6_0);   // 角色数据 (80字节/角色)
memmove(n8_0, v5 + 12451, 32);          // n8_0 数据

// 加载图标
int _rb__1 = fopen("fdicon.b24", "rb");
dword_53BDF = 0;
for (int n6 = 0; n6 < n6_0; ++n6) {
    *(char *)(80 * n6 + n8_1 + 2) = sub_11019(
        *(unsigned __int8 *)(80 * n6 + n8_1 + 7),  // 角色类型
        _rb__1
    );
}
fclose(_rb__1);
```

### 2.5 状态变量恢复

```c
// 恢复游戏状态
n999 = *(unsigned __int8 *)(v5 + 12483);
qword_53AA9 = *(unsigned __int8 *)(v5 + 12486);
qword_53AA9 |= *(unsigned __int8 *)(v5 + 12487) << 8;
qword_53AB1 = *(unsigned __int8 *)(v5 + 12488);
qword_53AB1 |= *(unsigned __int8 *)(v5 + 12489) << 8;
n10 = *(unsigned __int8 *)(v5 + 12490);
n2 = *(unsigned __int8 *)(v5 + 12491);
n16_1 = *(unsigned __int8 *)(v5 + 12492);
n999_0 = *(DWORD *)(v5 + 12493);
byte_53AF9 = *(char *)(v5 + 12497);
byte_51AAB = *(char *)(v5 + 12498);
n127 = *(char *)(v5 + 12499);
byte_51E62 = *(char *)(v5 + 12500);

// 释放临时数据
free(v5);
free(FDFIELD_DAT);
FDFIELD_DAT = 0;
```

### 2.6 过渡动画

```c
// 播放场景音乐
sub_25977(byte_51E63[n17], 0);

n6_5 = 0;
sub_12263();              // 处理地图特殊状态
sub_11CAC(1);             // 淡入效果
sub_1F525();              // 刷新屏幕

// 播放对话动画 (索引 83-91)
for (int n6_1 = 0; n6_1 < 9; ++n6_1) {
    sub_15F0E(FDOTHER_DAT__7, 655360, 320, 120, 84, n6_1 + 83);
    if (n6_1 > 6)
        sub_187D6(684651, 320, n999, 42, 3);
    delay(70);
    if (n6_1 == 8)
        delay(500);
    sub_15E71(655360, 320);
}

// 播放战斗动画 (n2=2,3,4,9)
for (int n2 = 2; n2 < 6; ++n2) {
    if (n2 == 5)
        n2 = 9;
    sub_15F0E(FDOTHER_DAT__7, n655360 + 32904, 456, 116, n2 * n2 + 84, 91);
    int v20 = 456 * (n2 * n2 + 90);
    sub_187D6(v20 + n655360 + 33071, 456, n999, 42, 3);
    int v21 = sub_11EB0(n655360 + 32904, v20, n2, a3, 656644, 320,
                        n655360 + 32904, 456, 312, 192);
    sub_17AA9(v21, v20, n2, a3, 1);
    sub_15E71(n655360 + 32904, 456);
}

sub_11CAC(0);            // 淡出效果
delay(200);

// 设置战斗状态
dword_53AE9 = 0;         // 角色索引归零
n6_5 = 1;                // 设置标志
sub_4E381();             // 刷新屏幕
```

**注意**: 函数末尾有 `JUMPOUT(0x22BBE)`，表示返回到调用者 (sub_25EBB) 继续执行。

---

## 三、main 主循环结构

### 3.1 主循环代码

**地址**: 0x25BF4

```c
while (1) {
    v11 = sub_25977(v11, a2, v7, a4, (unsigned __int8)byte_51E63[n17], 0);
    v11 = sub_25EBB(a1, a2, v7, a4, a5);
    
    if (v11 == 0) {
        // 状态 0: 主输入处理循环
        for (int i = 0; ; ++i) {
            v11 = sub_117E7(a1, n80_1, a3, a2, a5, a6);
            
            if (n2_0 == 1) {
                sub_22E5C(a1, n80_1, a3, a4, a5);
                n2_0 = 0;
            }
            else if (n2_0 == 2) {
                ((void (*)(void))funcs_25E23[n17])();
                if (!sub_26152(a1, n80_1, a3, a4, a5, a6)) {
                    ((void (*)(void))funcs_25E3A[n17])();
                    v11 = sub_25977(v11, a2, v7, a4,
                                    (unsigned __int8)byte_51E63[n17], 0);
                }
                n2_0 = 0;
            }
            
            if (v11)
                break;
        }
    }
    else if (v11 == 1) {
        // Load: 加载营地存档后进入场景
        byte_51AAC = 0;
        v16 = sub_26152(a1, n80_1, a3, a4, a5, a6);
        if (!v16) {
            ((void (*)(void))funcs_25E3A[n17])();
            sub_25977(v11, a2, v7, a4,
                      (unsigned __int8)byte_51E63[n17], 0);
        }
        byte_51AAC = 1;
    }
    // v11 == -1: 退出游戏
}
```

### 3.2 Continue 选项后的状态流

```
Continue 选项
  └── sub_25EBB 返回 0
       └── sub_10010 执行完毕
            └── main 进入 while(!i) 循环
                 └── sub_117E7() 主输入处理
                      ├── n44 == 1,44,76: 角色移动
                      ├── n44 == 57,28: 事件处理
                      ├── n44 == 59,73: 菜单系统
                      └── 战斗触发
                           ├── sub_25A96(..., 7, 1)  播放音效
                           └── while(!sub_18890(n6))  等待战斗结束
```

---

## 四、sub_117E7 主输入处理函数

### 4.1 函数签名

```c
int sub_117E7(
    int a1@<edx>,
    int n80_1@<ebx>,
    int a3@<esi>,
    __int32 a4@<eax>,
    int a5@<ecx>,
    unsigned __int8 *a6@<edi>
);
```

### 4.2 输入模式处理

```c
int n44 = sub_11AA8();  // 获取输入模式

// 模式 1, 44, 76: 角色移动
if (n44 == 1 || n44 == 44 || n44 == 76) {
    int v7 = 0;
    int v8 = dword_53AE9;
    for (int n6 = 0; n6 < n6_0; ++n6) {
        int v10 = n8_1 + 80 * v8;
        if ((*(_BYTE *)(v10 + 5) & 0x85) == 0 &&  // 可移动标志
            *(_BYTE *)(v10 + 6) == 2 &&            // 角色状态
            !v7) {
            sub_12D7B(v8);                        // 处理移动
            dword_53AE9 = v8 + 1;
            if (v8 + 1 == n6_0)
                dword_53AE9 = 0;
            v7 = 1;
        }
        if (++v8 == n6_0)
            v8 = 0;
    }
    sub_4E381();
    return 0;
}

// 模式 57, 28: 事件处理
if (n44 != 57 && n44 != 28) {
    // ... 其他模式处理
    return 0;
}

// 事件处理逻辑
if (byte_51A42)
    --byte_51A42;

int n6_2 = sub_12C0D();  // 查找可交互对象
int n6_1 = n6_2;
if (n6_2 != -1) {
    char *v16 = (char *)(n8_1 + 80 * n6_2);
    int n2 = (unsigned __int8)v16[6];
    dword_53EC8 = 0;
    
    if (v16[7] != 121) {          // 非隐藏对象
        int n10 = (unsigned __int8)v16[31];
        if (n10 != 10) {           // 非不可交互对象
            // 判断是否触发战斗
            if (n2 == 2 && (char)v16[5] >= 0 && !v16[38]) {
                sub_25A96(0, 2, n10, a5, FDOTHER_DAT__2, 7, 1);
                while (!sub_18890(n6_1))
                    ;  // 等待战斗结束
            }
            else {
                sub_17AED(n6_1, a3);  // 普通交互
            }
            
            sub_11CAC(0);           // 淡入淡出
            sub_1E292(a6, n6_1);    // 处理交互结果
            funcs_1197B[n17]();     // 调用场景处理函数
            sub_13565();            // 处理返回值
            
            if (n255 != 255)
                funcs_1199C[n255](a6);  // 调用扩展处理
            n255 = 255;
        }
    }
}

// 战斗循环等待
do {
    v14 = sub_16F55();
    v15 = v14;
} while (!v14);

if (v14 == 1)
    return 0;
return v15;
```

### 4.3 其他输入模式

```c
// 模式 34: 特殊事件
if (n44 != 34) {
    switch (n44) {
        case 59:  // ';'
        case 73:  // 'I'
            sub_2000A();
            return 0;
            
        case 60:  // '<'
        case 71:  // 'G'
            n3_1 = sub_12C0D();
            if (n3_1 != -1) {
                int v21 = 80 * n3_1 + n8_1;
                if (*(_BYTE *)(v21 + 7) != 121 &&
                    *(_BYTE *)(v21 + 31) != 10) {
                    sub_17AED(n3, a3);
                    return 0;
                }
            }
            break;
            
        case 72:  // 'H'
            sub_25A96(72, ..., FDOTHER_DAT__2, 0, 1);
            sub_11B48();
            return 0;
            
        case 80:  // 'P'
            sub_25A96(80, ..., FDOTHER_DAT__2, 0, 1);
            sub_11B9B();
            return 0;
            
        case 75:  // 'K'
            sub_25A96(75, ..., FDOTHER_DAT__2, 0, 1);
            sub_11C59();
            return 0;
            
        case 77:  // 'M'
            sub_25A96(77, ..., FDOTHER_DAT__2, 0, 1);
            sub_11BFA();
            break;
    }
}
return 0;
```

---

## 五、sub_22E5C 状态 1 处理函数

### 5.1 函数签名

```c
void sub_22E5C(__int32 a1, int a2, int a3, int a4);
```

### 5.2 执行逻辑

```c
// 停止当前音乐
sub_25977(v4, a2, a3, a4, -1, 1);

// 延迟
sub_17AA9(v5, a2, a3, a4, 1);

// 清屏
sub_1F882();

// 加载 FDOTHER#79
char *_FDOTHER_DAT_ = sub_111BA(v6, a2, a3, a4, "FDOTHER.DAT", 0, 79);

// 清屏内存
memset(_FDOTHER_DAT_, 655360, 0, 64000);

// 渲染场景帧 0
int v8 = sub_2EB9F(_FDOTHER_DAT_, 0, 655360, 320, -1);
sub_1F525(v8, a2, _FDOTHER_DAT_, a4);
sub_17AA9(v9, a2, _FDOTHER_DAT_, a4, 9);

// 渲染场景帧 1
int v10 = sub_2EB9F(_FDOTHER_DAT_, 1, 655360, 320, -1);
sub_17AA9(v10, a2, _FDOTHER_DAT_, a4, 36);
```

**注意**: 函数末尾有 `JUMPOUT(0x15E94)`，表示返回到调用者继续执行。

---

## 六、函数指针表

### 6.1 funcs_25E23 (地址 0x51DE9)

| 索引 | 函数 | 用途 |
|------|------|------|
| 0 | sub_22EF6 | 场景处理函数 |

### 6.2 funcs_25E3A (地址 0x51D71)

| 索引 | 函数 | 用途 |
|------|------|------|
| 0 | sub_3231B | 开场剧情场景 |

### 6.3 funcs_1197B (地址 0x51B19)

| 索引 | 函数 | 用途 |
|------|------|------|
| 0 | sub_205B4 | 场景事件处理 |

### 6.4 funcs_1199C (地址 0x51B91)

| 索引 | 函数 | 用途 |
|------|------|------|
| 0 | sub_34531 | 扩展处理 |
| 1 | sub_3460B | 扩展处理 |
| 2 | sub_34673 | 扩展处理 |

---

## 七、关键全局变量

### 状态控制变量

| 变量 | 类型 | 用途 |
|------|------|------|
| n2_0 | int | 外层状态 (0=输入处理, 1=过渡, 2=战斗/场景) |
| n17 | int | 场景/地图索引 |
| n6_0 | int | 角色数量 |
| n6_5 | int | 场景标志 (0=初始化, 1=运行中) |
| n44 | int | 输入处理模式 |
| n255 | int | 扩展处理函数索引 |
| byte_51AAC | char | 操作启用标志 |
| dword_53AE9 | int | 当前角色索引 |
| dword_53BF7 | int | 临时地图数据 |

### 资源指针变量

| 变量 | 类型 | 用途 |
|------|------|------|
| FDOTHER_DAT | int | FDOTHER.DAT 加载指针 |
| FDOTHER_DAT__7 | int | FDOTHER#7 指针 |
| FDFIELD_DAT | int | FDFIELD.DAT 加载指针 |
| FDFIELD_DAT__0 | int | FDFIELD.DAT 主数据指针 |
| FDFIELD_DAT__1 | int | FDFIELD.DAT 副本指针 |
| FDSHAP_DAT | int | FDSHAP.DAT 加载指针 |
| FDSHAP_DAT__0 | int | FDSHAP.DAT 主数据指针 |
| FDTXT_DAT | int | FDTXT.DAT 加载指针 |
| n8_1 | int | 角色数据指针 (7680字节) |
| n8_0 | int | 角色状态指针 (32字节) |
| dword_53BF7 | int | 临时地图数据 (2560字节) |

### 地图数据变量

| 变量 | 类型 | 用途 |
|------|------|------|
| dword_53AC1 | int | 地图宽度 |
| n40 | int | 地图高度 |

### 音频变量

| 变量 | 类型 | 用途 |
|------|------|------|
| byte_51E63[] | char[] | 每个场景对应的音乐索引 |
| n999 | int | 音乐相关变量 |

---

## 八、完整流程图

```
Continue 选项
  │
  ├─ sub_25EBB()
  │    ├── sub_25977(..., -1, 0)  停止音乐
  │    ├── sub_10010()  加载战场存档
  │    │    ├── 读取 FD2.SAV (22987字节)
  │    │    ├── sub_4DF28() 解密
  │    │    ├── sub_4DF09() 校验
  │    │    ├── 恢复地图数据 (2211字节)
  │    │    ├── 加载 FDFIELD.DAT[3*n17], FDFIELD.DAT[3*n17+2]
  │    │    ├── 加载 FDSHAP.DAT[v10], FDSHAP.DAT[v10+1]
  │    │    ├── 加载 FDTXT.DAT[n17+1]
  │    │    ├── 恢复角色数据 (80*n6_0字节)
  │    │    ├── 加载 fdicon.b24 图标
  │    │    ├── 恢复状态变量 (n999, n6_0, n17, 等)
  │    │    ├── sub_25977(byte_51E63[n17], 0) 播放音乐
  │    │    ├── sub_12263() 处理地图状态
  │    │    ├── sub_11CAC(1) 淡入
  │    │    ├── 播放对话 83-91
  │    │    ├── 播放战斗动画 (n2=2,3,4,9)
  │    │    ├── sub_11CAC(0) 淡出
  │    │    ├── delay(200)
  │    │    ├── dword_53AE9 = 0
  │    │    ├── n6_5 = 1
  │    │    └── sub_4E381() 刷新屏幕
  │    └── sub_25977(byte_51E63[n17], 0) 播放音乐
  │
  └─ main() 返回 0，进入主循环
       └── while (!i) {
            v11 = sub_117E7();
            
            if (n2_0 == 1) {
                sub_22E5C();  // 过渡/加载
                n2_0 = 0;
            }
            else if (n2_0 == 2) {
                funcs_25E23[n17]();  // 场景处理
                if (!sub_26152()) {
                    funcs_25E3A[n17]();
                    sub_25977(byte_51E63[n17], 0);
                }
                n2_0 = 0;
            }
            
            if (v11) break;
         }
```

---

## 九、sub_22EF6 场景处理函数

### 9.1 函数签名

```c
void sub_22EF6(
    unsigned __int8 *a1@<edi>,
    __int32 a2@<eax>,
    int a3@<edx>,
    int a4@<ecx>,
    int a5@<ebx>
);
```

### 9.2 执行逻辑

```c
// 显示对话文本
sub_15F84(a1, FDTXT_DAT, 9, 655360, 320, 205, 76, 74, 19, 1);

// 处理输入
sub_11506();

// 切换到场景 1
n17 = 1;
```

---

## 十、战斗触发逻辑

### 10.1 战斗触发条件

```c
if (n2 == 2 && (char)v16[5] >= 0 && !v16[38]) {
    // n2 == 2: 角色类型为 2
    // v16[5] >= 0: 角色状态标志
    // !v16[38]: 未被触发过
    
    // 播放音效
    sub_25A96(0, 2, n10, a5, FDOTHER_DAT__2, 7, 1);
    
    // 等待战斗结束
    while (!sub_18890(n6_1))
        ;
}
```

### 10.2 sub_18890 战斗函数

```c
int sub_18890(__int32 a1, int a2, int a3, int a4, int n6);
```

**功能**: 执行战斗逻辑，返回战斗结果

**参数**:
- `n6`: 角色索引

**返回值**:
- 0: 战斗继续
- 1: 战斗结束
- -1: 战斗失败

---

## 十一、总结

1. **Continue 选项逻辑**:
   - 返回值 != 0 且 != 1
   - 通过 sub_10010 加载战场存档
   - 恢复完整的战场状态
   - 进入 main 主循环

2. **main 主循环**:
   - while(1) 主循环
   - sub_25EBB() 入口点
   - 根据 v11 返回值进入不同分支
   - v11 == 0: 主输入处理循环
   - v11 == 1: 加载营地存档
   - v11 == -1: 退出游戏

3. **输入处理 (sub_117E7)**:
   - 根据 n44 模式处理不同输入
   - 角色移动 (n44=1,44,76)
   - 事件触发 (n44=57,28)
   - 菜单系统 (n44=59,73)
   - 音效处理 (n44=72,80,75,77)

4. **状态切换**:
   - n2_0 == 1: 过渡状态 (sub_22E5C)
   - n2_0 == 2: 场景状态 (funcs_25E23 + sub_26152 + funcs_25E3A)

5. **存档数据结构**:
   - 总大小: 22987 字节
   - 包含: 地图数据、角色数据、状态变量、校验和

---

## 相关文档

- [开始菜单3个选项逻辑分析](start-menu-options-analysis.md)
- [游戏循环状态机分析](game-loop-states-analysis.md)
- [开场场景逻辑分析](opening-scene-logic-analysis.md)
- IDA 反编译文件目录：`tools/export-for-ai/decompile/`
