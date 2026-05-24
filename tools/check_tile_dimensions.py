import struct

dat_path = 'bin/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    f.read(6)  # 跳过文件头
    resource_count = struct.unpack('<I', f.read(4))[0]
    
    offsets = []
    for i in range(resource_count):
        offset = struct.unpack('<I', f.read(4))[0]
        offsets.append(offset)
    
    print(f"资源总数: {resource_count}")
    print(f"\n索引4偏移: 0x{offsets[4]:X}, 索引5偏移: 0x{offsets[5]:X}")
    print(f"索引4大小: {offsets[5] - offsets[4]}")
    
    # 读取索引4
    f.seek(offsets[4])
    res_data = f.read(offsets[5] - offsets[4])
    
    print("\n" + "="*60)
    print("索引4 tile尺寸分析:")
    print("="*60)
    
    print(f"\n前4字节: {res_data[:4]}")
    print(f"字节[4-5]: 0x{res_data[4]:02X} 0x{res_data[5]:02X}")
    
    tile_count = struct.unpack('<H', res_data[4:6])[0]
    print(f"Tile数量: {tile_count}")
    
    print(f"\n前20个tile:")
    for i in range(min(20, tile_count)):
        offset = struct.unpack('<I', res_data[6 + i*4:10 + i*4])[0]
        if offset < len(res_data):
            w = struct.unpack('<H', res_data[offset:offset+2])[0]
            h = struct.unpack('<H', res_data[offset+2:offset+4])[0]
            print(f"  Tile {i:2d}: {w:3d}x{h:3d}  (偏移: 0x{offset:04X})")
        else:
            print(f"  Tile {i:2d}: 偏移超出范围 (0x{offset:04X})")
