#!/usr/bin/env python3
"""
提取FDOTHER.DAT所有索引下的tile图像
包括直接索引和嵌套DAT中的tile
"""
import struct
from PIL import Image
import os

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"
output_dir = f"{WORKSPACE}/output/fdother_all_tiles_v2"
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
    """RLE解压缩 - sub_4E98D实现"""
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
        
        if col_pos >= width:
            current_row += 1
            row_start += width
            col_pos = 0
    
    return bytes(output)

# 读取调色板（索引0）
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

def save_tile_image(decompressed, w, h, filename):
    """保存tile图像"""
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
    
    img_path = os.path.join(output_dir, filename)
    img.save(img_path)
    return img_path

# 分析所有422个索引
print("分析FDOTHER.DAT所有索引:")
print(f"总索引数: 422")

tile_count = 0
nested_dat_count = 0

for i in range(422):
    res_data, res_offset, res_size = read_dat_resource(data, 0, i)
    if res_data is None or len(res_data) < 4:
        continue
    
    # 检查是否是嵌套DAT
    if res_data[:6] == b"LLLLLL":
        nested_dat_count += 1
        
        # 解析嵌套DAT
        nested_count = struct.unpack_from('<I', res_data, 6)[0]
        if nested_count > 1000:  # 防止错误解析
            continue
        
        # 提取嵌套DAT中的tile
        for j in range(nested_count):
            nested_res_data, _, _ = read_dat_resource(res_data, 0, j)
            if nested_res_data is None or len(nested_res_data) < 4:
                continue
            
            # 检查是否是tile数据
            try:
                w = struct.unpack_from('<H', nested_res_data, 0)[0]
                h = struct.unpack_from('<H', nested_res_data, 2)[0]
            except:
                continue
            
            if 0 < w <= 320 and 0 < h <= 200:
                rle_data = nested_res_data[4:]
                decompressed = decompress_rle(rle_data, w, h)
                
                actual_pixels = w * h
                non_zero = sum(1 for v in decompressed[:actual_pixels] if v > 0)
                
                if non_zero > 0:
                    filename = f"nested_{i}_tile_{j}_{w}x{h}.png"
                    save_tile_image(decompressed, w, h, filename)
                    tile_count += 1
                    
                    if tile_count <= 10 or (tile_count <= 50 and tile_count % 10 == 0):
                        print(f"  嵌套DAT[{i}] tile[{j}]: {w}x{h} (非零像素: {non_zero}/{actual_pixels})")
    
    else:
        # 检查是否是直接tile数据
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
                filename = f"tile_{i}_{w}x{h}.png"
                save_tile_image(decompressed, w, h, filename)
                tile_count += 1
                
                if tile_count <= 20 or (tile_count <= 100 and tile_count % 10 == 0):
                    print(f"直接索引[{i}]: {w}x{h} (非零像素: {non_zero}/{actual_pixels})")

print(f"\n完成！")
print(f"共提取 {tile_count} 个tile图像")
print(f"发现 {nested_dat_count} 个嵌套DAT")
print(f"输出目录: {output_dir}")
