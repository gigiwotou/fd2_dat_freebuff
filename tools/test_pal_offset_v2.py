#!/usr/bin/env python3
"""
测试嵌套DAT tile的调色板偏移
根据分析，tile数据结构可能是: [w:2][h:2][pal_offset:1][rle_data...]
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

# 测试嵌套DAT 63的tile 3 (24x20)
nested63_data, _, _ = read_dat_resource(data, 0, 63)
tile3_data, _, tile3_size = read_dat_resource(nested63_data, 0, 3)

print(f"嵌套DAT 63 tile 3:")
print(f"  总大小: {tile3_size}")
print(f"  前16字节: {' '.join(f'{b:02X}' for b in tile3_data[:16])}")

w = struct.unpack_from('<H', tile3_data, 0)[0]
h = struct.unpack_from('<H', tile3_data, 2)[0]
print(f"  尺寸: {w}x{h}")

# offset+4处的BYTE作为调色板偏移
pal_offset = tile3_data[4]
print(f"  offset+4处的BYTE: {pal_offset} (0x{pal_offset:02X})")

# 使用offset+5作为RLE数据开始
rle_data = tile3_data[5:]
print(f"  RLE数据大小: {len(rle_data)}")

decompressed = decompress_rle_with_palette_offset(rle_data, w, h, pal_offset)

output_dir = f"{WORKSPACE}/output/test_pal_offset_v2"
os.makedirs(output_dir, exist_ok=True)

# 保存图像
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

img.save(os.path.join(output_dir, f"nested63_tile3_paloff{pal_offset}.png"))
print(f"  已保存使用调色板偏移 {pal_offset} 的图像")

# 也测试嵌套DAT 7的tile 1
print(f"\n嵌套DAT 7 tile 1:")
nested7_data, _, _ = read_dat_resource(data, 0, 7)
tile1_data_7, _, tile1_size_7 = read_dat_resource(nested7_data, 0, 1)

print(f"  前16字节: {' '.join(f'{b:02X}' for b in tile1_data_7[:16])}")

w7 = struct.unpack_from('<H', tile1_data_7, 0)[0]
h7 = struct.unpack_from('<H', tile1_data_7, 2)[0]
pal_offset_7 = tile1_data_7[4]

print(f"  尺寸: {w7}x{h7}")
print(f"  offset+4处的BYTE: {pal_offset_7} (0x{pal_offset_7:02X})")

rle_data_7 = tile1_data_7[5:]
decompressed_7 = decompress_rle_with_palette_offset(rle_data_7, w7, h7, pal_offset_7)

img7 = Image.new('RGB', (w7, h7))
for y in range(h7):
    for x in range(w7):
        px_idx = y * w7 + x
        if px_idx < len(decompressed_7):
            pal_val = decompressed_7[px_idx]
            if pal_val < 256:
                img7.putpixel((x, y), palette0[pal_val])
            else:
                img7.putpixel((x, y), (0, 0, 0))

img7.save(os.path.join(output_dir, f"nested7_tile1_paloff{pal_offset_7}.png"))
print(f"  已保存使用调色板偏移 {pal_offset_7} 的图像")
