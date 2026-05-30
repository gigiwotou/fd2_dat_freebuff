#!/usr/bin/env python3
"""
最终测试：嵌套DAT tile的正确显示方法
结合像素偏移和正确调色板的使用
"""
import struct
from PIL import Image
import os

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"

with open(dat_path, 'rb') as f:
    data = f.read()

def read_dat_resource(file_data, base_offset, index):
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

def decompress_rle_with_offset(rle_data, width, height, pixel_offset):
    """RLE解压缩，应用像素偏移"""
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
                        # 应用像素偏移
                        pixel = (pixel + pixel_offset) & 0xFF
                        out_pos = row_start + col_pos
                        if out_pos < len(output):
                            output[out_pos] = pixel
                        col_pos += 1
        else:
            if src_pos < src_len:
                fill_value = rle_data[src_pos]
                src_pos += 1
                # 应用像素偏移
                fill_value = (fill_value + pixel_offset) & 0xFF
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

# 输出目录
output_dir = f"{WORKSPACE}/output/final_nested_solution"
os.makedirs(output_dir, exist_ok=True)

# 嵌套DAT索引
nested_indices = [7, 12, 63]

for nested_idx in nested_indices:
    print(f"\n处理嵌套DAT {nested_idx}:")
    nested_data, _, _ = read_dat_resource(data, 0, nested_idx)
    if not nested_data:
        continue
    
    for tile_idx in range(1, 23):
        tile_data, _, tile_size = read_dat_resource(nested_data, 0, tile_idx)
        if not tile_data or len(tile_data) < 5:
            continue
        
        w = struct.unpack_from('<H', tile_data, 0)[0]
        h = struct.unpack_from('<H', tile_data, 2)[0]
        pixel_offset = tile_data[4]  # offset+4处的字节作为像素偏移
        
        print(f"  tile {tile_idx}: {w}x{h}, pixel_offset=0x{pixel_offset:02X}({pixel_offset})")
        
        # 使用offset+5作为RLE数据开始
        rle_data = tile_data[5:]
        
        # 使用像素偏移解压
        decompressed = decompress_rle_with_offset(rle_data, w, h, pixel_offset)
        
        # 使用调色板0渲染图像
        palette = load_palette(0)
        if not palette:
            continue
        
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
        
        filename = f"nested_{nested_idx}_tile_{tile_idx}_{w}x{h}_offset{pixel_offset:02X}.png"
        img.save(os.path.join(output_dir, filename))

print(f"\n完成！输出目录: {output_dir}")

# 同时也生成一些特殊tile使用其他调色板的版本以供比较
print("\n生成一些特殊tile使用其他调色板的版本以供比较:")

special_tiles = [
    (7, 1, 0x10),
    (12, 1, 0x60),
    (63, 1, 0x60)
]

for nested_idx, tile_idx, expected_offset in special_tiles:
    tile_data, _, tile_size = read_dat_resource(read_dat_resource(data, 0, nested_idx)[0], 0, tile_idx)
    w = struct.unpack_from('<H', tile_data, 0)[0]
    h = struct.unpack_from('<H', tile_data, 2)[0]
    pixel_offset = tile_data[4]
    
    rle_data = tile_data[5:]
    decompressed = decompress_rle_with_offset(rle_data, w, h, pixel_offset)
    
    # 测试所有调色板
    palettes = [0, 8, 57, 76, 99, 101, 102]
    for pal_idx in palettes:
        palette = load_palette(pal_idx)
        if not palette:
            continue
        
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
        
        filename = f"special_nested_{nested_idx}_tile_{tile_idx}_{w}x{h}_pal{pal_idx}_offset{pixel_offset:02X}.png"
        img.save(os.path.join(output_dir, filename))
        
    print(f"  嵌套DAT {nested_idx} tile {tile_idx} 使用所有调色板版本已生成")