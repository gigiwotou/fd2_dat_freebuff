import struct

data = open('game/FDOTHER.DAT', 'rb').read()
off4 = struct.unpack('<I', data[10 + 4*4:10 + 4*4 + 4])[0]
off5 = struct.unpack('<I', data[10 + 5*4:10 + 5*4 + 4])[0]
res4 = data[off4:off5]

print(f'索引4大小: {len(res4)}')
print(f'索引4魔数: {res4[:4]}')

if res4[:4] == b'LMI1':
    count = struct.unpack('<H', res4[4:6])[0]
    print(f'子资源数量: {count}')
    
    # 分析所有子资源的尺寸
    base_offset = 6
    sizes_16x16 = []
    sizes_24x24 = []
    other_sizes = []
    
    for i in range(count):
        off = struct.unpack('<I', res4[base_offset + i*4:base_offset + i*4 + 4])[0]
        if i + 1 < count:
            next_off = struct.unpack('<I', res4[base_offset + (i+1)*4:base_offset + (i+1)*4 + 4])[0]
        else:
            next_off = len(res4)
        
        sub_data = res4[off:next_off]
        if len(sub_data) >= 4:
            w = struct.unpack('<H', sub_data[0:2])[0]
            h = struct.unpack('<H', sub_data[2:4])[0]
            
            if w == 16 and h == 16:
                sizes_16x16.append(i)
            elif w == 24 and h == 24:
                sizes_24x24.append(i)
            else:
                other_sizes.append((i, w, h))
    
    print(f'\n16x16子资源索引: {sizes_16x16}')
    print(f'24x24子资源索引: {sizes_24x24}')
    print(f'其他尺寸: {other_sizes[:20]}')
    
    # 查看第一个16x16子资源
    if sizes_16x16:
        idx = sizes_16x16[0]
        off = struct.unpack('<I', res4[base_offset + idx*4:base_offset + idx*4 + 4])[0]
        if idx + 1 < count:
            next_off = struct.unpack('<I', res4[base_offset + (idx+1)*4:base_offset + (idx+1)*4 + 4])[0]
        else:
            next_off = len(res4)
        
        sub_data = res4[off:next_off]
        print(f'\n16x16字体资源{idx}数据(前64字节): {sub_data[:64].hex(" ")}')
        print(f'总大小: {len(sub_data)}')
