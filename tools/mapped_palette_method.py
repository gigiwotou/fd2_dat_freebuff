#!/usr/bin/env python3
"""
尝试其他可能的映射方法
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

def read_nested_dat_resource(nested_data, index):
    """读取嵌套DAT中的资源"""
    if len(nested_data) < 10:
        return None, 0, 0
    
    # 检查魔数
    magic = nested_data[:6]
    if magic != b'LLLLLL':
        return None, 0, 0
    
    num_resources = struct.unpack_from('<I', nested_data, 6)[0]
    if index >= num_resources or index < 0:
        return None, 0, 0
    
    # 计算偏移位置
    offset_pos = 6 + 4 + index * 4  # 魔数(6) + 资源数量(4) + 索引*4
    if offset_pos + 4 > len(nested_data):
        return None, 0, 0
    
    offset = struct.unpack_from('<I', nested_data, offset_pos)[0]
    
    # 计算大小
    if index < num_resources - 1:
        next_offset_pos = offset_pos + 4
        if next_offset_pos + 4 <= len(nested_data):
            next_offset = struct.unpack_from('<I', nested_data, next_offset_pos)[0]
            size = next_offset - offset
        else:
            # 如果无法获取下一个偏移，则读取到文件末尾
            size = len(nested_data) - offset
    else:
        # 最后一个资源到文件结束
        size = len(nested_data) - offset
    
    # 检查偏移是否合理
    if offset >= len(nested_data) or size <= 0 or size > 100000:  # 限制最大大小防止错误
        return None, 0, 0
    
    resource_data = nested_data[offset:offset + size]
    return resource_data, offset, size

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
        # 6位颜色扩展到8位: (value << 2) | (value >> 4)
        r = (r << 2) | (r >> 4)
        g = (g << 2) | (g >> 4)
        b = (b << 2) | (b >> 4)
        palette_rgb.append((r, g, b))
    return palette_rgb

def find_closest_palette_idx(value):
    """尝试找到最接近的已知调色板索引"""
    known_palette_indices = [0, 8, 57, 76, 99, 101, 102]
    
    # 尝试直接匹配
    if value in known_palette_indices:
        return value
    
    # 尝试模运算（可能所有调色板都在同一个组中）
    for idx in known_palette_indices:
        if value % 256 == idx:  # 简单的模运算
            return idx
    
    # 找最接近的值
    closest = min(known_palette_indices, key=lambda x: abs(x - value))
    return closest

# 输出目录
output_dir = f"{WORKSPACE}/output/mapped_palette_method"
os.makedirs(output_dir, exist_ok=True)

# 已知的调色板索引
known_palette_indices = {0, 8, 57, 76, 99, 101, 102}

print("使用映射方法将offset+4值映射到已知调色板索引...")

# 特别处理您提到的图像：nested_7_tile_1_61x7_pal8.png 和 nested_7_tile_2_61x7_pal8.png
nested_idx = 7
nested_data, _, _ = read_dat_resource(data, 0, nested_idx)
if nested_data:
    for tile_idx in [1, 2]:  # 您提到的正确图像对应的tile
        tile_data, _, _ = read_nested_dat_resource(nested_data, tile_idx)
        if tile_data and len(tile_data) >= 5:
            w = struct.unpack_from('<H', tile_data, 0)[0]
            h = struct.unpack_from('<H', tile_data, 2)[0]
            raw_value = tile_data[4]  # offset+4处的原始值
            mapped_value = find_closest_palette_idx(raw_value)  # 映射到已知调色板
            
            print(f"嵌套DAT {nested_idx} tile {tile_idx}: {w}x{h}, 原始值=0x{raw_value:02X}({raw_value}), 映射值={mapped_value}")
            
            # 解压数据
            rle_data = tile_data[5:]
            try:
                decompressed = decompress_rle(rle_data, w, h)
                
                # 加载映射后的调色板
                palette = load_palette(mapped_value)
                if palette:
                    # 渲染图像
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
                    
                    filename = f"nested_{nested_idx:02d}_tile_{tile_idx:02d}_{w}x{h}_pal_{mapped_value:02X}_mapped.png"
                    img.save(os.path.join(output_dir, filename))
                    print(f"  生成映射图像: {filename}")
                else:
                    print(f"  错误: 无法加载调色板 {mapped_value}")
            except Exception as e:
                print(f"  错误: {e}")

# 也处理嵌套DAT 12和63的tile 1，它们有较大的值
for nested_idx in [12, 63]:
    print(f"\\n处理嵌套DAT {nested_idx}的tile 1 (您可能提到的图像):")
    
    nested_data, _, _ = read_dat_resource(data, 0, nested_idx)
    if nested_data:
        tile_idx = 1
        tile_data, _, _ = read_nested_dat_resource(nested_data, tile_idx)
        if tile_data and len(tile_data) >= 5:
            w = struct.unpack_from('<H', tile_data, 0)[0]
            h = struct.unpack_from('<H', tile_data, 2)[0]
            raw_value = tile_data[4]  # offset+4处的原始值
            mapped_value = find_closest_palette_idx(raw_value)  # 映射到已知调色板
            
            print(f"嵌套DAT {nested_idx} tile {tile_idx}: {w}x{h}, 原始值=0x{raw_value:02X}({raw_value}), 映射值={mapped_value}")
            
            # 解压数据
            rle_data = tile_data[5:]
            try:
                decompressed = decompress_rle(rle_data, w, h)
                
                # 加载映射后的调色板
                palette = load_palette(mapped_value)
                if palette:
                    # 渲染图像
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
                    
                    filename = f"nested_{nested_idx:02d}_tile_{tile_idx:02d}_{w}x{h}_pal_{mapped_value:02X}_mapped.png"
                    img.save(os.path.join(output_dir, filename))
                    print(f"  生成映射图像: {filename}")
                else:
                    print(f"  错误: 无法加载调色板 {mapped_value}")
            except Exception as e:
                print(f"  错误: {e}")

print(f"\\n映射方法处理完成，输出目录: {output_dir}")
print("\\n这种方法尝试将offset+4的值映射到已知的调色板索引。")