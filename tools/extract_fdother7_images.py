#!/usr/bin/env python3
"""
提取 _FDOTHER.DAT__7 使用的资源图片 (1:1 根据反汇编实现)

根据 sub_2EB9F:
  v9 = (WORD *)(*(DWORD *)(a5 + 4*a6 + 8) + a5);
  sub_4E98D(v9+9, *v9, v9[1], a7, a8, value);

Tile 头格式 (10 字节):
  [0-1] WORD: width
  [2-3] WORD: height
  [4-7] DWORD: 未知
  [8-9] WORD: 未知
  [9+]   RLE 压缩像素数据
"""

import struct
import os
from PIL import Image

def decompress_rle(src_data, width, height):
    """1:1 实现 fd2_decoder.c 的 fd2_rle_decompress (palette_offset=-1 模式)
    
    根据 sub_4E98D 反汇编:
    value = *src++;
    v12 = 2 * value;
    if (!__CFSHL__(value, 1))  // bit7 = 0
    if (!__CFSHL__(v12, 1))    // bit6 = 0
    
    控制字节格式:
    - Bit7=0, Bit6=0: Fill (填充)
    - Bit7=0, Bit6=1: Copy (复制)
    - Bit7=1, Bit6=0: Skip (跳过)
    - Bit7=1, Bit6=1: Interleaved (交错填充)
    """
    output = bytearray(width * height)
    src_pos = 0
    src_end = len(src_data)
    
    for row in range(height):
        dst_pos = row * width
        count = width
        
        while count > 0 and src_pos < src_end:
            ctrl = src_data[src_pos]
            src_pos += 1
            
            count_1 = (ctrl & 0x3F) + 1
            bit7 = (ctrl >> 7) & 1
            bit6 = (ctrl >> 6) & 1
            
            if bit7 and bit6:
                # Interleaved: 每隔一个像素填充
                if src_pos >= src_end:
                    break
                if dst_pos + count_1 * 2 > width * height:
                    break
                fill = src_data[src_pos]
                src_pos += 1
                for i in range(count_1):
                    if dst_pos + 1 < width * height:
                        output[dst_pos + 1] = fill
                    dst_pos += 2
                count = count - count_1 - count_1
            elif bit7 and not bit6:
                # Skip: 跳过像素
                if dst_pos + count_1 > width * height:
                    break
                dst_pos += count_1
                count -= count_1
            elif not bit7 and bit6:
                # Copy: 复制像素
                if src_pos + count_1 > src_end:
                    break
                if dst_pos + count_1 > width * height:
                    break
                for i in range(count_1):
                    output[dst_pos] = src_data[src_pos]
                    dst_pos += 1
                    src_pos += 1
                count -= count_1
            else:
                # Fill: 填充相同像素
                if src_pos >= src_end:
                    break
                if dst_pos + count_1 > width * height:
                    break
                fill = src_data[src_pos]
                src_pos += 1
                for i in range(count_1):
                    output[dst_pos] = fill
                    dst_pos += 1
                count -= count_1
    
    return bytes(output)

def apply_palette(palette_data, pixel_data):
    """应用调色板 (6位颜色扩展到8位)"""
    palette = []
    for i in range(256):
        if i * 3 + 2 < len(palette_data):
            r = palette_data[i * 3]
            g = palette_data[i * 3 + 1]
            b = palette_data[i * 3 + 2]
            # 6位扩展到8位: (value << 2) | (value >> 4)
            r = (r << 2) | (r >> 4)
            g = (g << 2) | (g >> 4)
            b = (b << 2) | (b >> 4)
            palette.append((r, g, b))
        else:
            palette.append((0, 0, 0))
    
    img_data = bytearray(len(pixel_data) * 3)
    for i, idx in enumerate(pixel_data):
        img_data[i * 3] = palette[idx][0]
        img_data[i * 3 + 1] = palette[idx][1]
        img_data[i * 3 + 2] = palette[idx][2]
    
    return bytes(img_data)

def extract_images(dat_path, palette_path, output_dir):
    """提取嵌套 DAT 中的所有 tile 图片"""
    with open(dat_path, 'rb') as f:
        data = f.read()
    
    with open(palette_path, 'rb') as f:
        palette_data = f.read()
    
    os.makedirs(output_dir, exist_ok=True)
    
    if data[:6] != b'LLLLLL':
        print(f"不是有效的 DAT 文件: {dat_path}")
        return
    
    count = struct.unpack_from('<I', data, 6)[0]
    print(f"资源数量: {count}")
    
    for res_idx in range(count):
        offset = struct.unpack_from('<I', data, 10 + res_idx * 4)[0]
        print(f"\n=== 资源 {res_idx} (偏移 0x{offset:X}) ===")
        
        if offset + 6 > len(data):
            continue
        
        if data[offset:offset+6] != b'LLLLLL':
            print(f"  不是嵌套 DAT，跳过")
            continue
        
        inner_count = struct.unpack_from('<I', data, offset + 6)[0]
        print(f"  内部 tile 数量: {inner_count}")
        
        offset_table_end = offset + 10 + inner_count * 4
        
        for tile_idx in range(inner_count):
            tile_offset = struct.unpack_from('<I', data, offset + 10 + tile_idx * 4)[0]
            
            if tile_offset < offset_table_end or tile_offset >= len(data):
                print(f"  Tile {tile_idx}: 偏移无效 (0x{tile_offset:X})")
                continue
            
            tile_data = data[tile_offset:]
            
            if len(tile_data) < 10:
                print(f"  Tile {tile_idx}: 数据太短")
                continue
            
            width = struct.unpack_from('<H', tile_data, 0)[0]
            height = struct.unpack_from('<H', tile_data, 2)[0]
            
            print(f"  Tile {tile_idx}: 偏移=0x{tile_offset:X}, width={width}, height={height}")
            
            if width > 1024 or height > 1024 or width == 0 or height == 0:
                print(f"    尺寸不合理，跳过")
                continue
            
            rle_data = tile_data[9:]
            
            pixel_data = decompress_rle(rle_data, width, height)
            
            img_rgb = apply_palette(palette_data, pixel_data)
            
            img = Image.frombytes('RGB', (width, height), img_rgb)
            
            output_path = os.path.join(output_dir, f'res{res_idx}_tile{tile_idx}_{width}x{height}.png')
            img.save(output_path)
            print(f"    [OK] 导出: {output_path}")

if __name__ == '__main__':
    dat_path = 'output/fdother7/scene_0_nested.dat'
    palette_path = 'output/fdother7/palette.bin'
    output_dir = 'output/fdother7/tiles'
    
    extract_images(dat_path, palette_path, output_dir)
