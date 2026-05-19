import struct

with open('game/FDTXT.DAT', 'rb') as f:
    data = f.read()

file_size = len(data)
count = struct.unpack_from('<I', data, 6)[0]

print('FDTXT.DAT 文件大小:', file_size, '字节')
print('偏移表数量:', count)
print()

# 读取所有偏移
offsets = []
for i in range(count):
    off = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(off)

# 统计有效偏移
valid_offsets = [o for o in offsets if o < file_size]
print('有效偏移数量:', len(valid_offsets))
print('无效偏移数量:', count - len(valid_offsets))
print()

# 检查从索引33开始的数据
print('=== 检查偏移[33]之后的数据 ===')
for i in range(33, min(45, count)):
    off = offsets[i]
    if off < file_size:
        print('偏移[%2d] = 0x%08X (%d) - 有效' % (i, off, off))
    else:
        # 解析为两个WORD
        word0 = off & 0xFFFF
        word1 = (off >> 16) & 0xFFFF
        print('偏移[%2d] = 0x%08X - WORD0=0x%04X (%d), WORD1=0x%04X (%d)' % (i, off, word0, word0, word1, word1))

# 检查偏移33的特殊性
print()
print('=== 偏移33的值 ===')
off33 = offsets[33]
print('偏移[33] = 0x%08X = %d' % (off33, off33))
print('文件大小 = %d' % file_size)
print('偏移[33] == 文件大小?', off33 == file_size)
