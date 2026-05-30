#!/usr/bin/env python3
"""
正确的嵌套DAT读取和解析
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

def decompress_rle_with_offset(rle_data, width, height, pixel_offset):
    """RLE解压缩，应用像素偏移"""
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
                        # 应用像素偏移
                        pixel = (pixel + pixel_offset) & 0xFF
                        out_pos = row_start + col_pos
                        if out_pos < len(output):
                            output[out_pos] = pixel
                        col_pos += 1
        else:
            if src_pos < src_len:
                fill_value = rle_data[src_pos]
                src_pos += 1
                # 应用像素偏移
                fill_value = (fill_value + pixel_offset) & 0xFF
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

def analyze_tile_header(tile_data, tile_idx, nested_idx):
    """分析tile头部结构"""
    if len(tile_data) < 8:
        return
    
    w = struct.unpack_from('<H', tile_data, 0)[0]
    h = struct.unpack_from('<H', tile_data, 2)[0]
    
    print(f"    tile {tile_idx}: {w}x{h}")
    print(f"      前8字节: {' '.join(f'{b:02X}' for b in tile_data[:8])}")
    
    # 检查可能的额外字段
    if len(tile_data) >= 5:
        extra1 = tile_data[4]
        print(f"      offset+4 (可能的像素偏移): 0x{extra1:02X} ({extra1})")
    if len(tile_data) >= 6:
        extra2 = tile_data[5]
        print(f"      offset+5: 0x{extra2:02X} ({extra2})")

# 输出目录
output_dir = f"{WORKSPACE}/output/corrected_nested_solution"
os.makedirs(output_dir, exist_ok=True)

# 加载调色板0
palette = load_palette(0)
if not palette:
    print("无法加载调色板0")
    exit(1)

# 嵌套DAT索引
nested_indices = [7, 12, 63]

for nested_idx in nested_indices:
    print(f"\n处理嵌套DAT {nested_idx}:")
    nested_data, _, _ = read_dat_resource(data, 0, nested_idx)
    if not nested_data:
        continue
    
    # 先分析结构
    magic = nested_data[:6]
    num_resources = struct.unpack_from('<I', nested_data, 6)[0]
    print(f"  魔数: {magic.decode('ascii', errors='ignore')}, 资源数量: {num_resources}")
    
    # 读取前几个有效的tile
    for tile_idx in range(1, min(23, num_resources)):
        tile_data, _, tile_size = read_nested_dat_resource(nested_data, tile_idx)
        if not tile_data or len(tile_data) < 5:
            continue
        
        # 分析tile头部
        analyze_tile_header(tile_data, tile_idx, nested_idx)
        
        w = struct.unpack_from('<H', tile_data, 0)[0]
        h = struct.unpack_from('<H', tile_data, 2)[0]
        pixel_offset = tile_data[4]  # offset+4处的字节作为像素偏移
        
        print(f"      使用像素偏移: 0x{pixel_offset:02X} ({pixel_offset})")
        
        # 使用offset+5作为RLE数据开始
        rle_data = tile_data[5:]
        
        if len(rle_data) == 0:
            print(f"      错误: RLE数据为空")
            continue
            
        # 使用像素偏移解压
        try:
            decompressed = decompress_rle_with_offset(rle_data, w, h, pixel_offset)
            
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
            
            filename = f"nested_{nested_idx}_tile_{tile_idx}_{w}x{h}_offset{pixel_offset:02X}.png"
            img.save(os.path.join(output_dir, filename))
            print(f"      保存图像: {filename}")
        except Exception as e:
            print(f"      解压错误: {e}")

print(f"\n完成！输出目录: {output_dir}")