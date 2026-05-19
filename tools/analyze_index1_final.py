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

print('索引1结构详细分析')
print(f'大小: {size} bytes\n')

# 显示前0x50字节
print('前0x50字节:')
for i in range(0, 0x50, 16):
    chunk = data[i:i+16]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    print(f'  0x{i:04X}: {hex_str}')
print()

# 从0x46开始是4字节资源表
print('4字节资源偏移表 (0x46开始):')
num_entries = (len(data) - 0x46) // 4
print(f'总条目数: {num_entries}\n')

# 显示前30个条目
print('前30个条目:')
for i in range(min(30, num_entries)):
    off = 0x46 + i * 4
    val = struct.unpack('<I', data[off:off+4])[0]
    print(f'  [{i:3d}] 0x{off:06X} -> 0x{val:06X}')
print()

# 检查201, 205, 514, 549, 550
print('目标资源ID:')
for rid in [201, 205, 514, 549, 550]:
    if rid < num_entries:
        table_off = 0x46 + rid * 4
        res_off = struct.unpack('<I', data[table_off:table_off+4])[0]
        print(f'  资源ID {rid:3d}: 表位置0x{table_off:06X}, 偏移0x{res_off:06X}')
print()

fd.close()
