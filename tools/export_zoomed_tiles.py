"""放大显示前20个tile，验证图像数据"""
import struct
import os
from PIL import Image

def load_palette(data_dir):
    """加载索引75调色板"""
    path = os.path.join(data_dir, "FDOTHER.DAT")
    with open(path, "rb") as f:
        f.read(6)
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
        f.read(6)
        count = struct.unpack("<I", f.read(4))[0]
        offsets = struct.unpack(f"<{count}I", f.read(count * 4))
        
        start = offsets[index]
        end = offsets[index + 1] if index + 1 < count else None
        f.seek(start)
        if end:
            data = f.read(end - start)
        else:
            f.seek(0, 2)
            data = f.read(f.tell() - start)
    
    return data

def export_zoomed_tiles(data, palette_rgb, output_dir, zoom=10):
    """放大导出前20个tile"""
    if len(data) < 6:
        return
    
    magic = data[0:4]
    if magic != b'LMI1':
        return
    
    tile_count = struct.unpack("<H", data[4:6])[0]
    print(f"Tile集: {tile_count} 个tiles, 放大倍数: {zoom}x")
    
    # 解析前20个tile
    tiles = []
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
            pixel_size = w * h
            if tile_offset + 4 + pixel_size <= len(data):
                pixel_data = data[tile_offset + 4:tile_offset + 4 + pixel_size]
                
                # 创建原始图像
                img = Image.new("RGB", (w, h))
                pixels = img.load()
                for y in range(h):
                    for x in range(w):
                        idx = y * w + x
                        if idx < len(pixel_data):
                            pal_idx = pixel_data[idx]
                            pixels[x, y] = palette_rgb[pal_idx]
                
                tiles.append((i, w, h, img, pixel_data))
    
    print(f"成功解析 {len(tiles)} 个tiles")
    
    # 放大每个tile并保存
    for i, w, h, img, pixel_data in tiles:
        # 原始大小
        img_path = os.path.join(output_dir, f"tile_{i:03d}_{w}x{h}.png")
        img.save(img_path)
        
        # 放大版本
        if zoom > 1:
            zoomed = img.resize((w * zoom, h * zoom), Image.NEAREST)
            zoomed_path = os.path.join(output_dir, f"tile_{i:03d}_{w}x{h}_zoom{zoom}x.png")
            zoomed.save(zoomed_path)
        
        # 打印像素统计
        non_zero = sum(1 for p in pixel_data if p > 0)
        print(f"  Tile {i:2d}: {w}x{h}, 非零像素: {non_zero}/{w*h}")
        
        # 打印调色板索引示例
        if len(pixel_data) > 0:
            sample = pixel_data[:min(9, len(pixel_data))]
            rgb_sample = [palette_rgb[p] for p in sample]
            print(f"    前9个像素索引: {list(sample)}")
            print(f"    对应RGB: {rgb_sample}")

if __name__ == "__main__":
    data_dir = r"D:\workspace\fd2_dat_freebuff\bin"
    
    print(f"数据目录: {data_dir}")
    
    palette_rgb = load_palette(data_dir)
    print("调色板加载成功")
    
    data = load_fdother_index(data_dir, 4)
    print(f"索引4数据大小: {len(data)} 字节")
    
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "ui_tiles_zoomed")
    os.makedirs(output_dir, exist_ok=True)
    
    export_zoomed_tiles(data, palette_rgb, output_dir, zoom=10)
    
    print("\n=== 完成 ===")
    print(f"图像已保存到: {output_dir}")
