"""修正 stride 问题"""
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

def decompress_rle_v2(data, width, height, stride=None):
    """RLE 解压缩，修正 stride 处理"""
    if stride is None:
        stride = width
    
    output = bytearray(stride * height)
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
        
        # 下一行
        dst_pos = row_start + stride
    
    return bytes(output)

def create_image(pixel_data, width, height, stride, palette_rgb):
    """创建图像 (考虑 stride)"""
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    
    for y in range(height):
        for x in range(width):
            idx = y * stride + x
            if idx < len(pixel_data):
                pal_idx = pixel_data[idx]
                if pal_idx < len(palette_rgb):
                    pixels[x, y] = palette_rgb[pal_idx]
    
    return img

fdother_path = r"D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT"
output_dir = r"D:\workspace\fd2_dat_freebuff\output\fdother_7_tiles_v2"

os.makedirs(output_dir, exist_ok=True)
palette = load_palette(fdother_path)

with open(fdother_path, "rb") as f:
    f.read(6)
    count = struct.unpack("<I", f.read(4))[0]
    offsets = struct.unpack(f"<{count}I", f.read(count * 4))
    f.seek(offsets[82])
    nested_data = f.read(offsets[83] - offsets[82])

offset_table_start = 10
res_count = struct.unpack("<I", nested_data[6:10])[0]
valid_offsets = []
for i in range(res_count):
    offset_addr = offset_table_start + i * 4
    if offset_addr + 4 > len(nested_data):
        break
    offset_val = struct.unpack("<I", nested_data[offset_addr:offset_addr + 4])[0]
    offset_table_end = offset_table_start + res_count * 4
    if offset_val < len(nested_data) and offset_val >= offset_table_end:
        valid_offsets.append(offset_val)
    else:
        break

print(f"有效偏移: {valid_offsets}")

# 测试不同尺寸和 stride 组合
test_configs = [
    (80, 80, 80),
    (80, 80, 320),
    (160, 200, 320),
    (320, 200, 320),
]

for idx in range(len(valid_offsets)):
    tile_start = valid_offsets[idx]
    tile_end = valid_offsets[idx + 1] if idx + 1 < len(valid_offsets) else len(nested_data)
    tile_rle = nested_data[tile_start:tile_end]
    
    print(f"\nTile {idx}: RLE大小={len(tile_rle)}")
    
    for width, height, stride in test_configs:
        try:
            pixel_data = decompress_rle_v2(tile_rle, width, height, stride)
            
            # 检查非零像素
            non_zero = sum(1 for p in pixel_data if p != 0)
            total = width * height
            ratio = non_zero / total if total > 0 else 0
            
            if ratio > 0.05:  # 至少 5% 非零
                print(f"  {width}x{height} (stride={stride}): 非零={non_zero}/{total} ({ratio*100:.1f}%)")
                
                # 创建并保存图像
                img = create_image(pixel_data, width, height, stride, palette)
                img_path = os.path.join(output_dir, f"tile_{idx}_{width}x{height}_s{stride}.png")
                img.save(img_path)
                
                # 如果尺寸小，放大保存
                if min(width, height) < 100:
                    zoom = max(2, 100 // min(width, height))
                    zoomed = img.resize((width * zoom, height * zoom), Image.NEAREST)
                    zoomed_path = os.path.join(output_dir, f"tile_{idx}_{width}x{height}_s{stride}_zoom{zoom}x.png")
                    zoomed.save(zoomed_path)
        except Exception as e:
            print(f"  {width}x{height} (stride={stride}): 错误 - {e}")
