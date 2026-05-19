import struct

fd = open('d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT', 'rb')

# 读取文件头
fd.seek(6)
count = struct.unpack('<H', fd.read(2))[0]
print(f'FDOTHER.DAT索引数: {count}\n')

# 读取索引1
fd.seek(10 + 1 * 4)
offset_idx1 = struct.unpack('<I', fd.read(4))[0]
next_offset = struct.unpack('<I', fd.read(4))[0]
size = next_offset - offset_idx1

print(f'索引1信息:')
print(f'  文件偏移: 0x{offset_idx1:06X} ({offset_idx1})')
print(f'  大小: {size} bytes')
print(f'  下一个索引偏移: 0x{next_offset:06X}\n')

fd.seek(offset_idx1)
data = fd.read(size)

# 分析前100字节
print('索引1前100字节:')
for i in range(0, min(100, len(data)), 16):
    hex_str = ' '.join(f'{data[i+j]:02X}' for j in range(min(16, len(data)-i)))
    ascii_str = ''.join(chr(data[i+j]) if 32 <= data[i+j] < 127 else '.' for j in range(min(16, len(data)-i)))
    print(f'  0x{i:04X}: {hex_str:<48s} {ascii_str}')
print()

# 尝试解析为2字节索引表
# 从sub_15F84代码看：v15 = (__int16 *)(*(arg0 + 2 * arg4) + arg0)
# 这意味着arg0是一个包含2字节偏移的表
print('解析为2字节偏移表:')
print('(每个条目2字节，表示该资源在索引1内的偏移)')
print()

# 检查前20个条目
print('前20个条目:')
for i in range(20):
    off = i * 2
    if off + 2 <= len(data):
        val = struct.unpack('<H', data[off:off+2])[0]
        print(f'  条目[{i:2d}] (偏移0x{off:04X}): 0x{val:04X} ({val})')
print()

# 检查特定资源ID
target_ids = [201, 205, 514, 549, 550]
print('特定资源ID:')
for rid in target_ids:
    table_off = rid * 2
    if table_off + 2 <= len(data):
        res_off = struct.unpack('<H', data[table_off:table_off+2])[0]
        print(f'  资源ID {rid:3d}: 表偏移0x{table_off:04X}, 资源偏移0x{res_off:04X} ({res_off})')
        
        # 获取下一个资源偏移计算大小
        next_table_off = (rid + 1) * 2
        if next_table_off + 2 <= len(data):
            next_res_off = struct.unpack('<H', data[next_table_off:next_table_off+2])[0]
            res_size = next_res_off - res_off
        else:
            res_size = len(data) - res_off
        
        print(f'    资源大小: {res_size} bytes')
        
        # 如果资源偏移有效，读取内容
        if res_off < len(data):
            # 显示前32字节
            chunk = data[res_off:res_off+32]
            hex_str = ' '.join(f'{b:02X}' for b in chunk)
            print(f'    前32字节: {hex_str}')
            
            # 尝试解析为图像（前2字节宽，接下来2字节高）
            if res_size >= 4:
                w = struct.unpack('<H', data[res_off:res_off+2])[0]
                h = struct.unpack('<H', data[res_off+2:res_off+4])[0]
                print(f'    可能的尺寸: 宽{w} x 高{h}')
                
                # 显示像素数据（假设从偏移4开始）
                if w > 0 and h > 0 and w < 400 and h < 300:
                    pixel_off = res_off + 4
                    print(f'    像素数据:')
                    for row in range(min(3, h)):
                        row_off = pixel_off + row * w
                        if row_off + min(20, w) <= len(data):
                            row_data = data[row_off:row_off + min(20, w)]
                            row_hex = ' '.join(f'{b:02X}' for b in row_data)
                            print(f'      行{row}: {row_hex}')
        print()

fd.close()
