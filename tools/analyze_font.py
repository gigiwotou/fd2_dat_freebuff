import struct

with open('game/FDOTHER.DAT', 'rb') as f:
    data = f.read()

# 解析索引表
offsets = []
table_start = 6
for i in range(103):
    offset_addr = table_start + i * 4
    offset_val = struct.unpack_from('<I', data, offset_addr)[0]
    offsets.append(offset_val)

# 索引2 (字体候选)
for idx in [2, 4]:
    start = offsets[idx]
    end = offsets[idx + 1]
    size = end - start
    print(f'Index {idx}: offset={start}, size={size} bytes, chars={size//32}')

font_data = data[offsets[4]:offsets[5]]

# 检查前几个字符
print(f'\nCharacter 0 bitmap (16x16):')
for row in range(16):
    bits = struct.unpack_from('<H', font_data, row * 2)[0]
    row_str = ''
    for col in range(16):
        if bits & (1 << (15 - col)):
            row_str += '#'
        else:
            row_str += '.'
    print(f'  Row {row:2d}: {bits:016b}  {row_str}')

print(f'\nCharacter 1 bitmap (16x16):')
for row in range(16):
    bits = struct.unpack_from('<H', font_data, 32 + row * 2)[0]
    row_str = ''
    for col in range(16):
        if bits & (1 << (15 - col)):
            row_str += '#'
        else:
            row_str += '.'
    print(f'  Row {row:2d}: {bits:016b}  {row_str}')
