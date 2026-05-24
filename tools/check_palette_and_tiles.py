"""检查调色板和tile数据是否正常"""
import struct
import os

def check_palette(data_dir):
    """检查调色板数据"""
    path = os.path.join(data_dir, "FDOTHER.DAT")
    with open(path, "rb") as f:
        f.read(6)  # LLLLLL
        count = struct.unpack("<I", f.read(4))[0]
        offsets = struct.unpack(f"<{count}I", f.read(count * 4))
        
        start = offsets[75]
        end = offsets[76] if 76 < count else None
        f.seek(start)
        pal_data = f.read(768) if end is None else f.read(end - start)
    
    print(f"调色板大小: {len(pal_data)} 字节")
    print(f"\n前20个调色板条目:")
    for i in range(20):
        r_raw = pal_data[i * 3]
        g_raw = pal_data[i * 3 + 1]
        b_raw = pal_data[i * 3 + 2]
        
        # 按照FD2的方式转换
        r = (r_raw << 2) | (r_raw >> 4)
        g = (g_raw << 2) | (g_raw >> 4)
        b = (b_raw << 2) | (b_raw >> 4)
        
        print(f"  [{i:2d}] 原始: ({r_raw:3d}, {g_raw:3d}, {b_raw:3d}) -> RGB: ({r:3d}, {g:3d}, {b:3d})")
    
    # 检查是否有非零的调色板条目
    non_zero_count = 0
    max_val = 0
    for i in range(256):
        r = pal_data[i * 3]
        g = pal_data[i * 3 + 1]
        b = pal_data[i * 3 + 2]
        
        if r > 0 or g > 0 or b > 0:
            non_zero_count += 1
        
        max_val = max(max_val, r, g, b)
    
    print(f"\n非零调色板条目数: {non_zero_count}/256")
    print(f"调色板最大原始值: {max_val}")

def check_tile_data(data_dir):
    """检查tile数据"""
    path = os.path.join(data_dir, "FDOTHER.DAT")
    with open(path, "rb") as f:
        f.read(6)
        count = struct.unpack("<I", f.read(4))[0]
        offsets = struct.unpack(f"<{count}I", f.read(count * 4))
        
        start = offsets[4]
        end = offsets[5]
        f.seek(start)
        data = f.read(end - start)
    
    print(f"\n索引4数据大小: {len(data)} 字节")
    print(f"Magic: {data[0:4]}")
    
    tile_count = struct.unpack("<H", data[4:6])[0]
    print(f"Tile数量: {tile_count}")
    
    # 检查前5个tile
    print(f"\n前5个tile信息:")
    for i in range(5):
        offset_addr = 6 + i * 4
        tile_offset = struct.unpack("<I", data[offset_addr:offset_addr + 4])[0]
        
        w = struct.unpack("<H", data[tile_offset:tile_offset + 2])[0]
        h = struct.unpack("<H", data[tile_offset + 2:tile_offset + 4])[0]
        pixel_size = w * h
        
        if tile_offset + 4 + pixel_size <= len(data):
            pixel_data = data[tile_offset + 4:tile_offset + 4 + pixel_size]
            
            # 统计像素值分布
            zero_count = sum(1 for p in pixel_data if p == 0)
            non_zero = pixel_size - zero_count
            
            # 找最大和最小非零值
            non_zero_vals = [p for p in pixel_data if p > 0]
            min_val = min(non_zero_vals) if non_zero_vals else 0
            max_val = max(non_zero_vals) if non_zero_vals else 0
            
            print(f"  Tile {i}: {w}x{h}, 非零像素: {non_zero}/{pixel_size}, 范围: [{min_val}, {max_val}]")
            
            # 显示前20个像素值
            pixel_sample = pixel_data[:20]
            print(f"    前20个像素: {list(pixel_sample)}")

if __name__ == "__main__":
    data_dir = r"D:\workspace\fd2_dat_freebuff\bin"
    check_palette(data_dir)
    check_tile_data(data_dir)
