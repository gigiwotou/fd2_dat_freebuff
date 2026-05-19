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

print('FDOTHER.DAT索引1完整结构分析')
print(f'索引1大小: {size} bytes')
print()

# 显示前100字节
print('索引1前100字节:')
for i in range(0, min(100, len(data)), 16):
    chunk = data[i:i+16]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    print(f'  0x{i:04X}: {hex_str:<48s} {ascii_str}')
print()

# 前2字节可能是某种计数
count_val = struct.unpack('<H', data[0:2])[0]
print(f'前2字节: 0x{count_val:04X} = {count_val}')
print()

# 从0x46开始是2字节偏移表
print('从0x46开始的2字节偏移表:')
for i in range(30):
    table_off = 0x46 + i * 2
    if table_off + 2 <= len(data):
        val = struct.unpack('<H', data[table_off:table_off+2])[0]
        if i % 10 == 0:
            print()
        print(f'  [{i:3d}] 0x{table_off:04X}=0x{val:04X}', end='')
print()
print()

# 检查资源ID 201, 205, 514, 549, 550
print('目标资源ID:')
for rid in [201, 205, 514, 549, 550]:
    table_off = 0x46 + rid * 2
    if table_off + 2 <= len(data):
        res_off = struct.unpack('<H', data[table_off:table_off+2])[0]
        print(f'  ID {rid:3d}: 表位置0x{table_off:04X}, 偏移0x{res_off:04X}')
        
        # 获取资源数据
        if res_off < len(data):
            next_table_off = 0x46 + (rid + 1) * 2
            if next_table_off + 2 <= len(data):
                next_res_off = struct.unpack('<H', data[next_table_off:next_table_off+2])[0]
                res_size = next_res_off - res_off
            else:
                res_size = len(data) - res_off
            
            print(f'        大小: {res_size} bytes')
            
            # 保存资源
            if res_size > 0:
                out_file = f'd:/workspace/fd2_dat_freebuff/output/resource_{rid}.bin'
                with open(out_file, 'wb') as out:
                    out.write(data[res_off:res_off + res_size])
                print(f'        已保存: {out_file}')
                
                # 显示内容
                chunk = data[res_off:res_off+min(64, res_size)]
                print(f'        前64字节:')
                for j in range(0, len(chunk), 16):
                    hex_str = ' '.join(f'{chunk[j+k]:02X}' for k in range(min(16, len(chunk)-j)))
                    print(f'          0x{res_off+j:04X}: {hex_str}')
        print()

fd.close()
