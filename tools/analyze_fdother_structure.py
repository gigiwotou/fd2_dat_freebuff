import struct

data = open('game/FDOTHER.DAT', 'rb').read()

# 查看文件头
print(f'FDOTHER.DAT总大小: {len(data)}')
print(f'文件头前16字节: {data[:16].hex(" ")}')

# 尝试解析为：4字节魔数 + 2字节索引数量
magic = data[:4]
count = struct.unpack('<H', data[4:6])[0]
print(f'\n假设结构: 4字节魔数 + 2字节索引数量')
print(f'魔数: {magic}')
print(f'索引数量: {count}')

# 如果索引数量是19532，那肯定不对
if count > 1000:
    print(f'\n索引数量{count}太大，重新解析...')
    # 尝试：4字节魔数 + 4字节索引数量
    count = struct.unpack('<I', data[4:8])[0]
    print(f'4字节索引数量: {count}')
    
# 查看索引表结构
if count <= 200:
    print(f'\n索引表（每个索引4字节）:')
    for i in range(min(count, 50)):
        off = struct.unpack('<I', data[6 + i*4:6 + i*4 + 4])[0]
        if i + 1 < count:
            next_off = struct.unpack('<I', data[6 + (i+1)*4:6 + (i+1)*4 + 4])[0]
        else:
            next_off = len(data)
        
        size = next_off - off
        header = data[off:off+min(8, size)]
        
        print(f'索引{i:2d}: 偏移={off:8d} (0x{off:06X}), 大小={size:8d} (0x{size:06X}), 前8字节: {header.hex(" ")}')
