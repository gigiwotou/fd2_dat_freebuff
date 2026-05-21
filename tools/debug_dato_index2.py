import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

file_size = len(data)
count = struct.unpack('<I', data[6:10])[0]

# 检查索引196的原始字节
idx = 196
offset = 10 + idx * 4
raw_bytes = data[offset:offset+4]
print(f'索引196的原始字节 (偏移{offset}): {raw_bytes.hex()} = {struct.unpack("<I", raw_bytes)[0]}')

# 检查索引195和197
for i in [195, 196, 197]:
    offset = 10 + i * 4
    raw_bytes = data[offset:offset+4]
    val = struct.unpack('<I', raw_bytes)[0]
    print(f'  索引[{i}] (偏移{offset}): {raw_bytes.hex()} = {val} (0x{val:08x})')

# 检查是否索引表有特殊的结束标记
# 或者索引表使用了不同的字节序
print(f'\n检查索引表范围:')
for i in range(min(20, count-1)):
    offset = 10 + i * 4
    val = struct.unpack('<I', data[offset:offset+4])[0]
    if val > file_size:
        print(f'  *** 索引[{i}] 偏移{val} 超出文件大小{file_size} ***')
    else:
        print(f'  索引[{i}] (偏移{offset}): {val} (0x{val:08x})')

# 检查文件结构
print(f'\nDATO.DAT文件结构分析:')
print(f'  文件大小: {file_size}')
print(f'  文件头(0-5): {data[:6].hex()}')
print(f'  索引数量(6-9): {count}')
print(f'  索引表(10-{10+count*4-1})')

# 检查是否有额外的头部信息
# 可能索引表不是从10开始的
# 或者索引表有特殊结构
print(f'\n检查可能的大索引偏移:')
# 看看索引196附近是否有合理的偏移值
for i in range(190, 200):
    offset = 10 + i * 4
    val = struct.unpack('<I', data[offset:offset+4])[0]
    is_valid = val < file_size
    print(f'  索引[{i}] (偏移{offset}): {val} {"OK" if is_valid else "INVALID"}')
