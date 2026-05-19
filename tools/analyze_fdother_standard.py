import struct
import sys

filename = 'd:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT'
with open(filename, 'rb') as f:
    data = f.read()

print(f'文件大小: {len(data)} (0x{len(data):X})')

# 标准DAT格式:
# 0x00: 魔术头 "LLLLLL" (6字节)
# 0x06: 资源数量 (4字节)
# 0x0A: 偏移表 (每个资源4字节)
# 然后是资源数据

magic = data[0:6].decode('ascii', errors='ignore')
print(f'魔术头: "{magic}"')

num_resources = struct.unpack('<I', data[6:10])[0]
print(f'资源数量: {num_resources}')

print('\n=== 关键资源分析 ===')
for rid in [0, 1, 2, 3, 10, 13, 14, 31, 50, 74, 76, 77, 78, 88, 96, 97, 98, 99, 100, 201, 205, 514, 549, 550]:
    if rid >= num_resources:
        print(f'资源{rid}: 超出范围')
        continue
    
    # 偏移表位置: 0x0A + rid*4
    offset_table_pos = 0x0A + rid * 4
    
    if offset_table_pos + 8 > len(data):
        print(f'资源{rid}: 偏移表超出范围')
        continue
    
    start = struct.unpack('<I', data[offset_table_pos:offset_table_pos+4])[0]
    end = struct.unpack('<I', data[offset_table_pos+4:offset_table_pos+8])[0]
    size = end - start
    
    print(f'\n资源{rid}:')
    print(f'  偏移表位置: 0x{offset_table_pos:X}')
    print(f'  start: 0x{start:X} ({start})')
    print(f'  end: 0x{end:X} ({end})')
    print(f'  size: {size} bytes')
    
    if start < len(data) and size > 0 and size < 1000000:
        # 显示前32字节
        print(f'  内容:')
        for i in range(0, min(32, size), 16):
            hex_str = ' '.join(f'{data[start+i+j]:02X}' for j in range(16) if i+j < size)
            print(f'    {i:4d}: {hex_str}')
