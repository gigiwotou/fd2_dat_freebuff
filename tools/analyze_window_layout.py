"""
分析索引4的tile布局和窗口绘制逻辑
根据MCP汇编代码168B6.c分析
"""
import struct
import os

data_dir = r"d:\workspace\fd2_dat_freebuff\bin"
dat_path = os.path.join(data_dir, "FDOTHER.DAT")

with open(dat_path, "rb") as f:
    magic = f.read(6)
    print(f"Magic: {magic}")
    
    resource_count = struct.unpack("<I", f.read(4))[0]
    print(f"Resource count: {resource_count}")
    
    f.seek(10)
    offsets = []
    for i in range(resource_count):
        offsets.append(struct.unpack("<I", f.read(4))[0])
    
    # 分析索引4
    start = offsets[4]
    end = offsets[5] if 5 < resource_count else None
    size = end - start if end else 0
    
    print(f"\n索引4: offset=0x{start:X}, size={size}")
    
    f.seek(start)
    data = f.read(size)
    
    # 解析tile集
    magic = data[0:4]
    print(f"Tile magic: {magic}")
    
    tile_count = struct.unpack("<H", data[4:6])[0]
    print(f"Tile count: {tile_count}")
    
    # 读取偏移表
    tile_offsets = []
    for i in range(tile_count):
        offset = struct.unpack("<I", data[6 + i*4 : 10 + i*4])[0]
        tile_offsets.append(offset)
    
    # 解析每个tile
    print("\nTile详细分析:")
    print(f"{'索引':<6} {'偏移':<10} {'宽':<6} {'高':<6} {'用途':<20}")
    print("-" * 60)
    
    for i in range(min(tile_count, 20)):
        addr = tile_offsets[i]
        if addr + 4 > len(data):
            continue
        
        w, h = struct.unpack("<HH", data[addr:addr+4])
        
        # 根据汇编代码推测用途
        purpose = ""
        if w == 3 and h == 3:
            if i <= 4:
                purpose = "角部"
            else:
                purpose = "未知"
        elif w == 16 and h == 3:
            purpose = "水平边框"
        elif w == 3 and h == 16:
            purpose = "垂直边框"
        elif w == 16 and h == 16:
            purpose = "内容区"
        elif w == 16 and h == 3:
            purpose = "水平边框"
        elif w == 1 and h == 3:
            purpose = "小分隔"
        else:
            purpose = f"其他"
        
        print(f"Tile {i:<4} 0x{addr:<7X} {w:<4}x{h:<4} {purpose}")
