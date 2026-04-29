#!/usr/bin/env python3
"""深入分析FDOTHER.DAT资源15的结构"""
import struct

with open('game/FDOTHER.DAT', 'rb') as f:
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

print(f"FDOTHER.DAT总资源数: {len(offsets)}\n")

# 分析资源15
res15_start = offsets[15]
res15_end = offsets[16] if 16 < len(offsets) else len(data)
res15_data = data[res15_start:res15_end]

print(f"资源15:")
print(f"  偏移: 0x{res15_start:x}")
print(f"  大小: {len(res15_data)} 字节")
print(f"  前64字节: {res15_data[:64].hex(' ')}")

# 检查前768字节
if len(res15_data) >= 768:
    palette_part = res15_data[:768]
    print(f"\n前768字节:")
    print(f"  唯一值: {len(set(palette_part))}")
    print(f"  最大值: {max(palette_part)}")
    print(f"  最小值: {min(palette_part)}")
    
    # 打印前10个颜色
    print(f"  前10个颜色:")
    for i in range(10):
        r, g, b = palette_part[i*3], palette_part[i*3+1], palette_part[i*3+2]
        print(f"    [{i}] RGB({r}, {g}, {b})")
    
    # 检查是否有6-bit值 (0-63)
    if max(palette_part) <= 63:
        print(f"  -> 6-bit调色板")
    else:
        print(f"  -> 不是6-bit调色板")
    
    # 检查重复模式
    print(f"\n  检查重复模式:")
    for size in [4, 8, 16, 32]:
        pattern_count = 0
        for i in range(0, 768 - size, size):
            if palette_part[i:i+size] == palette_part[i+size:i+size*2]:
                pattern_count += 1
        print(f"    块大小{size}: {pattern_count} 个重复模式")
    
    # 剩余部分
    rest_part = res15_data[768:]
    print(f"\n后 {len(rest_part)} 字节:")
    print(f"  前64字节: {rest_part[:64].hex(' ')}")
    
    # 如果是图像数据，检查尺寸
    # 64000 = 320x200 (标准VGA分辨率)
    if len(rest_part) == 64000:
        print(f"  -> 可能是320x200的图像数据 (64000字节)")
    elif len(rest_part) == 64004:
        print(f"  -> 64004字节，可能是64000字节图像+4字节头")
