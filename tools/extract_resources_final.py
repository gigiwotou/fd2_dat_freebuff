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

print('索引1完整结构分析')
print(f'大小: {size} bytes\n')

# 索引1的结构：
# 前0x46字节是头部信息
# 从0x46开始是4字节资源偏移表

print('头部信息 (前0x46字节):')
for i in range(0, 0x46, 4):
    if i + 4 <= len(data):
        val = struct.unpack('<I', data[i:i+4])[0]
        print(f'  0x{i:04X}: 0x{val:08X}')
print()

print('从0x46开始的4字节资源偏移表:')
print('(每个条目是一个资源的偏移量)')
for i in range(min(20, (len(data) - 0x46) // 4)):
    off = 0x46 + i * 4
    val = struct.unpack('<I', data[off:off+4])[0]
    print(f'  资源[{i:3d}] 0x{off:06X}: 0x{val:06X}')
print()

# 检查特定资源
print('特定资源ID:')
for rid in [201, 205, 514, 549, 550]:
    table_off = 0x46 + rid * 4
    if table_off + 4 <= len(data):
        res_off = struct.unpack('<I', data[table_off:table_off+4])[0]
        print(f'\n  资源ID {rid}:')
        print(f'    表位置: 0x{table_off:06X}')
        print(f'    资源偏移: 0x{res_off:06X}')
        
        # 获取下一个资源
        next_table_off = 0x46 + (rid + 1) * 4
        if next_table_off + 4 <= len(data):
            next_res_off = struct.unpack('<I', data[next_table_off:next_table_off+4])[0]
            res_size = next_res_off - res_off
        else:
            res_size = size - res_off
        
        print(f'    资源大小: {res_size} bytes')
        
        if res_off < size and res_size > 0:
            # 保存资源
            out_file = f'd:/workspace/fd2_dat_freebuff/output/resource_{rid}.bin'
            with open(out_file, 'wb') as out:
                out.write(data[res_off:res_off + res_size])
            print(f'    已保存: {out_file}')
            
            # 分析资源内容
            chunk = data[res_off:res_off+min(64, res_size)]
            print(f'    前64字节:')
            for j in range(0, len(chunk), 16):
                hex_str = ' '.join(f'{chunk[j+k]:02X}' for k in range(min(16, len(chunk)-j)))
                print(f'      0x{res_off+j:06X}: {hex_str}')

fd.close()
