import struct
from PIL import Image

data = open('game/FDOTHER.DAT', 'rb').read()

# 解析索引表
print(f'FDOTHER.DAT总大小: {len(data)}')
print(f'索引表偏移: 6 (前6字节可能是魔数+索引数量)')

# 假设前6字节是魔数(4字节) + 索引数量(2字节)
magic = data[:4]
count = struct.unpack('<H', data[4:6])[0]
print(f'魔数: {magic}')
print(f'索引数量: {count}')

# 读取所有索引
for i in range(min(count, 30)):  # 只看前30个
    off_start = struct.unpack('<I', data[6 + i*4:6 + i*4 + 4])[0]
    off_end = struct.unpack('<I', data[6 + (i+1)*4:6 + (i+1)*4 + 4])[0] if i+1 < count else len(data)
    
    size = off_end - off_start
    sub_data = data[off_start:off_start+min(8, size)]
    
    print(f'\n索引{i}: 偏移={off_start} (0x{off_start:X}), 大小={size} (0x{size:X})')
    print(f'  前8字节: {sub_data.hex(" ")}')
    
    # 如果是LMI1格式,显示子资源数量
    if sub_data[:4] == b'LMI1' and len(sub_data) >= 6:
        sub_count = struct.unpack('<H', sub_data[4:6])[0]
        print(f'  LMI1格式, 子资源数量: {sub_count}')
