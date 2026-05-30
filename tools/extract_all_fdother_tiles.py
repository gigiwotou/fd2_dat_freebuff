#!/usr/bin/env python3
"""
提取FDOTHER.DAT所有索引下的tile图像
"""
import struct
from PIL import Image
import os

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"
output_dir = f"{WORKSPACE}/output/fdother_all_tiles"
os.makedirs(output_dir, exist_ok=True)

# 读取FDOTHER.DAT
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
    if offset0 + size > len(file_data):
        size = len(file_data) - offset0
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

# 读取调色板
palette_data, _, _ = read_dat_resource(data, 0, 0)
palette_rgb = []
for i in range(256):
    r = palette_data[i * 3]
    g = palette_data[i * 3 + 1]
    b = palette_data[i * 3 + 2]
    r = (r << 2) | (r >> 4)
    g = (g << 2) | (g >> 4)
    b = (b << 2) | (b >> 4)
    palette_rgb.append((r, g, b))

# 分析所有索引，提取tile图像
print("提取所有tile图像:")
print(f"{'索引':<5} {'宽度':<6} {'高度':<6} {'状态'}")
print("-" * 40)

tile_count = 0
for i in range(422):
    res_data, res_offset, res_size = read_dat_resource(data, 0, i)
    if res_data is None or len(res_data) < 4:
        continue
    
    # 检查是否是tile数据
    try:
        w = struct.unpack_from('<H', res_data, 0)[0]
        h = struct.unpack_from('<H', res_data, 2)[0]
    except:
        continue
    
    # 检查是否是合理的tile尺寸
    if 0 < w <= 320 and 0 < h <= 200:
        rle_data = res_data[4:]
        
        # 尝试解压缩
        decompressed = decompress_rle(rle_data, w, h)
        
        # 检查解压缩是否成功
        actual_pixels = w * h
        non_zero = sum(1 for v in decompressed[:actual_pixels] if v > 0)
        
        if non_zero > 0:
            # 创建RGB图像
            img = Image.new('RGB', (w, h))
            for y in range(h):
                for x in range(w):
                    px_idx = y * w + x
                    if px_idx < len(decompressed):
                        pal_idx = decompressed[px_idx]
                        if pal_idx < 256:
                            img.putpixel((x, y), palette_rgb[pal_idx])
                        else:
                            img.putpixel((x, y), (0, 0, 0))
            
            # 保存
            filename = f"tile_{i}_{w}x{h}.png"
            img_path = os.path.join(output_dir, filename)
            img.save(img_path)
            
            tile_count += 1
            status = f"已保存 (非零像素: {non_zero}/{actual_pixels})"
            print(f"{i:<5} {w:<6} {h:<6} {status}")

print(f"\n共提取 {tile_count} 个tile图像")
print(f"输出目录: {output_dir}")
