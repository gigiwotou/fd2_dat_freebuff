#!/usr/bin/env python3
"""
测试嵌套DAT使用不同的调色板索引
根据游戏逻辑，可能嵌套DAT使用特定的调色板索引
"""
import struct
from PIL import Image
import os

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"

with open(dat_path, 'rb') as f:
    data = f.read()

def read_dat_resource(file_data, base_offset, index):
    """正确的DAT读取方式"""
    index_offset = base_offset + 4 * index + 6
    if index_offset + 8 > len(file_data):
        return None, 0, 0
    offset0 = struct.unpack_from('<I', file_data, index_offset)[0]
    offset1 = struct.unpack_from('<I', file_data, index_offset + 4)[0]
    size = offset1 - offset0
    if size <= 0 or offset0 >= len(file_data):
        return None, 0, 0
    resource_data = file_data[offset0:offset0 + size]
    return resource_data, offset0, size

def decompress_rle(rle_data, width, height):
    """RLE解压缩"""
    output = bytearray(width * height)
    src_pos = 0
    src_len = len(rle_data)
    row_start = 0
    col_pos = 0
    current_row = 0
    
    while current_row < height and src_pos < src_len:
        ctrl = rle_data[src_pos]
        src_pos += 1
        count = (ctrl & 0x3F) + 1
        
        if ctrl & 0x80:
            if ctrl & 0x40:
                col_pos += count
            else:
                for i in range(count):
                    if src_pos < src_len and col_pos < width:
                        pixel = rle_data[src_pos]
                        src_pos += 1
                        out_pos = row_start + col_pos
                        if out_pos < len(output):
                            output[out_pos] = pixel
                        col_pos += 1
        else:
            if src_pos < src_len:
                fill_value = rle_data[src_pos]
                src_pos += 1
                for i in range(count):
                    if col_pos < width:
                        out_pos = row_start + col_pos
                        if out_pos < len(output):
                            output[out_pos] = fill_value
                        col_pos += 1
        
        if col_pos >= width:
            current_row += 1
            row_start += width
            col_pos = 0
    
    return bytes(output)

def load_palette(pal_idx):
    """加载指定索引的调色板"""
    pal_data, _, pal_size = read_dat_resource(data, 0, pal_idx)
    if not pal_data or pal_size != 768:
        return None
    
    palette_rgb = []
    for i in range(256):
        r = pal_data[i * 3]
        g = pal_data[i * 3 + 1]
        b = pal_data[i * 3 + 2]
        r = (r << 2) | (r >> 4)
        g = (g << 2) | (g >> 4)
        b = (b << 2) | (b >> 4)
        palette_rgb.append((r, g, b))
    return palette_rgb

# 所有调色板索引
palette_indices = [0, 8, 57, 76, 99, 101, 102]

# 加载所有调色板
palettes = {}
for pal_idx in palette_indices:
    pal = load_palette(pal_idx)
    if pal:
        palettes[pal_idx] = pal
        print(f"已加载调色板 {pal_idx}")

# 测试嵌套DAT 63的tile 3 (24x20)
print(f"\n测试嵌套DAT 63 tile 3 (24x20) 使用不同调色板:")
nested63_data, _, _ = read_dat_resource(data, 0, 63)
tile3_data, _, _ = read_dat_resource(nested63_data, 0, 3)

w = struct.unpack_from('<H', tile3_data, 0)[0]
h = struct.unpack_from('<H', tile3_data, 2)[0]
rle_data = tile3_data[4:]
decompressed = decompress_rle(rle_data, w, h)

for pal_idx, palette in palettes.items():
    output_dir = f"{WORKSPACE}/output/test_nested63_pal{pal_idx}"
    os.makedirs(output_dir, exist_ok=True)
    
    img = Image.new('RGB', (w, h))
    for y in range(h):
        for x in range(w):
            px_idx = y * w + x
            if px_idx < len(decompressed):
                pal_val = decompressed[px_idx]
                if pal_val < 256:
                    img.putpixel((x, y), palette[pal_val])
                else:
                    img.putpixel((x, y), (0, 0, 0))
    
    filename = f"nested63_tile3_24x20_pal{pal_idx}.png"
    img.save(os.path.join(output_dir, filename))
    print(f"  已保存调色板 {pal_idx}: {filename}")
