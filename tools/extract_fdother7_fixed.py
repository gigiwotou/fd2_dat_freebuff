"""修正 RLE 解压缩，使用正确的 stride"""
import struct
import os
from PIL import Image

def load_palette(fdother_path):
    """加载调色板"""
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
    """加载资源"""
    with open(fdother_path, "rb") as f:
        f.read(6)
        count = struct.unpack("<I", f.read(4))[0]
        offsets = struct.unpack(f"<{count}I", f.read(count * 4))
        start = offsets[index]
        end = offsets[index + 1] if index + 1 < count else None
        f.seek(start)
        data = f.read(end - start) if end else f.read()
    return data

def decompress_rle_fixed(data, width, height):
    """RLE 解压缩，stride = width"""
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
                    # 跳过
                    skip_count = ((value & 0x3F) >> 2) + 1
                    dst_pos += skip_count
                    count -= skip_count
                else:
                    # 复制
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
                # 填充
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
        
        dst_pos = row_start + width  # 关键修改: stride = width
    
    return bytes(output)

def create_image(pixel_data, width, height, palette_rgb):
    """创建图像"""
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

fdother_path = r"D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT"
output_dir = r"D:\workspace\fd2_dat_freebuff\output\fdother_7_tiles_fixed"

os.makedirs(output_dir, exist_ok=True)
palette = load_palette(fdother_path)

# 加载索引 82
resource_data = load_fdother_resource(fdother_path, 82)
print(f"资源大小: {len(resource_data)}")
print(f"Magic: {resource_data[:6]}")

# 解析嵌套 DAT
offset_table_start = 10
res_count = struct.unpack("<I", resource_data[6:10])[0]
print(f"偏移数量: {res_count}")

valid_offsets = []
for i in range(res_count):
    offset_addr = offset_table_start + i * 4
    if offset_addr + 4 > len(resource_data):
        break
    offset_val = struct.unpack("<I", resource_data[offset_addr:offset_addr + 4])[0]
    offset_table_end = offset_table_start + res_count * 4
    if offset_val < len(resource_data) and offset_val >= offset_table_end:
        valid_offsets.append(offset_val)
    else:
        break

print(f"有效偏移: {len(valid_offsets)} 个")
print(f"偏移值: {valid_offsets}")

# 提取每个 tile
for idx in range(len(valid_offsets)):
    tile_start = valid_offsets[idx]
    tile_end = valid_offsets[idx + 1] if idx + 1 < len(valid_offsets) else len(resource_data)
    tile_rle = resource_data[tile_start:tile_end]
    
    print(f"\nTile {idx}: {tile_start}-{tile_end}, RLE大小={len(tile_rle)}")
    
    # 估算原始像素数
    src_pos = 0
    dst_count = 0
    while src_pos < len(tile_rle):
        value = tile_rle[src_pos]
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
            if src_pos < len(tile_rle):
                src_pos += 1
            dst_count += count
    
    print(f"  估算像素数: {dst_count}")
    
    # 尝试 80x80 (因为 6400 像素)
    if dst_count == 6400:
        w, h = 80, 80
        pixel_data = decompress_rle_fixed(tile_rle, w, h)
        img = create_image(pixel_data, w, h, palette)
        
        # 统计非零像素
        non_zero = sum(1 for p in pixel_data if p != 0)
        print(f"  非零像素: {non_zero}/{len(pixel_data)}")
        
        # 保存
        img_path = os.path.join(output_dir, f"tile_{idx:03d}_{w}x{h}.png")
        img.save(img_path)
        print(f"  -> 保存: {img_path}")
        
        # 放大 4x
        zoomed = img.resize((w * 4, h * 4), Image.NEAREST)
        zoomed_path = os.path.join(output_dir, f"tile_{idx:03d}_{w}x{h}_zoom4x.png")
        zoomed.save(zoomed_path)
        print(f"  -> 保存放大: {zoomed_path}")
