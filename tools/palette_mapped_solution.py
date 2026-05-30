#!/usr/bin/env python3
"""
尝试另一种方法：将offset+4处的值视为调色板索引或调色板偏移
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
    """RLE解压缩，不应用任何偏移"""
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

def apply_palette_mapping(original_palette, mapping_start):
    """
    根据mapping_start创建一个新的调色板映射
    这可能模拟游戏中的调色板变化效果
    """
    new_palette = []
    for i in range(256):
        # 使用循环映射，将原调色板的某些区域映射到新位置
        mapped_idx = (i + mapping_start) % 256
        new_palette.append(original_palette[mapped_idx])
    return new_palette

# 输出目录
output_dir = f"{WORKSPACE}/output/palette_mapped_solution"
os.makedirs(output_dir, exist_ok=True)

# 加载基础调色板
base_palette = load_palette(0)
if not base_palette:
    print("无法加载基础调色板")
    exit(1)

# 嵌套DAT索引
nested_indices = [7, 12, 63]

for nested_idx in nested_indices:
    print(f"\n处理嵌套DAT {nested_idx}:")
    nested_data, _, _ = read_dat_resource(data, 0, nested_idx)
    if not nested_data:
        continue
    
    # 读取前几个有效的tile
    for tile_idx in range(1, 23):
        tile_data, _, tile_size = read_nested_dat_resource(nested_data, tile_idx)
        if not tile_data or len(tile_data) < 5:
            continue
        
        w = struct.unpack_from('<H', tile_data, 0)[0]
        h = struct.unpack_from('<H', tile_data, 2)[0]
        mapping_start = tile_data[4]  # offset+4处的字节作为调色板映射起点
        
        # 使用offset+5作为RLE数据开始
        rle_data = tile_data[5:]
        
        if len(rle_data) == 0:
            continue
            
        # 解压数据
        try:
            decompressed = decompress_rle(rle_data, w, h)
            
            # 根据mapping_start创建新的调色板
            mapped_palette = apply_palette_mapping(base_palette, mapping_start)
            
            # 渲染图像
            img = Image.new('RGB', (w, h))
            for y in range(h):
                for x in range(w):
                    px_idx = y * w + x
                    if px_idx < len(decompressed):
                        pal_val = decompressed[px_idx]
                        if pal_val < 256:
                            img.putpixel((x, y), mapped_palette[pal_val])
                        else:
                            img.putpixel((x, y), (0, 0, 0))
            
            filename = f"nested_{nested_idx}_tile_{tile_idx}_{w}x{h}_mapstart{mapping_start:02X}.png"
            img.save(os.path.join(output_dir, filename))
            print(f"  保存图像: {filename} (调色板映射起点: 0x{mapping_start:02X})")
        except Exception as e:
            print(f"  解压/渲染错误: {e}")

print(f"\n完成！输出目录: {output_dir}")
print("这种方法使用offset+4处的值作为调色板条目的起始映射点，而不是像素偏移。")