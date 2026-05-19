import struct

fd = open('d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT', 'rb')

# 读取索引1
fd.seek(10 + 1 * 4)
offset_idx1 = struct.unpack('<I', fd.read(4))[0]
next_offset = struct.unpack('<I', fd.read(4))[0]
size = next_offset - offset_idx1

fd.seek(offset_idx1)
data = fd.read(size)

print(f'索引1大小: {size} bytes')
print()

# 分析为2字节偏移表
print('索引1作为2字节偏移表 (前50项):')
for i in range(min(50, len(data) // 2)):
    val = struct.unpack('<H', data[i*2:i*2+2])[0]
    if i % 10 == 0:
        print()
    print(f'  [{i:3d}]=0x{val:04X}', end='')
print('\n')

# 检查资源ID 201, 205, 514, 549, 550
print('检查特定资源ID (作为2字节表索引):')
check_ids = [201, 205, 514, 549, 550]
for rid in check_ids:
    if rid * 2 + 2 <= len(data):
        offset = struct.unpack('<H', data[rid*2:rid*2+2])[0]
        next_off = struct.unpack('<H', data[(rid+1)*2:(rid+1)*2+2])[0] if rid+1 < len(data)//2 else size
        print(f'  资源ID {rid:3d}: 偏移=0x{offset:04X} ({offset}), 下一偏移=0x{next_off:04X}')
        
        # 读取该偏移的内容
        if offset < len(data):
            end_offset = min(next_off, len(data))
            chunk_size = min(32, end_offset - offset)
            chunk = data[offset:offset+chunk_size]
            hex_str = ' '.join(f'{b:02X}' for b in chunk)
            print(f'            内容 ({chunk_size} bytes): {hex_str}')
print()

# 检查资源ID 1-10
print('检查资源ID 1-10:')
for rid in range(1, 11):
    if rid * 2 + 2 <= len(data):
        offset = struct.unpack('<H', data[rid*2:rid*2+2])[0]
        next_off = struct.unpack('<H', data[(rid+1)*2:(rid+1)*2+2])[0]
        res_size = next_off - offset
        print(f'  资源ID {rid:2d}: 偏移=0x{offset:04X}, 大小={res_size} bytes')
print()

fd.close()
