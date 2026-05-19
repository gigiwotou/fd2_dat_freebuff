import struct
import sys

filename = 'd:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT'
with open(filename, 'rb') as f:
    data = f.read()

# FDOTHER.DAT标准格式:
# 0x00-0x05: "LLLLLL" 魔术
# 0x06-0x09: 资源数量 (422)
# 0x0A-...: 偏移表

num_resources = struct.unpack('<I', data[6:10])[0]
print(f'资源总数: {num_resources}')

# 分析资源1和13
for rid in [1, 13]:
    offset_table_pos = 0x0A + rid * 4
    start = struct.unpack('<I', data[offset_table_pos:offset_table_pos+4])[0]
    end = struct.unpack('<I', data[offset_table_pos+4:offset_table_pos+8])[0]
    size = end - start
    
    print(f'\n资源{rid}:')
    print(f'  起始位置: 0x{start:X}')
    print(f'  大小: {size} bytes')
    
    # 资源1内部可能有嵌套的偏移表
    if rid == 1:
        # 查看前100个4字节值
        print(f'  前20个4字节值:')
        for i in range(20):
            off = start + i * 4
            val = struct.unpack('<I', data[off:off+4])[0]
            print(f'    [{i:2d}] @ 0x{off-start:X} = 0x{val:X} ({val})')
