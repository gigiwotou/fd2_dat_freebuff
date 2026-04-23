#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
RLE解压可视化调试脚本
尝试多种调色板组合，生成对比图
'''

import struct
import sys
from PIL import Image
import os

def load_fdother_offsets(dat_path='game/FDOTHER.DAT'):
    '''加载FDOTHER.DAT偏移表'''
    with open(dat_path, 'rb') as f:
        f.seek(10)  # skip LLLLLL magic + count
        offsets = []
        for i in range(422):
            off = struct.unpack('<I', f.read(4))[0]
            offsets.append(off)
    return offsets

def load_palette(dat_path, res_idx):
    '''加载指定资源的调色板'''
    offsets = load_fdother_offsets(dat_path)
    with open(dat_path, 'rb') as f:
        f.seek(offsets[res_idx])
        return f.read(768)

def decode_rle_verbose(src_data, width, height):
    '''详细RLE解码，跟踪每一步'''
    pixels = []
    count = width
    src_idx = 0
    
    stats = {'SKIP': 0, 'COPY': 0, 'FILL': 0, 'SPARSE': 0, 'total_src': 0}
    
    for row in range(height):
        count = width
        while count > 0:
            if src_idx >= len(src_data):
                break
            
            value = src_data[src_idx]
            src_idx += 1
            
            cnt = (value & 0x3F) + 1
            bit7 = (value >> 7) & 1
            bit6 = (value >> 6) & 1
            
            if bit7:
                if bit6:  # SKIP
                    stats['SKIP'] += 1
                    count -= cnt
                    # SKIP: advance dst without writing
                else:  # COPY
                    stats['COPY'] += 1
                    n = min(cnt, count)
                    if src_idx + n > len(src_data):
                        n = len(src_data) - src_idx
                    for i in range(n):
                        pixels.append(src_data[src_idx + i])
                        src_idx += 1
                    count -= n
            else:
                if bit6:  # FILL
                    stats['FILL'] += 1
                    if src_idx >= len(src_data):
                        break
                    fill = src_data[src_idx]
                    src_idx += 1
                    n = min(cnt, count)
                    for i in range(n):
                        pixels.append(fill)
                    count -= n
                else:  # SPARSE
                    stats['SPARSE'] += 1
                    if src_idx >= len(src_data):
                        break
                    fill = src_data[src_idx]
                    src_idx += 1
                    
                    remaining = cnt
                    while remaining > 0 and count >= 4:
                        # Skip position 0, write at position 1
                        pixels.append(fill)
                        # Skip positions 2,3
                        count -= 4
                        remaining -= 1
                    
                    # Apply formula
                    count = count - cnt - cnt
                    if count < 0:
                        count = 0
    
    stats['total_src'] = src_idx
    stats['total_pixels'] = len(pixels)
    return pixels, stats

def create_image_with_palette(pixels, width, height, palette_6bit, output_path):
    '''使用指定调色板创建PNG'''
    # Convert 6-bit palette to 8-bit
    palette_8bit = bytearray(256 * 3)
    for i in range(256):
        for c in range(3):
            v6 = palette_6bit[i * 3 + c] & 0x3F
            palette_8bit[i * 3 + c] = ((v6 << 2) | (v6 >> 4)) & 0xFF
    
    # Create image
    img = Image.frombytes('P', (width, height), bytes(pixels))
    img.putpalette(palette_8bit)
    img.save(output_path)
    return output_path

def analyze_and_export(resource_idx, palette_idx, output_dir='output/fdother_test'):
    '''分析并导出一个资源'''
    os.makedirs(output_dir, exist_ok=True)
    
    # Load offsets
    offsets = load_fdother_offsets()
    
    # Read resource
    with open('game/FDOTHER.DAT', 'rb') as f:
        start = offsets[resource_idx]
        end = offsets[resource_idx + 1] if resource_idx + 1 < 422 else 3382481
        
        f.seek(start)
        header = f.read(4)
        w = struct.unpack('<H', header[0:2])[0]
        h = struct.unpack('<H', header[2:4])[0]
        comp_data = f.read(end - start - 4)
    
    # Decode with verbose output
    pixels, stats = decode_rle_verbose(comp_data, w, h)
    
    print(f'=== Resource {resource_idx} ===')
    print(f'Dimensions: {w}x{h} = {w*h} expected pixels')
    print(f'Compressed data: {len(comp_data)} bytes')
    print(f'Decoded pixels: {len(pixels)}')
    print('RLE stats: SKIP=%d, COPY=%d, FILL=%d, SPARSE=%d' % (stats['SKIP'], stats['COPY'], stats['FILL'], stats['SPARSE']))
    print('Source bytes used: %d' % stats['total_src'])
    
    # Load palette
    palette = load_palette('game/FDOTHER.DAT', palette_idx)
    
    # Create image
    output_path = f'{output_dir}/res{resource_idx}_pal{palette_idx}.png'
    create_image_with_palette(pixels, w, h, palette, output_path)
    print(f'Saved: {output_path}')
    
    # Show color distribution
    from collections import Counter
    counts = Counter(pixels)
    non_zero = sum(cnt for val, cnt in counts.items() if val != 0)
    print(f'Non-zero pixels: {non_zero} ({non_zero*100/len(pixels):.1f}%)')
    print(f'Unique colors: {len(counts)}')
    
    return output_path

def main():
    print('=== FDOTHER RLE 解压可视化调试 ===\n')
    
    # Test multiple resources with different palettes
    test_cases = [
        # (resource_idx, palette_idx, description)
        (74, 77, 'Title with palette 77'),
        (74, 75, 'Title with palette 75'),
        (74, 7, 'Title with palette 7'),
        (99, 100, 'Overlay with palette 100'),
        (99, 7, 'Overlay with palette 7'),
        (99, 101, 'Overlay with palette 101'),
        (69, 7, 'Scroll frame 1 with palette 7'),
        (69, 100, 'Scroll frame 1 with palette 100'),
        (69, 75, 'Scroll frame 1 with palette 75'),
    ]
    
    results = []
    for res_idx, pal_idx, desc in test_cases:
        try:
            print(f'\n--- {desc} ---')
            path = analyze_and_export(res_idx, pal_idx)
            results.append((res_idx, pal_idx, path, desc))
        except Exception as e:
            print(f'Error: {e}')
    
    print('\n\n=== 生成结果汇总 ===')
    for res_idx, pal_idx, path, desc in results:
        print(f'{desc}: {path}')

if __name__ == '__main__':
    main()