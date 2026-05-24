import struct

# 打开FDOTHER.DAT文件
with open('data/FDOTHER.DAT', 'rb') as f:
    # 读取魔术字节
    magic = f.read(4)
    print(f"魔术字节: {magic}")
    
    # 读取tile数量
    tile_count = struct.unpack('<H', f.read(2))[0]
    print(f"Tile总数: {tile_count}")
    
    # 读取偏移表
    offsets = []
    for i in range(tile_count):
        offset = struct.unpack('<I', f.read(4))[0]
        offsets.append(offset)
    
    print(f"\n索引7的偏移: 0x{offsets[7]:X}")
    
    # 跳转到索引7
    f.seek(offsets[7])
    
    # 读取前100字节
    data = f.read(100)
    print(f"\n索引7前100字节（十六进制）:")
    for i in range(0, len(data), 16):
        hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
        print(f"  {i:04X}: {hex_str}")
    
    # 检查是否是LMI1格式
    if data[:4] == b'LMI1':
        print("\n是LMI1格式的tile集！")
        
        # 读取tile数量
        inner_tile_count = struct.unpack('<H', data[4:6])[0]
        print(f"  Tile数量: {inner_tile_count}")
        
        # 读取前10个tile的宽高
        print("\n  前10个tile的尺寸:")
        for i in range(min(10, inner_tile_count)):
            offset_idx = 6 + i * 4
            tile_offset = struct.unpack('<I', data[offset_idx:offset_idx+4])[0]
            
            # 读取宽高（假设在tile数据的开头）
            w = struct.unpack('<H', data[tile_offset:tile_offset+2])[0]
            h = struct.unpack('<H', data[tile_offset+2:tile_offset+4])[0]
            print(f"    Tile {i}: {w}x{h} (偏移: 0x{tile_offset:X})")
    else:
        print(f"\n不是LMI1格式，前4字节: {data[:4]}")
        
        # 尝试直接读取前几个16x16 tile
        print("\n尝试读取前几个tile（假设每个tile是16x16=256字节）:")
        f.seek(offsets[7])
        for i in range(10):
            tile_data = f.read(256)
            non_zero = sum(1 for b in tile_data if b != 0)
            print(f"  Tile {i}: {non_zero}/256 非零字节")
