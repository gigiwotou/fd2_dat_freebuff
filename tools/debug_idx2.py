"""分析索引2的详细结构"""
import struct

with open("game/FDOTHER.DAT", "rb") as f:
    f.seek(6)
    
    offsets = []
    while True:
        data = f.read(4)
        if len(data) < 4:
            break
        off = struct.unpack('<I', data)[0]
        if off > 10000000:  # 明显无效
            break
        offsets.append(off)
        if len(offsets) > 103:
            break
    
    # 索引2的范围
    start = offsets[2]
    end = offsets[3]
    size = end - start
    
    print(f"索引2: 偏移 {start} - {end}, 大小 {size}")
    
    with open("game/FDOTHER.DAT", "rb") as f:
        f.seek(start)
        idx2_data = f.read(size)
        
    print(f"总大小: {len(idx2_data)} 字节")
    print(f"偏移值数量: {len(idx2_data) // 4}")
    
    # 读取前10个偏移
    for i in range(10):
        if i * 4 + 4 <= len(idx2_data):
            off = struct.unpack('<I', idx2_data[i*4:i*4+4])[0]
            print(f"  偏移[{i}] = {off}")
    
    first_off = struct.unpack('<I', idx2_data[0:4])[0]
    print(f"\n第一个偏移值: {first_off}")
    print(f"偏移表大小: {len(idx2_data)} 字节")
    print(f"第一个偏移是否在数据范围内: {first_off < len(idx2_data)}")
    print(f"第一个偏移指向的数据(前8字节):")
    if first_off < len(idx2_data):
        print(f"  {idx2_data[first_off:first_off+8].hex()}")
