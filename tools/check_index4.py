import struct
import os

dat_path = 'bin/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    magic = f.read(4)
    tile_count = struct.unpack('<H', f.read(2))[0]
    
    offsets = []
    for i in range(tile_count):
        offset = struct.unpack('<I', f.read(4))[0]
        offsets.append(offset)
    
    # 检查索引4
    print(f"索引4的文件偏移: 0x{offsets[4]:X}")
    print(f"索引5的文件偏移: 0x{offsets[5]:X}")
    print(f"索引4的大小: {offsets[5] - offsets[4]} 字节")
    
    f.seek(offsets[4])
    res_size = offsets[5] - offsets[4]
    res_data = f.read(res_size)
    
    print(f"\n索引4资源大小: {res_size} 字节")
    print(f"前4字节: {res_data[:4]}")
    
    if res_data[:4] == b'LMI1':
        inner_count = struct.unpack('<H', res_data[4:6])[0]
        print(f"Tile数量: {inner_count}")
        
        print("\n前20个tile的尺寸:")
        for i in range(min(20, inner_count)):
            offset = struct.unpack('<I', res_data[6 + i*4:10 + i*4])[0]
            if offset < res_size:
                w = struct.unpack('<H', res_data[offset:offset+2])[0]
                h = struct.unpack('<H', res_data[offset+2:offset+4])[0]
                print(f"  Tile {i}: {w}x{h} (偏移: 0x{offset:X})")
            else:
                print(f"  Tile {i}: 偏移0x{offset:X} 超出范围")
