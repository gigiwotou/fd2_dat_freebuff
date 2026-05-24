"""检查 FDOTHER 索引资源的格式"""
import struct
import os

fdother_path = r"D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT"

def load_fdother_resource(fdother_path, index):
    """加载 FDOTHER.DAT 指定索引的原始数据"""
    with open(fdother_path, "rb") as f:
        f.read(6)  # LLLLLL magic
        count = struct.unpack("<I", f.read(4))[0]
        offsets = struct.unpack(f"<{count}I", f.read(count * 4))
        
        start = offsets[index]
        end = offsets[index + 1] if index + 1 < count else None
        f.seek(start)
        if end:
            data = f.read(end - start)
        else:
            f.seek(0, 2)
            file_size = f.tell()
            data = f.read(file_size - start)
    
    return data

# 检查所有相关索引
indices_to_check = [51, 53, 63, 82, 83, 84, 85, 86, 87, 88, 89, 90]

for index in indices_to_check:
    print(f"\n索引 {index}:")
    data = load_fdother_resource(fdother_path, index)
    print(f"  大小: {len(data)} 字节")
    print(f"  前16字节: {data[:16].hex()}")
    print(f"  前4字节ASCII: {data[:4]}")
    
    # 检查是否是 LMI1 格式
    if data[:4] == b'LMI1':
        tile_count = struct.unpack("<H", data[4:6])[0]
        print(f"  ** LMI1 格式，tile 数量: {tile_count} **")
        # 打印前几个 tile 偏移
        for i in range(min(5, tile_count)):
            offset = struct.unpack("<I", data[6 + i*4:10 + i*4])[0]
            print(f"    Tile {i} 偏移: {offset} (0x{offset:X})")
            if offset < len(data):
                print(f"      前4字节: {data[offset:offset+4].hex()}")
    else:
        # 检查宽高头
        if len(data) >= 4:
            w = struct.unpack("<H", data[0:2])[0]
            h = struct.unpack("<H", data[2:4])[0]
            print(f"  宽高头: {w}x{h}")
            if 0 < w <= 320 and 0 < h <= 200:
                print(f"  ** 可能是单个图像 **")
