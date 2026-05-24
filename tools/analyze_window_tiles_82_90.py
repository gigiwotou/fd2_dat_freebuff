"""分析FDOTHER.DAT索引82-90，找到窗口Tile集"""
import struct
import os
from PIL import Image

def load_palette(data_dir):
    """加载索引75调色板"""
    path = os.path.join(data_dir, "FDOTHER.DAT")
    with open(path, "rb") as f:
        f.read(10)  # LLLLLL + count
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
    
    return palette_rgb

def load_fdother_index(data_dir, index):
    """加载FDOTHER指定索引"""
    path = os.path.join(data_dir, "FDOTHER.DAT")
    with open(path, "rb") as f:
        f.read(10)  # LLLLLL + count
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

def analyze_index(data, index, palette_rgb, output_dir):
    """分析一个索引，如果是LMI1则导出tile"""
    print(f"\n{'='*60}")
    print(f"分析索引 {index}")
    print(f"{'='*60}")
    
    if len(data) < 6:
        print(f"  数据太小: {len(data)} 字节")
        return False
    
    magic = data[0:4]
    if magic != b"LMI1":
        print(f"  Magic: {magic.hex()} (不是LMI1)")
        return False
    
    tile_count = struct.unpack("<H", data[4:6])[0]
    print(f"  Magic: LMI1")
    print(f"  Tile数量: {tile_count}")
    print(f"  数据大小: {len(data)} 字节")
    
    # 解析tile
    offset_table_start = 6
    for i in range(min(tile_count, 30)):  # 只分析前30个tile
        offset_addr = offset_table_start + i * 4
        if offset_addr + 4 > len(data):
            break
        
        tile_offset = struct.unpack("<I", data[offset_addr:offset_addr + 4])[0]
        
        if tile_offset + 4 > len(data):
            print(f"  Tile {i}: 偏移0x{tile_offset:X} 超出范围")
            continue
        
        w = struct.unpack("<H", data[tile_offset:tile_offset + 2])[0]
        h = struct.unpack("<H", data[tile_offset + 2:tile_offset + 4])[0]
        
        if w > 0 and h > 0 and w <= 320 and h <= 200:
            pixel_size = w * h
            if tile_offset + 4 + pixel_size <= len(data):
                pixel_data = data[tile_offset + 4:tile_offset + 4 + pixel_size]
                
                # 计算非零像素比例
                non_zero = sum(1 for p in pixel_data if p != 0)
                non_zero_pct = non_zero / len(pixel_data) * 100 if len(pixel_data) > 0 else 0
                
                print(f"  Tile {i:2d}: {w:3d}x{h:3d}, 非零={non_zero:4d}/{pixel_size:5d} ({non_zero_pct:5.1f}%)")
                
                # 导出图像
                img = Image.new("RGB", (w, h))
                pixels = img.load()
                for y in range(h):
                    for x in range(w):
                        idx = y * w + x
                        if idx < len(pixel_data):
                            pal_idx = pixel_data[idx]
                            pixels[x, y] = palette_rgb[pal_idx]
                
                img_path = os.path.join(output_dir, f"index{index}_tile{i:03d}_{w}x{h}.png")
                img.save(img_path)
            else:
                print(f"  Tile {i:2d}: {w:3d}x{h:3d}, 像素数据超出范围")
        else:
            print(f"  Tile {i:2d}: 尺寸异常 {w}x{h}")
    
    return True

if __name__ == "__main__":
    data_dir = r"D:\workspace\fd2_dat_freebuff\bin"
    
    print(f"数据目录: {data_dir}")
    
    # 加载调色板
    print("\n加载调色板...")
    palette_rgb = load_palette(data_dir)
    print("调色板加载成功")
    
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "window_tiles")
    os.makedirs(output_dir, exist_ok=True)
    
    # 分析索引82-90（"RRSTUVWXYZ"对应的ASCII值）
    for idx in range(82, 91):
        try:
            data = load_fdother_index(data_dir, idx)
            analyze_index(data, idx, palette_rgb, output_dir)
        except Exception as e:
            print(f"索引 {idx}: 加载失败 - {e}")
    
    print("\n=== 完成 ===")
    print(f"图像已保存到: {output_dir}")
