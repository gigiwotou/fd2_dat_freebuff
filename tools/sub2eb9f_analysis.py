#!/usr/bin/env python3
"""
分析sub_2EB9F函数的真实意图 - 通过对比正确和错误的图像
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

def create_modified_palette(original_palette, shift_value):
    """
    根据shift_value创建修改后的调色板
    这可能模拟sub_2EB9F函数的value参数对调色板的影响
    """
    if shift_value == 0:
        return original_palette
    
    modified_palette = []
    for i in range(256):
        orig_color = original_palette[i]
        # 尝试不同的修改策略
        # 策略1: RGB值加上偏移
        r = min(255, max(0, orig_color[0] + shift_value))
        g = min(255, max(0, orig_color[1] + shift_value))
        b = min(255, max(0, orig_color[2] + shift_value))
        modified_palette.append((r, g, b))
    
    return modified_palette

def create_shifted_palette(original_palette, shift_amount):
    """
    创建移位调色板 - 将调色板条目循环移位
    """
    shifted_palette = []
    for i in range(256):
        # 计算移位后的位置
        shifted_idx = (i + shift_amount) % 256
        shifted_palette.append(original_palette[shifted_idx])
    return shifted_palette

def analyze_tile_structure(tile_data, nested_idx, tile_idx):
    """分析tile结构并打印详细信息"""
    if len(tile_data) < 8:
        return None, None, None
    
    w = struct.unpack_from('<H', tile_data, 0)[0]
    h = struct.unpack_from('<H', tile_data, 2)[0]
    unknown1 = tile_data[4]  # 这是我们一直在讨论的值
    unknown2 = tile_data[5]  # 第六个字节
    
    print(f"    嵌套DAT {nested_idx} tile {tile_idx}: {w}x{h}, "
          f"offset+4=0x{unknown1:02X}, offset+5=0x{unknown2:02X}")
    
    return w, h, unknown1

# 加载基础调色板
base_palette = load_palette(0)
if not base_palette:
    print("无法加载基础调色板")
    exit(1)

# 输出目录
output_dir = f"{WORKSPACE}/output/sub2eb9f_analysis"
os.makedirs(output_dir, exist_ok=True)

# 分析特定的tile - 选择一些典型的
test_cases = [
    (7, 1),    # 嵌套DAT 7的tile 1 - 用户说调色板错误
    (12, 15),  # 嵌套DAT 12的tile 15 - 有0x60偏移值
    (63, 15),  # 嵌套DAT 63的tile 15 - 与12类似
]

print("分析sub_2EB9F函数的行为...")

for nested_idx, tile_idx in test_cases:
    print(f"\n分析嵌套DAT {nested_idx} tile {tile_idx}:")
    
    # 获取嵌套DAT数据
    nested_data, _, _ = read_dat_resource(data, 0, nested_idx)
    if not nested_data:
        continue
    
    # 获取tile数据
    tile_data, _, tile_size = read_nested_dat_resource(nested_data, tile_idx)
    if not tile_data or len(tile_data) < 6:
        continue
    
    # 分析tile结构
    w, h, offset4_value = analyze_tile_structure(tile_data, nested_idx, tile_idx)
    
    # 提取RLE数据（从offset+6开始，跳过width(2)+height(2)+offset4(1)+offset5(1)）
    rle_data = tile_data[6:]
    
    if len(rle_data) == 0:
        continue
    
    # 解压数据
    try:
        decompressed = decompress_rle(rle_data, w, h)
        
        # 尝试多种调色板修改方法
        methods = [
            ("original", base_palette),
            ("shift_by_" + str(offset4_value), create_shifted_palette(base_palette, offset4_value)),
            ("modify_by_" + str(offset4_value), create_modified_palette(base_palette, offset4_value)),
        ]
        
        for method_name, palette in methods:
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
            
            filename = f"nested_{nested_idx}_tile_{tile_idx}_{w}x{h}_{method_name}.png"
            img.save(os.path.join(output_dir, filename))
            print(f"      生成图像: {filename}")
        
    except Exception as e:
        print(f"      处理错误: {e}")

print(f"\n分析完成！输出目录: {output_dir}")

# 同时生成一些已知正确的图像用于对比
print("\n生成已知正确的图像用于对比 (直接索引):")
correct_indices = [11, 56, 61, 62, 71, 73, 97, 98, 100]
for idx in correct_indices[:3]:  # 只处理前3个以避免过多输出
    resource_data, _, size = read_dat_resource(data, 0, idx)
    if resource_data and len(resource_data) >= 6:
        w = struct.unpack_from('<H', resource_data, 0)[0]
        h = struct.unpack_from('<H', resource_data, 2)[0]
        
        rle_data = resource_data[4:]  # 跳过width(2)+height(2)
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
            
            filename = f"direct_index_{idx}_{w}x{h}_correct.png"
            img.save(os.path.join(output_dir, filename))
            print(f"  生成正确图像: {filename}")
        except Exception as e:
            print(f"  生成正确图像错误: {e}")