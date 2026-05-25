#!/usr/bin/env python3
"""
分析tile_16的RLE解压缩问题 - 检查stride问题
"""
import struct
from PIL import Image
import os

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"
output_dir = f"{WORKSPACE}/output/nested_dat_tiles_v5_rle_debug"
os.makedirs(output_dir, exist_ok=True)

with open(dat_path, 'rb') as f:
    data = f.read()

def read_dat_resource(file_data, base_offset, index):
    """正确的DAT读取方式"""
    index_offset = base_offset + 4 * index + 6
    offset0 = struct.unpack_from('<I', file_data, index_offset)[0]
    offset1 = struct.unpack_from('<I', file_data, index_offset + 4)[0]
    size = offset1 - offset0
    if size <= 0 or offset0 >= len(file_data):
        return None, 0, 0
    resource_data = file_data[offset0:offset0 + size]
    return resource_data, offset0, size

# 读取索引63
idx63_data, _, _ = read_dat_resource(data, 0, 63)

# 读取tile_16
res16_data, res16_offset, res16_size = read_dat_resource(idx63_data, 0, 16)

w = struct.unpack_from('<H', res16_data, 0)[0]
h = struct.unpack_from('<H', res16_data, 2)[0]
rle_data = res16_data[4:]

print(f"tile_16: {w}x{h}")
print(f"RLE数据大小: {len(rle_data)}")

# 尝试不同的stride值
for stride in [w, w + 1, w + 2, 320, 512]:
    if stride < w:
        continue
    
    # 解压缩
    output = bytearray(stride * h)
    src_pos = 0
    src_len = len(rle_data)
    row_start = 0
    col_pos = 0
    current_row = 0
    
    while current_row < h and src_pos < src_len:
        ctrl = rle_data[src_pos]
        src_pos += 1
        count = (ctrl & 0x3F) + 1
        
        if ctrl & 0x80:
            if ctrl & 0x40:
                col_pos += count
            else:
                for i in range(count):
                    if src_pos < src_len and col_pos < w:
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
                    if col_pos < w:
                        out_pos = row_start + col_pos
                        if out_pos < len(output):
                            output[out_pos] = fill_value
                        col_pos += 1
        
        if col_pos >= w:
            current_row += 1
            row_start += stride
            col_pos = 0
    
    # 检查是否成功解压缩
    non_zero = sum(1 for v in output[:w*h] if v > 0)
    print(f"\nstride={stride}: 非零像素 {non_zero}/{w*h} ({non_zero/(w*h)*100:.1f}%)")
    
    # 创建图像
    img = Image.new('RGB', (w, h))
    for y in range(h):
        for x in range(w):
            px_idx = y * w + x
            if px_idx < len(output):
                val = output[px_idx]
                img.putpixel((x, y), (val, val, val))
    
    img_path = os.path.join(output_dir, f"tile_16_stride_{stride}.png")
    img.save(img_path)
    print(f"  已保存: tile_16_stride_{stride}.png")
