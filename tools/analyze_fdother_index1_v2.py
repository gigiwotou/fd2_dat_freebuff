import struct

fd = open('d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT', 'rb')

# 读取文件头
fd.seek(6)
count = struct.unpack('<H', fd.read(2))[0]

print(f'FDOTHER.DAT索引数: {count}')
print()

# 读取索引1
idx = 1
fd.seek(10 + idx * 4)
offset = struct.unpack('<I', fd.read(4))[0]
next_offset = struct.unpack('<I', fd.read(4))[0]
size = next_offset - offset

print(f'索引{idx}详细信息:')
print(f'  偏移: 0x{offset:06X} ({offset})')
print(f'  大小: {size} bytes')
print(f'  下一个偏移: 0x{next_offset:06X} ({next_offset})')
print()

# 读取索引1的数据
fd.seek(offset)
data = fd.read(size)

# 分析前16字节
print(f'索引{idx}前16字节:')
hex_str = ' '.join(f'{b:02X}' for b in data[0:16])
print(f'  {hex_str}')
print()

# 假设是2字节偏移表
print('尝试解析为2字节偏移表 (前20项):')
for i in range(min(20, len(data) // 2)):
    off = struct.unpack('<H', data[i*2:i*2+2])[0]
    if i % 5 == 0:
        print()
    print(f'  [{i:3d}]=0x{off:04X}', end='')
print('\n')

# 检查201, 205, 514, 549, 550
print('检查资源ID (2字节表):')
for rid in [201, 205, 514, 549, 550]:
    if rid * 2 + 2 <= len(data):
        offset_val = struct.unpack('<H', data[rid*2:rid*2+2])[0]
        next_val = struct.unpack('<H', data[(rid+1)*2:(rid+1)*2+2])[0]
        print(f'  资源ID {rid:3d}: 偏移=0x{offset_val:04X}, 下一偏移=0x{next_val:04X}')
        
        # 读取该偏移处的内容
        if offset_val < len(data):
            chunk_size = min(32, next_val - offset_val, len(data) - offset_val)
            if chunk_size > 0:
                chunk = data[offset_val:offset_val+chunk_size]
                chunk_hex = ' '.join(f'{b:02X}' for b in chunk)
                print(f'            内容: {chunk_hex}')
print()

# 尝试解析为4字节偏移表
print('尝试解析为4字节偏移表 (前20项):')
for i in range(min(20, len(data) // 4)):
    off = struct.unpack('<I', data[i*4:i*4+4])[0]
    if i % 5 == 0:
        print()
    print(f'  [{i:3d}]=0x{off:06X}', end='')
print('\n')

fd.close()
