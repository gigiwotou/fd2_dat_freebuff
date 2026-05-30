#!/usr/bin/env python3
"""
检查嵌套DAT的tile数据中的额外字段
根据sub_2EB9F的反编译代码，tile数据可能包含调色板偏移
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

# 加载调色板0
palette0 = load_palette(0)

# 测试嵌套DAT 63的tile 3 (24x20)
nested63_data, _, _ = read_dat_resource(data, 0, 63)
tile3_data, _, tile3_size = read_dat_resource(nested63_data, 0, 3)

print(f"嵌套DAT 63 tile 3:")
print(f"  总大小: {tile3_size}")
print(f"  前20字节: {' '.join(f'{b:02X}' for b in tile3_data[:20])}")

w = struct.unpack_from('<H', tile3_data, 0)[0]
h = struct.unpack_from('<H', tile3_data, 2)[0]
print(f"  尺寸: {w}x{h}")

# offset+4处的值
field4 = struct.unpack_from('<H', tile3_data, 4)[0]
print(f"  offset+4处的WORD: {field4} (0x{field4:04X})")
print(f"  offset+4处的BYTE: {tile3_data[4]} (0x{tile3_data[4]:02X}), {tile3_data[5]} (0x{tile3_data[5]:02X})")

# 尝试用不同的RLE起始位置解压缩
# 假设offset+8是RLE数据的开始
rle_data_v1 = tile3_data[8:]
decompressed_v1 = decompress_rle(rle_data_v1, w, h)

output_dir = f"{WORKSPACE}/output/test_rle_offset"
os.makedirs(output_dir, exist_ok=True)

# 保存用offset+8开始的RLE数据解压缩的图像
img = Image.new('RGB', (w, h))
for y in range(h):
    for x in range(w):
        px_idx = y * w + x
        if px_idx < len(decompressed_v1):
            pal_val = decompressed_v1[px_idx]
            if pal_val < 256:
                img.putpixel((x, y), palette0[pal_val])
            else:
                img.putpixel((x, y), (0, 0, 0))

img.save(os.path.join(output_dir, "nested63_tile3_offset8.png"))
print(f"  已保存使用offset+8的图像")

# 再尝试offset+6
rle_data_v2 = tile3_data[6:]
decompressed_v2 = decompress_rle(rle_data_v2, w, h)

img2 = Image.new('RGB', (w, h))
for y in range(h):
    for x in range(w):
        px_idx = y * w + x
        if px_idx < len(decompressed_v2):
            pal_val = decompressed_v2[px_idx]
            if pal_val < 256:
                img2.putpixel((x, y), palette0[pal_val])
            else:
                img2.putpixel((x, y), (0, 0, 0))

img2.save(os.path.join(output_dir, "nested63_tile3_offset6.png"))
print(f"  已保存使用offset+6的图像")

# 标准offset+4
rle_data_v3 = tile3_data[4:]
decompressed_v3 = decompress_rle(rle_data_v3, w, h)

img3 = Image.new('RGB', (w, h))
for y in range(h):
    for x in range(w):
        px_idx = y * w + x
        if px_idx < len(decompressed_v3):
            pal_val = decompressed_v3[px_idx]
            if pal_val < 256:
                img3.putpixel((x, y), palette0[pal_val])
            else:
                img3.putpixel((x, y), (0, 0, 0))

img3.save(os.path.join(output_dir, "nested63_tile3_offset4.png"))
print(f"  已保存使用offset+4的图像")
