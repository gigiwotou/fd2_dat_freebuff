#!/usr/bin/env python3
"""分析FDOTHER.DAT中所有调色板资源，找出对话场景使用的调色板"""
import struct

with open('game/FDOTHER.DAT', 'rb') as f:
    data = f.read()

count = struct.unpack('<I', data[6:10])[0]
print(f"FDOTHER.DAT: {count} resources, file size: {len(data)}\n")

# 查找所有768字节资源(256色*3字节)
palette_indices = []
for i in range(count - 1):
    s = struct.unpack_from('<I', data, 10 + i*4)[0]
    e = struct.unpack_from('<I', data, 10 + (i+1)*4)[0]
    sz = e - s
    if sz == 768:
        palette_indices.append(i)

print(f"找到 {len(palette_indices)} 个调色板资源: {palette_indices}\n")

# 分析每个调色板的颜色分布
for idx in palette_indices:
    s = struct.unpack_from('<I', data, 10 + idx*4)[0]
    print(f"=== 调色板索引 {idx} ===")
    
    # 读取所有256个颜色
    colors = []
    for j in range(256):
        r, g, b = struct.unpack_from('<BBB', data, s + j*3)
        colors.append((r, g, b))
    
    # 统计颜色特征
    # 1. 肤色色调: R高, G中等, B低
    skin_count = sum(1 for r, g, b in colors if r > 30 and 15 <= g <= 50 and b < 30)
    
    # 2. 蓝色色调: B高, R/G低
    blue_count = sum(1 for r, g, b in colors if b > 40 and r < 20 and g < 20)
    
    # 3. 暖色调: R高, G中等
    warm_count = sum(1 for r, g, b in colors if r > 40 and 20 <= g <= 50)
    
    # 4. 暗色调: 所有分量都低
    dark_count = sum(1 for r, g, b in colors if r < 10 and g < 10 and b < 10)
    
    print(f"  肤色色调: {skin_count} 个颜色")
    print(f"  蓝色色调: {blue_count} 个颜色")
    print(f"  暖色调: {warm_count} 个颜色")
    print(f"  暗色调: {dark_count} 个颜色")
    
    # 显示前10个颜色
    print("  前10个颜色 (R, G, B):")
    for j in range(min(10, len(colors))):
        r, g, b = colors[j]
        print(f"    [{j:3d}]: R={r:3d} G={g:3d} B={b:3d}")
    print()
