import struct

filename = 'd:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT'
with open(filename, 'rb') as f:
    data = f.read()

# 资源1起始位置
res1_start = struct.unpack('<I', data[0x0E:0x12])[0]

# 资源1嵌套条目数
num_entries = struct.unpack('<I', data[res1_start:res1_start+4])[0]
print(f'资源1嵌套条目数: {num_entries}')

# 偏移表从res1_start+4开始
offset_table_start = res1_start + 4

# 查看特定索引的资源
for idx in [0, 1, 2, 3, 4, 5, 10, 50, 74, 75, 76, 77, 78, 100, 150, 200, 201, 202, 205, 206]:
    if idx >= num_entries:
        print(f'\n资源[{idx}]: 超出范围')
        continue
    
    entry_off = offset_table_start + idx * 4
    res_offset = struct.unpack('<I', data[entry_off:entry_off+4])[0]
    
    if idx + 1 < num_entries:
        next_res_offset = struct.unpack('<I', data[entry_off+4:entry_off+8])[0]
        res_size = next_res_offset - res_offset
    else:
        res_size = 0
    
    res_data_start = res1_start + res_offset
    
    # 读取资源头
    if res_data_start + 4 <= len(data):
        width = struct.unpack('<H', data[res_data_start:res_data_start+2])[0]
        height = struct.unpack('<H', data[res_data_start+2:res_data_start+4])[0]
        
        print(f'\n资源[{idx}]:')
        print(f'  偏移: 0x{res_offset:X}')
        print(f'  大小: {res_size}')
        print(f'  尺寸: {width}x{height}')
        print(f'  预期像素大小: {width*height}')
