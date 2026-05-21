import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

file_size = len(data)
print(f'DATO.DAT文件大小: {file_size} 字节')

# 读取头像数量
count = struct.unpack('<I', data[6:10])[0]
print(f'头像数量: {count}')

# 检查索引表起始偏移
print(f'\n索引表起始偏移: 10 (0x{10:06x})')
print(f'索引表结束偏移: {10 + count * 4} (0x{10 + count * 4:06x})')

# 检查前几个索引
print('\n前10个索引:')
for i in range(min(10, count - 1)):
    off_start = struct.unpack('<I', data[10 + i * 4:14 + i * 4])[0]
    off_end = struct.unpack('<I', data[10 + (i + 1) * 4:14 + (i + 1) * 4])[0]
    print(f'  索引[{i}]: {off_start} - {off_end} (大小: {off_end - off_start})')

# 检查索引196
print('\n检查索引196:')
idx = 196
off_start = struct.unpack('<I', data[10 + idx * 4:14 + idx * 4])[0]
off_end = struct.unpack('<I', data[10 + (idx + 1) * 4:14 + (idx + 1) * 4])[0]
print(f'  off_start = {off_start} (0x{off_start:08x})')
print(f'  off_end = {off_end} (0x{off_end:08x})')
print(f'  文件大小 = {file_size}')
print(f'  偏移是否有效: {off_start < file_size and off_end <= file_size}')

# 看看索引表实际有多大
print(f'\n索引表最后一个条目 (索引{count-2}):')
idx = count - 2
off_start = struct.unpack('<I', data[10 + idx * 4:14 + idx * 4])[0]
off_end = struct.unpack('<I', data[10 + (idx + 1) * 4:14 + (idx + 1) * 4])[0]
print(f'  off_start = {off_start} (0x{off_start:08x})')
print(f'  off_end = {off_end} (0x{off_end:08x})')

# 检查索引表是否真的是从偏移10开始
print('\n检查DATO.DAT文件头:')
header = data[:20]
print(f'  偏移0-5: {header[:6].hex()}')
print(f'  偏移6-9 (count): {struct.unpack("<I", header[6:10])[0]}')
print(f'  偏移10-13 (索引0): {struct.unpack("<I", header[10:14])[0]}')
