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

print('=== FDOTHER.DAT索引1完整分析 ===')
print(f'大小: {size} bytes')
print()

# 分析前70字节
print('前70字节 (hex):')
for i in range(0, 70, 16):
    chunk = data[i:i+16]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    print(f'  0x{i:04X}: {hex_str}')
print()

# 前4字节
print('前4字节解析:')
val0 = struct.unpack('<I', data[0:4])[0]
print(f'  dword[0] = 0x{val0:08X} = {val0}')
print()

# 检查0x38, 0x3A, 0x3C等位置
print('特定偏移:')
for off in [0x38, 0x3A, 0x3C, 0x3E, 0x40, 0x42, 0x44, 0x46]:
    if off + 2 <= len(data):
        val = struct.unpack('<H', data[off:off+2])[0]
        print(f'  0x{off:04X}: 0x{val:04X} ({val})')
print()

# 从0x46开始是2字节偏移表
print('从0x46开始的2字节偏移表:')
for i in range(20):
    off = 0x46 + i * 2
    if off + 2 <= len(data):
        val = struct.unpack('<H', data[off:off+2])[0]
        print(f'  [{i:2d}] 0x{off:04X} -> 0x{val:04X}')
print()

# 检查资源ID 201, 205等
print('目标资源ID:')
for rid in [201, 205, 514, 549, 550]:
    table_off = 0x46 + rid * 2
    if table_off + 2 <= len(data):
        res_off = struct.unpack('<H', data[table_off:table_off+2])[0]
        print(f'  ID {rid:3d}: 表位置0x{table_off:04X}, 值=0x{res_off:04X}')
        
        # 获取资源数据
        if res_off < len(data):
            # 读取前32字节
            chunk = data[res_off:res_off+min(32, len(data)-res_off)]
            hex_str = ' '.join(f'{b:02X}' for b in chunk)
            print(f'           数据: {hex_str}')
print()

fd.close()
