#!/usr/bin/env python3
"""验证FDSHAP调色板数据"""
import struct

fdshap = open('game/FDSHAP.DAT', 'rb').read()

# 正确格式：byte 6 = 计数, byte 10+ = 偏移表
count = struct.unpack_from('<I', fdshap, 6)[0]
print(f'FDSHAP resource count: {count}')

offsets = []
for i in range(count):
    offset = struct.unpack_from('<I', fdshap, 10 + i*4)[0]
    offsets.append(offset)

# 调色板资源（资源0）
res0_start = offsets[0]
res0_end = offsets[1] if 1 < count else len(fdshap)
res0_data = fdshap[res0_start:res0_end]
print(f'\nPalette resource 0: offset={res0_start}, size={len(res0_data)}')

# 调色板前768字节
palette_6bit = res0_data[:768]
print(f'Palette data (first 768 bytes):')
print(f'  First 32 bytes: {palette_6bit[:32].hex(chr(32))}')

# 转换为8-bit RGB
print(f'\nFirst 16 colors:')
for i in range(16):
    r = palette_6bit[i*3]
    g = palette_6bit[i*3+1]
    b = palette_6bit[i*3+2]
    r8 = (r << 2) | (r >> 4)
    g8 = (g << 2) | (g >> 4)
    b8 = (b << 2) | (b >> 4)
    print(f'  Color {i:2d}: 6bit=({r:3d},{g:3d},{b:3d}) -> 8bit=({r8:3d},{g8:3d},{b8:3d})')

# 调色板后432字节
extra = res0_data[768:]
print(f'\nExtra data after palette: {len(extra)} bytes')
print(f'First 32 bytes: {extra[:32].hex(chr(32))}')

# 瓦片集资源（资源1）
res1_start = offsets[1]
res1_end = offsets[2] if 2 < count else len(fdshap)
res1_data = fdshap[res1_start:res1_end]
print(f'\nTileset resource 1: offset={res1_start}, size={len(res1_data)}')

tile_w = struct.unpack_from('<H', res1_data, 0)[0]
tile_h = struct.unpack_from('<H', res1_data, 2)[0]
tile_count = struct.unpack_from('<H', res1_data, 4)[0]
print(f'  Tile dimensions: {tile_w}x{tile_h}')
print(f'  Tile count: {tile_count}')

# 瓦片偏移表
tile_offsets = []
pos = 6
for i in range(tile_count):
    if pos + 4 > len(res1_data):
        break
    off = struct.unpack_from('<I', res1_data, pos)[0]
    tile_offsets.append(off)
    pos += 4

print(f'  Tile offsets found: {len(tile_offsets)}')
print(f'  First 5 offsets: {tile_offsets[:5]}')
