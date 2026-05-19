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

print(f'索引1总大小: {size} bytes')
print()

fd.seek(offset_idx1)
data = fd.read(size)

# 分析前8字节
print('前8字节:')
for i in range(8):
    print(f'  [{i}] = 0x{data[i]:02X}')
print()

# 检查偏移0x46处的值
print('偏移0x46处的值:')
val_46 = struct.unpack('<H', data[0x46:0x48])[0]
print(f'  data[0x46:0x48] = 0x{val_46:04X} ({val_46})')
print()

# 尝试不同的解析方式
print('解析方式1: 前2字节是计数')
count_val = struct.unpack('<H', data[0:2])[0]
print(f'  count = {count_val}')
print()

print('解析方式2: 前4字节是某种表')
dword0 = struct.unpack('<I', data[0:4])[0]
print(f'  dword[0] = 0x{dword0:08X}')
print()

print('解析方式3: 从0x46开始的2字节值表')
for i in range(20):
    off = 0x46 + i * 2
    if off + 2 <= len(data):
        val = struct.unpack('<H', data[off:off+2])[0]
        print(f'  [{i}] offset=0x{off:04X}, value=0x{val:04X} ({val})')
print()

# 检查0x38处的值
print('偏移0x38处的值:')
val_38 = struct.unpack('<H', data[0x38:0x3A])[0]
print(f'  data[0x38:0x3A] = 0x{val_38:04X} ({val_38})')

# 从0x38开始的表
print('\n从0x38开始的2字节表:')
for i in range(10):
    off = 0x38 + i * 2
    if off + 2 <= len(data):
        val = struct.unpack('<H', data[off:off+2])[0]
        print(f'  [{i}] offset=0x{off:04X}, value=0x{val:04X} ({val})')
print()

fd.close()
