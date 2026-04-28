# FD2 游戏启动与剧情系统分析

> 分析时间：2026-04-28  
> 分析工具：IDA Pro MCP  
> 分析文件：FD2.EXE (DOS游戏)

## 概述

本文档记录了从开始菜单选择"Start"到进入游戏剧情的完整流程分析，包括菜单交互、场景数据结构和剧情播放系统。

---

## 1. 菜单选择与游戏启动

### 1.1 菜单交互循环 (sub_1F894)

**地址**: `0x1F894`  
**功能**: intro动画 + 开始菜单

```c
// 0x1FCC6: 加载菜单资源
_FDOTHER.DAT__2 = sub_111BA("FDOTHER.DAT", _FDOTHER.DAT_, 7);  // 嵌套DAT

// 0x1FD4A: 绘制菜单背景
sub_16886(655360, 320, _FDOTHER.DAT__2, 0);

// 0x1FD90-0x1FE13: 读取存档文件判断菜单项数
n3 = fopen("FD2.SAV", "rb");
if (n3) {
    v15 = malloc(22987);
    fread(v15, 1, 22987, n3);
    fclose(n3);
    sub_4DF28(v15, 22987);  // 解密存档
    if (校验通过 && v15[12485] != 0xFF) {
        n100 = 3;  // 有存档：3个菜单项
    } else {
        n100 = 2;  // 无存档：2个菜单项
    }
    free(v15);
}

// 0x1FE24: 绘制菜单
sub_1FF79(_FDOTHER.DAT_, 0, n100);

// 0x1FE31-0x1FEE3: 等待用户输入
while (!n12) {
    sub_1FF79(_FDOTHER.DAT_, n3_1, n100);  // 重绘菜单(n3_1=选中索引)
    int386(22, &::n3, &::n3);               // BIOS键盘中断
    n3 = n100 - 1;
    
    if (按键扫描码 == 72) {        // 上箭头
        sub_25A96(v36, 2, 1);      // 播放音效
        if (n3_1) --n3_1;          // 上移
        else n3_1 = n3;
    } else if (按键扫描码 == 80) { // 下箭头
        sub_25A96(v36, 2, 1);
        if (n3_1 == n3) n3_1 ^= n3;
        else ++n3_1;
    } else {
        // Enter(13), Space(32), 插入键(0xE0), 其他(82)
        if (按键 == 13 || 32 || 0xE0 || 82) {
            sub_25A96(v36, 1, 1);  // 播放确认音效
            n12 = 1;               // 退出循环
        }
    }
}
```

### 1.2 菜单闪烁动画

```c
// 0x1FEF0-0x1FF23
for (n4 = 0; n4 < 4; ++n4) {
    sub_1FF79(_FDOTHER.DAT_, -1, n100);  // 清除选中
    delay(80);
    sub_1FF79(_FDOTHER.DAT_, n3_1, n100);  // 高亮选中
    delay(80);
}
```

### 1.3 返回到调用者

```c
// 0x1FF31: 淡入过渡
sub_1F882(v15, ...);  // 64帧淡入动画

// 0x1FF42-0x1FF6A: 清理资源
memset(0xA0000, 0, 64000);
free(_FDOTHER.DAT_);
sub_25A96(v36, -1, 1);
free(v36);

// 0x13994: 退出函数
JUMPOUT(0x13994);
```

---

## 2. 游戏启动调度器 (sub_25EBB)

**地址**: `0x25EBB`  
**功能**: 根据菜单选择决定后续流程

```c
int result = sub_1F894();

if (result == 0) {
    // 选择 Start
    sub_1F882();
    n17 = 0;
    sub_111BA("FDOTHER.DAT", _FDOTHER.DAT_, 0);
    dword_53BFB = 0;
    byte_51AAC = 0;
    funcs_25E3A[n17]();  // 调用函数表索引0
}
else if (result == 1) {
    // 选择 Load
    sub_111BA("FDOTHER.DAT", 0, 0x0D);  // 资源13
    sub_1F882();
    sub_111BA("FDOTHER.DAT", _FDOTHER.DAT_, 0);
    memset(0xA0000, 0, 64000);
    // 读取存档...
}
```

### 2.1 函数表 funcs_25E3A

**地址**: `0x51D71`

| 索引 | 函数地址 | 功能 |
|------|----------|------|
| 0 | 0x3231B | Start游戏 - 剧情模式 |
| 1 | 0x32D18 | Load存档 |
| 2 | 0x32E8C | - |
| 3 | 0x32FB2 | - |
| 4 | 0x33049 | - |
| 5 | 0x3314B | - |
| 6 | 0x33169 | - |
| 7 | 0x33219 | - |
| 8 | 0x3327D | - |
| 9 | 0x3332B | - |

---

## 3. Start游戏主流程 (sub_3231B)

**地址**: `0x3231B`  
**功能**: 播放开场剧情

### 3.1 剧情序列

```c
// ===== 第一阶段：开场动画 =====
n17 = 32;
sub_205DA(v5);           // 初始化系统
sub_135DD(3, 34);        // 设置状态
sub_1366A(99);           // 播放场景99 (开场剧情)

// 延迟循环
for (n0xF = 0; n0xF < 0xF; ++n0xF)
    sub_13185(2);

// 绘制场景0
sub_15F84(a5, dword_53A79, 0, 655360, 320, 205, 76, 74, 19, 1);
dword_51A83 = 0;

// ===== 第二阶段：剧情对话 =====
for (n0xD = 0; n0xD < 0xD; ++n0xD)
    sub_13185(2);

sub_15F84(a5, dword_53A79, 1, 655360, 320, 205, 76, 74, 19, 1);
dword_51A83 = 0;

sub_25977(-1, 0);        // 音频相关
n64 = 1;

// ===== 第三阶段：更多剧情 =====
sub_1366A(100);          // 场景100
n64 = 0;
sub_135DD(0, 43);        // 设置状态

v8 = sub_25977(11, 0);
sub_1F525(v8);
sub_1366A(101);          // 场景101

sub_15F84(a5, dword_53A79, 2, 655360, 320, 205, 76, 74, 19, 1);
sub_1366A(102);          // 场景102
sub_15F84(a5, dword_53A79, 3, 655360, 320, 205, 76, 74, 19, 1);
sub_1366A(103);          // 场景103
sub_15F84(a5, dword_53A79, 4, 655360, 320, 205, 76, 74, 19, 1);
sub_1366A(104);          // 场景104
sub_15F84(a5, dword_53A79, 5, 655360, 320, 205, 76, 74, 19, 1);

n64 = 1;
sub_1366A(105);          // 场景105
n64 = 0;

// ===== 第四阶段：角色选择/对话 =====
n17 = 31;
sub_205DA(v9);
sub_135DD(5, 42);
sub_1366A(90);
sub_15F84(a5, dword_53A79, 0, 655360, 320, 205, 76, 74, 19, 1);
sub_1366A(91);
sub_15F84(a5, dword_53A79, 1, 655360, 320, 205, 76, 74, 19, 1);
// ... 场景92-98

// ===== 第五阶段：进入战场 =====
n17 = 0;
sub_112A5(0);
sub_112A5(9);
sub_112A5(4);
sub_112A5(0x1E);
sub_205DA(v13);
sub_135DD(4, 12);

sub_1366A(0);            // 战场场景0
delay(200);
sub_15F84(a5, dword_53A79, 0, 655360, 320, 205, 76, 74, 19, 1);
delay(200);

sub_135DD(0, 0);
sub_32999(1);
sub_1366A(1);            // 战场场景1
sub_135DD(0, 15);
sub_32999(2);
sub_1366A(2);            // 战场场景2
sub_15F84(a5, dword_53A79, 1, 655360, 320, 205, 76, 74, 19, 1);
delay(200);

sub_1366A(5);            // 战场场景5
v14 = sub_32975(9);
sub_11CAC(v14, 0);
delay(100);
sub_15F84(a5, dword_53A79, 2, 655360, 320, 205, 76, 74, 19, 1);

sub_134E4(v15);
sub_12D7B(v16, ...);
dword_53BF3 = 0;
```

---

## 4. 场景播放系统 (sub_1366A)

**地址**: `0x1366A`  
**功能**: 解析并播放场景数据（角色移动、动画）

### 4.1 场景数据表

**地址**: `0x627D8`  
**类型**: 指针数组，每个指针指向一个场景数据

```c
int* off_627D8[] = {
    0x62980,  // 场景0
    0x6299B,  // 场景1
    0x629A6,  // 场景2
    0x629D1,  // 场景3
    0x629F0,  // 场景4
    0x62A01,  // 场景5
    0x62A06,  // 场景6
    0x62A1B,  // 场景7
    0x62A30,  // 场景8
    0x62A3D,  // 场景9
    // ... 更多场景
};
```

### 4.2 场景数据格式

```
场景数据:
  字节0:     命令数量 (uint8)
  字节1+:    命令列表

命令格式:
  字节0:     命令类型 (uint8)
             - bit7=0: 普通动画命令
             - bit7=1: 特殊命令(角色选择/切换)
  字节1:     参数数量 (uint8)
  字节2+:    参数列表 (每个参数2字节)
             - param[0]: 角色ID/操作码
             - param[1]: 动作/状态值
```

### 4.3 场景播放逻辑

```c
int sub_1366A(int scene_id) {
    scene_data = sub_4EB48(scene_id);  // 从 off_627D8[scene_id] 获取
    command_count = scene_data[0];
    data_ptr = scene_data + 1;
    
    for (cmd_idx = 0; cmd_idx < command_count; ++cmd_idx) {
        cmd_type = data_ptr[0];
        param_count = data_ptr[1];
        data_ptr += 2;
        
        // 解析参数
        for (j = 0; j < param_count; ++j) {
            v16[j] = data_ptr[0];   // 角色ID/操作码
            v15[j] = data_ptr[1];   // 动作值
            data_ptr += 2;
        }
        
        if ((cmd_type & 0x80) == 0) {
            // 普通命令：角色动画和移动
            for (i = 0; i < cmd_type; ++i) {
                // 7个动画帧
                for (n7 = 1; n7 < 7; ++n7) {
                    sub_32230(v16[0]);  // 执行角色操作
                    
                    // 更新角色状态 (每个角色80字节)
                    // 偏移3: 动作值
                    // 偏移4: 动画帧
                    for (j = 0; j < param_count; ++j) {
                        ptr = dword_53A45 + 80 * v16[j];
                        ptr[3] = v15[j];
                        ptr[4] = n7;
                    }
                    
                    if (n64 == 0 || n64 == 64) {
                        sub_11CAC(0);  // 无淡入
                    } else {
                        ++n64;
                        sub_11CAC(1);
                        sub_11D40(0, 255, n64);  // 淡入
                    }
                    
                    sub_4E381();  // 刷新屏幕
                }
                
                // 更新角色位置
                for (j = 0; j < param_count; ++j) {
                    ptr = dword_53A45 + 80 * v16[j];
                    n3 = v15[j];
                    
                    if (n3 == 1) {
                        --ptr[0];   // 向左移动
                    } else if (n3 == 3) {
                        ++ptr[0];   // 向右移动
                    } else {
                        --ptr[1];   // 向上移动
                    }
                    ptr[4] = 0;     // 重置动画帧
                }
            }
        } else {
            // 特殊命令 (0x80标志)
            cmd_type &= ~0x80;
            
            if (cmd_type == 0) {
                // 角色选择/切换界面
                sub_17AA9(1);
                sub_11EEE(dword_53A49 + 32904, 456, 13, 8, ...);
                
                for (k = 0; k < n6_0; ++k) {
                    // 更新角色信息
                    for (j = 0; j < param_count; ++j) {
                        if (k == v16[j]) {
                            dword_53A49 -= 5472;
                            ptr[3] = v15[j];
                        }
                    }
                    
                    if ((ptr[5] & 1) == 0) {
                        sub_127E0(k);  // 初始化角色
                    }
                }
                
                sub_129EC();  // 角色渲染准备
                sub_11EB0(0xA0504, 320, dword_53A49 + 32904, 456, 312, 192);
                sub_17AA9(2);
                sub_11CAC(0);
                sub_4E381();  // 刷新屏幕
            } else {
                // 其他特殊命令
                for (j = 0; j < param_count; ++j) {
                    ptr = dword_53A45 + 80 * v16[j];
                    ptr[3] = v15[j];
                }
                
                for (j = 0; j < cmd_type; ++j) {
                    sub_11CAC(0);
                    sub_17AA9(1);
                    sub_4E381();
                }
            }
        }
    }
    
    return sub_11CAC(1);
}
```

---

## 5. 场景绘制系统 (sub_15F84)

**地址**: `0x15F84`  
**功能**: 绘制场景背景和角色

```c
// 参数:
// a1: 未知
// a2: dword_53A79 (场景数据?)
// a3: 场景索引 (0, 1, 2, ...)
// a4: 655360 (0xA0000, VGA显存基址)
// a5: 320 (行宽)
// a6: 205
// a7: 76
// a8: 74
// a9: 19
// a10: 1

sub_15F84(a5, dword_53A79, scene_idx, 655360, 320, 205, 76, 74, 19, 1);
```

**推测**: 该函数负责：
1. 加载场景背景图
2. 绘制角色精灵（根据dword_53A45中的状态）
3. 合成到VGA显存

---

## 6. 关键数据结构

### 6.1 角色状态 (dword_53A45)

**地址**: `0x53A45`  
**大小**: 每个角色80字节

```c
struct Character {
    // 偏移0-2: 位置坐标
    int8_t x;        // X坐标
    int8_t y;        // Y坐标
    int8_t z;        // Z坐标(高度)
    
    // 偏移3: 动作值
    int8_t action;   // 来自场景命令的v15[j]
    
    // 偏移4: 动画帧
    int8_t frame;    // 1-6循环
    
    // 偏移5: 标志位
    int8_t flags;    // bit0: 是否初始化
    
    // 其他: 未知(75字节)
    uint8_t pad[75];
};
```

### 6.2 场景状态

```c
int n64;         // 淡入控制 (0=无, 1-64=淡入中)
int n17;         // 游戏状态索引 (0=战场, 31=剧情, 32=开场)
int dword_51A83; // 绘制标志 (总是设为0)
int dword_53BF3; // 结束标志 (最后设为0)
```

---

## 7. 函数调用关系

```
main()
  └─ sub_25EBB()
      ├─ sub_1F894()                    # intro+菜单
      │   ├─ sub_111BA()                # 加载资源
      │   ├─ sub_16886()                # 绘制菜单背景
      │   ├─ sub_1FF79()                # 绘制菜单项
      │   ├─ sub_1F882()                # 淡入动画
      │   └─ return 0/1                 # 0=Start, 1=Load
      │
      └─ funcs_25E3A[n17]()
          └─ sub_3231B()                # Start游戏
              ├─ sub_1366A(scene_id)    # 播放场景
              │   ├─ sub_4EB48()        # 获取场景数据
              │   ├─ sub_32230()        # 角色操作
              │   ├─ sub_11CAC()        # 显示控制
              │   ├─ sub_11D40()        # 调色板
              │   └─ sub_4E381()        # 刷新屏幕
              │
              ├─ sub_15F84()            # 场景绘制
              ├─ sub_135DD()            # 状态设置
              ├─ sub_25977()            # 音频
              └─ sub_32975()            # 未知
```

---

## 8. 场景ID列表

根据sub_3231B调用序列：

| 场景ID | 说明 | 类型 |
|--------|------|------|
| 99 | 开场动画 | 剧情 |
| 100-105 | 剧情对话 | 剧情 |
| 90-96 | 角色对话/选择 | 剧情 |
| **97** | **战场地图主场景** | **战场** |
| 98 | 剧情过渡 | 剧情 |
| 0-5 | 战场子场景 | 战场 |

---

## 9. 关键地址汇总

| 名称 | 地址 | 说明 |
|------|------|------|
| sub_1F894 | 0x1F894 | intro+菜单控制器 |
| sub_25EBB | 0x25EBB | 游戏启动调度器 |
| funcs_25E3A | 0x51D71 | 函数表指针数组 |
| sub_3231B | 0x3231B | Start游戏主流程 |
| sub_1366A | 0x1366A | 场景播放器 |
| sub_15F84 | 0x15F84 | 场景绘制器 |
| off_627D8 | 0x627D8 | 场景数据表 |
| dword_53A45 | 0x53A45 | 角色状态数组 |
| sub_4EB48 | 0x4EB48 | 场景数据获取函数 |
| sub_4E381 | 0x4E381 | 屏幕刷新函数 |

---

## 6. 场景绘制系统实现

> 基于IDA MCP分析，实现了完整的场景播放系统。

### 6.1 实现的文件

- `include/fd2_scene.h` - 场景数据结构和API定义
- `src/fd2_scene.c` - 场景播放器实现
- `src/fd2_game.c` - 添加了CUTSCENE状态处理

### 6.2 完整场景序列

根据sub_3231B分析，从选择Start到进入战场的完整场景序列：

```c
game->cutscene_sequence[0] = 99;   /* 开场动画 */
game->cutscene_sequence[1] = 100;  /* 剧情场景1 */
game->cutscene_sequence[2] = 101;  /* 剧情场景2 */
game->cutscene_sequence[3] = 102;  /* 剧情场景3 */
game->cutscene_sequence[4] = 103;  /* 剧情场景4 */
game->cutscene_sequence[5] = 104;  /* 剧情场景5 */
game->cutscene_sequence[6] = 105;  /* 剧情场景6 */
game->cutscene_sequence[7] = 90;   /* 战斗入场1 */
game->cutscene_sequence[8] = 91;   /* 战斗入场2 */
game->cutscene_sequence[9] = 92;   /* 战斗入场3 */
game->cutscene_sequence[10] = 93;  /* 战斗入场4 */
game->cutscene_sequence[11] = 94;  /* 战斗入场5 */
game->cutscene_sequence[12] = 95;  /* 战斗入场6 */
game->cutscene_sequence[13] = 96;  /* 战斗入场7 */
game->cutscene_sequence[14] = 97;  /* 战斗入场8 */
game->cutscene_sequence[15] = 98;  /* 战斗入场9 */
game->cutscene_sequence[16] = 0;   /* 战场场景0 */
game->cutscene_sequence[17] = 1;   /* 战场场景1 */
game->cutscene_sequence[18] = 2;   /* 战场场景2 */
game->cutscene_sequence[19] = 5;   /* 战场场景5 */
game->cutscene_count = 20;
```

### 6.3 状态转换流程

```
MENU (选择1 Player)
    ↓
CUTSCENE (播放场景99 - 开场动画)
    ↓
CUTSCENE (播放场景100-105 - 剧情)
    ↓
CUTSCENE (播放场景90-98 - 战斗入场)
    ↓
CUTSCENE (播放场景0-5 - 战场)
    ↓
BATTLE (进入实际战斗)
```

### 6.4 编译状态

由于当前Windows环境缺少MSYS2 GCC编译器，代码尚未编译测试。需要以下环境：
- MSYS2 with ucrt64 toolchain
- SDL2 development libraries

---

## 7. 参考资料

---

## 8. 待分析项目

1. **sub_15F84详细逻辑**: ✅ 已分析 - 场景命令处理、角色精灵加载
2. **场景数据文件位置**: ✅ 已确认 - 硬编码在exe数据段0x627D8
3. **角色精灵数据**: ⏳ 待分析 - DATO.DAT的资源结构
4. **战场逻辑**: ⏳ 待分析 - 进入战场后的游戏控制流程
5. **存档格式**: ⏳ 待分析 - FD2.SAV的完整结构

---

*本文档基于IDA Pro MCP反编译分析，所有地址和逻辑均来自二进制分析*
