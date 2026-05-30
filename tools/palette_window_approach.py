#!/usr/bin/env python3
"""
基于新发现：尝试调色板窗口方法
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

# 输出目录
output_dir = f"{WORKSPACE}/output/palette_window_approach"
os.makedirs(output_dir, exist_ok=True)

# 加载基础调色板
base_palette = load_palette(0)
if not base_palette:
    print("无法加载基础调色板")
    exit(1)

# 尝试处理嵌套DAT 7 tile 1
nested_idx = 7
tile_idx = 1

nested_data, _, _ = read_dat_resource(data, 0, nested_idx)
if nested_data:
    tile_data, _, _ = read_nested_dat_resource(nested_data, tile_idx)
    if tile_data and len(tile_data) >= 5:
        w = struct.unpack_from('<H', tile_data, 0)[0]
        h = struct.unpack_from('<H', tile_data, 2)[0]
        shift_val = tile_data[4]  # 这是sub_2EB9F函数的value参数
        
        print(f"处理嵌套DAT {nested_idx} tile {tile_idx}: {w}x{h}, shift_val=0x{shift_val:02X}")
        
        rle_data = tile_data[5:]
        try:
            decompressed = decompress_rle(rle_data, w, h)
            
            # 新方法：使用shift_val作为调色板窗口的起始位置
            # 这意味着像素值0映射到调色板的shift_val位置，像素值1映射到shift_val+1位置，等等
            img = Image.new('RGB', (w, h))
            for y in range(h):
                for x in range(w):
                    px_idx = y * w + x
                    if px_idx < len(decompressed):
                        # 将像素值映射到调色板窗口
                        palette_idx = (shift_val + decompressed[px_idx]) % 256
                        if palette_idx < 256:
                            img.putpixel((x, y), base_palette[palette_idx])
                        else:
                            img.putpixel((x, y), (0, 0, 0))
            
            filename = f"nested_{nested_idx:02d}_tile_{tile_idx:02d}_{w}x{h}_window_start_{shift_val:02X}.png"
            img.save(os.path.join(output_dir, filename))
            print(f"生成窗口映射图像: {filename}")
            
            # 同时生成传统的加法偏移图像用于对比
            img_offset = Image.new('RGB', (w, h))
            for y in range(h):
                for x in range(w):
                    px_idx = y * w + x
                    if px_idx < len(decompressed):
                        # 传统的加法偏移方法
                        palette_idx = (decompressed[px_idx] + shift_val) % 256
                        if palette_idx < 256:
                            img_offset.putpixel((x, y), base_palette[palette_idx])
                        else:
                            img_offset.putpixel((x, y), (0, 0, 0))
            
            filename_offset = f"nested_{nested_idx:02d}_tile_{tile_idx:02d}_{w}x{h}_additive_offset_{shift_val:02X}.png"
            img_offset.save(os.path.join(output_dir, filename_offset))
            print(f"生成加法偏移图像: {filename_offset}")
            
            # 还可以尝试一种混合方法：将像素值作为索引，但在调色板的特定段中查找
            # 这类似于使用shift_val来选择调色板的不同"页面"
            img_mixed = Image.new('RGB', (w, h))
            for y in range(h):
                for x in range(w):
                    px_idx = y * w + x
                    if px_idx < len(decompressed):
                        # 使用像素值作为相对索引，在以shift_val为基址的区域内查找
                        relative_idx = decompressed[px_idx]
                        palette_idx = (shift_val + relative_idx) % 256
                        img_mixed.putpixel((x, y), base_palette[palette_idx])
            
            filename_mixed = f"nested_{nested_idx:02d}_tile_{tile_idx:02d}_{w}x{h}_mixed_method_{shift_val:02X}.png"
            img_mixed.save(os.path.join(output_dir, filename_mixed))
            print(f"生成混合方法图像: {filename_mixed}")
            
        except Exception as e:
            print(f"处理错误: {e}")

# 也处理嵌套DAT 12和63的一些tiles，看看是否有一致性
for nested_idx in [12, 63]:
    print(f"\\n处理嵌套DAT {nested_idx}:")
    
    nested_data, _, _ = read_dat_resource(data, 0, nested_idx)
    if nested_data:
        # 处理tile 1和15，它们有代表性的shift值
        for tile_idx in [1, 15]:
            tile_data, _, _ = read_nested_dat_resource(nested_data, tile_idx)
            if tile_data and len(tile_data) >= 5:
                w = struct.unpack_from('<H', tile_data, 0)[0]
                h = struct.unpack_from('<H', tile_data, 2)[0]
                shift_val = tile_data[4]
                
                print(f"  处理 tile {tile_idx}: {w}x{h}, shift_val=0x{shift_val:02X}")
                
                rle_data = tile_data[5:]
                try:
                    decompressed = decompress_rle(rle_data, w, h)
                    
                    # 使用窗口方法
                    img = Image.new('RGB', (w, h))
                    for y in range(h):
                        for x in range(w):
                            px_idx = y * w + x
                            if px_idx < len(decompressed):
                                palette_idx = (shift_val + decompressed[px_idx]) % 256
                                if palette_idx < 256:
                                    img.putpixel((x, y), base_palette[palette_idx])
                                else:
                                    img.putpixel((x, y), (0, 0, 0))
                    
                    filename = f"nested_{nested_idx:02d}_tile_{tile_idx:02d}_{w}x{h}_window_start_{shift_val:02X}.png"
                    img.save(os.path.join(output_dir, filename))
                    print(f"    生成图像: {filename}")
                    
                except Exception as e:
                    print(f"    处理错误: {e}")

print(f"\\n窗口方法处理完成，输出目录: {output_dir}")
print("\\n这种方法将offset+4处的值作为调色板窗口的起始位置，")
print("像素值作为相对于该起始位置的偏移量来访问调色板。")