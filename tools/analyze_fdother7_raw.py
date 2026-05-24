"""
直接分析 FDOTHER.DAT 索引 7 的原始数据结构
"""
import struct

fdother_path = r"D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT"

with open(fdother_path, "rb") as f:
    # 读取 DAT 头部
    magic = f.read(6)
    count = struct.unpack("<I", f.read(4))[0]
    offsets = struct.unpack(f"<{count}I", f.read(count * 4))
    
    print(f"DAT 文件:")
    print(f"  Magic: {magic}")
    print(f"  资源数量: {count}")
    
    # 定位索引 7
    idx7_start = offsets[7]
    idx7_end = offsets[8] if 8 < count else None
    idx7_size = idx7_end - idx7_start if idx7_end else 0
    
    print(f"\n索引 7 (0x53a81):")
    print(f"  起始位置: {idx7_start} (0x{idx7_start:X})")
    print(f"  结束位置: {idx7_end}")
    print(f"  大小: {idx7_size}")
    
    # 读取索引 7 的数据
    f.seek(idx7_start)
    idx7_data = f.read(idx7_size)
    
    print(f"\n索引 7 前 200 字节:")
    for i in range(0, min(200, len(idx7_data)), 16):
        hex_str = " ".join(f"{b:02x}" for b in idx7_data[i:i+16])
        ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in idx7_data[i:i+16])
        print(f"  {i:04x}: {hex_str:<48} {ascii_str}")
    
    # 检查偏移 6 处
    print(f"\n偏移 6 处的 4 字节 (小端 DWORD):")
    val_at_6 = struct.unpack("<I", idx7_data[6:10])[0]
    print(f"  值: {val_at_6} (0x{val_at_6:X})")
    
    # 尝试解释为 tile 偏移表
    # 根据 sub_2EB9F: tile_data = base + *(DWORD*)(base + 4*tile_index + 6)
    # 所以偏移 6 处开始是 tile 偏移表
    
    print(f"\n尝试解释为 tile 偏移表 (从偏移 6 开始):")
    tile_count_guess = 20  # 猜测
    for i in range(min(tile_count_guess, (len(idx7_data) - 6) // 4)):
        offset_addr = 6 + i * 4
        if offset_addr + 4 > len(idx7_data):
            break
        tile_offset = struct.unpack("<I", idx7_data[offset_addr:offset_addr+4])[0]
        print(f"  Tile {i}: 偏移 = {tile_offset} (0x{tile_offset:X})")
        
        # 检查偏移是否合理
        if tile_offset > len(idx7_data):
            print(f"    -> 偏移超出范围，停止")
            break
        
        # 检查偏移处的数据
        if tile_offset + 4 <= len(idx7_data):
            tile_data = idx7_data[tile_offset:tile_offset+8]
            print(f"    -> 数据: {tile_data.hex()}")
