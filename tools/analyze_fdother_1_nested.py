import struct

filename = 'd:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT'
with open(filename, 'rb') as f:
    data = f.read()

# 资源1起始位置
res1_start = struct.unpack('<I', data[0x0E:0x12])[0]
res1_size = struct.unpack('<I', data[0x12:0x16])[0] - res1_start

print(f'资源1起始: 0x{res1_start:X}, 大小: {res1_size}')

# 资源1内部有嵌套的4字节偏移表
# 第一个值在res1_start
num_entries = struct.unpack('<I', data[res1_start:res1_start+4])[0]
print(f'资源1嵌套条目数: {num_entries}')

# 偏移表从res1_start+4开始
offset_table_start = res1_start + 4

# 分析前20个UI资源
print('\n=== UI资源分析 ===')
for i in range(20):
    entry_off = offset_table_start + i * 4
    entry_off_end = offset_table_start + (i + 1) * 4
    
    if entry_off_end > res1_start + res1_size:
        break
    
    res_offset = struct.unpack('<I', data[entry_off:entry_off+4])[0]
    
    if i + 1 < 100:
        next_res_offset = struct.unpack('<I', data[entry_off+4:entry_off+8])[0]
        res_size = next_res_offset - res_offset
    else:
        res_size = 0
    
    print(f'\n资源[{i}] @ 0x{entry_off-offset_table_start:X}:')
    print(f'  偏移: 0x{res_offset:X}')
    print(f'  大小: {res_size}')
    
    # 显示资源内容
    res_data_start = res1_start + res_offset
    if res_data_start < len(data) and res_size > 0 and res_size < 10000:
        print(f'  内容 (前32字节):')
        for j in range(0, min(32, res_size), 16):
            hex_str = ' '.join(f'{data[res_data_start+j+k]:02X}' for k in range(16) if j+k < res_size)
            print(f'    {j:4d}: {hex_str}')
