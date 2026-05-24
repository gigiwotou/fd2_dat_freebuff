# FDOTHER.DAT 资源使用完整分析

> 基于IDA Pro MCP对FD2.EXE的反汇编分析
> 分析日期: 2026-05-24

---

## 📋 目录

1. [FDOTHER.DAT全局变量与实际索引映射](#1-fdotherdat全局变量与实际索引映射)
2. [资源加载核心函数 sub_111BA](#2-资源加载核心函数-sub_111ba)
3. [FDOTHER.DAT文件索引结构](#3-fdotherdat文件索引结构)
4. [各函数调用点实际使用的索引值](#4-各函数调用点实际使用的索引值)
5. [各绘制函数使用的FDOTHER资源](#5-各绘制函数使用的fdother资源)
6. [资源读取流程](#6-资源读取流程)
7. [资源使用总结](#7-资源使用总结)

---

## 1. FDOTHER.DAT全局变量与实际索引映射

**重要说明: 全局变量名中的数字≠实际文件索引!**

游戏使用14个全局变量存储FDOTHER.DAT资源指针,但变量名中的索引号与实际加载的文件索引不一致:

| 全局变量           | 地址    | 实际文件索引 | 加载位置          | 用途确认         |
| --------------- | ----- | ------- | ------------- | ------------- |
| `_FDOTHER.DAT__0`  | 0x53aff | **0**   | sub_25EBB     | 存档相关?         |
| `_FDOTHER.DAT__1`  | 0x627ac | (待确认)   | -             | -             |
| `_FDOTHER.DAT__2`  | 0x53eec | **31**  | main(0x25BF4) | 调色板数据?        |
| `_FDOTHER.DAT__3`  | 0x53a4d | **1**   | main(0x25BF4) | (待确认)         |
| `_FDOTHER.DAT__4`  | 0x53a89 | **2**   | main(0x25BF4) | 字体位图?         |
| `_FDOTHER.DAT__5`  | 0x53a6d | **3**   | main(0x25BF4) | (待确认)         |
| `_FDOTHER.DAT__6`  | 0x53a75 | **4**   | main(0x25BF4) | **字符位图**       |
| `_FDOTHER.DAT__7`  | 0x53a81 | **5**   | main(0x25BF4) | **UI Tiles**   |
| `_FDOTHER.DAT__8`  | 0x53ad1 | **6**   | main(0x25BF4) | (待确认)         |
| `_FDOTHER.DAT__9`  | 0x53b13 | (待确认)   | -             | -             |
| `_FDOTHER.DAT__10` | 0x53b0f | (待确认)   | -             | -             |
| `_FDOTHER.DAT__11` | 0x53f66 | (待确认)   | -             | -             |
| `_FDOTHER.DAT__12` | 0x53f5a | (待确认)   | -             | -             |
| `_FDOTHER.DAT__13` | 0x54153 | **13**  | sub_25EBB     | 存档恢复时加载       |

**关键发现**:
- `FDOTHER_DAT__6` 实际加载的是**文件索引4**,不是索引6
- `FDOTHER_DAT__7` 实际加载的是**文件索引5**,不是索引7
- `FDOTHER_DAT__2` 实际加载的是**文件索引31**,不是索引2

---

## 2. 资源加载核心函数 sub_111BA

**地址**: 0x111BA  
**大小**: 0xEB (235字节)  
**功能**: 从DAT文件中加载指定索引的资源到内存

### 2.1 函数签名

```c
_BYTE *__fastcall sub_111BA(
    __int32 a1,         // 标准参数1
    int a2,             // 标准参数2
    int a3,             // 标准参数3
    int a4,             // 标准参数4
    int a5,             // 文件名指针 ("DATO.DAT" 或 "FDOTHER.DAT")
    int a6,             // 旧资源指针 (如果不为空则先free)
    int a7              // 资源索引号 (实际文件中的索引)
);
```

### 2.2 核心实现

```c
_BYTE *__fastcall sub_111BA(..., int filename, int old_ptr, int resource_index)
{
  sub_3702F(a1, a2, a3, a4, 32);
  
  // 1. 如果旧资源存在,先释放
  if (old_ptr)
    free(old_ptr);
  
  // 2. 打开文件 ("rb" 二进制读模式)
  FILE *fp = fopen(filename, "rb");
  if (!fp)
  {
    printf("\n\n File not found %s!!! \n\n", filename);
    return NULL;
  }
  
  // 3. 读取资源索引表 (每个索引8字节: 起始偏移 + 结束偏移)
  int *index_table = malloc(8);
  fseek(fp, 4 * resource_index + 6, SEEK_SET);  // 跳到索引位置
  sub_373CA(index_table, 1, 8, fp);             // 读取8字节索引
  
  int start_offset = index_table[0];            // 资源起始偏移
  int end_offset = index_table[1];              // 资源结束偏移
  int resource_size = end_offset - start_offset; // 资源大小
  free(index_table);
  
  // 4. 分配内存并读取资源数据
  _BYTE *resource_data = malloc(resource_size);
  if (!resource_data)
  {
    printf("Out of Memory at Load %s Number:%d!!\n", filename, resource_index);
    fclose(fp);
    return NULL;
  }
  
  // 5. 跳到资源起始位置并读取
  fseek(fp, start_offset, SEEK_SET);
  sub_373CA(resource_data, 1, resource_size, fp);
  fclose(fp);
  
  return resource_data;
}
```

### 2.3 文件读取函数 sub_373CA

**地址**: 0x373CA  
**功能**: 标准fread封装,支持缓冲读取

---

## 3. FDOTHER.DAT文件索引结构

### 3.1 索引表格式

```
FDOTHER.DAT文件结构:
├─ 偏移 0-5:    文件头 (6字节)
├─ 偏移 6-13:   索引0 (起始偏移4字节 + 结束偏移4字节)
├─ 偏移 14-21:  索引1 (起始偏移4字节 + 结束偏移4字节)
├─ 偏移 22-29:  索引2 (起始偏移4字节 + 结束偏移4字节)
├─ ...
└─ 索引N之后:   实际资源数据
```

### 3.2 索引计算公式

```c
// 读取索引N的位置
fseek(fp, 4 * N + 6, SEEK_SET);

// 索引格式 (8字节)
struct ResourceIndex {
    int start_offset;  // 资源在文件中的起始偏移
    int end_offset;    // 资源在文件中的结束偏移
};

// 资源大小
int size = end_offset - start_offset;
```

---

## 4. 各函数调用点实际使用的索引值

### 4.1 main 函数 (0x25BF4) - 游戏启动初始化

| 序号 | 文件名        | 实际索引 | 保存到变量           | 用途        |
|----|-----------|------|---------------|----------|
| 1  | FDOTHER.DAT | **31** | FDOTHER_DAT__2  | 调色板数据?    |
| 2  | FDOTHER.DAT | **1**  | FDOTHER_DAT__3  | (待确认)    |
| 3  | FDOTHER.DAT | **2**  | FDOTHER_DAT__4  | 字体位图?     |
| 4  | FDOTHER.DAT | **3**  | FDOTHER_DAT__5  | (待确认)    |
| 5  | FDOTHER.DAT | **4**  | FDOTHER_DAT__6  | **字符位图**  |
| 6  | FDOTHER.DAT | **5**  | FDOTHER_DAT__7  | **UI Tiles** |
| 7  | FDTXT.DAT   | 0    | FDTXT_DAT__0    | 文本数据      |
| 8  | FDOTHER.DAT | **6**  | FDOTHER_DAT__8  | (待确认)    |

### 4.2 sub_25EBB (0x25EBB) - 存档恢复/场景切换

| 序号 | 文件名        | 实际索引 | 说明       |
|----|-----------|------|----------|
| 1  | FDOTHER.DAT | **13** | 从存档恢复时加载 |
| 2  | FDOTHER.DAT | **0**  | 首次启动加载   |
| 3  | FDOTHER.DAT | **0**  | 其他分支加载   |

### 4.3 sub_1F894 (0x1F894) - 启动画面/菜单

| 序号 | 文件名        | 实际索引 | 用途        |
|----|-----------|------|-----------|
| 1  | FDOTHER.DAT | **77** | 标题画面背景    |
| 2  | FDOTHER.DAT | **76** | 调色板数据     |
| 3  | FDOTHER.DAT | **74** | 标题文字      |
| 4  | FDOTHER.DAT | **99** | 过渡画面      |
| 5  | FDOTHER.DAT | **101**| 过渡画面      |
| 6-10| FDOTHER.DAT | **69-73** | 5个菜单项(循环) |
| 11 | FDOTHER.DAT | **101**| 特殊帧处理     |
| 12 | FDOTHER.DAT | **102**| 关键帧       |
| 13 | FDOTHER.DAT | **7**  | 动画背景      |
| 14 | FDOTHER.DAT | **8**  | 动画前景      |

### 4.4 sub_10652 (0x10652) - 背景系统 (根据地图编号条件加载)

| 序号 | 文件名        | 实际索引   | 地图条件     |
|----|-----------|--------|----------|
| 1  | FDOTHER.DAT | **15**   | 地图9,24,25 |
| 2  | FDOTHER.DAT | **35,36** | 地图17,21  |
| 3  | FDOTHER.DAT | **40,41** | 地图22     |
| 4  | FDOTHER.DAT | **42**    | 地图23     |
| 5  | FDOTHER.DAT | **46,47** | 地图27     |
| 6  | FDOTHER.DAT | **55,56** | 地图28,29  |

### 4.5 sub_15F84 (0x15F84) - 文本引擎

**注意**: sub_15F84中调用sub_111BA都是加载**DATO.DAT**,不是FDOTHER.DAT!

```c
// 加载DATO.DAT (对话文本),索引从dword_53C1B+7读取
DATO_DAT = sub_111BA(v21, v16, a5, a4, (int)aDatoDat, DATO_DAT, *(unsigned __int8 *)(dword_53C1B + 7));
```

**sub_15F84使用的FDOTHER资源** (通过参数传入,不是调用sub_111BA加载):
- 使用 `FDOTHER_DAT__6` 进行字符绘制 (索引4的资源)
- 使用 `FDTXT_DAT__0` 进行递归文本显示

---

## 5. 各绘制函数使用的FDOTHER资源

### 5.1 字符/精灵渲染 - FDOTHER_DAT__6 (文件索引4)

**函数**: sub_4ED7A()  
**全局变量**: `_FDOTHER.DAT__6` (0x53a75)  
**实际文件索引**: **4**  
**用途**: 16×16字符位图 (每个字符32字节)

```c
void __cdecl sub_4ED7A(
    int _FDOTHER.DAT_,    // 传入 FDOTHER_DAT__6 (文件索引4)
    int char_index,       // 字符索引
    int n658255,          // 屏幕位置
    unsigned __int16 argC,// 行距
    char arg10,           // 前景色
    char arg14,           // 背景色
    int arg18)            // 清空标志
{
  if (char_index != 10)
  {
    // 从FDOTHER_DAT__6读取字符位图 (实际是文件索引4的资源)
    __int16 *bitmap = (__int16 *)(32 * char_index + FDOTHER_DAT__6);
    // 逐行逐像素渲染...
  }
}
```

**调用者**:
- sub_15F84() - 文本引擎
- 文本显示: `sub_4ED7A(FDOTHER_DAT__6, char_index, ...)`

### 5.2 UI Tiles绘制 - FDOTHER_DAT__7 (文件索引5)

**函数**: sub_1685C()  
**全局变量**: `_FDOTHER.DAT__7` (0x53a81)  
**实际文件索引**: **5**  
**用途**: UI对话框tile元素 (17种tile)

```c
void __fastcall sub_1685C(
    ..., 
    char *dst,          // 目标显存位置
    int height,         // tile高度
    int FDOTHER_DAT_7,  // 传入 FDOTHER_DAT__7 (文件索引5)
    int tile_index)     // tile索引 (1-17)
{
  // 从FDOTHER_DAT__7读取tile指针表
  sub_4ED0B(dst, (_WORD *)(FDOTHER_DAT__7 + 6 + 4 * tile_index), height);
}
```

**tile索引用途**:
```
tile 1-4:   四个角 (左上、右上、左下、右下)
tile 5-8:   四条边
tile 9-12:  边缘循环部分
tile 13:    中心区域填充
tile 14-17: 额外边框元素
tile 18-19: 闪烁动画tile (在sub_16C57中使用)
```

### 5.3 调色板数据 - FDOTHER_DAT__2 (文件索引31)

**函数**: sub_11D40()  
**全局变量**: `_FDOTHER.DAT__2` (0x53eec)  
**实际文件索引**: **31**  
**用途**: VGA调色板颜色数据 (每颜色3字节RGB)

```c
void __fastcall sub_11D40(..., int start_color, int end_color, int color_offset)
{
  while (start_color <= end_color)
  {
    outp(968, start_color);  // VGA DAC写地址
    
    // 从FDOTHER_DAT__2读取调色板数据 (实际是文件索引31)
    int red   = FDOTHER_DAT__2[3 * start_color]     - color_offset;
    int green = FDOTHER_DAT__2[3 * start_color + 1] - color_offset;
    int blue  = FDOTHER_DAT__2[3 * start_color + 2] - color_offset;
    
    outp(969, max(0, red));
    outp(969, max(0, green));
    outp(969, max(0, blue));
    
    ++start_color;
  }
}
```

### 5.4 标题/菜单画面资源 (sub_1F894动态加载)

| 文件索引 | 用途         | 大小估算    |
|------|------------|---------|
| 77   | 标题画面背景    | 大 (全屏位图) |
| 76   | 调色板数据     | 768B (256色×3) |
| 74   | 标题文字      | 中等      |
| 69-73| 5个菜单项     | 中等      |
| 7, 8 | 动画前景/背景   | 中等      |

### 5.5 地图背景资源 (sub_10652动态加载)

| 文件索引  | 地图编号     |
|-------|----------|
| 15    | 9, 24, 25 |
| 35, 36| 17, 21   |
| 40, 41| 22       |
| 42    | 23       |
| 46, 47| 27       |
| 55, 56| 28, 29   |

---

## 6. 资源读取流程

### 6.1 完整加载流程

```
游戏启动 (main 0x25BF4)
    ↓
打开FDOTHER.DAT (fopen "rb")
    ↓
读取索引表 (fseek到 4*index+6)
    ↓
读取8字节索引 (start_offset, end_offset)
    ↓
计算资源大小 (end - start)
    ↓
分配内存 (malloc)
    ↓
读取资源数据 (fseek + fread)
    ↓
关闭文件 (fclose)
    ↓
保存指针到全局变量 (_FDOTHER.DAT__N)
    ↓
绘制函数使用全局指针访问资源
```

### 6.2 main函数加载示例 (真实代码)

```c
// 从main函数(0x25BF4)实际代码分析:

// 1. 加载字符资源 (文件索引4)
FDOTHER_DAT__6 = sub_111BA(
    ..., 
    "FDOTHER.DAT", 
    FDOTHER_DAT__6,  
    4                // 实际文件索引是4,不是6!
);

// 2. 加载UI tiles资源 (文件索引5)
FDOTHER_DAT__7 = sub_111BA(
    ..., 
    "FDOTHER.DAT", 
    FDOTHER_DAT__7, 
    5                // 实际文件索引是5,不是7!
);

// 3. 加载调色板数据 (文件索引31)
FDOTHER_DAT__2 = sub_111BA(
    ..., 
    "FDOTHER.DAT", 
    FDOTHER_DAT__2, 
    31               // 实际文件索引是31,不是2!
);
```

### 6.3 绘制函数调用链

```c
// 文本引擎绘制字符
sub_15F84(
    screen_buf,
    FDOTHER_DAT__6,  // 传入字符资源 (文件索引4)
    text_index,
    ...
);
    ↓
sub_4ED7A(
    FDOTHER_DAT__6,  // 使用字符资源
    char_index,
    ...
);
    ↓
// 从FDOTHER_DAT__6读取字符位图
__int16 *bitmap = (32 * char_index + FDOTHER_DAT__6);

// UI对话框绘制
sub_168B6(
    screen_buf,
    320,
    ...,
    FDOTHER_DAT__7,  // 传入UI tiles资源 (文件索引5)
    ...
);
    ↓
sub_1685C(
    ...,
    FDOTHER_DAT__7,  // 使用UI tiles资源
    tile_index
);
    ↓
// 从FDOTHER_DAT__7读取tile指针
__int16 *tile_ptr = (FDOTHER_DAT__7 + 6 + 4 * tile_index);
```

### 6.4 DATO.DAT vs FDOTHER.DAT

游戏使用两种DAT文件:

| 文件        | 用途                   | 加载函数      | 加载时机    |
| --------- | -------------------- | --------- | ------- |
| FDOTHER.DAT | 字体、UI tiles、调色板等固定资源 | sub_111BA | 游戏启动时  |
| DATO.DAT  | 场景对话文本资源             | sub_111BA | 对话触发时  |

---

## 7. 资源使用总结

### 7.1 FDOTHER.DAT完整文件索引映射表

| 文件索引 | 全局变量           | 加载位置          | 用途确认         | 数据格式          |
|------|---------------|--------------|--------------|---------------|
| 0    | FDOTHER_DAT__0  | sub_25EBB    | 存档相关?        | (待确认)         |
| 1    | FDOTHER_DAT__3  | main         | (待确认)        | -             |
| 2    | FDOTHER_DAT__4  | main         | 字体位图?         | (待确认)         |
| 3    | FDOTHER_DAT__5  | main         | (待确认)        | -             |
| **4**  | FDOTHER_DAT__6  | main         | **字符位图**      | 32B/字符,16×16   |
| **5**  | FDOTHER_DAT__7  | main         | **UI Tiles**  | 指针表+tile数据    |
| 6    | FDOTHER_DAT__8  | main         | (待确认)        | -             |
| 7    | (动态加载)         | sub_1F894    | 动画背景         | 位图?           |
| 8    | (动态加载)         | sub_1F894    | 动画前景         | 位图?           |
| 13   | FDOTHER_DAT__13 | sub_25EBB    | 存档恢复         | (待确认)         |
| 15   | (动态加载)         | sub_10652    | 地图9,24,25背景  | 地图位图          |
| 31   | FDOTHER_DAT__2  | main         | **调色板数据**     | 3B/颜色(RGB)    |
| 35-36| (动态加载)         | sub_10652    | 地图17,21背景    | 地图位图          |
| 40-42| (动态加载)         | sub_10652    | 地图22,23背景    | 地图位图          |
| 46-47| (动态加载)         | sub_10652    | 地图27背景       | 地图位图          |
| 55-56| (动态加载)         | sub_10652    | 地图28,29背景    | 地图位图          |
| 69-73| (动态加载)         | sub_1F894    | 5个菜单项         | 菜单位图          |
| 74   | (动态加载)         | sub_1F894    | 标题文字         | 位图?           |
| 76   | (动态加载)         | sub_1F894    | 标题调色板         | 768B          |
| 77   | (动态加载)         | sub_1F894    | 标题画面背景       | 全屏位图          |

### 7.2 关键绘制函数资源使用

| 绘制函数      | 使用的全局变量      | 实际文件索引 | 资源用途    | 数据访问方式          |
| --------- | ----------- | ------- | ------- | ---------------- |
| sub_4ED7A | FDOTHER_DAT__6  | **4**   | 字符位图    | `32*index + ptr` |
| sub_1685C | FDOTHER_DAT__7  | **5**   | UI tiles| `ptr + 6 + 4*index` |
| sub_11D40 | FDOTHER_DAT__2  | **31**  | 调色板     | `3*color_index`  |

### 7.3 资源读取关键函数

| 函数        | 地址    | 功能              |
| --------- | ----- | --------------- |
| sub_111BA | 0x111BA | 加载DAT文件指定索引资源到内存 |
| sub_373CA | 0x373CA | fread封装,缓冲读取     |

---

**分析工具**: IDA Pro MCP Server  
**文件路径**: D:\workspace\fd2ida\FD2\FD2.EXE  
**分析完成日期**: 2026-05-24
