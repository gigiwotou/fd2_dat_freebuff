import struct

fd = open('d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT', 'rb')

# 读取文件头
fd.seek(6)
count = struct.unpack('<H', fd.read(2))[0]
print(f'FDOTHER.DAT索引数: {count}')
print()

# 读取索引13
idx = 13
fd.seek(10 + idx * 4)
offset = struct.unpack('<I', fd.read(4))[0]
next_offset = struct.unpack('<I', fd.read(4))[0]
size = next_offset - offset

print(f'索引{idx}详细信息:')
print(f'  偏移: 0x{offset:06X} ({offset})')
print(f'  大小: {size} bytes')
print(f'  下一个偏移: 0x{next_offset:06X} ({next_offset})')
print()

# 读取索引13的数据
fd.seek(offset)
data = fd.read(size)

# 显示前200字节
print(f'索引{idx}前200字节:')
for i in range(0, min(200, len(data)), 16):
    chunk = data[i:i+16]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    print(f'  0x{i:04X}: {hex_str:<48s} {ascii_str}')
print()

# 检查是否是DAT格式
if data[0:6] == b'LLLLLL':
    print('索引13是嵌套DAT文件!')
    nested_count = struct.unpack('<H', data[6:8])[0]
    print(f'  嵌套DAT索引数: {nested_count}')
    
    # 显示嵌套DAT的前10个索引
    print('  嵌套DAT索引表 (前10项):')
    for i in range(min(10, nested_count)):
        off = 10 + i * 4
        if off + 8 > len(data):
            break
        off_start = struct.unpack('<I', data[off:off+4])[0]
        off_end = struct.unpack('<I', data[off+4:off+8])[0]
        nested_size = off_end - off_start
        print(f'    索引[{i:3d}] = 偏移0x{off_start:04X}, 大小{nested_size:6d} bytes')
    
    # 检查嵌套DAT中是否有精灵201, 205等
    print()
    print('  检查嵌套DAT中资源201, 205, 514, 549, 550:')
    for rid in [201, 205, 514, 549, 550]:
        if rid < nested_count:
            off = 10 + rid * 4
            if off + 8 <= len(data):
                off_start = struct.unpack('<I', data[off:off+4])[0]
                off_end = struct.unpack('<I', data[off+4:off+8])[0]
                res_size = off_end - off_start
                print(f'    资源ID {rid:3d}: 偏移=0x{off_start:04X}, 大小={res_size} bytes')
            else:
                print(f'    资源ID {rid:3d}: 偏移表超出范围')
        else:
            print(f'    资源ID {rid:3d}: 超出嵌套DAT索引范围 (最大{nested_count-1})')
else:
    # 检查前2字节是否是宽度
    width = struct.unpack('<H', data[0:2])[0]
    height = struct.unpack('<H', data[2:4])[0] if len(data) >= 4 else 0
    print(f'索引13不是嵌套DAT')
    print(f'  前4字节: 0x{data[0]:02X} {data[1]:02X} {data[2]:02X} {data[3]:02X}')
    print(f'  可能的宽度: {width}, 高度: {height}')
    
    # 检查偏移70处的数据（sub_29BCB使用dword_53F66 + 70）
    if len(data) > 74:
        dword_at_70 = struct.unpack('<I', data[70:74])[0]
        print(f'  偏移70处的DWORD: 0x{dword_at_70:08X} ({dword_at_70})')
        print(f'  dword_53F66 + dword_at_70 = 0x{offset + dword_at_70:06X}')
        
        # 如果dword_at_70是偏移量，读取该位置的数据
        if dword_at_70 < len(data):
            target = offset + dword_at_70
            print(f'  目标位置在文件中的偏移: 0x{target:06X}')
            
            # 读取目标位置的前16字节作为宽度/高度
            fd.seek(target)
            target_data = fd.read(16)
            w = struct.unpack('<H', target_data[0:2])[0]
            h = struct.unpack('<H', target_data[2:4])[0]
            print(f'  目标位置数据: 宽度={w}, 高度={h}')
print()

fd.close()
