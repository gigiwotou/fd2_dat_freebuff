"""
详细分析 FDOTHER.DAT 索引 82 (scene_0) 的嵌套 DAT 结构
"""
import struct

def analyze_nested_dat(resource_data, name="resource"):
    """详细分析嵌套 DAT 结构"""
    print(f"\n{'='*60}")
    print(f"分析 {name} (大小 {len(resource_data)} 字节)")
    print(f"{'='*60}")
    
    if resource_data[:6] != b'LLLLLL':
        print("不是嵌套 DAT 格式")
        return
    
    magic = resource_data[:6]
    count = struct.unpack("<I", resource_data[6:10])[0]
    print(f"Magic: {magic}")
    print(f"偏移数量: {count}")
    
    # 解析所有偏移
    print(f"\n偏移表 (从偏移 10 开始):")
    offset_table = []
    for i in range(min(count, 30)):
        offset_addr = 10 + i * 4
        if offset_addr + 4 > len(resource_data):
            break
        offset_val = struct.unpack("<I", resource_data[offset_addr:offset_addr + 4])[0]
        offset_table.append(offset_val)
        print(f"  偏移[{i:2d}] @ {offset_addr:5d} = {offset_val:6d} (0x{offset_val:04X})")
    
    offset_table_end = 10 + count * 4
    print(f"\n偏移表结束: 字节 {offset_table_end}")
    
    # 找出有效偏移
    valid_offsets = []
    for i, off in enumerate(offset_table):
        if off < len(resource_data) and off >= offset_table_end:
            valid_offsets.append(off)
        else:
            if valid_offsets:
                print(f"  在 {len(valid_offsets)} 个有效偏移后停止")
            break
    
    print(f"\n有效偏移数量: {len(valid_offsets)}")
    print(f"有效偏移: {valid_offsets}")
    
    # 分析每个 tile 块
    print(f"\nTile 块分析:")
    for idx, tile_offset in enumerate(valid_offsets):
        tile_end = valid_offsets[idx + 1] if idx + 1 < len(valid_offsets) else len(resource_data)
        tile_data = resource_data[tile_offset:tile_end]
        
        print(f"\n  Tile {idx}:")
        print(f"    偏移范围: {tile_offset} - {tile_end}")
        print(f"    数据大小: {len(tile_data)} 字节")
        print(f"    前 20 字节: {tile_data[:20].hex()}")
        
        # 尝试解析为宽高头
        if len(tile_data) >= 4:
            w, h = struct.unpack("<HH", tile_data[:4])
            print(f"    前4字节作为宽高: {w} x {h}")
            if w > 0 and w <= 640 and h > 0 and h <= 480:
                print(f"    [可能是有效尺寸] 宽高头: {w}x{h}")
                print(f"    RLE 数据大小: {len(tile_data) - 4}")
                print(f"    预期解码像素: {w * h}")
        
        # 尝试不同尺寸的 w*h = size
        print(f"    可能的尺寸 (w*h = {len(tile_data)}):")
        for w in range(8, 321, 8):
            if len(tile_data) % w == 0:
                h = len(tile_data) // w
                if h > 0 and h <= 480:
                    print(f"      {w} x {h}")

if __name__ == "__main__":
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
        
        analyze_nested_dat(resource_data, f"FDOTHER 索引 {index} (scene_0)")
        
        # 分析索引 83 (scene_2)
        index = 83
        start = offsets[index]
        end = offsets[index + 1]
        f.seek(start)
        resource_data = f.read(end - start)
        
        analyze_nested_dat(resource_data, f"FDOTHER 索引 {index} (scene_2)")
