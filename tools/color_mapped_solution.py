#!/usr/bin/env python3
"""
尝试颜色索引映射方法 - 这可能是sub_2EB9F函数的真实作用
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
        # 6位颜色扩展到8位: (value << 2) | (value >> 4)
        r = (r << 2) | (r >> 4)
        g = (g << 2) | (g >> 4)
        b = (b << 2) | (b >> 4)
        palette_rgb.append((r, g, b))
    return palette_rgb

def create_color_mapped_data(decompressed_data, color_shift):
    """
    创建颜色索引映射后的数据
    这模拟sub_2EB9F函数的value参数对像素索引的影响
    """
    mapped_data = bytearray(len(decompressed_data))
    for i, pixel in enumerate(decompressed_data):
        # 将像素值加上偏移，然后模256确保在有效范围内
        new_pixel = (pixel + color_shift) % 256
        mapped_data[i] = new_pixel
    return bytes(mapped_data)

# 加载基础调色板
base_palette = load_palette(0)
if not base_palette:
    print("无法加载基础调色板")
    exit(1)

# 输出目录
output_dir = f"{WORKSPACE}/output/color_mapped_solution"
os.makedirs(output_dir, exist_ok=True)

# 测试一些关键的嵌套DAT tile
test_cases = [
    (7, 1),    # 嵌套DAT 7的tile 1 - 用户说调色板错误
    (12, 1),   # 嵌套DAT 12的tile 1 - 有0x49偏移值
    (12, 15),  # 嵌套DAT 12的tile 15 - 有0x60偏移值
    (63, 1),   # 嵌套DAT 63的tile 1 - 有0x49偏移值
    (63, 15),  # 嵌套DAT 63的tile 15 - 有0x60偏移值
]

print("使用颜色索引映射方法处理图像...")

for nested_idx, tile_idx in test_cases:
    print(f"\n处理嵌套DAT {nested_idx} tile {tile_idx}:")
    
    # 获取嵌套DAT数据
    nested_data, _, _ = read_dat_resource(data, 0, nested_idx)
    if not nested_data:
        continue
    
    # 获取tile数据
    tile_data, _, tile_size = read_nested_dat_resource(nested_data, tile_idx)
    if not tile_data or len(tile_data) < 6:
        continue
    
    # 分析tile结构
    w = struct.unpack_from('<H', tile_data, 0)[0]
    h = struct.unpack_from('<H', tile_data, 2)[0]
    color_shift = tile_data[4]  # offset+4处的值作为颜色索引偏移
    
    print(f"  尺寸: {w}x{h}, 颜色偏移: 0x{color_shift:02X} ({color_shift})")
    
    # 提取RLE数据（从offset+5开始，跳过width(2)+height(2)+color_shift(1)）
    rle_data = tile_data[5:]
    
    if len(rle_data) == 0:
        continue
    
    # 解压数据
    try:
        decompressed = decompress_rle(rle_data, w, h)
        
        # 应用颜色索引映射
        mapped_data = create_color_mapped_data(decompressed, color_shift)
        
        # 使用原始调色板渲染映射后的数据
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
        
        filename = f"nested_{nested_idx}_tile_{tile_idx}_{w}x{h}_color_mapped_shift{color_shift:02X}.png"
        img.save(os.path.join(output_dir, filename))
        print(f"  生成颜色映射图像: {filename}")
        
        # 同时生成未映射的对比图像
        img_orig = Image.new('RGB', (w, h))
        for y in range(h):
            for x in range(w):
                px_idx = y * w + x
                if px_idx < len(decompressed):
                    pal_val = decompressed[px_idx]
                    if pal_val < 256:
                        img_orig.putpixel((x, y), base_palette[pal_val])
                    else:
                        img_orig.putpixel((x, y), (0, 0, 0))
        
        filename_orig = f"nested_{nested_idx}_tile_{tile_idx}_{w}x{h}_original.png"
        img_orig.save(os.path.join(output_dir, filename_orig))
        print(f"  生成原始图像: {filename_orig}")
        
    except Exception as e:
        print(f"  处理错误: {e}")

print(f"\n颜色索引映射方法完成！输出目录: {output_dir}")
print("\n这种方法将像素索引加上offset+4处的值作为偏移量，模拟sub_2EB9F函数的value参数行为。")