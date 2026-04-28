import struct
from pathlib import Path

data = Path("game/FDFIELD.DAT").read_bytes()

# 测试：资源1的前4字节是 1b001500 => w=27, h=21
# 这可能是正确的地图0布局数据

# 根据之前verify_fdfield.py的结果，资源1确实有有效的宽高
# 所以正确的映射可能是：
# 3*N+1 = 布局数据
# 3*N = 控制数据
# 3*N+2 = 出场数据

# 但这与IDA代码矛盾...

# 让我检查IDC资料说的：
# 各地圖資料位置：每地圖3個4 byte整數，共12 byte
# (1)地圖構成資料位置 (2)地圖控制與寶箱資料位置 (3)人物出場位置資料位置

# 这意味着每个地图在偏移表中有3个条目，每个条目是4字节
# 但sub_111BA使用 4*a7+6 来计算偏移，说明每个资源占用8字节（start+end各4字节）

# 重新理解：可能是每个地图的3个资源不是连续的索引！

# 让我用另一种方式：查看已知有效的地图0资源1
print("=== Testing hypothesis: map N uses resources at different indices ===")

# 假设资源1是地图0的布局数据
for map_id in range(5):
    res_idx = map_id * 3 + 1  # 测试这个索引
    pos = 10 + res_idx * 8
    start, end = struct.unpack_from("<II", data, pos)
    size = end - start
    
    if size >= 4:
        w, h = struct.unpack_from("<HH", data, start)
        print(f"Map {map_id}, Resource {res_idx}: w={w}, h={h}, size={size}")
