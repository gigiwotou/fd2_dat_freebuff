#!/usr/bin/env python3
"""
根据IDA分析，查找嵌套DAT使用的调色板
可能嵌套DAT的索引0就是调色板
"""
import struct
from PIL import Image
import os

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"
output_dir = f"{WORKSPACE}/output/nested_dat_fixed_palettes"
os.makedirs(output_dir, exist_ok=True)

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

def load_palette_from_resource(pal_data):
    """从资源数据加载调色板"""
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

# 嵌套DAT索引
nested_indices = [7, 12, 63]

for nested_idx in nested_indices:
    print(f"\n处理嵌套DAT {nested_idx}:")
    nested_data, _, _ = read_dat_resource(data, 0, nested_idx)
    if not nested_data:
        continue
    
    # 检查嵌套DAT索引0是否是调色板
    res0_data, res0_offset, res0_size = read_dat_resource(nested_data, 0, 0)
    if res0_size == 768:
        print(f"  嵌套DAT {nested_idx} 索引0是调色板 (768字节)")
        palette = load_palette_from_resource(res0_data)
        
        # 用这个调色板处理所有tile
        for tile_idx in range(1, 30):
            tile_data, tile_offset, tile_size = read_dat_resource(nested_data, 0, tile_idx)
            if not tile_data or len(tile_data) < 4:
                continue
            
            w = struct.unpack_from('<H', tile_data, 0)[0]
            h = struct.unpack_from('<H', tile_data, 2)[0]
            rle_data = tile_data[4:]
            
            decompressed = decompress_rle(rle_data, w, h)
            
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
            
            filename = f"nested_{nested_idx}_tile_{tile_idx}_{w}x{h}_pal_nested0.png"
            img.save(os.path.join(output_dir, filename))
            print(f"  已保存: {filename}")
    else:
        print(f"  嵌套DAT {nested_idx} 索引0不是调色板 (大小: {res0_size})")
