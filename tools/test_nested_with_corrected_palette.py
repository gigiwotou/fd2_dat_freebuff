#!/usr/bin/env python3
"""
测试嵌套DAT tile数据结构中的调色板选择
根据用户反馈：索引11，56，61，62，71，73，97，98，100正确，说明它们使用调色板0
嵌套DAT（7,12,63）的tile 1-22错误，说明它们应该使用不同的调色板
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

def decompress_rle(rle_data, width, height):
    """RLE解压缩，不应用调色板偏移"""
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

def get_correct_palette_index_for_nested_tile(nested_idx, tile_idx, pal_byte):
    """
    根据嵌套DAT索引和tile索引确定正确的调色板索引
    这里需要根据实际情况调整映射关系
    """
    # 已知的调色板索引
    palette_indices = [0, 8, 57, 76, 99, 101, 102]
    
    # 对于嵌套DAT，根据pal_byte确定调色板索引
    # 这可能是一个映射表，需要进一步分析
    # 目前我们只知道offset+4处的字节与调色板选择有关
    if nested_idx == 7 and tile_idx == 1:
        # 根据分析，嵌套DAT 7 tile 1的pal_byte=0x10(16)，可能对应某个特定调色板
        if pal_byte == 0x10:  # 16
            return 0  # 暂时仍使用调色板0，后续再调整
    elif nested_idx == 12 and tile_idx == 1:
        # 嵌套DAT 12 tile 1的pal_byte=0x60(96)
        if pal_byte == 0x60:  # 96
            return 0  # 暂时仍使用调色板0，后续再调整
    elif nested_idx == 63 and tile_idx == 1:
        # 嵌套DAT 63 tile 1的pal_byte=0x60(96)，和12一样
        if pal_byte == 0x60:  # 96
            return 0  # 暂时仍使用调色板0，后续再调整
    elif nested_idx == 63 and tile_idx == 3:
        # 嵌套DAT 63 tile 3的pal_byte=0x00(0)
        if pal_byte == 0x00:  # 0
            return 0  # 暂时仍使用调色板0，后续再调整
            
    # 默认使用调色板0
    return 0

# 输出目录
output_dir = f"{WORKSPACE}/output/test_nested_corrected_palette"
os.makedirs(output_dir, exist_ok=True)

# 嵌套DAT索引
nested_indices = [7, 12, 63]

for nested_idx in nested_indices:
    print(f"\n处理嵌套DAT {nested_idx}:")
    nested_data, _, _ = read_dat_resource(data, 0, nested_idx)
    if not nested_data:
        continue
    
    for tile_idx in range(1, 23):
        tile_data, _, tile_size = read_dat_resource(nested_data, 0, tile_idx)
        if not tile_data or len(tile_data) < 5:
            continue
        
        w = struct.unpack_from('<H', tile_data, 0)[0]
        h = struct.unpack_from('<H', tile_data, 2)[0]
        pal_byte = tile_data[4]  # offset+4处的字节，可能指示调色板
        
        # 获取正确的调色板
        correct_pal_idx = get_correct_palette_index_for_nested_tile(nested_idx, tile_idx, pal_byte)
        palette = load_palette(correct_pal_idx)
        if not palette:
            print(f"  无法加载调色板 {correct_pal_idx}")
            continue
        
        # 使用offset+5作为RLE数据开始
        rle_data = tile_data[5:]
        
        decompressed = decompress_rle(rle_data, w, h)
        
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
        
        filename = f"nested_{nested_idx}_tile_{tile_idx}_{w}x{h}_pal{correct_pal_idx}_byte{pal_byte:02X}.png"
        img.save(os.path.join(output_dir, filename))
        
        if tile_idx <= 5:
            print(f"  tile {tile_idx}: {w}x{h}, pal_idx={correct_pal_idx}, pal_byte=0x{pal_byte:02X}, 已保存")

print(f"\n完成！输出目录: {output_dir}")