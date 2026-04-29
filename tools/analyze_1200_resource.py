#!/usr/bin/env python3
"""深入分析FDSHAP.DAT的1200字节资源"""
import struct

with open('game/FDSHAP.DAT', 'rb') as f:
    data = f.read()

# 解析偏移表
offsets = []
pos = 6
while pos < len(data) - 4:
    offset = struct.unpack_from("<I", data, pos)[0]
    if offset > pos and offset < len(data):
        offsets.append(offset)
    else:
        break
    pos += 4

print(f"总资源数: {len(offsets)}\n")

# 分析所有1200字节的资源（偶数索引 = 调色板位置）
for i in range(0, min(34, len(offsets)), 2):
    res_size = offsets[i+1] - offsets[i] if i+1 < len(offsets) else len(data) - offsets[i]
    
    if res_size == 1200:
        res_data = data[offsets[i]:offsets[i]+res_size]
        
        print(f"资源#{i} (1200字节):")
        
        # 检查前768字节
        palette_part = res_data[:768]
        rest_part = res_data[768:]
        
        unique_palette = len(set(palette_part))
        unique_rest = len(set(rest_part))
        max_palette = max(palette_part)
        max_rest = max(rest_part)
        
        print(f"  前768字节: 唯一值={unique_palette}, 最大值={max_palette}")
        print(f"  后432字节: 唯一值={unique_rest}, 最大值={max_rest}")
        
        # 打印前768字节的颜色
        print(f"  前5个颜色:")
        for c in range(5):
            r, g, b = palette_part[c*3], palette_part[c*3+1], palette_part[c*3+2]
            print(f"    [{c}] RGB({r}, {g}, {b})")
        
        # 检查是否有重复模式
        pattern = res_data[:16]
        print(f"  前16字节: {pattern.hex(' ')}")
        
        # 检查1200字节的其他可能结构
        # 300个4字节条目?
        print(f"  如果是300个4字节条目:")
        for j in range(5):
            entry = struct.unpack_from("<I", res_data, j*4)[0]
            print(f"    [{j}] = 0x{entry:x}")
        
        print()
