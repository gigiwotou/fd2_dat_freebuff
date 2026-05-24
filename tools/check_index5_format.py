"""检查FDOTHER索引5的数据格式"""
import struct
import os

data_dir = r"D:\workspace\fd2_dat_freebuff\bin"
path = os.path.join(data_dir, "FDOTHER.DAT")

with open(path, "rb") as f:
    f.read(10)  # LLLLLL + count
    count = struct.unpack("<I", f.read(4))[0]
    offsets = struct.unpack(f"<{count}I", f.read(count * 4))
    
    for idx in [4, 5, 8, 12, 13]:
        start = offsets[idx]
        end = offsets[idx + 1] if idx + 1 < count else None
        size = end - start if end else "unknown"
        
        f.seek(start)
        data = f.read(16)
        
        print(f"索引 {idx}:")
        print(f"  偏移: 0x{start:X}")
        print(f"  大小: {size}")
        print(f"  前16字节: {data.hex()}")
        print(f"  Magic: {data[0:4]}")
        if data[0:4] == b"LMI1":
            tile_count = struct.unpack("<H", data[4:6])[0]
            print(f"  Tile数量: {tile_count}")
        print()
