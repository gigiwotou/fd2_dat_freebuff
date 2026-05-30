#!/usr/bin/env python3
"""
最终尝试：使用offset+4处的值创建像素到调色板的映射
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

def apply_complex_mapping(decompressed_data, mapping_value, base_palette):
    """
    应用复杂的像素到调色板映射
    这是基于对sub_2EB9F函数行为的推测
    """
    # 创建一个像素映射表
    # 这里我们尝试多种可能的映射策略
    
    # 策略1: 使用mapping_value作为基础偏移
    mapped_pixels = bytearray(len(decompressed_data))
    for i, pixel in enumerate(decompressed_data):
        # 尝试不同的映射公式
        # 这里使用 pixel + mapping_value 作为基础，但确保在0-255范围内
        mapped_pixel = (pixel + mapping_value) % 256
        mapped_pixels[i] = mapped_pixel
    
    return bytes(mapped_pixels)

# 输出目录
output_dir = f"{WORKSPACE}/output/final_approach"
os.makedirs(output_dir, exist_ok=True)

# 加载基础调色板
base_palette = load_palette(0)
if not base_palette:
    print("无法加载基础调色板")
    exit(1)

# 测试所有有问题的嵌套DAT
nested_indices = [7, 12, 63]
for nested_idx in nested_indices:
    print(f"\\n处理嵌套DAT {nested_idx}:")
    
    nested_data, _, _ = read_dat_resource(data, 0, nested_idx)
    if not nested_data:
        print(f"  无法读取嵌套DAT {nested_idx}")
        continue
    
    # 处理嵌套DAT中的tile 1-22
    for tile_idx in range(1, 23):
        tile_data, _, tile_size = read_nested_dat_resource(nested_data, tile_idx)
        if not tile_data or len(tile_data) < 5:
            continue
        
        w = struct.unpack_from('<H', tile_data, 0)[0]
        h = struct.unpack_from('<H', tile_data, 2)[0]
        mapping_value = tile_data[4]  # offset+4处的值
        
        print(f"  处理 tile {tile_idx}: {w}x{h}, 映射值=0x{mapping_value:02X}")
        
        # 提取RLE数据
        rle_data = tile_data[5:]
        
        try:
            decompressed = decompress_rle(rle_data, w, h)
            
            # 应用像素映射
            mapped_data = apply_complex_mapping(decompressed, mapping_value, base_palette)
            
            # 渲染图像
            img = Image.new('RGB', (w, h))
            for y in range(h):
                for x in range(w):
                    px_idx = y * w + x
                    if px_idx < len(mapped_data):
                        pal_val = mapped_data[px_idx]
                        if pal_val < 256:
                            img.putpixel((x, y), base_palette[pal_val])
                        else:
                            img.putpixel((x, y), (0, 0, 0))
            
            filename = f"nested_{nested_idx:02d}_tile_{tile_idx:02d}_{w}x{h}_map_{mapping_value:02X}.png"
            img.save(os.path.join(output_dir, filename))
            print(f"    生成图像: {filename}")
            
        except Exception as e:
            print(f"    处理错误: {e}")

print(f"\\n最终处理完成，输出目录: {output_dir}")

# 也生成一些直接索引的图像用于对比
print("\\n生成直接索引图像用于对比:")
direct_indices = [11, 56, 61, 62, 71, 73, 97, 98, 100]
for idx in direct_indices[:3]:  # 只处理前3个
    resource_data, _, size = read_dat_resource(data, 0, idx)
    if resource_data and len(resource_data) >= 4:
        w = struct.unpack_from('<H', resource_data, 0)[0]
        h = struct.unpack_from('<H', resource_data, 2)[0]
        
        rle_data = resource_data[4:]
        try:
            decompressed = decompress_rle(rle_data, w, h)
            
            img = Image.new('RGB', (w, h))
            for y in range(h):
                for x in range(w):
                    px_idx = y * w + x
                    if px_idx < len(decompressed):
                        pal_val = decompressed[px_idx]
                        if pal_val < 256:
                            img.putpixel((x, y), base_palette[pal_val])
                        else:
                            img.putpixel((x, y), (0, 0, 0))
            
            filename = f"direct_{idx:03d}_{w}x{h}.png"
            img.save(os.path.join(output_dir, filename))
            print(f"  生成直接索引图像: {filename}")
        except Exception as e:
            print(f"  生成直接索引图像错误: {e}")

print("\\n所有处理完成！")