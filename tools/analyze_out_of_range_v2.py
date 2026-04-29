#!/usr/bin/env python3
"""分析超出范围的瓦片"""
import struct

fdfield = open('game/FDFIELD.DAT','rb').read()
offsets = []
pos = 6
while pos < len(fdfield) - 4:
    o = struct.unpack_from('<I',fdfield,pos)[0]
    if o > pos and o < len(fdfield): offsets.append(o)
    else: break
    pos += 4

layout = fdfield[offsets[0]:offsets[1]]
w = struct.unpack_from('<H',layout,0)[0]
h = struct.unpack_from('<H',layout,2)[0]

print(f'Map size: {w}x{h}')
print()

# 找出所有超出范围的瓦片 (tile_idx >= 192)
out_of_range = []
for i in range(w*h):
    pos = 4+4*i
    b0=layout[pos]; b1=layout[pos+1]; b2=layout[pos+2]; b3=layout[pos+3]
    
    # 使用b0作为瓦片索引（当b1=0时），或b0+192（当b1=1时）
    if b1 == 0:
        tile_idx = b0
    else:
        tile_idx = b0 + 192
    
    if tile_idx >= 192:
        y = i // w
        x = i % w
        out_of_range.append((x, y, b0, b1, tile_idx))

print(f'Out of range tiles: {len(out_of_range)}')
for x, y, b0, b1, tile_idx in out_of_range:
    print(f'  ({x:2d},{y:2d}): b0={b0:3d} (0x{b0:02x}), b1={b1}, tile_idx={tile_idx}')
    if b0 >= 192:
        # 可能的映射：减去128? 减去64? 模运算?
        print(f'    b0-128={b0-128}, b0-64={b0-64}, b0%128={b0%128}, b0%64={b0%64}')
