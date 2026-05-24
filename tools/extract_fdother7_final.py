"""
提取 _FDOTHER.DAT__7 (0x53a81) 使用的所有 tile 图片

修正版本: stride = tile_width (不是固定320)
"""
import struct
import os
from PIL import Image


def load_palette(fdother_path):
    """加载 FDOTHER.DAT 索引 75 的调色板"""
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


def load_fdother_resource(fdother_path, index):
    """加载 FDOTHER.DAT 指定索引的原始数据"""
    with open(fdother_path, "rb") as f:
        f.read(6)
        count = struct.unpack("<I", f.read(4))[0]
        offsets = struct.unpack(f"<{count}I", f.read(count * 4))
        start = offsets[index]
        end = offsets[index + 1] if index + 1 < count else None
        f.seek(start)
        data = f.read(end - start) if end else f.read()
    return data


def decompress_rle(data, width, height):
    """
    实现 sub_4E98D 的 RLE 解压缩逻辑
    关键修正: stride = width (不是固定值)
    """
    output = bytearray(width * height)
    src_pos = 0
    dst_pos = 0
    
    for row in range(height):
        row_start = dst_pos
        count = width
        
        while count > 0 and src_pos < len(data):
            value = data[src_pos]
            src_pos += 1
            
            if value & 0x80:
                if value & 0x40:
                    # 跳过像素
                    skip_count = ((value & 0x3F) >> 2) + 1
                    dst_pos += skip_count
                    count -= skip_count
                else:
                    # 复制像素数据
                    copy_count = ((value & 0x3F) >> 2) + 1
                    if src_pos + copy_count > len(data):
                        break
                    for i in range(copy_count):
                        if dst_pos < len(output):
                            output[dst_pos] = data[src_pos]
                        dst_pos += 1
                        src_pos += 1
                    count -= copy_count
            else:
                # 填充相同像素
                fill_count = ((value & 0x3F) >> 2) + 1
                if src_pos < len(data):
                    fill_value = data[src_pos]
                    src_pos += 1
                else:
                    fill_value = 0
                
                for i in range(fill_count):
                    if dst_pos < len(output):
                        output[dst_pos] = fill_value
                    dst_pos += 1
                count -= fill_count
        
        # 关键修正: stride = width
        dst_pos = row_start + width
    
    return bytes(output)


def create_image_from_pixels(pixel_data, width, height, palette_rgb):
    """从像素数据创建 PIL 图像"""
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    
    for y in range(height):
        for x in range(width):
            idx = y * width + x
            if idx < len(pixel_data):
                pal_idx = pixel_data[idx]
                if pal_idx < len(palette_rgb):
                    pixels[x, y] = palette_rgb[pal_idx]
    
    return img


def estimate_pixel_count(data):
    """估算 RLE 数据的原始像素数量"""
    src_pos = 0
    dst_count = 0
    
    while src_pos < len(data):
        value = data[src_pos]
        src_pos += 1
        
        if value & 0x80:
            count = ((value & 0x3F) >> 2) + 1
            if value & 0x40:
                dst_count += count
            else:
                dst_count += count
                src_pos += count
        else:
            count = ((value & 0x3F) >> 2) + 1
            if src_pos < len(data):
                src_pos += 1
            dst_count += count
    
    return dst_count


def extract_tile_atlas(nested_data, palette_rgb, output_dir, prefix=""):
    """提取 tile 图集"""
    if len(nested_data) < 10 or nested_data[:6] != b'LLLLLL':
        print("  不是有效的嵌套 DAT 格式")
        return
    
    offset_count = struct.unpack("<I", nested_data[6:10])[0]
    print(f"  偏移数量: {offset_count}")
    
    offset_table_start = 10
    valid_offsets = []
    
    for i in range(offset_count):
        offset_addr = offset_table_start + i * 4
        if offset_addr + 4 > len(nested_data):
            break
        
        offset_val = struct.unpack("<I", nested_data[offset_addr:offset_addr + 4])[0]
        offset_table_end = offset_table_start + offset_count * 4
        if offset_val < len(nested_data) and offset_val >= offset_table_end:
            valid_offsets.append((i, offset_val))
        else:
            if valid_offsets:
                print(f"  偏移表在 {len(valid_offsets)} 个有效偏移后结束")
            break
    
    print(f"  有效偏移: {len(valid_offsets)} 个")
    
    for idx, (tile_idx, tile_offset) in enumerate(valid_offsets):
        tile_end = valid_offsets[idx + 1][1] if idx + 1 < len(valid_offsets) else len(nested_data)
        tile_rle_data = nested_data[tile_offset:tile_end]
        
        print(f"\n  Tile {tile_idx}: 偏移 {tile_offset}-{tile_end}, RLE 数据大小 {len(tile_rle_data)} 字节")
        
        # 估算像素数
        pixel_count = estimate_pixel_count(tile_rle_data)
        print(f"    估算像素数: {pixel_count}")
        
        # 找出合理的 w*h 组合
        found_dimensions = []
        for w in range(8, 321, 8):
            if pixel_count % w == 0:
                h = pixel_count // w
                if 8 <= h <= 400:
                    found_dimensions.append((w, h))
        
        print(f"    可能的尺寸: {found_dimensions[:10]}")
        
        # 尝试解压缩并保存
        for w, h in found_dimensions[:5]:
            try:
                pixel_data = decompress_rle(tile_rle_data, w, h)
                
                non_zero = sum(1 for p in pixel_data if p != 0)
                ratio = non_zero / len(pixel_data) if len(pixel_data) > 0 else 0
                
                if ratio > 0.01:
                    img = create_image_from_pixels(pixel_data, w, h, palette_rgb)
                    
                    img_path = os.path.join(output_dir, f"{prefix}tile_{tile_idx:03d}_{w}x{h}.png")
                    img.save(img_path)
                    print(f"    -> 成功: {w}x{h}, 非零像素: {non_zero}/{len(pixel_data)} ({ratio*100:.1f}%)")
                    
                    if min(w, h) < 100:
                        zoom = max(2, 100 // min(w, h))
                        zoomed = img.resize((w * zoom, h * zoom), Image.NEAREST)
                        zoomed_path = os.path.join(output_dir, f"{prefix}tile_{tile_idx:03d}_{w}x{h}_zoom{zoom}x.png")
                        zoomed.save(zoomed_path)
            except Exception as e:
                pass


def extract_fdother7_tiles(data_dir, output_dir):
    """提取 _FDOTHER.DAT__7 使用的所有 tile 图片"""
    fdother_path = os.path.join(data_dir, "FDOTHER.DAT")
    
    if not os.path.exists(fdother_path):
        print(f"错误: 找不到 FDOTHER.DAT 文件: {fdother_path}")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("加载调色板...")
    palette_rgb = load_palette(fdother_path)
    print(f"调色板加载成功 ({len(palette_rgb)} 颜色)")
    
    dynamic_indices = {
        "scene_0_index": ord('R'),  # 82
        "scene_32_index": ord('?'),  # 63
    }
    
    print("\n提取 _FDOTHER.DAT__7 使用的资源...")
    for scene_name, index in dynamic_indices.items():
        print(f"\n处理 {scene_name} (索引 {index})...")
        
        scene_dir = os.path.join(output_dir, scene_name)
        os.makedirs(scene_dir, exist_ok=True)
        
        try:
            resource_data = load_fdother_resource(fdother_path, index)
            print(f"  资源大小: {len(resource_data)} 字节")
        except Exception as e:
            print(f"  错误: 无法加载索引 {index}: {e}")
            continue
        
        if resource_data[:6] == b'LLLLLL':
            print("  ** 嵌套 DAT 格式 **")
            extract_tile_atlas(resource_data, palette_rgb, scene_dir)
    
    print(f"\n所有资源已导出到: {output_dir}")


if __name__ == "__main__":
    data_dir = r"D:\workspace\fd2_dat_freebuff\bin"
    output_dir = r"D:\workspace\fd2_dat_freebuff\output\fdother_7_tiles_fixed"
    
    print(f"数据目录: {data_dir}")
    print(f"输出目录: {output_dir}")
    print("=" * 60)
    
    extract_fdother7_tiles(data_dir, output_dir)
    
    print("\n=== 完成 ===")
