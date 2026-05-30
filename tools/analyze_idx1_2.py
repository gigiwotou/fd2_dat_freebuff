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

# 分析索引1
print('=== 索引 1 分析 ===')
start1 = offsets[1]
end1 = offsets[2]
size1 = end1 - start1
res1 = data[start1:end1]
print(f'偏移: {start1}, 大小: {size1} 字节')
print(f'前2字节: {struct.unpack("<H", res1[:2])[0]}')
print(f'第3字节: {res1[2]}')
print(f'前16字节 hex: {res1[:16].hex(" ")}')

# 分析索引2
print(f'\n=== 索引 2 分析 ===')
start2 = offsets[2]
end2 = offsets[3]
size2 = end2 - start2
res2 = data[start2:end2]
print(f'偏移: {start2}, 大小: {size2} 字节')
print(f'前16字节 hex: {res2[:16].hex(" ")}')

# 检查索引2是否也是字体 (37680 / 32 = 1177.5 不是整数)
# 检查37680 = 24 * 24 * 65.625 不是标准tile
# 检查是否可能是 16x16 字体: 37680 / 32 = 1177.5 (不是整数)
# 检查是否可能是 8x8 字体: 37680 / 8 = 4710 (不是标准)
# 检查是否可能是 8x16 字体: 8*16/8 = 16字节/字: 37680/16 = 2355
# 检查是否可能是 12x12 字体: 12*12/8 = 18字节/字: 37680/18 = 2093.3
# 检查是否可能是 24x24 图标: 24*24/8 = 72字节/字: 37680/72 = 523.3
# 检查是否可能是 16x16 位图 (每行2字节): 32字节/字: 37680/32 = 1177.5

# 检查前几个字节是否为RLE数据
print(f'\n索引1 数据模式分析:')
print(f'字节0-1 (宽度?): {struct.unpack("<H", res1[:2])[0]}')
print(f'字节2-3 (高度?): {struct.unpack("<H", res1[2:4])[0]}')
print(f'字节4 (调色板窗口?): {res1[4]}')

# 如果宽度=24, 高度=24
w = struct.unpack("<H", res1[:2])[0]
h = struct.unpack("<H", res1[2:4])[0]
print(f'\n如果 w={w}, h={h}:')
print(f'预期像素数: {w*h}')
print(f'RLE数据从偏移5开始, 大小: {size1-5}')

# 检查是否为LMI1格式
print(f'\n检查LMI1格式:')
print(f'前4字节: {res1[:4].hex(" ")}')
if res1[:4] == b'LMI1':
    print('是LMI1格式!')
    tile_count = struct.unpack('<H', res1[4:6])[0]
    print(f'Tile数量: {tile_count}')
else:
    print('不是LMI1格式')

# 打印索引2前64字节
print(f'\n索引2 前64字节:')
for i in range(0, min(64, len(res2)), 16):
    hex_str = res2[i:i+16].hex(' ')
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in res2[i:i+16])
    print(f'  {i:3d}: {hex_str}  {ascii_str}')
