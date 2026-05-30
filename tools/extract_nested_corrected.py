#!/usr/bin/env python3
"""
为嵌套DAT tile应用正确的调色板偏移
tile结构: [w:2][h:2][pal_offset:1][rle_data...]
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

def decompress_rle_with_palette_offset(rle_data, width, height, pal_offset):
    """RLE解压缩，应用调色板偏移"""
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
                        # 应用调色板偏移
                        pixel = (pixel + pal_offset) & 0xFF
                        out_pos = row_start + col_pos
                        if out_pos < len(output):
                            output[out_pos] = pixel
                        col_pos += 1
        else:
            if src_pos < src_len:
                fill_value = rle_data[src_pos]
                src_pos += 1
                # 应用调色板偏移
                fill_value = (fill_value + pal_offset) & 0xFF
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

# 加载调色板0
palette0 = load_palette(0)

# 输出目录
output_dir = f"{WORKSPACE}/output/nested_dat_corrected_v2"
os.makedirs(output_dir, exist_ok=True)

# 嵌套DAT索引
nested_indices = [7, 12, 63]

# 处理每个嵌套DAT
for nested_idx in nested_indices:
    print(f"\n处理嵌套DAT {nested_idx}:")
    nested_data, _, _ = read_dat_resource(data, 0, nested_idx)
    if not nested_data:
        continue
    
    # 提取tile 1-22
    for tile_idx in range(1, 23):
        tile_data, _, tile_size = read_dat_resource(nested_data, 0, tile_idx)
        if not tile_data or len(tile_data) < 5:
            continue
        
        w = struct.unpack_from('<H', tile_data, 0)[0]
        h = struct.unpack_from('<H', tile_data, 2)[0]
        
        # offset+4处的BYTE作为调色板偏移
        pal_offset = tile_data[4]
        
        # 使用offset+5作为RLE数据开始
        rle_data = tile_data[5:]
        
        # 解压缩
        decompressed = decompress_rle_with_palette_offset(rle_data, w, h, pal_offset)
        
        # 创建图像
        img = Image.new('RGB', (w, h))
        for y in range(h):
            for x in range(w):
                px_idx = y * w + x
                if px_idx < len(decompressed):
                    pal_val = decompressed[px_idx]
                    if pal_val < 256:
                        img.putpixel((x, y), palette0[pal_val])
                    else:
                        img.putpixel((x, y), (0, 0, 0))
        
        # 保存
        filename = f"nested_{nested_idx}_tile_{tile_idx}_{w}x{h}_paloff{pal_offset}.png"
        img.save(os.path.join(output_dir, filename))
        
        if tile_idx <= 3 or tile_idx % 5 == 0:
            print(f"  tile {tile_idx}: {w}x{h}, 调色板偏移={pal_offset}, 已保存")

print(f"\n完成！输出目录: {output_dir}")
