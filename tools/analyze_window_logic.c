/**
 * 详细分析FD2窗口绘制逻辑
 * 基于MCP汇编代码sub_168B6的详细分析
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// 基于MCP汇编分析sub_168B6函数
/*
void __fastcall sub_168B6(__int32 a1, int a2, int a3, int a4, int a5, int a6, int a7, int a8, int a9, int a10)
{
  __int32 v10; // eax
  int v11; // ebp
  int v12; // edx
  int v13; // ebx
  int v14; // eax
  int v15; // edx
  int v16; // eax
  int v17; // eax
  int v18; // ebx
  int v19; // edx
  int v20; // eax
  int i; // ebx
  int j; // ebx
  int v23; // edi
  int v24; // ebx
  int k; // edi
  int m; // ebx
  int v27; // [esp+10h] [ebp-20h]
  int v28; // [esp+18h] [ebp-18h]
  int v29; // [esp+1Ch] [ebp-14h]

  sub_3702F(a1, a2, a3, a4, 68);  // 边界检查等
  v27 = a10 - 2;  // a10 = 高度（行数），v27 = 高度-2
  v28 = 16 * a6;  // v28 = 16 * a6 (a6 = Y坐标？)
  v29 = 3 * a6;   // v29 = 3 * a6
  v10 = a5 + a6 * a8;  // v10 = a5 + a6 * a8
  v11 = v10 + a7;      // v11 = v10 + a7 (a7 = X坐标？)
  
  // 根据汇编代码，调用序列是：
  sub_1685C(v10, a2, a3, a4, v10 + a7, a6, dword_53A81, 1);   // Tile 1
  v12 = 16 * a9 + v11 + 3;                                    // 计算新位置
  sub_1685C(16 * a9, v12, a3, a4, v12, a6, dword_53A81, 2);  // Tile 2
  v13 = a10 * v28;                                            // 计算偏移
  sub_1685C(v11 + v29 + a10 * v28, v12, a10 * v28, a4, v11 + v29 + a10 * v28, a6, dword_53A81, 3);  // Tile 3
  v14 = sub_1685C(v13 + v29 + v12, v12, v13, a4, v13 + v29 + v12, a6, dword_53A81, 4);            // Tile 4
  sub_1685C(v14, v12, a10 * 16 * a6, a4, v11 + 3, a6, dword_53A81, 5);                           // Tile 5
  v15 = v11 + 19 + 16 * (a9 - 2);                                                                   // 计算新位置
  sub_1685C(v11 + 19, v15, a10 * 16 * a6, a4, v15, a6, dword_53A81, 6);                          // Tile 6
  sub_1685C(v13 + v29 + v11 + 3, v15, v13, a4, v13 + v29 + v11 + 3, a6, dword_53A81, 7);        // Tile 7
  v16 = sub_1685C(v13 + v29 + v15, v15, v13, a4, v13 + v29 + v15, a6, dword_53A81, 8);          // Tile 8
  v17 = sub_1685C(v16, v15, a10 * 16 * a6, a4, v11 + 3 * a6, a6, dword_53A81, 14);              // Tile 14
  v18 = 16 * (a9 - 2) + v11 + 3 * a6 + 35;                                                        // 计算新位置
  sub_1685C(v17, v15, v18, a4, v18, a6, dword_53A81, 15);                                         // Tile 15
  v19 = (a10 - 1) * 16 * a6;
  v20 = sub_1685C(a10 - 1, v19, v18, a4, v19 + v11 + 3 * a6, a6, dword_53A81, 16);             // Tile 16
  sub_1685C(v20, v19, v19 + v18, a4, v19 + v18, a6, dword_53A81, 17);                            // Tile 17
  
  // 水平边框循环
  if ( a9 - 2 > 0 )  // a9 = 宽度（列数）
  {
    for ( i = 0; i < a9 - 2; ++i )
    {
      sub_1685C(16 * i, v19, i, a4, 16 * i + v11 + 19, a6, dword_53A81, 9);     // Tile 9 (上边框)
      sub_1685C(a10 * v28, v19, i, a4, v29 + a10 * v28 + 16 * i + v11 + 19, a6, dword_53A81, 12); // Tile 12 (下边框)
    }
  }
  
  // 垂直边框循环
  if ( v27 > 0 )  // v27 = 高度 - 2
  {
    for ( j = 0; j < v27; j = v23 )
    {
      v23 = j + 1;
      v24 = v11 + v29 + (j + 1) * v28;
      sub_1685C(v11 + v29, v19, v24, a4, v24, a6, dword_53A81, 10);  // Tile 10 (左边框)
      sub_1685C(v24 + 16 * a9 + 3, v19, v24, a4, v24 + 16 * a9 + 3, a6, dword_53A81, 11); // Tile 11 (右边框)
    }
  }
  
  // 内容区域循环
  for ( k = 0; k < a10; ++k )  // k < 高度
  {
    for ( m = 0; m < a9; ++m )  // m < 宽度
      sub_1685C(
        16 * m + v11 + v29 + 3 + k * v28,  // 目标X
        16 * m + v11 + v29 + 3,            // 源X
        m,                                   // ?
        a4,                                  // ?
        16 * m + v11 + v29 + 3 + k * v28,  // 目标地址
        a6,                                  // pitch
        dword_53A81,                         // tile数据基址
        13);                                 // Tile 13 (内容区域)
  }
}
*/

// 基于上述分析，正确的窗口绘制逻辑应该是：
void print_window_logic_analysis() {
    printf("FD2窗口绘制逻辑分析 (基于sub_168B6汇编代码):\n");
    printf("=============================================\n");
    printf("参数含义推测:\n");
    printf("  a5 = X起始位置\n");
    printf("  a6 = Y起始位置\n");
    printf("  a7 = 窗口宽度（列数）\n");
    printf("  a8 = 窗口高度（行数）\n");
    printf("  a1, a2, a3, a4 = 其他参数（如显存地址、pitch等）\n");
    printf("\n");
    
    printf("窗口元素绘制顺序:\n");
    printf("  1. 左上角 (Tile 1)\n");
    printf("  2. 右上角 (Tile 2)\n");
    printf("  3. 左下角 (Tile 3)\n");
    printf("  4. 右下角 (Tile 4)\n");
    printf("  5. 上边框 (Tile 9) - 在宽度-2的范围内循环\n");
    printf("  6. 下边框 (Tile 12) - 在宽度-2的范围内循环\n");
    printf("  7. 左边框 (Tile 10) - 在高度-2的范围内循环\n");
    printf("  8. 右边框 (Tile 11) - 在高度-2的范围内循环\n");
    printf("  9. 内容区域 (Tile 13) - 在整个窗口区域内循环填充\n");
    printf("\n");
    
    printf("关键计算公式:\n");
    printf("  v28 = 16 * a6\n");
    printf("  v29 = 3 * a6\n");
    printf("  v11 = (a5 + a6 * pitch) + offset_x  (窗口左上角的内存偏移)\n");
    printf("\n");
    
    printf("这表明原版游戏的窗口绘制使用了复杂的内存偏移计算，\n");
    printf("而不只是简单的X,Y坐标绘制。\n");
}

int main() {
    print_window_logic_analysis();
    return 0;
}