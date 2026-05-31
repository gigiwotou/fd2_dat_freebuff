import struct

with open('game/FDOTHER.DAT', 'rb') as f:
    data = f.read()

# 读取索引表
offset = 6
offsets = []
while offset + 4 <= len(data):
    off = struct.unpack_from('<I', data, offset)[0]
    if off == 0 or off >= len(data):
        break
    offsets.append(off)
    offset += 4

# 索引1
idx1_start = offsets[1]
idx1_end = offsets[2]
idx1_data = data[idx1_start:idx1_end]

print(f'索引1: 0x{idx1_start:X} - 0x{idx1_end:X}, {len(idx1_data)}字节')
print(f'前30字节: {" ".join(f"{b:02X}" for b in idx1_data[:30])}')

# 外头宽高
w = struct.unpack_from('<H', idx1_data, 0)[0]
h = struct.unpack_from('<H', idx1_data, 2)[0]
pal_win = idx1_data[4]
print(f'外头: {w}x{h}, pal_window={pal_win}')

# 相对偏移表
rel_offs = []
pos = 6
for i in range(20):
    rel_off = struct.unpack_from('<I', idx1_data, pos)[0]
    rel_offs.append(rel_off)
    pos += 4

print(f'\n找到 {len(rel_offs)} 个相对偏移')
for i, rel_off in enumerate(rel_offs[:5]):
    print(f'  图标{i}: 相对偏移 0x{rel_off:X}, 绝对偏移 {rel_off}')
    icon_data = idx1_data[rel_off:rel_off+16]
    print(f'    前16字节: {" ".join(f"{b:02X}" for b in icon_data)}')
