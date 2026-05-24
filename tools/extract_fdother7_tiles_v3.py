"""
解压 FDOTHER.DAT 索引 7 变量使用的所有资源图片
修复版: 正确解析嵌套 DAT 的内联 RLE 数据
"""
import struct
import os
from PIL import Image

def load_palette(fdother_path):
    with open(fdother_path, "rb") as f:
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

def decompress_rle(src_data, width, height):
    """
    RLE 解压缩 (1:1 实现 fd2_decoder.c 的 fd2_rle_decompress, value_1=-1 模式)
    """
    output = bytearray(width * height)
    src_pos = 0
    dst_pos = 0
    src_end = len(src_data)
    
    for row in range(height):
        count = width
        
        while count > 0 and src_pos < src_end:
            ctrl = src_data[src_pos]
            src_pos += 1
            
            count_1 = (ctrl & 0x3F) + 1
            bit7 = (ctrl >> 7) & 1
            bit6 = (ctrl >> 6) & 1
            
            if bit7 and bit6:
                dst_pos += count_1
                count -= count_1
            elif bit7 and not bit6:
                if src_pos + count_1 > src_end:
                    break
                for i in range(count_1):
                    output[dst_pos] = src_data[src_pos]
                    dst_pos += 1
                    src_pos += 1
                count -= count_1
            elif not bit7 and bit6:
                if src_pos >= src_end:
                    break
                fill = src_data[src_pos]
                src_pos += 1
                for i in range(count_1):
                    output[dst_pos + 1] = fill
                    dst_pos += 2
                count = count - count_1 - count_1
            else:
                if src_pos >= src_end:
                    break
                fill = src_data[src_pos]
                src_pos += 1
                for i in range(count_1):
                    output[dst_pos] = fill
                    dst_pos += 1
                count -= count_1
        
        dst_pos = row * width + width
    
    return bytes(output)

def extract_nested_dat(resource_data, palette_rgb, output_dir):
    if len(resource_data) < 10 or resource_data[:6] != b'LLLLLL':
        print("  -> 不是有效的嵌套 DAT 格式")
        return
    
    offset_count = struct.unpack("<I", resource_data[6:10])[0]
    offset_table_end = 10 + offset_count * 4
    
    print(f"  偏移数量: {offset_count}")
    print(f"  偏移表结束: 字节 {offset_table_end}")
    
    # 解析所有偏移，找到有效的
    all_offsets = []
    for i in range(offset_count):
        offset_addr = 10 + i * 4
        if offset_addr + 4 > len(resource_data):
            break
        offset_val = struct.unpack("<I", resource_data[offset_addr:offset_addr + 4])[0]
        all_offsets.append(offset_val)
    
    # 找到连续的有效偏移序列
    valid_offsets = []
    for off in all_offsets:
        if off >= offset_table_end and off < len(resource_data):
            valid_offsets.append(off)
        else:
            if valid_offsets:
                break
    
    print(f"  有效偏移: {len(valid_offsets)} 个")
    
    # 第一个 tile 是偏移表后到第一个有效偏移之间的数据
    if valid_offsets:
        first_tile_data = resource_data[offset_table_end:valid_offsets[0]]
        print(f"\n  Tile 0 (内联): 偏移 {offset_table_end}-{valid_offsets[0]}, 大小 {len(first_tile_data)}")
        
        # 尝试解析宽高
        if len(first_tile_data) >= 4:
            w, h = struct.unpack("<HH", first_tile_data[:4])
            if 0 < w <= 640 and 0 < h <= 480:
                print(f"    尺寸: {w}x{h} (有宽高头)")
                rle_data = first_tile_data[4:]
                save_tile_image(rle_data, w, h, palette_rgb, output_dir, 0)
    
    # 解析后续 tiles
    for idx, tile_offset in enumerate(valid_offsets):
        if idx == 0:
            continue
        
        tile_end = valid_offsets[idx] if idx < len(valid_offsets) else len(resource_data)
        tile_data = resource_data[tile_offset:tile_end]
        
        print(f"\n  Tile {idx}: 偏移 {tile_offset}-{tile_end}, 大小 {len(tile_data)}")
        
        if len(tile_data) >= 4:
            w, h = struct.unpack("<HH", tile_data[:4])
            if 0 < w <= 640 and 0 < h <= 480:
                print(f"    尺寸: {w}x{h}")
                rle_data = tile_data[4:]
                save_tile_image(rle_data, w, h, palette_rgb, output_dir, idx)

def save_tile_image(rle_data, width, height, palette_rgb, output_dir, tile_idx):
    try:
        pixels = decompress_rle(rle_data, width, height)
        
        img = Image.new("RGB", (width, height))
        px = img.load()
        
        for y in range(height):
            for x in range(width):
                idx = y * width + x
                pal_idx = pixels[idx]
                if pal_idx < len(palette_rgb):
                    px[x, y] = palette_rgb[pal_idx]
        
        filename = f"tile_{tile_idx:02d}_{width}x{height}.png"
        filepath = os.path.join(output_dir, filename)
        img.save(filepath)
        
        non_zero = sum(1 for p in pixels if p != 0)
        total = len(pixels)
        print(f"    [OK] 已保存 {filename} ({non_zero}/{total} 非零像素)")
        
        if min(width, height) < 100:
            zoom = max(4, 100 // min(width, height))
            zoomed = img.resize((width * zoom, height * zoom), Image.NEAREST)
            zoomed.save(filepath.replace(".png", f"_zoom{zoom}x.png"))
            
    except Exception as e:
        print(f"    错误: {e}")

def extract_fdother7_tiles(data_dir, output_dir):
    fdother_path = os.path.join(data_dir, "FDOTHER.DAT")
    
    if not os.path.exists(fdother_path):
        print(f"错误: 找不到 FDOTHER.DAT: {fdother_path}")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 60)
    print("解压 _FDOTHER.DAT__7 变量使用的资源图片")
    print("=" * 60)
    
    print("\n加载调色板...")
    palette_rgb = load_palette(fdother_path)
    print(f"[OK] 调色板加载成功 (256 颜色)")
    
    dynamic_indices = {
        "scene_0": 82,
        "scene_1": 82,
        "scene_2": 83,
        "scene_3": 84,
        "scene_4": 85,
        "scene_5": 86,
        "scene_6": 87,
        "scene_7": 88,
        "scene_8": 89,
        "scene_9": 90,
        "scene_32": 63,
        "scene_33": 51,
        "scene_34": 53,
        "scene_35": 53,
    }
    
    with open(fdother_path, "rb") as f:
        f.read(6)
        count = struct.unpack("<I", f.read(4))[0]
        offsets = struct.unpack(f"<{count}I", f.read(count * 4))
        
        print(f"\nFDOTHER.DAT 资源数量: {count}")
        
        for scene_name, index in dynamic_indices.items():
            if index >= count:
                print(f"\n跳过 {scene_name} (索引 {index} 超出范围)")
                continue
            
            print(f"\n{'='*60}")
            print(f"处理 {scene_name} (索引 {index})...")
            print(f"{'='*60}")
            
            scene_dir = os.path.join(output_dir, scene_name)
            os.makedirs(scene_dir, exist_ok=True)
            
            start = offsets[index]
            end = offsets[index + 1] if index + 1 < count else None
            f.seek(start)
            resource_data = f.read(end - start) if end else f.read()
            
            print(f"  资源大小: {len(resource_data)} 字节")
            
            if resource_data[:6] == b'LLLLLL':
                print("  ** 嵌套 DAT 格式 **")
                extract_nested_dat(resource_data, palette_rgb, scene_dir)
            else:
                print("  -> 不是嵌套 DAT 格式")
    
    print(f"\n{'='*60}")
    print(f"所有资源已导出到: {output_dir}")
    print(f"{'='*60}")

if __name__ == "__main__":
    data_dir = r"D:\workspace\fd2_dat_freebuff\bin"
    output_dir = r"D:\workspace\fd2_dat_freebuff\output\fdother_7_tiles_v3"
    
    extract_fdother7_tiles(data_dir, output_dir)
