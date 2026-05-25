#!/usr/bin/env python3
"""
使用sub_4E98D的完整逻辑重新解压缩tile_16
关键：sub_4E98D可能使用不同的stride/行宽参数
"""
import struct
from PIL import Image
import os

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"
output_dir = f"{WORKSPACE}/output/tile16_debug"
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

def decompress_rle_v2(rle_data, width, height, stride=None):
    """使用sub_4E98D的完整逻辑解压缩"""
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
                # 跳过
                col_pos += count
            else:
                # 复制
                for i in range(count):
                    if src_pos < src_len and col_pos < width:
                        pixel = rle_data[src_pos]
                        src_pos += 1
                        out_pos = row_start + col_pos
                        if out_pos < len(output):
                            output[out_pos] = pixel
                        col_pos += 1
        else:
            # 填充
            if src_pos < src_len:
                fill_value = rle_data[src_pos]
                src_pos += 1
                for i in range(count):
                    if col_pos < width:
                        out_pos = row_start + col_pos
                        if out_pos < len(output):
                            output[out_pos] = fill_value
                        col_pos += 1
        
        # 换行检查
        if col_pos >= width:
            current_row += 1
            row_start += stride
            col_pos = 0
    
    return bytes(output)

# 读取索引63
idx63_data, _, _ = read_dat_resource(data, 0, 63)

# 读取tile_16
res16_data, res16_offset, res16_size = read_dat_resource(idx63_data, 0, 16)
w = struct.unpack_from('<H', res16_data, 0)[0]
h = struct.unpack_from('<H', res16_data, 2)[0]
rle_data = res16_data[4:]

print(f"tile_16: {w}x{h}")
print(f"RLE数据大小: {len(rle_data)}")
print(f"期望像素数: {w * h}")

# 尝试不同的stride值
strides_to_try = [w, w + 1, w + 2, 320, 512, 1024]

for stride in strides_to_try:
    if stride < w:
        continue
    
    decompressed = decompress_rle_v2(rle_data, w, h, stride)
    
    # 统计
    actual_pixels = w * h
    non_zero = sum(1 for v in decompressed[:actual_pixels] if v > 0)
    
    print(f"\nstride={stride}:")
    print(f"  输出缓冲区大小: {len(decompressed)}")
    print(f"  非零像素: {non_zero}/{actual_pixels} ({non_zero/actual_pixels*100:.1f}%)")
    
    # 创建图像
    img = Image.new('RGB', (w, h))
    for y in range(h):
        for x in range(w):
            px_idx = y * w + x
            if px_idx < len(decompressed):
                val = decompressed[px_idx]
                img.putpixel((x, y), (val, val, val))
    
    img_path = os.path.join(output_dir, f"tile_16_stride_{stride}.png")
    img.save(img_path)
    print(f"  已保存: {img_path}")
