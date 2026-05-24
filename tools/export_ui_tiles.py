"""导出FDOTHER索引4的UI tile图像，验证数据正确性"""
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
    
    return palette_rgb

def load_fdother_index(data_dir, index):
    """加载FDOTHER指定索引"""
    path = os.path.join(data_dir, "FDOTHER.DAT")
    with open(path, "rb") as f:
        f.read(6)  # LLLLLL
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

def export_tileset(data, palette_rgb, output_dir):
    """导出tile集为图像"""
    if len(data) < 6:
        print("数据太小")
        return
    
    magic = data[0:4]
    if magic != b'LMI1':
        print(f"不是LMI1格式: {magic}")
        return
    
    tile_count = struct.unpack("<H", data[4:6])[0]
    print(f"Tile集: {tile_count} 个tiles")
    
    # 解析所有tile
    tiles = []
    for i in range(tile_count):
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
                
                # 创建图像
                img = Image.new("RGB", (w, h))
                pixels = img.load()
                for y in range(h):
                    for x in range(w):
                        idx = y * w + x
                        if idx < len(pixel_data):
                            pal_idx = pixel_data[idx]
                            pixels[x, y] = palette_rgb[pal_idx]
                
                tiles.append((i, w, h, img))
                
                # 保存单个tile
                img_path = os.path.join(output_dir, f"tile_{i:03d}_{w}x{h}.png")
                img.save(img_path)
    
    print(f"成功导出 {len(tiles)} 个tile")
    
    # 创建组合预览图
    # 前20个tile，每个放大20倍便于查看
    zoom = 20
    preview_cols = 10
    
    # 计算最大尺寸
    max_w = max(w for _, w, _, _ in tiles[:20])
    max_h = max(h for _, _, h, _ in tiles[:20])
    
    preview_w = preview_cols * (max_w * zoom + 4) + 4
    preview_h = 2 * (max_h * zoom + 4) + 4  # 2行
    
    preview = Image.new("RGB", (preview_w, preview_h), (0, 0, 0))
    
    for idx in range(min(20, len(tiles))):
        i, w, h, img = tiles[idx]
        
        col = idx % preview_cols
        row = idx // preview_cols
        
        x = col * (max_w * zoom + 4) + 2
        y = row * (max_h * zoom + 4) + 2
        
        # 放大图像
        zoomed_img = img.resize((w * zoom, h * zoom), Image.NEAREST)
        preview.paste(zoomed_img, (x, y))
    
    preview_path = os.path.join(output_dir, "tileset_preview_zoomed.png")
    preview.save(preview_path)
    print(f"\n预览图已保存: {preview_path}")
    print(f"单个tile图像已保存到: {output_dir}")
    
    # 打印tile信息
    print(f"\n前20个tile信息:")
    for i, w, h, img in tiles[:20]:
        print(f"  Tile {i:2d}: {w}x{h}")

if __name__ == "__main__":
    data_dir = r"D:\workspace\fd2_dat_freebuff\bin"
    
    print(f"数据目录: {data_dir}")
    
    # 加载调色板
    print("\n加载调色板...")
    palette_rgb = load_palette(data_dir)
    print("调色板加载成功")
    
    # 加载索引4
    print("\n加载FDOTHER索引4 (窗口边框tile集)...")
    data = load_fdother_index(data_dir, 4)
    print(f"数据大小: {len(data)} 字节")
    
    # 导出图像
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "ui_tiles_export")
    os.makedirs(output_dir, exist_ok=True)
    
    export_tileset(data, palette_rgb, output_dir)
    
    print("\n=== 完成 ===")
