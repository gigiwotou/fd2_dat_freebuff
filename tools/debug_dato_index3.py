import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

file_size = len(data)

# 查找所有合理的索引值 (小于文件大小)
print('查找索引表中所有合理的偏移值:')
valid_count = 0
invalid_count = 0
for i in range(553):
    offset = 10 + i * 4
    val = struct.unpack('<I', data[offset:offset+4])[0]
    if val < file_size:
        valid_count += 1
    else:
        invalid_count += 1

print(f'  有效索引: {valid_count}')
print(f'  无效索引: {invalid_count}')

# 看看索引表是不是有不同的结构
# 可能是2字节索引而不是4字节？
print('\n尝试2字节索引:')
for i in range(10):
    offset = 10 + i * 2
    val = struct.unpack('<H', data[offset:offset+2])[0]
    print(f'  索引[{i}] (偏移{offset}): {val} (0x{val:04x})')

# 或者索引表有特殊的分隔符
# 检查文件头的实际结构
print('\nDATO.DAT文件头详细分析:')
print(f'  字节0-5: {" ".join(f"0x{b:02x}" for b in data[:6])}')
print(f'  字节6-9: {" ".join(f"0x{b:02x}" for b in data[6:10])}')
count = struct.unpack('<I', data[6:10])[0]
print(f'  count = {count}')

# 检查从索引0到索引20的连续4字节值
print('\n检查索引表连续性:')
prev = None
for i in range(20):
    offset = 10 + i * 4
    val = struct.unpack('<I', data[offset:offset+4])[0]
    if prev is not None:
        diff = val - prev
        print(f'  索引[{i}] = {val}, 差值 = {diff}')
    else:
        print(f'  索引[{i}] = {val}')
    prev = val

# 看看索引表是否以某个特殊值结束
# 检查索引552和553
print('\n检查最后几个索引:')
for i in range(549, 554):
    offset = 10 + i * 4
    if offset + 4 <= len(data):
        val = struct.unpack('<I', data[offset:offset+4])[0]
        print(f'  索引[{i}] (偏移{offset}): {val} (0x{val:08x})')
