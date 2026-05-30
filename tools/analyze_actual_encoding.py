#!/usr/bin/env python3
"""
分析FDOTHER.DAT中实际使用的像素编码格式
"""

import struct
from pathlib import Path
from PIL import Image

FDOTHER_PATH = Path("game/FDOTHER.DAT")

def try_rle_decode(rle_data, width, height):
    """尝试sub_4E98D RLE解码 (value_1 == -1)"""
    dst = bytearray(width * height)
    dst_idx = 0
    src_idx = 0
    
    while src_idx < len(rle_data) and dst_idx < width * height:
        ctrl = rle_data[src_idx]
        src_idx += 1
        
        bit7 = (ctrl >> 7) & 1
        bit6 = (ctrl >> 6) & 1
        count = (ctrl & 0x3F) + 1
        
        if bit7 == 0:
            if bit6 == 0:
                # FILL
                actual = min(count, width*height - dst_idx)
                if src_idx < len(rle_data):
                    val = rle_data[src_idx]
                    src_idx += 1
                    for i in range(actual):
                        if dst_idx < len(dst):
                            dst[dst_idx] = val
                            dst_idx += 1
            else:
                # COPY_SPEC
                total = count * 2
                actual = count
                if total > width*height - dst_idx:
                    actual = (width*height - dst_idx) // 2
                    total = actual * 2
                if src_idx < len(rle_data):
                    val = rle_data[src_idx]
                    src_idx += 1
                    for i in range(actual):
                        if dst_idx < len(dst):
                            dst[dst_idx] = val
                            dst_idx += 2
        else:
            if bit6 == 0:
                # SKIP
                actual = min(count, width*height - dst_idx)
                dst_idx += actual
            else:
                # COPY_STD
                actual = min(count, width*height - dst_idx, len(rle_data) - src_idx)
                for i in range(actual):
                    if dst_idx < len(dst) and src_idx < len(rle_data):
                        dst[dst_idx] = rle_data[src_idx]
                        src_idx += 1
                        dst_idx += 1
    
    return dst

def try_ec66_decode(src_data, width, height, offset):
    """尝试sub_4EC66像素解码"""
    pixel_data = src_data[offset:]
    dst = bytearray(width * height)
    
    src_pos = 0
    ah = 0
    prev_al = 0
    dst_pos = 0
    
    for row in range(height):
        for col in range(width):
            if dst_pos >= len(dst):
                break
            
            if ah > 0:
                ah -= 1
                pixel = prev_al
            else:
                if src_pos >= len(pixel_data):
                    break
                al = pixel_data[src_pos]
                src_pos += 1
                
                if al > 0xC0:
                    ah = al - 0xC1
                    if src_pos >= len(pixel_data):
                        break
                    al = pixel_data[src_pos]
                    src_pos += 1
                    prev_al = al
                    pixel = al
                else:
                    prev_al = al
                    pixel = al
            
            dst[dst_pos] = pixel
            dst_pos += 1
    
    return dst

def analyze_encoding():
    """分析实际使用的编码格式"""
    with open(FDOTHER_PATH, 'rb') as f:
        data = f.read()
    
    # 读取索引表
    offsets = []
    table_offset = 6
    while table_offset + 4 <= len(data):
        res_offset = struct.unpack_from('<I', data, table_offset)[0]
        if res_offset == 0 or res_offset > len(data):
            break
        offsets.append(res_offset)
        table_offset += 4
    
    # 索引0调色板
    idx0_data = data[offsets[0]:offsets[1]]
    
    # 测试索引1和索引3
    for idx in [1, 3]:
        idx_data = data[offsets[idx]:offsets[idx+1] if idx+1 < len(offsets) else len(data)]
        
        print(f"\n{'='*60}")
        print(f"索引{idx} 分析:")
        print(f"  数据大小: {len(idx_data)} 字节")
        print(f"  前10字节: {' '.join(f'{b:02X}' for b in idx_data[:10])}")
        
        # 读取宽高
        width = struct.unpack_from('<H', idx_data, 0)[0]
        height = struct.unpack_from('<H', idx_data, 2)[0]
        
        if width > 320 or height > 200 or width == 0 or height == 0:
            print(f"  无效的宽高: {width}x{height}")
            continue
        
        print(f"  宽高: {width}x{height}")
        print(f"  预期像素: {width*height}")
        
        # 尝试RLE解码 (偏移5开始，跳过5字节头)
        if len(idx_data) > 5:
            rle_data = idx_data[5:]
            print(f"\n  尝试RLE解码 (偏移5):")
            print(f"    RLE数据大小: {len(rle_data)}")
            print(f"    前10字节: {' '.join(f'{b:02X}' for b in rle_data[:10])}")
            
            rle_decoded = try_rle_decode(rle_data, width, height)
            
            non_zero = sum(1 for p in rle_decoded if p != 0)
            unique_vals = len(set(rle_decoded))
            print(f"    非零像素: {non_zero}/{width*height}")
            print(f"    唯一值: {unique_vals}")
            
            # 渲染
            img = Image.new('RGB', (width, height))
            for y in range(height):
                for x in range(width):
                    idx = y * width + x
                    if idx < len(rle_decoded):
                        pal_idx = rle_decoded[idx]
                        if pal_idx < 256:
                            r = idx0_data[pal_idx * 3]
                            g = idx0_data[pal_idx * 3 + 1]
                            b = idx0_data[pal_idx * 3 + 2]
                            img.putpixel((x, y), (r, g, b))
            
            img.save(f'output/idx{idx}_rle_test.png')
            print(f"    已保存: output/idx{idx}_rle_test.png")
        
        # 尝试EC66解码 (偏移0, 4, 5开始)
        for start_offset in [0, 4, 5]:
            if len(idx_data) > start_offset:
                print(f"\n  尝试EC66解码 (偏移{start_offset}):")
                
                ec66_decoded = try_ec66_decode(idx_data, width, height, start_offset)
                
                if len(ec66_decoded) > 0:
                    non_zero = sum(1 for p in ec66_decoded if p != 0)
                    unique_vals = len(set(ec66_decoded))
                    print(f"    非零像素: {non_zero}/{width*height}")
                    print(f"    唯一值: {unique_vals}")
                    
                    # 渲染
                    img = Image.new('RGB', (width, height))
                    for y in range(height):
                        for x in range(width):
                            idx = y * width + x
                            if idx < len(ec66_decoded):
                                pal_idx = ec66_decoded[idx]
                                if pal_idx < 256:
                                    r = idx0_data[pal_idx * 3]
                                    g = idx0_data[pal_idx * 3 + 1]
                                    b = idx0_data[pal_idx * 3 + 2]
                                    img.putpixel((x, y), (r, g, b))
                    
                    img.save(f'output/idx{idx}_ec66_offset{start_offset}.png')
                    print(f"    已保存: output/idx{idx}_ec66_offset{start_offset}.png")

if __name__ == '__main__':
    analyze_encoding()
