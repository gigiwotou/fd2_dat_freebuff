import struct

fd = open('d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT', 'rb')

# 读取文件头
fd.seek(6)
count = struct.unpack('<H', fd.read(2))[0]

# 读取索引1
fd.seek(10 + 1 * 4)
offset_idx1 = struct.unpack('<I', fd.read(4))[0]
next_offset = struct.unpack('<I', fd.read(4))[0]
size = next_offset - offset_idx1

fd.seek(offset_idx1)
data = fd.read(size)

print(f'索引1大小: {size} bytes')
print()

# 分析前4字节
first_dword = struct.unpack('<I', data[0:4])[0]
print(f'前4字节: 0x{first_dword:08X}')
print()

# 从偏移0x46开始分析
print('从偏移0x46开始分析:')
for i in range(0, min(200, len(data) - 0x46), 2):
    val = struct.unpack('<H', data[0x46 + i:0x46 + i + 2])[0]
    if i % 20 == 0:
        print(f'\n  偏移0x{0x46 + i:04X}: ', end='')
    print(f'{val:04X} ', end='')
print()
print()

# 尝试作为精灵资源表分析
# 每个精灵可能有固定大小或变长
print('尝试作为精灵资源表 (每64字节一个资源):')
for i in range(10):
    start = 0x46 + i * 64
    if start + 4 <= len(data):
        w = struct.unpack('<H', data[start:start+2])[0]
        h = struct.unpack('<H', data[start+2:start+4])[0]
        print(f'  资源[{i}]: 偏移0x{start:04X}, 宽={w}, 高={h}')
print()

# 检查特定偏移的内容
print('检查偏移0x38, 0x3A, 0x3C, 0x3E处的值:')
for off in [0x38, 0x3A, 0x3C, 0x3E, 0x40, 0x42, 0x44, 0x46]:
    if off + 2 <= len(data):
        val = struct.unpack('<H', data[off:off+2])[0]
        print(f'  偏移0x{off:04X}: 0x{val:04X} ({val})')
print()

fd.close()
