#!/usr/bin/env python3
"""
最终版提取脚本 - 正确解析嵌套DAT结构

结构:
- [0-5]: LLLLLL magic
- [6-9]: 未知值 (不是资源数)
- [10-13]: Tile 0 起始偏移
- [14-17]: Tile 1 起始偏移
- [18-21]: Tile 2 起始偏移
- ...直到某个偏移 >= 文件大小

Tile 数据:
- 直接是RLE压缩的像素数据（没有宽高头）
- 需要通过其他方式获取宽高
"""
import struct
import os
from PIL import Image

def decompress_rle(src_data, width, height):
    """1:1 实现 sub_4E98D (value_1 == -1 模式)"""
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
                if dst_pos + count_1 > width * height:
                    break
                dst_pos += count_1
                count -= count_1
            elif bit7 and not bit6:
                if src_pos + count_1 > src_end:
                    break
                if dst_pos + count_1 > width * height:
                    break
                for i in range(count_1):
                    output[dst_pos] = src_data[src_pos]
                    dst_pos += 1
                    src_pos += 1
                count -= count_1
            elif not bit7 and not bit6:
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
            else:
                if src_pos >= src_end:
                    break
                if dst_pos + count_1 * 2 > width * height:
                    break
                fill = src_data[src_pos]
                src_pos += 1
                for i in range(count_1):
                    output[dst_pos + 1] = fill
                    dst_pos += 2
                count = count - count_1 - count_1
    
    return bytes(output)

def apply_palette(palette_data, pixel_data):
    """应用调色板 (6位颜色扩展到8位)"""
    palette = []
    for i in range(256):
        if i * 3 + 2 < len(palette_data):
            r = palette_data[i * 3]
            g = palette_data[i * 3 + 1]
            b = palette_data[i * 3 + 2]
            r = (r << 2) | (r >> 4)
            g = (g << 2) | (g >> 4)
            b = (b << 2) | (b >> 4)
            palette.append((r, g, b))
        else:
            palette.append((0, 0, 0))
    
    img_data = bytearray(len(pixel_data) * 3)
    for i, idx in enumerate(pixel_data):
        if idx < 256:
            img_data[i * 3] = palette[idx][0]
            img_data[i * 3 + 1] = palette[idx][1]
            img_data[i * 3 + 2] = palette[idx][2]
        else:
            img_data[i * 3] = 0
            img_data[i * 3 + 1] = 0
            img_data[i * 3 + 2] = 0
    
    return bytes(img_data)

def extract_tile_images(dat_path, output_dir):
    """提取嵌套 DAT 中的所有 tile 图片"""
    with open(dat_path, 'rb') as f:
        data = f.read()
    
    os.makedirs(output_dir, exist_ok=True)
    
    if data[:6] != b'LLLLLL':
        print(f"不是有效的 FDOTHER.DAT 文件")
        return
    
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(offset)
    
    # 提取调色板 (索引 75)
    pal_start = offsets[75]
    pal_end = offsets[76] if 76 < len(offsets) else len(data)
    palette_data = data[pal_start:pal_end]
    print(f"调色板大小: {len(palette_data)} 字节")
    
    # 获取索引 82 的资源
    res82_start = offsets[82]
    res82_end = offsets[83] if 83 < len(offsets) else len(data)
    res82 = data[res82_start:res82_end]
    
    print(f"\n索引 82 资源:")
    print(f"  大小: {len(res82)} 字节")
    
    # 解析嵌套偏移表 (只有4个有效偏移)
    tile_offsets = []
    for i in range(100):  # 最多检查100个
        offset = struct.unpack_from('<I', res82, 10 + i*4)[0]
        if offset >= len(res82):
            break
        tile_offsets.append(offset)
    
    print(f"  找到 {len(tile_offsets)} 个tile偏移")
    for i, off in enumerate(tile_offsets):
        print(f"    Tile {i}: 0x{off:X}")
    
    # 计算每个tile的大小
    tiles = []
    for i in range(len(tile_offsets) - 1):
        start = tile_offsets[i]
        end = tile_offsets[i + 1]
        tile_data = res82[start:end]
        tiles.append(tile_data)
        print(f"  Tile {i}: 大小={len(tile_data)} 字节")
    
    # 尝试不同的尺寸解压缩
    # FD2常见尺寸: 16x16, 32x32, 64x64, 320x200
    test_sizes = [(16, 16), (32, 32), (64, 64), (128, 128), (160, 100), (320, 200)]
    
    for tile_idx, tile_data in enumerate(tiles):
        print(f"\n=== Tile {tile_idx} ===")
        print(f"  数据大小: {len(tile_data)} 字节")
        
        for width, height in test_sizes:
            expected_size = width * height
            if expected_size == len(tile_data):
                print(f"  尝试 {width}x{height}...")
                
                pixel_data = decompress_rle(tile_data, width, height)
                img_rgb = apply_palette(palette_data, pixel_data)
                img = Image.frombytes('RGB', (width, height), img_rgb)
                
                output_path = os.path.join(output_dir, f'tile{tile_idx}_{width}x{height}.png')
                img.save(output_path)
                print(f"    [OK] 导出: {output_path}")
                
        # 如果没有匹配的固定尺寸，尝试根据数据大小反推
        data_len = len(tile_data)
        # 查找所有可能的宽高组合
        factors = []
        for w in range(8, 513):
            if data_len % w == 0:
                h = data_len // w
                if 8 <= h <= 512:
                    factors.append((w, h))
        
        if factors:
            print(f"  可能的尺寸组合: {factors[:5]}...")
            
            # 导出第一个可能的尺寸
            w, h = factors[0]
            pixel_data = decompress_rle(tile_data, w, h)
            img_rgb = apply_palette(palette_data, pixel_data)
            img = Image.frombytes('RGB', (w, h), img_rgb)
            
            output_path = os.path.join(output_dir, f'tile{tile_idx}_{w}x{h}_guess.png')
            img.save(output_path)
            print(f"    [猜测] 导出: {output_path}")

if __name__ == '__main__':
    dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'
    output_dir = r'D:\workspace\fd2_dat_freebuff\output\fdother7_tiles_final'
    
    extract_tile_images(dat_path, output_dir)
