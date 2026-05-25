#!/usr/bin/env python3
"""
应用正确调色板到v5_rle目录下的tile图像
"""
import struct
from PIL import Image
import os

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"
input_dir = f"{WORKSPACE}/output/nested_dat_tiles_v5_rle"
output_dir = f"{WORKSPACE}/output/nested_dat_tiles_v5_rle_colored"
os.makedirs(output_dir, exist_ok=True)

# 读取FDOTHER.DAT
with open(dat_path, 'rb') as f:
    data = f.read()

def read_dat_resource(file_data, base_offset, index):
    """正确的DAT读取方式"""
    index_offset = base_offset + 4 * index + 6
    offset0 = struct.unpack_from('<I', file_data, index_offset)[0]
    offset1 = struct.unpack_from('<I', file_data, index_offset + 4)[0]
    size = offset1 - offset0
    if size <= 0 or offset0 >= len(file_data):
        return None, 0, 0
    resource_data = file_data[offset0:offset0 + size]
    return resource_data, offset0, size

# 读取索引0的调色板
palette_data, _, _ = read_dat_resource(data, 0, 0)
print(f"索引0 (调色板): 大小 {len(palette_data)} 字节")

# 解析调色板为RGB列表
palette_rgb = []
for i in range(256):
    r = palette_data[i * 3]
    g = palette_data[i * 3 + 1]
    b = palette_data[i * 3 + 2]
    r = (r << 2) | (r >> 4)
    g = (g << 2) | (g >> 4)
    b = (b << 2) | (b >> 4)
    palette_rgb.append((r, g, b))

print(f"\n应用调色板到v5_rle目录下的图像:")
processed_count = 0
for filename in sorted(os.listdir(input_dir)):
    if not filename.endswith('.png'):
        continue
    
    input_path = os.path.join(input_dir, filename)
    
    try:
        img_gray = Image.open(input_path).convert('L')
    except:
        continue
    
    w, h = img_gray.size
    pixels_gray = img_gray.load()
    
    img_rgb = Image.new('RGB', (w, h))
    pixels_rgb = img_rgb.load()
    
    for y in range(h):
        for x in range(w):
            pal_idx = pixels_gray[x, y]
            if pal_idx < 256:
                pixels_rgb[x, y] = palette_rgb[pal_idx]
            else:
                pixels_rgb[x, y] = (0, 0, 0)
    
    output_path = os.path.join(output_dir, filename)
    img_rgb.save(output_path)
    processed_count += 1
    print(f"  已处理: {filename}")

print(f"\n完成！共处理 {processed_count} 个图像")
print(f"输出目录: {output_dir}")
