#!/usr/bin/env python3
"""分析FDOTHER.DAT资源7的调色板数据"""
import struct

fdother = open('game/FDOTHER.DAT', 'rb').read()

# 解析资源偏移表
count = struct.unpack_from('<I', fdother, 6)[0]
print(f'FDOTHER.DAT resource count: {count}')

offsets = []
for i in range(count):
    off = struct.unpack_from('<I', fdother, 10 + i*4)[0]
    offsets.append(off)

# 资源7是调色板（768字节）
res7_start = offsets[7]
res7_end = offsets[8] if 8 < count else len(fdother)
res7_size = res7_end - res7_start
print(f'\nResource 7 (palette):')
print(f'  Offset: {res7_start}')
print(f'  Size: {res7_size}')

palette_data = fdother[res7_start:res7_start + 768]
print(f'\nFirst 48 bytes (16 colors):')
for i in range(16):
    r,g,b = palette_data[i*3:i*3+3]
    print(f'  Color {i:2d}: ({r:3d}, {g:3d}, {b:3d})')

# 检查调色板是否有效（有多种颜色）
unique_colors = set()
for i in range(256):
    r,g,b = palette_data[i*3:i*3+3]
    unique_colors.add((r,g,b))

print(f'\nTotal unique colors: {len(unique_colors)}')
print(f'Is valid palette: {len(unique_colors) > 16}')

# 与FDSHAP资源0对比
fdshap = open('game/FDSHAP.DAT', 'rb').read()
fdshap_count = struct.unpack_from('<I', fdshap, 6)[0]
fdshap_offsets = [struct.unpack_from('<I', fdshap, 10 + i*4)[0] for i in range(fdshap_count)]
fdshap_res0 = fdshap[fdshap_offsets[0]:fdshap_offsets[0]+768]

# 对比两个调色板
diff = sum(1 for a,b in zip(palette_data, fdshap_res0) if a != b)
print(f'\nComparison with FDSHAP resource 0:')
print(f'  Different bytes: {diff}/768')
if diff == 0:
    print('  PALETTES ARE IDENTICAL')
else:
    print('  PALETTES ARE DIFFERENT - FDOTHER#7 is likely the correct one!')
