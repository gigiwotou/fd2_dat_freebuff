#!/usr/bin/env python3
"""
重新分析嵌套DAT图像渲染问题
检查是否可以通过对比直接索引和嵌套DAT的差异找出解决方案
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

def compare_direct_vs_nested():
    """
    比较直接索引和嵌套DAT的差异
    """
    print("比较直接索引和嵌套DAT的图像特征...")
    
    # 选取一个直接索引的320x200图像（已知正确）
    direct_idx = 11  # 已知正确的320x200图像
    direct_data, _, _ = read_dat_resource(data, 0, direct_idx)
    
    if direct_data and len(direct_data) >= 4:
        w = struct.unpack_from('<H', direct_data, 0)[0]
        h = struct.unpack_from('<H', direct_data, 2)[0]
        print(f"直接索引 {direct_idx} 尺寸: {w}x{h}")
        
        # 分析直接索引的像素分布
        rle_data = direct_data[4:]
        try:
            decompressed = decompress_rle(rle_data, w, h)
            unique_colors = set(decompressed)
            print(f"直接索引图像像素值统计:")
            print(f"  总像素数: {len(decompressed)}")
            print(f"  唯一颜色数: {len(unique_colors)}")
            print(f"  颜色范围: {min(decompressed)} - {max(decompressed)}")
            
            # 统计最常见的颜色
            color_counts = {}
            for pixel in decompressed:
                color_counts[pixel] = color_counts.get(pixel, 0) + 1
            
            sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
            print(f"  最常见颜色前5: {sorted_colors[:5]}")
            
        except Exception as e:
            print(f"直接索引解压错误: {e}")
    
    # 比较嵌套DAT中的一个图像
    nested_idx = 7
    tile_idx = 1
    nested_data, _, _ = read_dat_resource(data, 0, nested_idx)
    
    if nested_data:
        tile_data, _, _ = read_nested_dat_resource(nested_data, tile_idx)
        if tile_data and len(tile_data) >= 5:
            w = struct.unpack_from('<H', tile_data, 0)[0]
            h = struct.unpack_from('<H', tile_data, 2)[0]
            shift_val = tile_data[4]
            print(f"\\n嵌套DAT {nested_idx} tile {tile_idx} 尺寸: {w}x{h}, 偏移值: 0x{shift_val:02X}")
            
            # 分析嵌套DAT的像素分布
            rle_data = tile_data[5:]
            try:
                decompressed = decompress_rle(rle_data, w, h)
                unique_colors = set(decompressed)
                print(f"嵌套DAT图像像素值统计:")
                print(f"  总像素数: {len(decompressed)}")
                print(f"  唯一颜色数: {len(unique_colors)}")
                print(f"  颜色范围: {min(decompressed)} - {max(decompressed)}")
                
                # 统计最常见的颜色
                color_counts = {}
                for pixel in decompressed:
                    color_counts[pixel] = color_counts.get(pixel, 0) + 1
                
                sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
                print(f"  最常见颜色前5: {sorted_colors[:5]}")
                
                # 尝试应用偏移并再次统计
                shifted_data = [(pixel + shift_val) % 256 for pixel in decompressed]
                shifted_unique_colors = set(shifted_data)
                shifted_color_counts = {}
                for pixel in shifted_data:
                    shifted_color_counts[pixel] = shifted_color_counts.get(pixel, 0) + 1
                shifted_sorted_colors = sorted(shifted_color_counts.items(), key=lambda x: x[1], reverse=True)
                
                print(f"\\n应用偏移后的统计:")
                print(f"  唯一颜色数: {len(shifted_unique_colors)}")
                print(f"  颜色范围: {min(shifted_data)} - {max(shifted_data)}")
                print(f"  最常见颜色前5: {shifted_sorted_colors[:5]}")
                
            except Exception as e:
                print(f"嵌套DAT解压错误: {e}")

def try_alternative_method():
    """
    尝试替代方法 - 可能需要使用不同的调色板或变换
    """
    print("\\n尝试替代方法...")
    
    # 测试一个嵌套DAT图像
    nested_idx = 7
    tile_idx = 1
    output_dir = f"{WORKSPACE}/output/alternative_approach"
    os.makedirs(output_dir, exist_ok=True)
    
    nested_data, _, _ = read_dat_resource(data, 0, nested_idx)
    if nested_data:
        tile_data, _, _ = read_nested_dat_resource(nested_data, tile_idx)
        if tile_data and len(tile_data) >= 5:
            w = struct.unpack_from('<H', tile_data, 0)[0]
            h = struct.unpack_from('<H', tile_data, 2)[0]
            shift_val = tile_data[4]
            
            print(f"处理嵌套DAT {nested_idx} tile {tile_idx}: {w}x{h}, 偏移值=0x{shift_val:02X}")
            
            rle_data = tile_data[5:]
            try:
                decompressed = decompress_rle(rle_data, w, h)
                
                # 加载基础调色板
                base_palette = load_palette(0)
                if not base_palette:
                    print("无法加载基础调色板")
                    return
                
                # 方法1: 使用调色板环移 (palette cycling)
                # 将调色板按照shift_val进行循环移动
                cycled_palette = [base_palette[(i - shift_val) % 256] for i in range(256)]
                
                img = Image.new('RGB', (w, h))
                for y in range(h):
                    for x in range(w):
                        px_idx = y * w + x
                        if px_idx < len(decompressed):
                            pal_val = decompressed[px_idx]
                            if pal_val < 256:
                                img.putpixel((x, y), cycled_palette[pal_val])
                            else:
                                img.putpixel((x, y), (0, 0, 0))
                
                filename = f"nested_{nested_idx:02d}_tile_{tile_idx:02d}_{w}x{h}_cycled.png"
                img.save(os.path.join(output_dir, filename))
                print(f"  生成循环调色板图像: {filename}")
                
                # 方法2: 尝试反向偏移（减法而不是加法）
                img_reverse = Image.new('RGB', (w, h))
                for y in range(h):
                    for x in range(w):
                        px_idx = y * w + x
                        if px_idx < len(decompressed):
                            # 使用反向偏移
                            adjusted_val = (decompressed[px_idx] - shift_val) % 256
                            if adjusted_val < 256:
                                img_reverse.putpixel((x, y), base_palette[adjusted_val])
                            else:
                                img_reverse.putpixel((x, y), (0, 0, 0))
                
                filename_rev = f"nested_{nested_idx:02d}_tile_{tile_idx:02d}_{w}x{h}_reverse_shift.png"
                img_reverse.save(os.path.join(output_dir, filename_rev))
                print(f"  生成反向偏移图像: {filename_rev}")
                
                # 方法3: 尝试只使用调色板的一部分
                # 使用shift_val作为起始点，将像素值映射到调色板的不同区域
                img_partial = Image.new('RGB', (w, h))
                for y in range(h):
                    for x in range(w):
                        px_idx = y * w + x
                        if px_idx < len(decompressed):
                            # 将像素值映射到从shift_val开始的调色板区域
                            mapped_idx = (shift_val + decompressed[px_idx]) % 256
                            if mapped_idx < 256:
                                img_partial.putpixel((x, y), base_palette[mapped_idx])
                            else:
                                img_partial.putpixel((x, y), (0, 0, 0))
                
                filename_part = f"nested_{nested_idx:02d}_tile_{tile_idx:02d}_{w}x{h}_partial_map.png"
                img_partial.save(os.path.join(output_dir, filename_part))
                print(f"  生成部分映射图像: {filename_part}")
                
            except Exception as e:
                print(f"处理错误: {e}")

# 执行分析
compare_direct_vs_nested()
try_alternative_method()

print(f"\\n分析完成，替代方法的图像已保存到: d:\\workspace\\fd2_dat_freebuff\\output\\alternative_approach")