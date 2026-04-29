#!/usr/bin/env python3
"""验证IDA文档中的地形ID计算公式"""
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

# 测试三种公式
formulas = {
    'raw 16-bit': lambda b0,b1,b2,b3: b0 | (b1 << 8),
    'IDA doc formula': lambda b0,b1,b2,b3: (b2 & 0x1F) << 2 | (b1 & 3),
    'byte[2]&3 << 8 | byte[0]': lambda b0,b1,b2,b3: b0 | ((b2 & 3) << 8),
}

print(f'Map size: {w}x{h} = {w*h} tiles')
print()

for name, func in formulas.items():
    tids = []
    for i in range(w * h):
        pos = 4 + 4*i
        b0=layout[pos]; b1=layout[pos+1]; b2=layout[pos+2]; b3=layout[pos+3]
        tid = func(b0, b1, b2, b3)
        tids.append(tid)
    
    unique = set(tids)
    out_of_range = sum(1 for tid in tids if tid >= 192)
    print(f'{name}:')
    print(f'  Range: {min(tids)}-{max(tids)}')
    print(f'  Unique: {len(unique)}')
    print(f'  Out of range (>=192): {out_of_range}')
    print()

# 打印前10个瓦片的详细数据
print('First 10 tiles:')
for i in range(10):
    pos = 4 + 4*i
    b0=layout[pos]; b1=layout[pos+1]; b2=layout[pos+2]; b3=layout[pos+3]
    raw16 = b0 | (b1 << 8)
    ida_doc = (b2 & 0x1F) << 2 | (b1 & 3)
    byte2_8 = b0 | ((b2 & 3) << 8)
    print(f'Tile {i}: [{b0:02x} {b1:02x} {b2:02x} {b3:02x}] raw16={raw16}, ida_doc={ida_doc}, byte2_8={byte2_8}')
