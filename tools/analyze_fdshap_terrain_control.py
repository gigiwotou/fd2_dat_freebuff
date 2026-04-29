#!/usr/bin/env python3
"""分析FDSHAP.DAT中的地形控制资料结构"""
import struct

fdshap = open('game/FDSHAP.DAT', 'rb').read()
fdfield = open('game/FDFIELD.DAT', 'rb').read()

count = struct.unpack_from('<I', fdshap, 6)[0]
offsets = [struct.unpack_from('<I', fdshap, 10+i*4)[0] for i in range(count)]

# 资源0是调色板（1200字节），资源1是瓦片集
res0_data = fdshap[offsets[0]:offsets[1]]
res1_data = fdshap[offsets[1]:offsets[2]]

print(f'Resource 0 (palette): {len(res0_data)} bytes')
print(f'Resource 1 (tileset): {len(res1_data)} bytes')

# 调色板结构：前768字节是256色，后432字节可能是地形控制资料
pal_data = res0_data[:768]
extra_data = res0_data[768:]

print(f'\nPalette extra data (768-{len(res0_data)}): {len(extra_data)} bytes')
print(f'First 50 bytes: {extra_data[:50].hex(chr(32))}')

# 如果每地形ID对应1个字节控制信息，432字节可能对应432个地形
# 或每地形对应2字节：432/2 = 216个地形
# 或每地形对应4字节：432/4 = 108个地形

# 分析这些额外数据
if len(extra_data) >= 256:
    print(f'\nExtra data as byte table (first 32):')
    for i in range(32):
        val = extra_data[i]
        print(f'  [{i:3d}] = {val:3d} (0x{val:02x})')

# 检查是否地形控制表从某个位置开始
# 文档说地形编号2字节，可能是地形ID到瓦片索引的映射
# 测试从byte 770, 772, 774等位置开始
print(f'\nSearching for terrain->tile mapping table...')

# 如果调色板后有地形控制表，每个地形ID对应1字节瓦片索引
# 地形ID范围8-286，需要至少287个条目
# 测试不同起始位置

# 瓦片集资源中可能也有地形控制表
# 瓦片集：byte 0-1=width, 2-3=height, 4-5=tile_count
# byte 6+: 偏移表（192个DWORD = 768字节）
# byte 774+: 瓦片RLE数据

# 但也许在偏移表之前还有其他数据？
# 检查byte 4-5的值
tile_w = struct.unpack_from('<H', res1_data, 0)[0]
tile_h = struct.unpack_from('<H', res1_data, 2)[0]
tile_count = struct.unpack_from('<H', res1_data, 4)[0]

print(f'\nTileset header:')
print(f'  Width: {tile_w}')
print(f'  Height: {tile_h}')
print(f'  Tile count: {tile_count}')
print(f'  Byte 4-5 raw: {res1_data[4]:02x} {res1_data[5]:02x} = {struct.unpack_from("<H", res1_data, 4)[0]}')

# 如果byte 4-5不是tile_count，而是其他信息？
# 测试：如果byte 4-5是"地形控制资料"的偏移或大小？
byte_4_5 = struct.unpack_from('<H', res1_data, 4)[0]
print(f'\n  Byte 4-5 value: {byte_4_5} (0x{byte_4_5:04x})')

# 如果这个值是地形控制表的条目数？
# 192个瓦片，如果每个地形ID对应一个条目，需要多少条目？
# 地形ID最大286，但可能使用模运算或其他映射

# 让我检查FDFIELD.DAT中所有地图使用的地形ID范围
print('\n\nTerrain ID usage across all maps:')
all_tids = set()
fdfield_offsets = []
pos = 6
while pos < len(fdfield) - 4:
    o = struct.unpack_from('<I', fdfield, pos)[0]
    if o > pos and o < len(fdfield): fdfield_offsets.append(o)
    else: break
    pos += 4

for map_id in range(10):
    layout_idx = map_id * 3
    if layout_idx + 1 >= len(fdfield_offsets):
        break
    
    layout_data = fdfield[fdfield_offsets[layout_idx]:fdfield_offsets[layout_idx+1]]
    w = struct.unpack_from('<H', layout_data, 0)[0]
    h = struct.unpack_from('<H', layout_data, 2)[0]
    
    if w > 100 or h > 100:
        continue
    
    tids = set()
    pos = 4
    for i in range(w*h):
        if pos+4 > len(layout_data):
            break
        tid = struct.unpack_from('<H', layout_data, pos)[0]
        tids.add(tid)
        pos += 4
    
    all_tids.update(tids)
    out_of_range = sum(1 for tid in tids if tid >= 192)
    print(f'  Map {map_id}: {w}x{h}, unique tids: {len(tids)}, out of 192 range: {out_of_range}')

print(f'\nAll unique terrain IDs: {sorted(all_tids)}')
print(f'Max terrain ID: {max(all_tids)}')
print(f'Terrain IDs >= 192: {sorted([tid for tid in all_tids if tid >= 192])}')
