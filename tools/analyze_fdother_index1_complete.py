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

print('FDOTHER.DAT索引1完整结构')
print(f'总大小: {size} bytes\n')

# 索引1的结构：
# 头部（前0x46字节）
# 2字节偏移表（从0x46开始）

print('=== 头部信息 ===')
# 0x00-0x03: 某种计数或偏移
dword0 = struct.unpack('<I', data[0:4])[0]
print(f'0x00: dword = 0x{dword0:08X} ({dword0})')

# 显示头部
print('\n头部70字节:')
for i in range(0, 70, 16):
    chunk = data[i:i+16]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    print(f'  0x{i:04X}: {hex_str:<48s} {ascii_str}')
print()

print('=== 2字节偏移表 (从0x46开始) ===')
print('(每个条目2字节，指向资源在索引1内的偏移)')

# 显示前30个条目
for i in range(30):
    table_off = 0x46 + i * 2
    if table_off + 2 <= len(data):
        res_off = struct.unpack('<H', data[table_off:table_off+2])[0]
        print(f'  条目[{i:3d}] 0x{table_off:04X} -> 0x{res_off:04X}')
print()

# 检查特定资源
print('=== 目标资源 ===')
for rid in [201, 205, 514, 549, 550]:
    table_off = 0x46 + rid * 2
    if table_off + 2 <= len(data):
        res_off = struct.unpack('<H', data[table_off:table_off+2])[0]
        print(f'\n资源ID {rid}:')
        print(f'  表位置: 0x{table_off:04X}')
        print(f'  资源偏移: 0x{res_off:04X}')
        
        # 获取资源大小
        next_table_off = 0x46 + (rid + 1) * 2
        if next_table_off + 2 <= len(data):
            next_res_off = struct.unpack('<H', data[next_table_off:next_table_off+2])[0]
            res_size = next_res_off - res_off
        else:
            res_size = size - res_off
        
        print(f'  大小: {res_size} bytes')
        
        if res_off < size and res_size > 0:
            # 保存资源
            out_file = f'd:/workspace/fd2_dat_freebuff/output/resource_{rid}.bin'
            with open(out_file, 'wb') as out:
                out.write(data[res_off:res_off + res_size])
            print(f'  已保存: {out_file}')
            
            # 分析内容
            print(f'  前64字节:')
            chunk = data[res_off:res_off+min(64, res_size)]
            for j in range(0, len(chunk), 16):
                hex_str = ' '.join(f'{chunk[j+k]:02X}' for k in range(min(16, len(chunk)-j)))
                print(f'    0x{res_off+j:04X}: {hex_str}')

fd.close()
