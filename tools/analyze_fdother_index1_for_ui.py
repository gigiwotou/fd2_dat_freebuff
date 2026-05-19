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

print('=== FDOTHER.DAT索引1结构分析 ===')
print(f'大小: {size} bytes\n')

# 索引1的结构：前0x46字节是头部，从0x46开始是2字节偏移表
print('头部 (前0x46字节):')
for i in range(0, 0x46, 2):
    if i + 2 <= len(data):
        val = struct.unpack('<H', data[i:i+2])[0]
        if i % 8 == 0:
            print(f'  0x{i:04X}: ', end='')
        print(f'{val:04X} ', end='')
        if (i + 2) % 8 == 0:
            print()
print()

# 检查0x46处的值
print(f'偏移0x46处的值: 0x{struct.unpack("<H", data[0x46:0x48])[0]:04X}')
print()

# 从0x46开始是2字节偏移表
print('从0x46开始的2字节偏移表 (前20项):')
for i in range(20):
    table_off = 0x46 + i * 2
    if table_off + 2 <= len(data):
        val = struct.unpack('<H', data[table_off:table_off+2])[0]
        print(f'  资源[{i:3d}] 0x{table_off:04X} -> 0x{val:04X}')
print()

# 保存索引1的数据用于后续分析
out_file = 'd:/workspace/fd2_dat_freebuff/output/fdother_index1.bin'
with open(out_file, 'wb') as out:
    out.write(data)
print(f'已保存索引1到: {out_file}\n')

# 检查特定资源ID
print('=== 保存槽位UI相关资源 ===')
target_ids = [201, 205, 514, 549, 550]
for rid in target_ids:
    table_off = 0x46 + rid * 2
    if table_off + 2 <= len(data):
        res_off = struct.unpack('<H', data[table_off:table_off+2])[0]
        
        next_table_off = 0x46 + (rid + 1) * 2
        if next_table_off + 2 <= len(data):
            next_res_off = struct.unpack('<H', data[next_table_off:next_table_off+2])[0]
            res_size = next_res_off - res_off
        else:
            res_size = len(data) - res_off
        
        print(f'\n资源ID {rid}:')
        print(f'  表位置: 0x{table_off:04X}')
        print(f'  资源偏移: 0x{res_off:04X}')
        print(f'  大小: {res_size} bytes')
        
        if res_off < len(data) and res_size > 0:
            # 保存资源
            res_file = f'd:/workspace/fd2_dat_freebuff/output/resource_{rid}.bin'
            with open(res_file, 'wb') as out:
                out.write(data[res_off:res_off + res_size])
            print(f'  已保存: {res_file}')
            
            # 分析资源内容
            print(f'  前64字节:')
            chunk = data[res_off:res_off+min(64, res_size)]
            for j in range(0, len(chunk), 16):
                hex_str = ' '.join(f'{chunk[j+k]:02X}' for k in range(min(16, len(chunk)-j)))
                print(f'    0x{res_off+j:04X}: {hex_str}')

fd.close()
