"""分析FDOTHER.DAT索引7的Tile数据并导出图像"""
import struct
import os
from PIL import Image

def load_palette(data_dir):
    """加载FDOTHER索引75调色板"""
    pal_path = os.path.join(data_dir, "FDOTHER.DAT")
    with open(pal_path, "rb") as f:
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
    
    return palette_rgb

def load_index7(data_dir):
    """加载FDOTHER索引7"""
    path = os.path.join(data_dir, "FDOTHER.DAT")
    with open(path, "rb") as f:
        f.read(6)  # LLLLLL
        count = struct.unpack("<I", f.read(4))[0]
        offsets = struct.unpack(f"<{count}I", f.read(count * 4))
        
        start = offsets[7]
        end = offsets[8] if 8 < count else None
        f.seek(start)
        if end:
            data = f.read(end - start)
        else:
            data = f.read()
    
    return data

def parse_and_export_tiles(data, palette_rgb, output_dir):
    """解析Tile集并导出图像"""
    if len(data) < 6:
        print("数据太小")
        return
    
    # LMI1格式: Magic(4) + Count(2) + Offsets...
    magic = data[0:4]
    print(f"Magic: {magic}")
    
    if magic != b"LMI1":
        print(f"警告: 魔术字节不是LMI1: {magic}")
        return
    
    tile_count = struct.unpack("<H", data[4:6])[0]
    print(f"Tile数量: {tile_count}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 读取偏移表
    offset_table_start = 6
    for i in range(min(tile_count, 20)):  # 只分析前20个tile
        offset_addr = offset_table_start + i * 4
        if offset_addr + 4 > len(data):
            break
        
        tile_offset = struct.unpack("<I", data[offset_addr:offset_addr + 4])[0]
        print(f"\n--- Tile {i}: offset=0x{tile_offset:X} ---")
        
        if tile_offset + 4 > len(data):
            print(f"  偏移超出范围")
            continue
        
        # 读取宽度和高度
        w = struct.unpack("<H", data[tile_offset:tile_offset + 2])[0]
        h = struct.unpack("<H", data[tile_offset + 2:tile_offset + 4])[0]
        
        print(f"  尺寸: {w}x{h}")
        
        if w > 0 and h > 0 and w <= 320 and h <= 200:
            pixel_size = w * h
            if tile_offset + 4 + pixel_size > len(data):
                print(f"  像素数据超出范围 (需要 {pixel_size} 字节)")
                continue
            
            pixel_data = data[tile_offset + 4:tile_offset + 4 + pixel_size]
            
            # 打印前几个像素值
            pixel_vals = list(pixel_data[:min(20, len(pixel_data))])
            print(f"  前{len(pixel_vals)}个像素值: {pixel_vals}")
            
            # 检查是否全是0
            non_zero_count = sum(1 for p in pixel_data if p != 0)
            print(f"  非零像素: {non_zero_count}/{len(pixel_data)}")
            
            # 检查是否全是0xFF
            all_ff_count = sum(1 for p in pixel_data if p == 0xFF)
            print(f"  0xFF像素: {all_ff_count}/{len(pixel_data)}")
            
            # 创建图像
            img = Image.new("RGB", (w, h))
            pixels = img.load()
            
            for y in range(h):
                for x in range(w):
                    idx = y * w + x
                    if idx < len(pixel_data):
                        pal_idx = pixel_data[idx]
                        pixels[x, y] = palette_rgb[pal_idx]
            
            # 保存图像
            img_path = os.path.join(output_dir, f"tile_{i:03d}_{w}x{h}.png")
            img.save(img_path)
            print(f"  已保存: {img_path}")
            
            # 如果非零像素较多，打印一个小型ASCII预览
            if non_zero_count > 10:
                print(f"  ASCII预览 (每行40字符):")
                # 简化：只取前5行的中间部分
                for row in range(min(5, h)):
                    line = ""
                    for col in range(min(40, w)):
                        idx = row * w + col
                        val = pixel_data[idx] if idx < len(pixel_data) else 0
                        if val == 0:
                            line += "."
                        elif val < 128:
                            line += "#"
                        else:
                            line += "@"
                    print(f"    {line}")
        else:
            print(f"  尺寸异常，跳过")

if __name__ == "__main__":
    # 数据目录
    data_dir = os.path.dirname(os.path.abspath(__file__))
    # 尝试找到游戏数据目录
    possible_dirs = [
        data_dir,
        os.path.join(data_dir, "bin"),
        os.path.join(data_dir, "data"),
        r"D:\workspace\fd2_dat_freebuff\bin",
    ]
    
    for d in possible_dirs:
        if os.path.exists(os.path.join(d, "FDOTHER.DAT")):
            data_dir = d
            break
    
    print(f"数据目录: {data_dir}")
    
    print("\n=== 加载调色板 ===")
    palette_rgb = load_palette(data_dir)
    print(f"调色板加载成功 (256色)")
    
    print("\n=== 加载FDOTHER索引7 ===")
    data = load_index7(data_dir)
    print(f"索引7数据大小: {len(data)} 字节")
    
    print("\n=== 解析并导出Tile ===")
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "tiles_index7")
    parse_and_export_tiles(data, palette_rgb, output_dir)
    
    print("\n=== 完成 ===")
    print(f"图像已保存到: {output_dir}")
