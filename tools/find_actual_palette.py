#!/usr/bin/env python3
"""查找FDSHAP.DAT中实际的调色板数据"""
import struct

fdshap = open('game/FDSHAP.DAT', 'rb').read()

count = struct.unpack_from('<I', fdshap, 6)[0]
offsets = [struct.unpack_from('<I', fdshap, 10 + i*4)[0] for i in range(count)]

print(f'Total resources: {count}')
print(f'File size: {len(fdshap)}')
print()

# 分析前20个资源
print('Resource analysis (first 20):')
for i in range(min(20, count)):
    res_start = offsets[i]
    res_end = offsets[i+1] if i+1 < count else len(fdshap)
    res_size = res_end - res_start
    res_data = fdshap[res_start:res_start + min(20, res_size)]
    
    # 检查是否是调色板格式（768字节或更大）
    is_palette = (res_size >= 768 and res_size <= 1200)
    
    # 打印前20字节
    print(f'  Res {i:2d}: offset={res_start:6d}, size={res_size:6d}, '
          f'palette={is_palette}, first_bytes={res_data[:12].hex(chr(32))}')

# 查找所有大小在768-1200之间的资源（可能是调色板）
print(f'\nSearching for palette-like resources (768-1200 bytes):')
palette_resources = []
for i in range(count):
    res_start = offsets[i]
    res_end = offsets[i+1] if i+1 < count else len(fdshap)
    res_size = res_end - res_start
    if 768 <= res_size <= 1200:
        palette_resources.append((i, res_start, res_size))
        print(f'  Res {i}: offset={res_start}, size={res_size}')

print(f'\nFound {len(palette_resources)} palette-like resources')
print(f'Expected pairs (palette+tileset): {len(palette_resources)} palettes for terrain_set_id 0-{len(palette_resources)-1}')
