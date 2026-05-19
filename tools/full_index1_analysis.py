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

print('索引1完整结构分析')
print(f'大小: {size} bytes')
print()

# 前70字节是头部
print('头部70字节:')
for i in range(0, 70, 2):
    val = struct.unpack('<H', data[i:i+2])[0]
    print(f'  偏移0x{i:04X}: 0x{val:04X} ({val})')
print()

# 从0x46开始是4字节索引表
print('从0x46开始的4字节索引表 (前30项):')
for i in range(30):
    off = 0x46 + i * 4
    if off + 4 <= len(data):
        val = struct.unpack('<I', data[off:off+4])[0]
        print(f'  [{i:3d}] 0x{off:06X}: 0x{val:08X} ({val})')
print()

# 特定资源ID
print('特定资源ID:')
for rid in [201, 205, 514, 549, 550]:
    off = 0x46 + rid * 4
    if off + 4 <= len(data):
        val = struct.unpack('<I', data[off:off+4])[0]
        print(f'  资源ID {rid}: 偏移0x{off:06X}, 值=0x{val:08X}')
print()

fd.close()
