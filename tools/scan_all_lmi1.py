"""扫描FDOTHER.DAT所有LMI1格式的Tile集，查找窗口边框tile"""
import struct
import os
from PIL import Image

def load_palette(data_dir):
    """加载索引75调色板"""
    path = os.path.join(data_dir, "FDOTHER.DAT")
    with open(path, "rb") as f:
        f.read(6)  # LLLLLL
        count = struct.unpack("<I", f.read(4))[0]
        offsets = struct.unpack(f"<{count}I", f.read(count * 4))
        
        start = offsets[75]
        end = offsets[76] if 76 < count else None
        f.seek(start)
        pal_data = f.read(768) if end is None else f.read(end - start)
    
    palette_rgb = []
    for i in range(256):
        r = (pal_data[i * 3] << 2) | (pal_data[i * 3] >> 4)
        g = (pal_data[i * 3 + 1] << 2) | (pal_data[i * 3 + 1] >> 4)
        b = (pal_data[i * 3 + 2] << 2) | (pal_data[i * 3 + 2] >> 4)
        palette_rgb.append((r, g, b))
    
    return palette_rgb, count

def analyze_all_tilesets(data_dir, palette_rgb, total_count):
    """扫描所有索引，找到LMI1格式的Tile集"""
    path = os.path.join(data_dir, "FDOTHER.DAT")
    
    with open(path, "rb") as f:
        f.read(6)  # LLLLLL
        f.read(4)  # count
        offsets = struct.unpack(f"<{total_count}I", f.read(total_count * 4))
    
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "all_tilesets")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"扫描 {total_count} 个索引...")
    
    for idx in range(total_count):
        start = offsets[idx]
        end = offsets[idx + 1] if idx + 1 < total_count else None
        
        f = open(path, "rb")
        f.seek(start)
        if end:
            data = f.read(end - start)
        else:
            f.seek(0, 2)
            data = f.read(f.tell() - start)
        f.close()
        
        if len(data) < 6:
            continue
        
        magic = data[0:4]
        if magic != b'LMI1':
            continue
        
        tile_count = struct.unpack("<H", data[4:6])[0]
        if tile_count == 0 or tile_count > 500:
            continue
        
        print(f"\n索引 {idx}: LMI1, {tile_count} tiles, {len(data)} 字节")
        
        # 解析前20个tile
        tile_info = []
        for i in range(min(tile_count, 20)):
            offset_addr = 6 + i * 4
            if offset_addr + 4 > len(data):
                break
            
            tile_offset = struct.unpack("<I", data[offset_addr:offset_addr + 4])[0]
            if tile_offset + 4 > len(data):
                continue
            
            w = struct.unpack("<H", data[tile_offset:tile_offset + 2])[0]
            h = struct.unpack("<H", data[tile_offset + 2:tile_offset + 4])[0]
            
            if w > 0 and h > 0 and w <= 320 and h <= 200:
                tile_info.append((i, w, h, tile_offset))
                
                # 导出前5个tile的图像
                if i < 5:
                    pixel_size = w * h
                    if tile_offset + 4 + pixel_size <= len(data):
                        pixel_data = data[tile_offset + 4:tile_offset + 4 + pixel_size]
                        
                        img = Image.new("RGB", (w, h))
                        pixels = img.load()
                        for y in range(h):
                            for x in range(w):
                                px_idx = y * w + x
                                if px_idx < len(pixel_data):
                                    pal_idx = pixel_data[px_idx]
                                    pixels[x, y] = palette_rgb[pal_idx]
                        
                        img_path = os.path.join(output_dir, f"idx{idx}_tile{i}_{w}x{h}.png")
                        img.save(img_path)
        
        # 打印tile信息
        for i, w, h, offset in tile_info:
            print(f"  Tile {i:2d}: {w:3d}x{h:3d}")
        
        # 判断是否是窗口边框tile集
        # 窗口边框通常包含:
        # - 4个角部tile (小尺寸，如3x3, 5x5)
        # - 边框tile (细长，如16x3, 3x16)
        # - 中心tile (如16x16)
        has_small = any(w <= 8 and h <= 8 for _, w, h, _ in tile_info)
        has_long = any((w > 10 and h <= 5) or (w <= 5 and h > 10) for _, w, h, _ in tile_info)
        has_square = any(w == h and w >= 10 for _, w, h, _ in tile_info)
        
        if has_small and has_long and has_square:
            print(f"  >>> 可能是窗口边框Tile集！")

if __name__ == "__main__":
    data_dir = r"D:\workspace\fd2_dat_freebuff\bin"
    
    print(f"数据目录: {data_dir}")
    
    palette_rgb, total_count = load_palette(data_dir)
    print(f"调色板加载成功，总索引数: {total_count}")
    
    analyze_all_tilesets(data_dir, palette_rgb, total_count)
    
    print("\n=== 完成 ===")
