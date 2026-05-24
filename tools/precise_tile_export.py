"""精确导出FDOTHER索引4的tile图像，验证解析是否正确"""
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
        # FD2使用6位颜色值，扩展到8位
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

def parse_lmi1_tileset(data, palette_rgb, output_dir):
    """解析LMI1格式的tile集并导出图像"""
    if len(data) < 6:
        print("数据太小")
        return
    
    magic = data[0:4]
    if magic != b'LMI1':
        print(f"不是LMI1格式: {magic}")
        return
    
    tile_count = struct.unpack("<H", data[4:6])[0]
    print(f"解析 {tile_count} 个tile...")
    
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
                
                # 设置像素
                for y in range(h):
                    for x in range(w):
                        idx = y * w + x
                        if idx < len(pixel_data):
                            pal_idx = pixel_data[idx]
                            if pal_idx < len(palette_rgb):
                                pixels[x, y] = palette_rgb[pal_idx]
                
                tiles.append((i, w, h, img, pixel_data))
                
                # 保存图像
                img_path = os.path.join(output_dir, f"tile_{i:03d}_{w}x{h}.png")
                img.save(img_path)
                
                # 如果是重要的窗口组件，额外保存放大版
                if i in [1, 2, 3, 4, 5, 8, 10, 11, 13]:  # 窗口关键组件
                    zoom_factor = max(10, 20 // min(w, h)) if min(w, h) > 0 else 10
                    if zoom_factor > 1:
                        zoomed = img.resize((w * zoom_factor, h * zoom_factor), Image.NEAREST)
                        zoomed_path = os.path.join(output_dir, f"tile_{i:03d}_{w}x{h}_zoom{zoom_factor}x.png")
                        zoomed.save(zoomed_path)
    
    print(f"成功解析 {len(tiles)} 个tile")
    
    # 打印关键tile信息
    print(f"\n关键窗口组件:")
    for i, w, h, img, pixel_data in tiles:
        if i in [1, 2, 3, 4, 5, 8, 10, 11, 13]:
            non_zero = sum(1 for p in pixel_data if p != 0)
            unique_colors = len(set(pixel_data))
            print(f"  Tile {i}: {w}x{h}, 非零像素:{non_zero}/{len(pixel_data)}, 唯一颜色:{unique_colors}")
    
    return tiles

def create_visual_layout(tiles, output_dir):
    """创建可视化布局图，展示tile如何组成窗口"""
    # 创建一个大画布来展示窗口布局概念
    canvas_w, canvas_h = 300, 200
    canvas = Image.new("RGB", (canvas_w, canvas_h), (0, 0, 0))
    
    # 假设一个4x3的窗口
    tile_w, tile_h = 16, 16
    start_x, start_y = 50, 30
    
    # 绘制边框
    # 左上角 (1)
    if any(t[0] == 1 for t in tiles):
        _, w, h, img, _ = next(t for t in tiles if t[0] == 1)
        canvas.paste(img, (start_x, start_y))
    
    # 右上角 (2) 
    if any(t[0] == 2 for t in tiles):
        _, w, h, img, _ = next(t for t in tiles if t[0] == 2)
        canvas.paste(img, (start_x + 3 * tile_w, start_y))
    
    # 左下角 (3)
    if any(t[0] == 3 for t in tiles):
        _, w, h, img, _ = next(t for t in tiles if t[0] == 3)
        canvas.paste(img, (start_x, start_y + 2 * tile_h))
    
    # 右下角 (4)
    if any(t[0] == 4 for t in tiles):
        _, w, h, img, _ = next(t for t in tiles if t[0] == 4)
        canvas.paste(img, (start_x + 3 * tile_w, start_y + 2 * tile_h))
    
    # 上边框 (5)
    if any(t[0] == 5 for t in tiles):
        _, w, h, img, _ = next(t for t in tiles if t[0] == 5)
        for col in range(1, 3):  # 中间两列
            canvas.paste(img, (start_x + col * tile_w, start_y))
    
    # 下边框 (8)
    if any(t[0] == 8 for t in tiles):
        _, w, h, img, _ = next(t for t in tiles if t[0] == 8)
        for col in range(1, 3):  # 中间两列
            canvas.paste(img, (start_x + col * tile_w, start_y + 2 * tile_h))
    
    # 左边框 (10)
    if any(t[0] == 10 for t in tiles):
        _, w, h, img, _ = next(t for t in tiles if t[0] == 10)
        for row in range(1, 2):  # 中间行
            canvas.paste(img, (start_x, start_y + row * tile_h))
    
    # 右边框 (11)
    if any(t[0] == 11 for t in tiles):
        _, w, h, img, _ = next(t for t in tiles if t[0] == 11)
        for row in range(1, 2):  # 中间行
            canvas.paste(img, (start_x + 3 * tile_w, start_y + row * tile_h))
    
    # 中心 (13)
    if any(t[0] == 13 for t in tiles):
        _, w, h, img, _ = next(t for t in tiles if t[0] == 13)
        for row in range(1, 2):
            for col in range(1, 3):
                canvas.paste(img, (start_x + col * tile_w, start_y + row * tile_h))
    
    layout_path = os.path.join(output_dir, "window_layout_concept.png")
    canvas.save(layout_path)
    print(f"\n窗口布局概念图已保存: {layout_path}")

if __name__ == "__main__":
    data_dir = r"D:\workspace\fd2_dat_freebuff\bin"
    
    print(f"数据目录: {data_dir}")
    
    # 加载调色板
    print("\n加载调色板...")
    palette_rgb = load_palette(data_dir)
    print("调色板加载成功")
    
    # 加载索引4
    print("\n加载FDOTHER索引4...")
    data = load_fdother_index(data_dir, 4)
    print(f"数据大小: {len(data)} 字节")
    
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "correct_tile_export")
    os.makedirs(output_dir, exist_ok=True)
    
    # 解析并导出tile
    tiles = parse_lmi1_tileset(data, palette_rgb, output_dir)
    
    # 创建布局图
    create_visual_layout(tiles, output_dir)
    
    print(f"\n图像已保存到: {output_dir}")
    print("=== 完成 ===")