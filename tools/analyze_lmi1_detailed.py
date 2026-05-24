"""详细分析FDOTHER索引4的LMI1格式结构"""
import struct
import os

def analyze_lmi1_structure():
    data_dir = r"D:\workspace\fd2_dat_freebuff\bin"
    path = os.path.join(data_dir, "FDOTHER.DAT")
    
    with open(path, "rb") as f:
        f.read(6)  # LLLLLL
        count = struct.unpack("<I", f.read(4))[0]
        offsets = struct.unpack(f"<{count}I", f.read(count * 4))
        
        start = offsets[4]
        end = offsets[5] if 5 < count else None
        f.seek(start)
        if end:
            data = f.read(end - start)
        else:
            f.seek(0, 2)
            file_size = f.tell()
            data = f.read(file_size - start)
    
    print(f"索引4数据大小: {len(data)} 字节")
    print(f"Magic: {data[0:4]} ({data[0:4].decode('ascii', errors='replace')})")
    
    if data[0:4] != b'LMI1':
        print("不是LMI1格式!")
        return
    
    tile_count = struct.unpack("<H", data[4:6])[0]
    print(f"Tile数量: {tile_count}")
    
    print(f"\n偏移表 (前20个):")
    for i in range(min(20, tile_count)):
        offset_addr = 6 + i * 4
        if offset_addr + 4 > len(data):
            break
        tile_offset = struct.unpack("<I", data[offset_addr:offset_addr + 4])[0]
        print(f"  Tile {i:2d}: offset=0x{tile_offset:05X} ({tile_offset})")
    
    print(f"\nTile数据详情 (前20个):")
    for i in range(min(20, tile_count)):
        offset_addr = 6 + i * 4
        if offset_addr + 4 > len(data):
            break
        tile_offset = struct.unpack("<I", data[offset_addr:offset_addr + 4])[0]
        
        if tile_offset + 4 > len(data):
            continue
        
        w = struct.unpack("<H", data[tile_offset:tile_offset + 2])[0]
        h = struct.unpack("<H", data[tile_offset + 2:tile_offset + 4])[0]
        
        print(f"  Tile {i:2d}: offset=0x{tile_offset:05X}, 尺寸={w}x{h}")
        
        if w > 0 and h > 0:
            pixel_size = w * h
            if tile_offset + 4 + pixel_size <= len(data):
                pixel_data = data[tile_offset + 4:tile_offset + 4 + pixel_size]
                
                # 分析像素数据
                zero_count = sum(1 for p in pixel_data if p == 0)
                non_zero = pixel_size - zero_count
                
                # 统计调色板索引分布
                unique_indices = set(pixel_data)
                min_idx = min(unique_indices) if unique_indices else 0
                max_idx = max(unique_indices) if unique_indices else 0
                
                print(f"    像素: {non_zero}/{pixel_size} 非零, 调色板索引范围[{min_idx}, {max_idx}], 唯一值{len(unique_indices)}个")
                
                # 显示前16个像素
                sample = pixel_data[:16]
                print(f"    前16像素: {list(sample)}")

if __name__ == "__main__":
    analyze_lmi1_structure()
