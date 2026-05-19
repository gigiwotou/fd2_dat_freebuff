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

print('索引1结构分析')
print(f'大小: {size} bytes\n')

# 分析头部
print('=== 头部 (前0x46字节) ===')
for i in range(0, 0x46, 2):
    if i + 2 <= len(data):
        val = struct.unpack('<H', data[i:i+2])[0]
        if i % 8 == 0:
            print(f'  0x{i:04X}: ', end='')
        print(f'{val:04X} ', end='')
        if (i + 2) % 8 == 0:
            print()
print()

# 从0x46开始是4字节资源偏移表
print('\n=== 资源偏移表 (从0x46开始，4字节/项) ===')
print('(每个条目指向一个资源的起始偏移)')
for i in range(min(30, (len(data) - 0x46) // 4)):
    table_off = 0x46 + i * 4
    res_off = struct.unpack('<I', data[table_off:table_off+4])[0]
    print(f'  [{i:3d}] 0x{table_off:06X} -> 0x{res_off:06X}')
print()

# 特定资源
print('\n=== 保存槽位UI相关资源 ===')
target_ids = [201, 205, 514, 549, 550]
for rid in target_ids:
    table_off = 0x46 + rid * 4
    if table_off + 4 <= len(data):
        res_off = struct.unpack('<I', data[table_off:table_off+4])[0]
        
        next_table_off = 0x46 + (rid + 1) * 4
        if next_table_off + 4 <= len(data):
            next_res_off = struct.unpack('<I', data[next_table_off:next_table_off+4])[0]
            res_size = next_res_off - res_off
        else:
            res_size = size - res_off
        
        print(f'\n资源ID {rid}:')
        print(f'  表偏移: 0x{table_off:06X}')
        print(f'  资源偏移: 0x{res_off:06X}')
        print(f'  大小: {res_size} bytes')
        
        if res_off < size and res_size > 0:
            # 保存
            out_file = f'd:/workspace/fd2_dat_freebuff/output/resource_{rid}.bin'
            with open(out_file, 'wb') as out:
                out.write(data[res_off:res_off + res_size])
            print(f'  已保存: {out_file}')
            
            # 分析内容
            print(f'  前100字节:')
            chunk = data[res_off:res_off+min(100, res_size)]
            for j in range(0, len(chunk), 16):
                hex_str = ' '.join(f'{chunk[j+k]:02X}' for k in range(min(16, len(chunk)-j)))
                ascii_str = ''.join(chr(chunk[j+k]) if 32 <= chunk[j+k] < 127 else '.' for k in range(min(16, len(chunk)-j)))
                print(f'    0x{res_off+j:06X}: {hex_str:<48s} {ascii_str}')

fd.close()
