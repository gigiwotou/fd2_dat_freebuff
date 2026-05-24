"""根据文档，FDOTHER_DAT__7 的 tile 数据是**未压缩**的"""
import struct
import os
from PIL import Image

fdother_path = r"D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT"
output_dir = r"D:\workspace\fd2_dat_freebuff\output\fdother_7_uncompressed"

os.makedirs(output_dir, exist_ok=True)

# 加载调色板
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

# 加载索引 82 的资源
with open(fdother_path, "rb") as f:
    f.seek(offsets[82])
    nested_data = f.read(offsets[83] - offsets[82])

print(f"嵌套 DAT 大小: {len(nested_data)}")
print(f"Magic: {nested_data[:6]}")

# 解析嵌套 DAT
offset_table_start = 10
res_count = struct.unpack("<I", nested_data[6:10])[0]
print(f"资源数量: {res_count}")

# 找到有效偏移
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

print(f"有效偏移: {len(valid_offsets)} 个")

# 根据文档，每个 tile 的格式是:
# [0:2] width (WORD)
# [2:4] height (WORD)
# [4:] 未压缩的像素数据

for idx in range(len(valid_offsets)):
    tile_start = valid_offsets[idx]
    tile_end = valid_offsets[idx + 1] if idx + 1 < len(valid_offsets) else len(nested_data)
    tile_data = nested_data[tile_start:tile_end]
    
    print(f"\nTile {idx}: {tile_start}-{tile_end}, 大小={len(tile_data)}")
    print(f"  前 8 字节: {tile_data[:8].hex()}")
    
    if len(tile_data) < 4:
        print(f"  -> 数据太小，跳过")
        continue
    
    width = struct.unpack("<H", tile_data[:2])[0]
    height = struct.unpack("<H", tile_data[2:4])[0]
    
    print(f"  Width={width}, Height={height}")
    
    # 检查合理性
    if width == 0 or height == 0 or width > 320 or height > 200:
        print(f"  -> 尺寸不合理，跳过")
        continue
    
    pixel_data = tile_data[4:]
    expected_pixels = width * height
    
    print(f"  像素数据大小: {len(pixel_data)}, 预期: {expected_pixels}")
    
    if len(pixel_data) != expected_pixels:
        print(f"  -> 像素数据大小不匹配，可能是 RLE 压缩")
        
        # 如果是 RLE 压缩，使用之前的 RLE 解压缩
        # 但这次我们知道宽高，所以可以正确解压缩
        # 先跳过，稍后处理
        continue
    
    # 创建图像
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    
    for y in range(height):
        for x in range(width):
            idx_pixel = y * width + x
            if idx_pixel < len(pixel_data):
                pal_idx = pixel_data[idx_pixel]
                if pal_idx < len(palette_rgb):
                    pixels[x, y] = palette_rgb[pal_idx]
    
    # 保存
    img_path = os.path.join(output_dir, f"tile_{idx:03d}_{width}x{height}.png")
    img.save(img_path)
    print(f"  -> 保存: {img_path}")
    
    # 放大
    if min(width, height) < 100:
        zoom = max(2, 100 // min(width, height))
        zoomed = img.resize((width * zoom, height * zoom), Image.NEAREST)
        zoomed_path = os.path.join(output_dir, f"tile_{idx:03d}_{width}x{height}_zoom{zoom}x.png")
        zoomed.save(zoomed_path)
        print(f"  -> 保存放大: {zoomed_path}")
