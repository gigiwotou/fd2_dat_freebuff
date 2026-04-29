#!/usr/bin/env python3
"""分析地形ID模式"""
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
w = struct.unpack_from('<H', layout, 0)[0]
h = struct.unpack_from('<H', layout, 2)[0]

# 分析所有瓦片
out_of_range = []
in_range = []
for i in range(w * h):
    pos = 4 + 4*i
    b0=layout[pos]; b1=layout[pos+1]; b2=layout[pos+2]; b3=layout[pos+3]
    tid = b0 | (b1 << 8)
    if tid >= 192:
        out_of_range.append((i, tid, b0, b1, b2, b3))
    else:
        in_range.append((i, tid, b0, b1, b2, b3))

print(f'Tiles in range (<192): {len(in_range)}')
print(f'Tiles out of range (>=192): {len(out_of_range)}')
print()

# 分析超出范围的地形ID
unique_out = sorted(set(tid for _, tid, _, _, _, _ in out_of_range))
print(f'Unique out-of-range terrain IDs: {unique_out}')
print()

# 检查模式：是否有共同的位模式
for tid in unique_out:
    b0 = tid & 0xFF
    b1 = (tid >> 8) & 0xFF
    print(f'  tid={tid:3d} (0x{tid:04x}): b0={b0:02x}, b1={b1:02x}, b1&0x03={b1&3}, b1&0xFC={b1&0xFC}')
