import struct

data = open('game/FDOTHER.DAT', 'rb').read()

# 查看文件头
print(f'FDOTHER.DAT总大小: {len(data)}')
print(f'文件头前20字节: {data[:20].hex(" ")}')

# 前6字节是"LLLLLL"，这可能是魔数
# 从第6字节开始应该是索引表
# 尝试解析：前6字节是魔数，后面每4字节一个索引

# 假设索引数量 = (文件大小 - 6) / 4 不太可能
# 查看索引数量在哪里

# 查看0x1A6处的内容（之前发现的索引0偏移）
idx0_offset = 0x1A6
print(f'\n索引0位置0x1A6处的内容: {data[idx0_offset:idx0_offset+8].hex(" ")}')

# 尝试：索引表从第6字节开始，到索引0之前
# 索引表大小 = 0x1A6 - 6 = 0x1A0 = 416字节
# 索引数量 = 416 / 4 = 104个索引

idx_table_size = idx0_offset - 6
idx_count = idx_table_size // 4
print(f'\n索引表大小: {idx_table_size}字节 (0x{idx_table_size:X})')
print(f'索引数量: {idx_count}')

# 读取所有索引
print(f'\n所有{idx_count}个索引:')
for i in range(idx_count):
    off = struct.unpack('<I', data[6 + i*4:6 + i*4 + 4])[0]
    if i + 1 < idx_count:
        next_off = struct.unpack('<I', data[6 + (i+1)*4:6 + (i+1)*4 + 4])[0]
    else:
        next_off = idx0_offset  # 第一个索引位置
    
    size = next_off - off
    header = data[off:off+min(8, size)]
    
    print(f'索引{i:2d}: 偏移={off:8d} (0x{off:06X}), 大小={size:8d} (0x{size:06X}), 前8字节: {header.hex(" ")}')
