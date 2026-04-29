#!/usr/bin/env python3
"""分析FDSHAP.DAT资源0的实际结构"""
import struct

fdshap = open('game/FDSHAP.DAT', 'rb').read()
count = struct.unpack_from('<I', fdshap, 6)[0]
offsets = [struct.unpack_from('<I', fdshap, 10 + i*4)[0] for i in range(count)]

# 资源0：1200字节
res0_start = offsets[0]
res0_end = offsets[1]
res0_data = fdshap[res0_start:res0_end]

print(f'Resource 0: offset={res0_start}, size={len(res0_data)}')
print(f'First 100 bytes: {res0_data[:100].hex(chr(32))}')
print()

# 假设这是地形属性表，每4字节一个条目
# 1200 / 4 = 300个条目
print('Analyzing as 4-byte entries (300 total):')
for i in range(30):
    b0,b1,b2,b3 = res0_data[i*4:i*4+4]
    # 可能是地形ID -> 某种属性
    print(f'  [{i:3d}] = [{b0:02x} {b1:02x} {b2:02x} {b3:02x}] -> {b0},{b1},{b2},{b3}')

# 或者每3字节一个条目
print('\nAnalyzing as 3-byte entries (400 total):')
for i in range(30):
    b0,b1,b2 = res0_data[i*3:i*3+3]
    print(f'  [{i:3d}] = [{b0:02x} {b1:02x} {b2:02x}] -> {b0},{b1},{b2}')

# 或者每2字节一个条目
print('\nAnalyzing as 2-byte WORD entries (600 total):')
for i in range(40):
    val = struct.unpack_from('<H', res0_data, i*2)[0]
    print(f'  [{i:3d}] = {val:5d} (0x{val:04x})')

# 检查是否包含瓦片索引映射
# 如果资源0是"地形ID -> 瓦片索引"映射表
# 地形ID 0-299 -> 瓦片索引 0-191
print('\n\nChecking for tile index mapping:')
# 测试2字节条目
tile_indices_2byte = []
for i in range(400):
    if i*2+2 <= len(res0_data):
        val = struct.unpack_from('<H', res0_data, i*2)[0]
        if 0 <= val < 192:
            tile_indices_2byte.append(val)

print(f'If 2-byte entries: found {len(tile_indices_2byte)} entries with values in 0-191 range')

# 测试4字节条目（只取第一个字节）
tile_indices_4byte = []
for i in range(300):
    if i*4 < len(res0_data):
        val = res0_data[i*4]
        if 0 <= val < 192:
            tile_indices_4byte.append(val)

print(f'If 4-byte entries (byte 0): found {len(tile_indices_4byte)} entries with values in 0-191 range')

# 或者这是一个颜色表？
print('\n\nChecking if this is a palette:')
unique_vals = set(res0_data)
print(f'Unique values: {len(unique_vals)}')
if len(unique_vals) <= 64:
    print('Values are in 6-bit range (0-63) - might be palette!')
    # 转换为RGB
    if len(res0_data) >= 768:
        print(f'First 16 colors (as RGB):')
        for i in range(16):
            r,g,b = res0_data[i*3:i*3+3]
            r8 = (r<<2)|(r>>4)
            g8 = (g<<2)|(g>>4)
            b8 = (b<<2)|(b>>4)
            print(f'  [{i:2d}]: ({r8},{g8},{b8})')
