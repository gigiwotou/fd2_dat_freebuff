# sub_111BA 调用位置伪代码汇总

## 1. main函数 (地址: 0x25BF4) - 8次调用

```c
int __cdecl main(int argc, const char **argv, const char **envp)
{
  __int32 v3;
  int v4;
  int n16;
  int n80;
  int v9;
  int v10;
  
  // ... 初始化代码 ...
  
  v9 = sub_3908B(v8);
  v10 = v9;
  dword_53EDC = v9;
  
  if (v9)
  {
    byte_53EF1 = 1;
    sub_392D0(v9, v9, n80, n16, v9);
    // ...
  }
  
  // === 第1次调用: 加载FDOTHER.DAT索引31 ===
  FDOTHER_DAT__2 = (int)sub_111BA(v9, v10, n80, n16, 
                                   (int)"FDOTHER.DAT", 
                                   FDOTHER_DAT__2, 31);
  
  // === 第2次调用: 加载FDOTHER.DAT索引1 ===
  FDOTHER_DAT__3 = (int)sub_111BA(FDOTHER_DAT__2, v10, n80, n16, 
                                   (int)"FDOTHER.DAT", 
                                   FDOTHER_DAT__3, 1);
  
  // === 第3次调用: 加载FDOTHER.DAT索引2 ===
  FDOTHER_DAT__4 = (int)sub_111BA(FDOTHER_DAT__3, v10, n80, n16, 
                                   (int)"FDOTHER.DAT", 
                                   FDOTHER_DAT__4, 2);
  
  // === 第4次调用: 加载FDOTHER.DAT索引3 ===
  FDOTHER_DAT__5 = (int)sub_111BA(FDOTHER_DAT__4, v10, n80, n16, 
                                   (int)"FDOTHER.DAT", 
                                   FDOTHER_DAT__5, 3);
  
  // === 第5次调用: 加载FDOTHER.DAT索引4 ===
  FDOTHER_DAT__6 = (int)sub_111BA(FDOTHER_DAT__5, v10, n80, n16, 
                                   (int)"FDOTHER.DAT", 
                                   FDOTHER_DAT__6, 4);
  
  // === 第6次调用: 加载FDOTHER.DAT索引5 ===
  FDOTHER_DAT__7 = (int)sub_111BA(FDOTHER_DAT__6, v10, n80, n16, 
                                   (int)"FDOTHER.DAT", 
                                   FDOTHER_DAT__7, 5);
  
  // === 第7次调用: 加载FDTXT.DAT索引0 ===
  FDTXT_DAT__0 = (int)sub_111BA(FDOTHER_DAT__7, v10, n80, n16, 
                                 (int)"FDTXT.DAT", 
                                 FDTXT_DAT__0, 0);
  
  // === 第8次调用: 加载FDOTHER.DAT索引6 ===
  FDOTHER_DAT__8 = (int)sub_111BA(FDTXT_DAT__0, v10, n80, n16, 
                                   (int)"FDOTHER.DAT", 
                                   FDOTHER_DAT__8, 6);
  
  // 继续分配内存
  n8_0 = malloc(32);
  n655360 = malloc((char *)&loc_2567F + 1);
  n8_3 = malloc(2560);
  
  // ... 主循环 ...
  while (1)
  {
    v14 = sub_25977(18, 0);
    v15 = sub_25EBB(v14);
    // ...
  }
}
```

---

## 2. sub_10010 (地址: 0x10010) - 6次调用

```c
void __usercall sub_10010(
    __int32 a1@<eax>, 
    int a2@<edx>, 
    int a3@<ecx>, 
    int n99@<ebx>, 
    unsigned __int8 *a5@<edi>)
{
  int v5;         // 存档缓冲区
  int _rb_;       // 文件句柄
  __int64 v8;
  __int64 v9;
  int v10;
  int n6;
  int n17;        // 地图索引
  
  sub_3702F(a1, a2, n99, a3, 60);
  
  // 分配22987字节存档缓冲区
  v5 = malloc(22987);
  if (v5)
  {
    // 读取FD2.SAV存档文件
    _rb_ = fopen("FD2.SAV", "rb");
    sub_373CA((_BYTE *)v5, 1u, 22987, _rb_);
    fclose(_rb_);
    
    // 解密和校验存档
    sub_4DF28((char *)v5, 22987);
    if (sub_4DF09((_BYTE *)v5, 22987) != *(_DWORD *)(v5 + 22983))
    {
      // 校验失败处理
      sub_1956B(75);
      sub_15F84(a5, FDTXT_DAT__0, 436, 696099, 320, 205, 76, 74, 19, 1);
      sub_16559(0);
      sub_16C57(0);
      sub_196CB();
    }
    
    sub_1F882();
    
    // 复制地图单元数据
    v8 = memmove(n8_3, v5 + 2211, 2560);
    
    // === 第1次调用: 加载FDOTHER.DAT索引0 ===
    FDOTHER_DAT = (int)sub_111BA(v8, SHIDWORD(v8), _rb_, a3, 
                                  (int)"FDOTHER.DAT", 
                                  FDOTHER_DAT, 0);
    
    // 获取地图索引 (偏移12485)
    n17 = *(unsigned __int8 *)(v5 + 12485);
    
    // === 第2次调用: 加载FDFIELD.DAT索引(3*n17+2) ===
    FDFIELD_DAT = (int)sub_111BA(3 * n17 + 2, n17, _rb_, a3, 
                                  (int)"FDFIELD.DAT", 
                                  FDFIELD_DAT, 3 * n17 + 2);
    
    // 分配地图数据缓冲区
    if (FDFIELD_DAT__1)
      free(FDFIELD_DAT__1);
    FDFIELD_DAT__1 = malloc(2211);
    
    if (FDFIELD_DAT__1)
    {
      v9 = memmove(FDFIELD_DAT__1, v5, 2211);
      sub_10652(v9, SHIDWORD(v9), _rb_, a3);
      
      // === 第3次调用: 加载FDTXT.DAT索引(n17+1) ===
      FDTXT_DAT = (int)sub_111BA(n17 + 1, SHIDWORD(v9), _rb_, a3, 
                                  (int)"FDTXT.DAT", 
                                  FDTXT_DAT, n17 + 1);
      
      // === 第4次调用: 加载FDFIELD.DAT索引(3*n17) ===
      FDFIELD_DAT__0 = (int)sub_111BA(3 * n17, n17, _rb_, a3, 
                                       (int)"FDFIELD.DAT", 
                                       FDFIELD_DAT__0, 3 * n17);
      
      // 解析地图尺寸
      HIDWORD(v9) = *(__int16 *)FDFIELD_DAT__0;
      dword_53AC1 = HIDWORD(v9);        // 地图宽度
      n40 = *(__int16 *)(FDFIELD_DAT__0 + 2);  // 地图高度
      
      // 计算形状索引
      v10 = 2 * *(unsigned __int8 *)FDFIELD_DAT__1;
      
      // === 第5次调用: 加载FDSHAP.DAT索引(2*byte) ===
      FDSHAP_DAT = (int)sub_111BA(FDFIELD_DAT__1, SHIDWORD(v9), v10, a3, 
                                   (int)"FDSHAP.DAT", 
                                   FDSHAP_DAT, v10);
      
      // === 第6次调用: 加载FDSHAP.DAT索引(2*byte+1) ===
      FDSHAP_DAT__0 = (int)sub_111BA(FDSHAP_DAT, SHIDWORD(v9), v10 + 1, a3, 
                                      (int)"FDSHAP.DAT", 
                                      FDSHAP_DAT__0, v10 + 1);
      
      // 处理地图数据
      sub_4DF4C((unsigned __int8 *)FDFIELD_DAT__0);
      
      // 获取地图信息
      n6 = *(unsigned __int8 *)(FDFIELD_DAT__1 + 1);
      dword_53BE3 = *(unsigned __int8 *)(FDFIELD_DAT__1 + 2);
      n6_0 = *(unsigned __int8 *)(v5 + 12484);
      
      // 分配地图单元数据
      if (n8_1)
        free(n8_1);
      n8_1 = malloc(7680);
      
      if (n8_1)
      {
        memmove(n8_1, v5 + 4771, 80 * n6_0);
        memmove(n8_0, v5 + 12451, 32);
        
        // 加载图标
        if (dword_53A61)
          free(dword_53A61);
        _rb__1 = fopen("FDICON.B24", "rb");
        dword_53BDF = 0;
        
        for (n6 = 0; n6 < n6_0; ++n6)
          *(_BYTE *)(80 * n6 + n8_1 + 2) = 
              sub_11019(*(unsigned __int8 *)(80 * n6 + n8_1 + 7), _rb__1);
        
        fclose(_rb__1);
        
        // 恢复游戏状态
        n999 = *(unsigned __int8 *)(v5 + 12483);
        LODWORD(qword_53AA9) = *(unsigned __int8 *)(v5 + 12486);
        HIDWORD(qword_53AA9) = *(unsigned __int8 *)(v5 + 12487);
        LODWORD(qword_53AB1) = *(unsigned __int8 *)(v5 + 12488);
        HIDWORD(qword_53AB1) = *(unsigned __int8 *)(v5 + 12489);
        n10 = *(unsigned __int8 *)(v5 + 12490);
        n2 = *(unsigned __int8 *)(v5 + 12491);
        n16_1 = *(unsigned __int8 *)(v5 + 12492);
        n999_0 = *(_DWORD *)(v5 + 12493);
        byte_53AF9 = *(_BYTE *)(v5 + 12497);
        byte_51AAB = *(_BYTE *)(v5 + 12498);
        n127 = *(_BYTE *)(v5 + 12499);
        byte_51E62 = *(_BYTE *)(v5 + 12500);
        
        // 清理和初始化
        free(v5);
        free(FDFIELD_DAT);
        FDFIELD_DAT = 0;
        
        sub_25977((unsigned __int8)byte_51E63[n17], ...);
        n6_5 = 0;
        sub_12263();
        sub_11CAC(1);
        sub_1F525();
        
        // 显示加载动画
        for (n6_1 = 0; n6_1 < 9; ++n6_1)
        {
          sub_15F0E(FDOTHER_DAT__7, 655360, 320, 120, 84, n6_1 + 83);
          if (n6_1 > 6)
            sub_187D6(684651, 320, n999, 42, 3);
          delay(70);
          if (n6_1 == 8)
            delay(500);
          sub_15E71(v16, 655360, 320);
        }
        
        // 继续动画
        for (n2 = 2; n2 < 6; ++n2)
        {
          if (n2 == 5)
            n2 = 9;
          sub_15F0E(FDOTHER_DAT__7, n655360 + 32904, 456, 116, 
                    n2 * n2 + 84, 91);
          // ...
        }
        
        sub_11CAC(0);
        delay(200);
        dword_53AE9 = 0;
        n6_5 = 1;
        sub_4E381();
      }
      else
      {
        // 内存不足
        n3 = 3;
        int386(16, &n3, &n3);
        printf(" Out of Memory !!!\n");
      }
    }
  }
  exit(...);
}
```

---

## 3. sub_25EBB (地址: 0x25EBB) - 2次调用

```c
bool __usercall sub_25EBB@<eax>(
    __int32 a1@<eax>, 
    int a2@<edx>, 
    int a3@<ecx>, 
    int n99@<ebx>, 
    unsigned __int8 *a5@<edi>)
{
  int v5;
  __int32 v6;
  int v7;
  int v8;
  int v9;
  unsigned __int8 *v10;
  unsigned __int8 *v11;
  int v13;
  int v14;
  bool v15;
  __int32 v18;
  
  v5 = sub_3702F(a1, a2, n99, a3, 32);
  
  // 调用启动画面函数
  sub_1F894(v5, a2, n99, a3);
  
  // 根据启动画面返回值处理
  if (!v6)
  {
    // === 情况1: 首次启动 ===
    v7 = sub_1F882();
    n17 = 0;
    
    // === 第1次调用: 加载FDOTHER.DAT索引0 ===
    FDOTHER_DAT = (int)sub_111BA(v7, a2, n99, a3, 
                                  (int)"FDOTHER.DAT", 
                                  FDOTHER_DAT, 0);
    
    n16_1 = 0;
    byte_51AAC = 0;
    
    // 调用场景初始化
    ((void (__usercall *)(unsigned __int8 *@<edi>))funcs_25E3A[n17])(a5);
    sub_25977((unsigned __int8)byte_51E63[n17], a2, n99, a3, 
              (unsigned __int8)byte_51E63[n17], 0);
    byte_51AAC = 1;
    sub_4E381();
    return 0;
  }
  
  if (v6 != 1)
  {
    // === 情况2: 其他状态 ===
    sub_25977(v6, a2, n99, a3, -1, 0);
    sub_10010(v18, a2, a3, n99, a5);
    sub_25977((unsigned __int8)byte_51E63[n17], a2, n99, a3, 
              (unsigned __int8)byte_51E63[n17], 0);
    return 0;
  }
  
  // === 情况3: 从存档恢复 ===
  
  // === 第1次调用 (在此分支): 加载FDOTHER.DAT索引13 ===
  FDOTHER_DAT__11 = (int)sub_111BA(1, a2, n99, a3, 
                                    (int)"FDOTHER.DAT", 
                                    FDOTHER_DAT__11, 13);
  
  v8 = sub_1F882();
  
  // === 第2次调用 (在此分支): 加载FDOTHER.DAT索引0 ===
  FDOTHER_DAT = (int)sub_111BA(v8, a2, n99, a3, 
                                (int)"FDOTHER.DAT", 
                                FDOTHER_DAT, 0);
  
  // 清空屏幕
  v9 = memset(n99, 655360, 0, 64000);
  sub_11D40(v9, a2, n99, a3, 0, 255, 0);
  
  // 分配存档缓冲区
  v10 = (unsigned __int8 *)malloc(22987);
  v11 = v10;
  v12 = fopen("FD2.SAV", &unk_50220);
  v13 = v12;
  
  if ((_DWORD)v12)
  {
    // 读取并解密存档
    sub_373CA(v10, 1u, 22987, v12);
    sub_4DF28((char *)v10, 22987);
    fclose(v13);
  }
  else
  {
    // 无存档，填充0xFF
    memset((int)v10, (int)v10, 255, 22987);
  }
  
  // 处理存档数据
  n4_1 = 0;
  do
  {
    sub_29BCB((int)v11, 0);
    v15 = v14;
    
    if (v14 != -1)
    {
      v16 = (int)&v11[2600 * (_DWORD)n4_1 + 12587];
      v12 = memmove(n8_3, v16, 2560);
      v10 = (unsigned __int8 *)(v16 + 2560);
      
      // 解析游戏状态
      n17 = *v10;
      n16_1 = v10[1];
      n999_0 = *(_DWORD *)(v10 + 2);
      byte_51AAB = v10[6];
      byte_53AF9 = v10[7];
      n127 = v10[8];
      byte_51E62 = v10[9];
      
      if (n17 == 255)
        v15 = 0;
    }
    
    sub_26996();
  } while (!v15);
  
  // 清理
  free(v11);
  free(FDOTHER_DAT__11);
  FDOTHER_DAT__11 = 0;
  
  if (v15)
  {
    byte_51AAC = 0;
    v15 = sub_26152();
    
    if (!v15)
    {
      ((void (__usercall *)(unsigned __int8 *@<edi>))funcs_25E3A[n17])(v11);
      sub_25977((unsigned __int8)byte_51E63[n17], ...);
    }
    byte_51AAC = 1;
  }
  
  sub_4E381();
  return v15;
}
```

---

## 4. sub_1F894 (地址: 0x1F894) - 14次调用

```c
void __fastcall sub_1F894(__int32 a1, int a2, int n99_1, int a4)
{
  int n2_2;
  __int32 v9;
  __int32 v10;
  int v11;
  __int32 v12;
  int n15;
  __int64 n15_1;
  int n5;
  __int64 n8;
  int n535;
  int n40;
  _BYTE *_FDOTHER_DAT__3;
  int n40_1;
  int _rb_;
  int v22;
  int n2_3;
  int n4;
  _DWORD dst_[15];
  int v26;
  int v27;
  __int16 *_FDOTHER_DAT__1;
  _BYTE *_FDOTHER_DAT__2;
  int n12;
  int n2_1;
  _BYTE *_FDOTHER_DAT_;
  unsigned __int8 v33;
  int n99;
  
  v7 = sub_3702F(a1, a2, n99_1, a4, 136);
  n99 = n99_1;
  n2_1 = 1;
  v27 = 0;
  n2_2 = 0;
  _FDOTHER_DAT__2 = 0;
  n12 = 12;
  v33 = 0;
  qmemcpy(dst_, &src__14, sizeof(dst_));
  
  // === 第1次调用: 加载FDOTHER.DAT索引77 ===
  _FDOTHER_DAT_ = sub_111BA(v7, a2, n99_1, 0, 
                            (int)"FDOTHER.DAT", 0, 77);
  
  // 清空屏幕
  v9 = memset(655360, 0, 64000);
  
  // === 第2次调用: 加载FDOTHER.DAT索引76 ===
  FDOTHER_DAT = (int)sub_111BA(v9, a2, n99_1, 0, 
                                (int)"FDOTHER.DAT", 
                                FDOTHER_DAT, 76);
  
  // 设置调色板
  sub_11D40(0, 255, 64);
  
  // === 第3次调用: 加载FDOTHER.DAT索引74 ===
  _FDOTHER_DAT__1 = (__int16 *)sub_111BA(v10, a2, n99_1, 0, 
                                          (int)"FDOTHER.DAT", 0, 74);
  
  // 显示图像
  sub_4E98D(_FDOTHER_DAT__1, 0, 0, 655360, 320, -1);
  sub_1F525();
  sub_17AA9(1);
  sub_17AA9(30);
  
  v11 = sub_1F882();
  
  // === 第4次调用: 加载FDOTHER.DAT索引99 ===
  FDOTHER_DAT = (int)sub_111BA(v11, a2, n99_1, 0, 
                                (int)"FDOTHER.DAT", 
                                FDOTHER_DAT, 99);
  
  memset(655360, 0, 64000);
  sub_11D40(0, 255, 0);
  sub_20421(3, 90, 1);
  
  sub_1F882();
  v12 = memset(655360, 0, 64000);
  
  // === 第5次调用: 加载FDOTHER.DAT索引101 ===
  FDOTHER_DAT = (int)sub_111BA(v12, a2, n99_1, 0, 
                                (int)"FDOTHER.DAT", 
                                FDOTHER_DAT, 101);
  
  sub_11D40(0, 255, 64);
  
  // 分配屏幕缓冲区
  n15_1 = malloc(&loc_396C0);
  n15 = n15_1;
  memset(n15_1, 0, &loc_396C0);
  
  // === 第6-10次调用: 循环加载FDOTHER.DAT索引69-73 ===
  for (n5 = 0; n5 < 5; ++n5)
  {
    _FDOTHER_DAT__1 = (__int16 *)sub_111BA(
        n5 + 69,                    // 索引: 69, 70, 71, 72, 73
        SHIDWORD(n15_1),
        n99_1,
        0,
        (int)"FDOTHER.DAT",
        (int)_FDOTHER_DAT__1,
        n5 + 69);
    
    n99_1 = 147 * n5;
    sub_4E98D(_FDOTHER_DAT__1, 0, 147 * n5, n15, 320, -1);
  }
  
  sub_4E381();
  
  // 重新分配地图单元缓冲区
  if (n8_1)
    free(n8_1);
  n8 = malloc(160);
  n8_1 = n8;
  
  // 启动动画序列 (从y=535向下滚动)
  for (n535 = 535; ; --n535)
  {
    if (n535 < 0)
    {
      // === 动画结束，进入菜单选择 ===
      goto MENU_SELECTION;
    }
    
    sub_11EB0(655360, 320, n15 + 320 * n535, 320, 320, 200);
    
    if (n535 == 535)
      sub_1F525();
    
    // 特殊帧处理
    if (n535 == 25)
    {
      sub_1F81E(0, 15, 0);
      sub_11EB0(655360, 320, n15 + 320 * n535, 320, 320, 200);
      
      // === 第11次调用: 加载FDOTHER.DAT索引101 ===
      FDOTHER_DAT = (int)sub_111BA(n8, SHIDWORD(n8), n99_1, 0, 
                                    (int)"FDOTHER.DAT", 
                                    FDOTHER_DAT, 101);
      sub_1F525();
      goto LABEL_13;
    }
    
    switch (n535)
    {
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
      case 450:
        sub_1F73F(100, 99, n15, 450);
        break;
      case 10:
        sub_1F73F(75, 76, n15, 10);
        break;
    }
    
    LODWORD(n8) = v33;
    
    // 检查是否到达关键帧
    if (n535 == dst_[v33])
    {
      n12 = 0;
      LODWORD(n8) = sub_25A96((int)_FDOTHER_DAT_, 0, 1);
      
      // === 第12次调用: 加载FDOTHER.DAT索引102 ===
      FDOTHER_DAT = (int)sub_111BA(n8, SHIDWORD(n8), n99_1, 0, 
                                    (int)"FDOTHER.DAT", 
                                    FDOTHER_DAT, 102);
      sub_11D40(0, 255, 0);
      ++v33;
    }
    
    if (n12 == 11)
    {
      // === 第13次调用: 加载FDOTHER.DAT索引101 ===
      FDOTHER_DAT = (int)sub_111BA(n8, SHIDWORD(n8), n99_1, 0, 
                                    (int)"FDOTHER.DAT", 
                                    FDOTHER_DAT, 101);
      sub_11D40(0, 255, 0);
    }
    
    ++n12;
    delay(30);
    
    if (!n535)
      delay(1000);
    
    if (sub_10620())
      goto MENU_SELECTION;
  }

LABEL_13:
  sub_1F81E(0, 15, 0);
  LODWORD(n8) = sub_11EB0(655360, 320, n15 + 320 * n535, 320, 320, 200);
  
  // === 第14次调用: 加载FDOTHER.DAT索引101 ===
  FDOTHER_DAT = (int)sub_111BA(n8, SHIDWORD(n8), n99_1, 0, 
                                (int)"FDOTHER.DAT", 
                                FDOTHER_DAT, 101);
  sub_1F525();
  goto LABEL_24;

MENU_SELECTION:
  // 淡出效果
  for (n40 = 40; n40 >= 0; --n40)
  {
    sub_2DF01(0, 255, n40, 0x3Fu, 0, 0);
    delay(8);
  }
  delay(100);
  sub_4E381();
  free(n15);
  LODWORD(n8) = free(_FDOTHER_DAT__1);
  
  // === 第11次调用 (实际是第15次): 加载FDOTHER.DAT索引7 ===
  _FDOTHER_DAT__3 = sub_111BA(n8, SHIDWORD(n8), n99_1, 0, 
                               (int)"FDOTHER.DAT", 
                               (int)_FDOTHER_DAT__2, 7);
  _FDOTHER_DAT__2 = _FDOTHER_DAT__3;
  
  // === 第12次调用 (实际是第16次): 加载FDOTHER.DAT索引8 ===
  FDOTHER_DAT = (int)sub_111BA(
      (__int32)_FDOTHER_DAT__3,
      SHIDWORD(n8),
      (int)_FDOTHER_DAT__3,
      0,
      (int)"FDOTHER.DAT",
      FDOTHER_DAT,
      8);
  
  memset(655360, 0, 64000);
  sub_11D40(0, 255, 0);
  sub_20421(1, 15, 1);
  sub_25B45((int)_FDOTHER_DAT_, 3, 1);
  sub_11DF2(0, 255, 64);
  sub_16886(655360, 320, (int)_FDOTHER_DAT__3, 0);
  
  // 淡入效果
  for (n40_1 = 0; n40_1 <= 40; ++n40_1)
  {
    sub_2DF01(0, 255, n40_1, 0x38u, 0x3Cu, 0x3Fu);
    delay(8);
  }
  sub_4E381();
  
  // 检查存档文件
  _rb_ = fopen("FD2.SAV", "rb");
  if (_rb_)
  {
    v22 = malloc(22987);
    v26 = v22;
    sub_373CA((_BYTE *)v22, 1u, 22987, _rb_);
    fclose(_rb_);
    sub_4DF28((char *)v22, 22987);
    
    if (sub_4DF09((_BYTE *)v22, 22987) == *(_DWORD *)(v22 + 22983))
    {
      n2_1 = 2;
      if (*(unsigned __int8 *)(v22 + 12485) != 255)
        n2_1 = 3;
    }
    free(v26);
  }
  
  // 显示菜单并等待用户选择
  sub_1FF79((int)_FDOTHER_DAT__2, 0, n2_1);
  while (!v27)
  {
    sub_1FF79((int)_FDOTHER_DAT__2, n2_2, n2_1);
    HIBYTE(n3) = 16;
    int386(22, &n3, &n3);
    
    n2_3 = n2_1 - 1;
    
    // 上箭头
    if (HIBYTE(n3) == 72)
    {
      sub_25A96((int)_FDOTHER_DAT_, 2, 1);
      if (n2_2)
        --n2_2;
      else
        n2_2 = n2_3;
    }
    // 下箭头
    else if (HIBYTE(n3) == 80)
    {
      sub_25A96((int)_FDOTHER_DAT_, 2, 1);
      if (n2_2 == n2_3)
        n2_2 ^= n2_3;
      else
        ++n2_2;
    }
    // 确认选择
    else if ((unsigned __int8)n3 == 13 || 
             (unsigned __int8)n3 == 32 || 
             HIBYTE(n3) == 224 || 
             HIBYTE(n3) == 82)
    {
      sub_25A96((int)_FDOTHER_DAT_, 1, 1);
      v27 = 1;
    }
  }
  
  // 闪烁效果
  for (n4 = 0; n4 < 4; ++n4)
  {
    sub_1FF79((int)_FDOTHER_DAT__2, -1, n2_1);
    delay(80);
    sub_1FF79((int)_FDOTHER_DAT__2, n2_2, n2_1);
    delay(80);
  }
  
  // 清理并返回
  sub_1F882();
  memset(655360, 0, 64000);
  free(_FDOTHER_DAT__2);
  sub_25A96((int)_FDOTHER_DAT_, -1, 1);
  free(_FDOTHER_DAT_);
}
```

---

## 调用参数说明

```c
_BYTE *__fastcall sub_111BA(
    __int32 a1,    // 参数1: 上下文/寄存器传递
    int a2,        // 参数2: 上下文/寄存器传递
    int a3,        // 参数3: 上下文/寄存器传递
    int a4,        // 参数4: 上下文/寄存器传递
    int a5,        // 参数5: DAT文件名 (const char*)
    int a6,        // 参数6: 旧内存指针 (用于释放，可为0)
    int a7         // 参数7: 数据块索引号
);
```

## 调用模式总结

### 模式1: 初始化加载 (main函数)
```c
// 顺序加载多个索引，前一个返回值作为下一个的a1参数
ptr1 = sub_111BA(v9, v10, n80, n16, "FDOTHER.DAT", 0, 31);
ptr2 = sub_111BA(ptr1, v10, n80, n16, "FDOTHER.DAT", 0, 1);
ptr3 = sub_111BA(ptr2, v10, n80, n16, "FDOTHER.DAT", 0, 2);
```

### 模式2: 存档恢复 (sub_10010)
```c
// 根据动态计算的索引加载
FDOTHER_DAT = sub_111BA(..., "FDOTHER.DAT", FDOTHER_DAT, 0);
FDFIELD_DAT = sub_111BA(3*n17+2, n17, ... "FDFIELD.DAT", FDFIELD_DAT, 3*n17+2);
FDTXT_DAT   = sub_111BA(n17+1, ... "FDTXT.DAT", FDTXT_DAT, n17+1);
```

### 模式3: 循环加载 (sub_1F894)
```c
// 在循环中加载连续索引
for (n5 = 0; n5 < 5; ++n5) {
    ptr = sub_111BA(n5+69, ... "FDOTHER.DAT", ptr, n5+69);
    // 使用数据...
}
```

### 模式4: 条件加载 (sub_25EBB)
```c
// 根据启动结果决定加载
if (result == 0) {
    FDOTHER_DAT = sub_111BA(..., "FDOTHER.DAT", FDOTHER_DAT, 0);
} else if (result == 1) {
    FDOTHER_DAT__11 = sub_111BA(1, ... "FDOTHER.DAT", FDOTHER_DAT__11, 13);
    FDOTHER_DAT = sub_111BA(..., "FDOTHER.DAT", FDOTHER_DAT, 0);
}
```
