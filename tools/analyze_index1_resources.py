import struct

fd = open('d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT', 'rb')

# 读取文件头
fd.seek(0)
magic = fd.read(6)
fd.seek(6)
count = struct.unpack('<H', fd.read(2))[0]

print(f'FDOTHER.DAT索引数: {count}')
print()

# 读取索引1
idx = 1
fd.seek(10 + idx * 4)
offset_idx1 = struct.unpack('<I', fd.read(4))[0]
next_offset_idx1 = struct.unpack('<I', fd.read(4))[0]
size_idx1 = next_offset_idx1 - offset_idx1

print(f'索引1详细信息:')
print(f'  偏移: 0x{offset_idx1:06X} ({offset_idx1})')
print(f'  大小: {size_idx1} bytes')
print()

# 读取索引1的数据
fd.seek(offset_idx1)
data_idx1 = fd.read(size_idx1)

# 分析前200字节，查看是否是偏移表
print('索引1前100字节 (hex):')
for i in range(0, min(100, len(data_idx1)), 16):
    hex_str = ' '.join(f'{data_idx1[i+j]:02X}' for j in range(min(16, len(data_idx1)-i)))
    ascii_str = ''.join(chr(data_idx1[i+j]) if 32 <= data_idx1[i+j] < 127 else '.' for j in range(min(16, len(data_idx1)-i)))
    print(f'  0x{i:04X}: {hex_str:<48s} {ascii_str}')
print()

# 读取4字节表（偏移表）
print('索引1的4字节偏移表 (前30项):')
for i in range(min(30, len(data_idx1) // 4)):
    val = struct.unpack('<I', data_idx1[i*4:i*4+4])[0]
    print(f'  索引[{i:3d}] = 0x{val:06X} ({val:6d})')
print()

# 检查资源ID 201, 205, 514, 549, 550
print('检查特定资源ID:')
check_ids = [201, 205, 514, 549, 550]
for rid in check_ids:
    if rid < len(data_idx1) // 4:
        offset = struct.unpack('<I', data_idx1[rid*4:rid*4+4])[0]
        next_off = struct.unpack('<I', data_idx1[(rid+1)*4:(rid+1)*4+4])[0] if rid+1 < len(data_idx1)//4 else size_idx1
        res_size = next_off - offset
        print(f'  资源ID {rid:3d}: 偏移=0x{offset:06X}, 大小={res_size} bytes')
        
        # 读取该资源的前32字节
        if offset < len(data_idx1):
            chunk = data_idx1[offset:offset+32]
            hex_str = ' '.join(f'{b:02X}' for b in chunk)
            print(f'            内容: {hex_str}')
print()

fd.close()
