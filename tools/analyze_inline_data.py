"""
根据汇编代码分析，嵌套DAT的结构应该是：
- LLLLLL magic
- count (偏移数量)
- offsets[count] (每个tile的起始偏移)
- tile数据从第一个offset开始

但这里的问题是：
- 偏移数量字段可能是资源总数，不是当前资源的tile数
- 或者偏移数量后的数据包含了内联的tile数据

让我们尝试直接按偏移表解析：
偏移[0] = 6587 到 偏移[1] = 18611 -> tile 0 (12024字节)
偏移[1] = 18611 到 偏移[2] = 25484 -> tile 1 (6873字节)
偏移[2] = 25484 到 偏移[3] = 33848 -> tile 2 (8364字节)

但问题是偏移表后的数据（114-6587）是什么？
可能是tile数据之前的额外数据，或者是另一种格式

让我尝试另一种方法：不通过偏移表，直接查找所有可能的tile数据
"""
import struct

fdother_path = r"D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT"

with open(fdother_path, "rb") as f:
    f.read(6)
    count = struct.unpack("<I", f.read(4))[0]
    offsets = struct.unpack(f"<{count}I", f.read(count * 4))
    
    # 分析索引 82 (scene_0)
    index = 82
    start = offsets[index]
    end = offsets[index + 1]
    f.seek(start)
    resource_data = f.read(end - start)
    
    print(f"资源大小: {len(resource_data)} 字节")
    offset_count = struct.unpack("<I", resource_data[6:10])[0]
    print(f"偏移数量: {offset_count}")
    
    # 直接打印从字节 114 开始的数据，看看是什么
    print(f"\n从偏移 114 开始的数据 (偏移表后到第一个tile):")
    data_114 = resource_data[114:]
    print(f"数据大小: {len(data_114)}")
    print(f"前 100 字节 hex:")
    for i in range(0, 100, 16):
        hex_str = data_114[i:i+16].hex()
        print(f"  {i:4d}: {hex_str}")
    
    # 尝试按宽高头解析
    if len(data_114) >= 4:
        w, h = struct.unpack("<HH", data_114[:4])
        print(f"\n前4字节作为宽高: {w} x {h}")
        if 0 < w <= 640 and 0 < h <= 480:
            print(f"[有效尺寸!]")
    
    # 分析第一个tile (6587开始)
    print(f"\n{'='*60}")
    print(f"Tile 0 (偏移 6587):")
    tile0 = resource_data[6587:18611]
    print(f"大小: {len(tile0)}")
    print(f"前 100 字节 hex:")
    for i in range(0, 100, 16):
        hex_str = tile0[i:i+16].hex()
        print(f"  {i:4d}: {hex_str}")
    
    if len(tile0) >= 4:
        w, h = struct.unpack("<HH", tile0[:4])
        print(f"\n前4字节作为宽高: {w} x {h}")
        if 0 < w <= 640 and 0 < h <= 480:
            print(f"[有效尺寸!]")
