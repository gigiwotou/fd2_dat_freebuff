#!/usr/bin/env python3
"""分析调色板后的432字节地形控制资料"""
import struct

fdshap = open('game/FDSHAP.DAT', 'rb').read()
count = struct.unpack_from('<I', fdshap, 6)[0]
offsets = [struct.unpack_from('<I', fdshap, 10+i*4)[0] for i in range(count)]
res0_data = fdshap[offsets[0]:offsets[1]]

# 调色板后432字节
extra = res0_data[768:]
print(f'Extra data: {len(extra)} bytes')
print(f'First 100 bytes hex: {extra[:100].hex(chr(32))}')
print()

# 假设每4字节一个条目：432/4 = 108个条目
print('As 4-byte entries (108 total):')
for i in range(min(20, 108)):
    b0,b1,b2,b3 = extra[i*4:i*4+4]
    print(f'  [{i:3d}] = [{b0:02x} {b1:02x} {b2:02x} {b3:02x}] -> {b0:3d}, {b1:3d}, {b2:3d}, {b3:3d}')

# 如果每条目4字节对应一个地形ID
# 108个条目可能对应地形ID 0-107或8-115等
# 或者条目本身就是地形ID到瓦片索引的映射

print(f'\n\nAs 2-byte entries (216 total):')
for i in range(min(20, 216)):
    val = struct.unpack_from('<H', extra, i*2)[0]
    print(f'  [{i:3d}] = {val:5d} (0x{val:04x})')

# 如果这些是地形ID->瓦片索引的映射
# 地形ID 0-215 -> 瓦片索引
# 测试：检查地形ID 203对应的瓦片索引

# 或者这些条目有特定结构
# 根据文档，地形控制资料可能包含宝箱信息
# 让我分析432字节的可能结构

print(f'\n\nAnalyzing 432-byte structure:')
# 测试不同条目大小
for entry_size in [3, 4, 6, 8, 12, 16]:
    num_entries = 432 // entry_size
    if 432 % entry_size == 0:
        print(f'  {entry_size}-byte entries: {num_entries} entries')

# 最可能的是每条目4字节（108个）或每条目3字节（144个）
# 地形ID最大383，如果使用模144或模108映射呢？

# 检查所有地形ID % 108 或 % 144
fdfield = open('game/FDFIELD.DAT', 'rb').read()
fdfield_offsets = []
pos = 6
while pos < len(fdfield) - 4:
    o = struct.unpack_from('<I', fdfield, pos)[0]
    if o > pos and o < len(fdfield): fdfield_offsets.append(o)
    else: break
    pos += 4

all_tids = set()
for map_id in range(10):
    layout_idx = map_id * 3
    if layout_idx + 1 >= len(fdfield_offsets):
        break
    layout_data = fdfield[fdfield_offsets[layout_idx]:fdfield_offsets[layout_idx+1]]
    w = struct.unpack_from('<H', layout_data, 0)[0]
    h = struct.unpack_from('<H', layout_data, 2)[0]
    if w > 100 or h > 100:
        continue
    pos = 4
    for i in range(w*h):
        if pos+4 > len(layout_data):
            break
        tid = struct.unpack_from('<H', layout_data, pos)[0]
        all_tids.add(tid)
        pos += 4

print(f'\nTerrain IDs % 108:')
mods_108 = sorted(set([tid % 108 for tid in all_tids]))
print(f'  Range: {min(mods_108)}-{max(mods_108)}')
print(f'  Unique: {len(mods_108)}')
print(f'  All < 108? {max(mods_108) < 108}')

print(f'\nTerrain IDs % 144:')
mods_144 = sorted(set([tid % 144 for tid in all_tids]))
print(f'  Range: {min(mods_144)}-{max(mods_144)}')
print(f'  Unique: {len(mods_144)}')
print(f'  All < 144? {max(mods_144) < 144}')

print(f'\nTerrain IDs % 192:')
mods_192 = sorted(set([tid % 192 for tid in all_tids]))
print(f'  Range: {min(mods_192)}-{max(mods_192)}')
print(f'  Unique: {len(mods_192)}')
print(f'  All < 192? {max(mods_192) < 192}')
