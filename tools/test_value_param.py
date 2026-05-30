#!/usr/bin/env python3
"""
根据sub_2EB9F的反编译代码，分析value参数如何影响调色板
sub_2EB9F调用sub_4E98D时传入value参数，这个参数可能修改像素值
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

def decompress_rle_with_value(rle_data, width, height, value):
    """RLE解压缩，应用value参数修改像素值"""
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
                        # 应用value参数修改像素值
                        pixel = (pixel + value) & 0xFF
                        out_pos = row_start + col_pos
                        if out_pos < len(output):
                            output[out_pos] = pixel
                        col_pos += 1
        else:
            if src_pos < src_len:
                fill_value = rle_data[src_pos]
                src_pos += 1
                # 应用value参数修改填充值
                fill_value = (fill_value + value) & 0xFF
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

# 加载调色板0
pal0_data, _, _ = read_dat_resource(data, 0, 0)
palette0 = []
for i in range(256):
    r = pal0_data[i * 3]
    g = pal0_data[i * 3 + 1]
    b = pal0_data[i * 3 + 2]
    r = (r << 2) | (r >> 4)
    g = (g << 2) | (g >> 4)
    b = (b << 2) | (b >> 4)
    palette0.append((r, g, b))

# 测试嵌套DAT 63的tile 3
nested63_data, _, _ = read_dat_resource(data, 0, 63)
tile3_data, _, _ = read_dat_resource(nested63_data, 0, 3)

w = struct.unpack_from('<H', tile3_data, 0)[0]
h = struct.unpack_from('<H', tile3_data, 2)[0]
rle_data = tile3_data[4:]

output_dir = f"{WORKSPACE}/output/test_value_param"
os.makedirs(output_dir, exist_ok=True)

print(f"测试嵌套DAT 63 tile 3 (24x20) 使用不同value参数:")

# 测试不同的value值
for value in [0, 16, 32, 48, 64, 80, 96, 112, 128]:
    decompressed = decompress_rle_with_value(rle_data, w, h, value)
    
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
    
    filename = f"nested63_tile3_24x20_value{value}.png"
    img.save(os.path.join(output_dir, filename))
    print(f"  value={value}: {filename}")
