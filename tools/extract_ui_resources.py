import struct
import sys

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

print(f'索引1大小: {size} bytes')
print()

# 分析前70字节（头部）
print('索引1头部70字节分析:')
for i in range(0, 70, 2):
    val = struct.unpack('<H', data[i:i+2])[0]
    if i % 16 == 0:
        print(f'  偏移0x{i:04X}: ', end='')
    print(f'{val:04X} ', end='')
    if (i + 2) % 16 == 0:
        print()
print()
print()

# 从0x46开始是2字节偏移表
print('从偏移0x46开始的资源偏移表 (前20项):')
for i in range(20):
    offset_in_table = 0x46 + i * 2
    val = struct.unpack('<H', data[offset_in_table:offset_in_table+2])[0]
    print(f'  资源ID {i:3d}: 偏移=0x{val:04X} ({val})')
print()

# 提取资源201, 205, 549, 550
print('提取保存槽位UI相关资源:')
target_ids = [201, 205, 514, 549, 550]
for rid in target_ids:
    offset_in_table = 0x46 + rid * 2
    if offset_in_table + 2 <= len(data):
        res_offset = struct.unpack('<H', data[offset_in_table:offset_in_table+2])[0]
        
        # 获取下一个资源偏移
        next_offset_in_table = 0x46 + (rid + 1) * 2
        if next_offset_in_table + 2 <= len(data):
            next_res_offset = struct.unpack('<H', data[next_offset_in_table:next_offset_in_table+2])[0]
            res_size = next_res_offset - res_offset
        else:
            res_size = len(data) - res_offset
        
        print(f'\n资源ID {rid}:')
        print(f'  偏移表位置: 0x{offset_in_table:04X}')
        print(f'  数据偏移: 0x{res_offset:04X}')
        print(f'  大小: {res_size} bytes')
        
        # 保存原始数据
        if res_offset < len(data) and res_size > 0:
            output_file = f'd:/workspace/fd2_dat_freebuff/output/fdother_index1_resource_{rid}.bin'
            with open(output_file, 'wb') as out:
                out.write(data[res_offset:res_offset + res_size])
            print(f'  已保存: {output_file}')
            
            # 分析资源结构
            if res_size >= 4:
                w = struct.unpack('<H', data[res_offset:res_offset+2])[0]
                h = struct.unpack('<H', data[res_offset+2:res_offset+4])[0]
                print(f'  宽度: {w}, 高度: {h}')
                
                # 显示前几行像素数据
                if w > 0 and w < 400 and h > 0 and h < 300:
                    pixel_data_start = res_offset + 4
                    print(f'  像素数据从偏移0x{pixel_data_start:04X}开始')
                    print(f'  前3行像素:')
                    for row in range(min(3, h)):
                        row_offset = pixel_data_start + row * w
                        if row_offset + w <= len(data):
                            row_data = data[row_offset:row_offset + min(20, w)]
                            hex_str = ' '.join(f'{b:02X}' for b in row_data)
                            print(f'    行{row:2d}: {hex_str}')

fd.close()
