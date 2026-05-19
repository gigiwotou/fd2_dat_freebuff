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
print(f'4字节表项数: {size // 4}')
print()

# 分析为4字节偏移表
print('索引1作为4字节偏移表:')
print('前15项:')
for i in range(min(15, len(data) // 4)):
    val = struct.unpack('<I', data[i*4:i*4+4])[0]
    print(f'  索引[{i:3d}] = 0x{val:06X} ({val:6d})')
print()

# 检查特定资源ID
print('检查特定资源ID:')
check_ids = [0, 1, 2, 3, 4, 5, 6, 7, 201, 205, 514, 549, 550]
for rid in check_ids:
    if rid < len(data) // 4:
        offset = struct.unpack('<I', data[rid*4:rid*4+4])[0]
        if rid + 1 < len(data) // 4:
            next_off = struct.unpack('<I', data[(rid+1)*4:(rid+1)*4+4])[0]
            res_size = next_off - offset
        else:
            res_size = size - offset
        
        print(f'  资源ID {rid:3d}: 偏移=0x{offset:06X} ({offset:6d}), 大小={res_size:6d} bytes')
        
        # 读取该资源的前64字节
        if offset < len(data) and res_size > 0:
            chunk_size = min(64, res_size, len(data) - offset)
            chunk = data[offset:offset+chunk_size]
            
            # 显示hex
            hex_lines = []
            for j in range(0, chunk_size, 16):
                line = chunk[j:j+16]
                hex_str = ' '.join(f'{b:02X}' for b in line)
                ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in line)
                hex_lines.append(f'    {hex_str:<48s} {ascii_str}')
            
            if hex_lines:
                print(f'            内容:')
                for line in hex_lines[:3]:  # 只显示前3行
                    print(line)
                if chunk_size > 48:
                    print(f'            ... (共{chunk_size} bytes)')
            print()
print()

# 检查资源1到10的大小规律
print('资源1到10的大小:')
for rid in range(1, 11):
    if rid < len(data) // 4:
        offset = struct.unpack('<I', data[rid*4:rid*4+4])[0]
        if rid + 1 < len(data) // 4:
            next_off = struct.unpack('<I', data[(rid+1)*4:(rid+1)*4+4])[0]
            res_size = next_off - offset
        else:
            res_size = size - offset
        print(f'  资源ID {rid:2d}: 大小={res_size:6d} bytes')
print()

fd.close()
