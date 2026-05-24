#!/usr/bin/env python3
"""
提取嵌套DAT中的tile图片

根据反汇编sub_2EB9F:
  v9 = (WORD *)(*(DWORD *)(a5 + 4*a6 + 8) + a5);
  sub_4E98D(v9+9, *v9, v9[1], a7, a8, value);

Tile数据格式:
  [0-1] WORD: width
  [2-3] WORD: height
  [4-8] DWORD: 未知 (4字节)
  [8-9] WORD: 未知 (2字节)
  [9+]   RLE压缩像素数据
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

def extract_nested_dat_tiles(dat_path, res_index, output_dir):
    """提取指定索引的嵌套DAT中的所有tile图片"""
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
    
    # 获取指定索引的资源
    res_start = offsets[res_index]
    res_end = offsets[res_index+1] if res_index+1 < len(offsets) else len(data)
    res = data[res_start:res_end]
    
    print(f"\n索引 {res_index} 资源:")
    print(f"  大小: {len(res)} 字节")
    
    if res[:6] != b'LLLLLL':
        print(f"  不是嵌套DAT格式")
        return
    
    nested_count = struct.unpack_from('<I', res, 6)[0]
    print(f"  嵌套资源数: {nested_count}")
    
    # 提取有效偏移
    valid_offsets = []
    for i in range(nested_count):
        offset = struct.unpack_from('<I', res, 10 + i*4)[0]
        if offset < len(res):
            valid_offsets.append((i, offset))
    
    print(f"  有效偏移数: {len(valid_offsets)}")
    
    # 提取每个tile
    for tile_idx, (orig_idx, tile_offset) in enumerate(valid_offsets):
        tile_data = res[tile_offset:]
        
        if len(tile_data) < 11:
            continue
        
        width = struct.unpack_from('<H', tile_data, 0)[0]
        height = struct.unpack_from('<H', tile_data, 2)[0]
        
        print(f"\n  Tile {orig_idx} (实际{tile_idx}):")
        print(f"    偏移: 0x{tile_offset:X}")
        print(f"    宽度: {width}")
        print(f"    高度: {height}")
        
        if width > 1024 or height > 1024 or width == 0 or height == 0:
            print(f"    尺寸不合理，跳过")
            continue
        
        # RLE数据从偏移9开始
        rle_data = tile_data[9:]
        
        pixel_data = decompress_rle(rle_data, width, height)
        img_rgb = apply_palette(palette_data, pixel_data)
        img = Image.frombytes('RGB', (width, height), img_rgb)
        
        output_path = os.path.join(output_dir, f'tile{orig_idx:03d}_{width}x{height}.png')
        img.save(output_path)
        print(f"    [OK] 导出: {output_path}")

if __name__ == '__main__':
    dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'
    output_dir = r'D:\workspace\fd2_dat_freebuff\output\fdother6_tiles'
    
    extract_nested_dat_tiles(dat_path, 6, output_dir)
