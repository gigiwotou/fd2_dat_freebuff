#!/usr/bin/env python
"""
正确解析索引1的资源结构
"""

import os
import struct

fdother_path = r"d:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT"

with open(fdother_path, 'rb') as f:
    data = f.read()

file_size = len(data)
print(f"文件大小: {file_size} bytes (0x{file_size:X})\n")

# 解析FDOTHER头部 - LLLLLL格式
# [0-5]: magic "LLLLLL"
# [6+]: 资源偏移表 (每项4字节)

# 解析资源偏移表
offsets = []
pos = 6
while pos + 4 <= file_size:
    off = struct.unpack('<I', data[pos:pos+4])[0]
    if off == 0 or off > file_size:
        break
    offsets.append(off)
    pos += 4

# 添加文件末尾作为最后一个资源的结束
offsets.append(file_size)

print(f"资源数量: {len(offsets)-1}\n")

# 查看前10个资源
for i in range(min(10, len(offsets)-1)):
    start = offsets[i]
    end = offsets[i+1]
    size = end - start
    
    print(f"索引{i}: offset=0x{start:X}, size=0x{size:X} ({size} bytes)")
    
    # 打印前20字节
    if start < file_size:
        chunk = data[start:min(start+20, file_size)]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        print(f"  数据: {hex_str}")
        
        # 尝试解析头部
        if size >= 6:
            if chunk[0:6] == b'LLLLLL':
                print(f"  类型: 嵌套DAT")
            elif chunk[0:4] == b'LMI1':
                print(f"  类型: LMI1")
            elif size >= 4:
                w, h = struct.unpack('<HH', chunk[0:4])
                if 0 < w <= 640 and 0 < h <= 480:
                    print(f"  类型: TILE (宽高={w}x{h})")

# 特别查看索引1
print(f"\n{'='*60}")
print(f"索引1详细分析:")
print(f"{'='*60}")

idx1_start = offsets[1]
idx1_end = offsets[2]
idx1_size = idx1_end - idx1_start

print(f"起始: 0x{idx1_start:X}")
print(f"结束: 0x{idx1_end:X}")
print(f"大小: {idx1_size} bytes\n")

idx1_data = data[idx1_start:idx1_end]

# 打印前100字节
print("前100字节:")
for i in range(0, min(100, len(idx1_data)), 16):
    chunk = idx1_data[i:i+16]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    print(f"  {i:04X}: {hex_str}")

# 解析索引1的头部
if len(idx1_data) >= 6:
    w = struct.unpack('<H', idx1_data[0:2])[0]
    h = struct.unpack('<H', idx1_data[2:4])[0]
    palette_window = idx1_data[4]
    byte5 = idx1_data[5]
    
    print(f"\n头部解析:")
    print(f"  [0-1]: width={w} (0x{w:X})")
    print(f"  [2-3]: height={h} (0x{h:X})")
    print(f"  [4]: palette_window={palette_window} (0x{palette_window:X})")
    print(f"  [5]: byte5={byte5} (0x{byte5:X})")
    
    # 解析偏移表（从偏移6开始）
    print(f"\n偏移表（前20个）:")
    icon_offsets = []
    pos = 6
    for i in range(20):
        if pos + 4 > len(idx1_data):
            break
        off = struct.unpack('<I', idx1_data[pos:pos+4])[0]
        print(f"  偏移{pos}: 0x{off:X}")
        icon_offsets.append(off)
        pos += 4
        if off == 0 or off > idx1_size:
            break
    
    # 分析第一个图标
    if len(icon_offsets) >= 2 and icon_offsets[0] > 0 and icon_offsets[0] < idx1_size:
        icon0_start = icon_offsets[0]
        icon0_end = icon_offsets[1] if icon_offsets[1] <= idx1_size else idx1_size
        icon0_size = icon0_end - icon0_start
        
        print(f"\n图标0:")
        print(f"  起始: 0x{icon0_start:X}")
        print(f"  大小: {icon0_size} bytes")
        print(f"  前40字节:")
        icon0_data = idx1_data[icon0_start:icon0_start+min(40, icon0_size)]
        for i in range(0, len(icon0_data), 16):
            chunk = icon0_data[i:i+16]
            hex_str = ' '.join(f'{b:02X}' for b in chunk)
            print(f"    {i:04X}: {hex_str}")
