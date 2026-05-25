#!/usr/bin/env python3
"""
修正RLE解压缩算法，处理跨行边界的跳过命令
"""
import struct
from PIL import Image
import os

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"
output_dir = f"{WORKSPACE}/output/tile16_fixed"
os.makedirs(output_dir, exist_ok=True)

with open(dat_path, 'rb') as f:
    data = f.read()

def read_dat_resource(file_data, base_offset, index):
    index_offset = base_offset + 4 * index + 6
    offset0 = struct.unpack_from('<I', file_data, index_offset)[0]
    offset1 = struct.unpack_from('<I', file_data, index_offset + 4)[0]
    size = offset1 - offset0
    if size <= 0 or offset0 >= len(file_data):
        return None, 0, 0
    resource_data = file_data[offset0:offset0 + size]
    return resource_data, offset0, size

def decompress_rle_fixed(rle_data, width, height, stride=None):
    """修正的RLE解压缩，处理跨行边界"""
    if stride is None:
        stride = width
    
    output = bytearray(stride * height)
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
                # 跳过命令 - 需要处理跨行边界
                remaining_skip = count
                while remaining_skip > 0 and current_row < height:
                    pixels_in_row = width - col_pos
                    if remaining_skip <= pixels_in_row:
                        # 可以在当前行内跳过
                        col_pos += remaining_skip
                        remaining_skip = 0
                    else:
                        # 跳过当前行剩余像素，换行
                        remaining_skip -= pixels_in_row
                        col_pos = width
                        # 换行
                        if col_pos >= width:
                            current_row += 1
                            row_start += stride
                            col_pos = 0
            else:
                # 复制命令 - 也需要处理跨行边界
                for i in range(count):
                    if src_pos >= src_len:
                        break
                    if col_pos >= width:
                        current_row += 1
                        row_start += stride
                        col_pos = 0
                    if current_row >= height:
                        break
                    
                    pixel = rle_data[src_pos]
                    src_pos += 1
                    out_pos = row_start + col_pos
                    if out_pos < len(output):
                        output[out_pos] = pixel
                    col_pos += 1
        else:
            # 填充命令 - 也需要处理跨行边界
            if src_pos < src_len:
                fill_value = rle_data[src_pos]
                src_pos += 1
                
                remaining_fill = count
                while remaining_fill > 0 and current_row < height:
                    if col_pos >= width:
                        current_row += 1
                        row_start += stride
                        col_pos = 0
                    if current_row >= height:
                        break
                    
                    pixels_in_row = width - col_pos
                    fill_this_row = min(remaining_fill, pixels_in_row)
                    for j in range(fill_this_row):
                        out_pos = row_start + col_pos
                        if out_pos < len(output):
                            output[out_pos] = fill_value
                        col_pos += 1
                    remaining_fill -= fill_this_row
        
        # 最终换行检查
        if col_pos >= width:
            current_row += 1
            row_start += stride
            col_pos = 0
    
    return bytes(output)

# 读取索引63
idx63_data, _, _ = read_dat_resource(data, 0, 63)

# 读取tile_16
res16_data, _, _ = read_dat_resource(idx63_data, 0, 16)
w = struct.unpack_from('<H', res16_data, 0)[0]
h = struct.unpack_from('<H', res16_data, 2)[0]
rle_data = res16_data[4:]

print(f"tile_16: {w}x{h}")
print(f"RLE数据大小: {len(rle_data)}")
print(f"期望像素数: {w * h}")

# 使用修正的算法解压缩
decompressed = decompress_rle_fixed(rle_data, w, h, w)

# 统计
actual_pixels = w * h
non_zero = sum(1 for v in decompressed[:actual_pixels] if v > 0)
print(f"解压缩像素数: {len(decompressed)}")
print(f"非零像素: {non_zero}/{actual_pixels} ({non_zero/actual_pixels*100:.1f}%)")

# 创建图像
img = Image.new('RGB', (w, h))
for y in range(h):
    for x in range(w):
        px_idx = y * w + x
        if px_idx < len(decompressed):
            val = decompressed[px_idx]
            img.putpixel((x, y), (val, val, val))

img_path = os.path.join(output_dir, f"tile_16_fixed_{w}x{h}.png")
img.save(img_path)
print(f"已保存: {img_path}")
