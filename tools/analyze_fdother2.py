import struct

filepath = 'game/FDOTHER.DAT'

with open(filepath, 'rb') as f:
    file_size = f.seek(0, 2)
    f.seek(0)
    
    print(f'=== FDOTHER.DAT 分析 ===')
    print(f'文件大小: {file_size} 字节')
    
    # 读取前100字节查看原始数据
    f.seek(0)
    raw = f.read(100)
    print(f'前100字节(hex):')
    for i in range(0, 100, 16):
        hex_str = ' '.join(f'{b:02x}' for b in raw[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in raw[i:i+16])
        print(f'  {i:04x}: {hex_str:<48s} {ascii_str}')
    
    # 分析可能的结构
    print(f'\n=== 可能的解析方式 ===')
    
    # 方式1: 偏移0-5=魔数, 偏移6-9=资源数量, 偏移10开始=偏移表
    magic = raw[:6]
    count1 = struct.unpack('<I', raw[6:10])[0]
    print(f'方式1: 魔数={magic}, 资源数量={count1}')
    
    # 方式2: 偏移0-5=魔数, 偏移6开始就是偏移表（没有资源数量字段）
    # 从偏移6开始读取前几个值
    print(f'方式2: 从偏移6开始直接读取偏移表')
    for i in range(10):
        offset = struct.unpack('<I', raw[6 + i*4:10 + i*4])[0]
        print(f'  索引{i}: 偏移={offset} (0x{offset:X})')
