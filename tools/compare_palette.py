#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
调色板对比脚本
生成两组截图：使用RGB顺序和使用BGR顺序，对比颜色差异

用法:
  python3 compare_palette.py
'''

import struct
import os

try:
    from PIL import Image
except ImportError:
    print('错误: 需要PIL库 (pip install Pillow)')
    exit(1)

def load_dat_offsets(filepath):
    '''加载DAT文件的偏移表'''
    with open(filepath, 'rb') as f:
        # 读取魔数
        magic = f.read(6)
        if magic != b'LLLLLL':
            print(f'无效的DAT文件: {filepath}')
            return None
        
        # 读取资源数量
        count = struct.unpack('<I', f.read(4))[0]
        
        # 读取偏移表 (从0x0A开始)
        offsets = []
        for i in range(count):
            off = struct.unpack('<I', f.read(4))[0]
            offsets.append(off)
        
        return offsets

def read_resource(filepath, offsets, index):
    '''读取指定资源'''
    with open(filepath, 'rb') as f:
        start = offsets[index]
        end = offsets[index + 1] if index + 1 < len(offsets) else os.path.getsize(filepath)
        f.seek(start)
        return f.read(end - start)

def palette_6bit_to_8bit_rgb(palette_6bit):
    '''标准RGB转换（错误方式）'''
    palette_8bit = bytearray(768)
    for i in range(256):
        for c in range(3):
            v6 = palette_6bit[i * 3 + c] & 0x3F
            palette_8bit[i * 3 + c] = ((v6 << 2) | (v6 >> 4)) & 0xFF
    return palette_8bit

def palette_6bit_to_8bit_bgr(palette_6bit):
    '''BGR到RGB转换（正确方式） - 交换R和B通道'''
    palette_8bit = bytearray(768)
    for i in range(256):
        # 原始顺序: [B, G, R] (6-bit each)
        b6 = palette_6bit[i * 3 + 0] & 0x3F
        g6 = palette_6bit[i * 3 + 1] & 0x3F
        r6 = palette_6bit[i * 3 + 2] & 0x3F
        
        # 转换并重排为RGB
        palette_8bit[i * 3 + 0] = ((r6 << 2) | (r6 >> 4)) & 0xFF  # R ← 原B
        palette_8bit[i * 3 + 1] = ((g6 << 2) | (g6 >> 4)) & 0xFF  # G
        palette_8bit[i * 3 + 2] = ((b6 << 2) | (b6 >> 4)) & 0xFF  # B ← 原R
    return palette_8bit

def decode_rle(data, width, height):
    '''RLE解压（fd2_rle_decompress算法）'''
    pixels = bytearray(width * height)
    dst = 0
    src = 0
    src_end = len(data)
    
    for row in range(height):
        count = width
        
        while count > 0:
            if src >= src_end:
                break
            
            value = data[src]
            src += 1
            cnt = (value & 0x3F) + 1
            bit7 = (value >> 7) & 1
            bit6 = (value >> 6) & 1
            
            if bit7:
                if bit6:
                    # 11: SKIP
                    cnt = min(cnt, count)
                    dst += cnt
                    count -= cnt
                else:
                    # 10: COPY
                    cnt = min(cnt, count)
                    cnt = min(cnt, src_end - src)
                    if cnt > 0:
                        pixels[dst:dst+cnt] = data[src:src+cnt]
                        dst += cnt
                        src += cnt
                        count -= cnt
            else:
                if bit6:
                    # 01: FILL
                    if src >= src_end:
                        break
                    cnt = min(cnt, count)
                    fill = data[src]
                    src += 1
                    pixels[dst:dst+cnt] = bytes([fill]) * cnt
                    dst += cnt
                    count -= cnt
                else:
                    # 00: SPARSE
                    if src >= src_end:
                        break
                    fill = data[src]
                    src += 1
                    count_1 = cnt + 1
                    count = count - count_1 - count_1
                    while count_1 > 0 and count >= 4:
                        dst += 1  # skip
                        pixels[dst] = fill
                        dst += 1
                        dst += 2  # skip
                        count -= 4
                        count_1 -= 1
                    if count < 0:
                        count = 0
    
    return bytes(pixels)

def decode_image(resource_data):
    '''解码RLE图像'''
    if len(resource_data) < 4:
        return None
    
    w = struct.unpack('<H', resource_data[0:2])[0]
    h = struct.unpack('<H', resource_data[2:4])[0]
    
    if w == 0 or w > 640 or h == 0 or h > 480:
        return None
    
    try:
        pixels = decode_rle(resource_data[4:], w, h)
        return w, h, pixels
    except:
        return None

def create_comparison_png(dat_path, image_idx, palette_idx, output_dir='output/compare'):
    '''创建对比图：左侧RGB，右侧BGR'''
    os.makedirs(output_dir, exist_ok=True)
    
    # 加载DAT偏移表
    offsets = load_dat_offsets(dat_path)
    if not offsets:
        return False
    
    # 读取调色板
    if image_idx == palette_idx:
        pal_data = read_resource(dat_path, offsets, palette_idx)
    else:
        pal_data = read_resource(dat_path, offsets, palette_idx)
    
    palette_rgb = palette_6bit_to_8bit_rgb(pal_data)
    palette_bgr = palette_6bit_to_8bit_bgr(pal_data)
    
    # 读取图像
    img_data = read_resource(dat_path, offsets, image_idx)
    
    # 检查是否是嵌套DAT
    if img_data[:6] == b'LLLLLL':
        print(f'  资源 {image_idx} 是嵌套DAT，跳过')
        return False
    
    result = decode_image(img_data)
    if not result:
        print(f'  解码资源 {image_idx} 失败')
        return False
    
    w, h, pixels = result
    print(f'  图像: {w}x{h}, 调色板: FDOTHER[{palette_idx}]')
    
    # 创建两张图
    img_rgb = Image.frombytes('P', (w, h), pixels)
    img_rgb.putpalette(palette_rgb)
    
    img_bgr = Image.frombytes('P', (w, h), pixels)
    img_bgr.putpalette(palette_bgr)
    
    # 拼接对比图
    combined = Image.new('RGB', (w * 2 + 10, h))
    combined.paste(img_rgb.convert('RGB'), (0, 0))
    combined.paste(img_bgr.convert('RGB'), (w + 10, 0))
    
    # 添加标签
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(combined)
    draw.text((w // 2 - 30, h - 20), 'RGB (wrong)', fill='white')
    draw.text((w + 10 + w // 2 - 30, h - 20), 'BGR (correct)', fill='white')
    
    output_path = f'{output_dir}/compare_{image_idx}_pal{palette_idx}.png'
    combined.save(output_path)
    print(f'  已保存: {output_path}')
    
    # 也保存单独的图片
    img_bgr.save(f'{output_dir}/correct_{image_idx}_pal{palette_idx}.png')
    
    return True

def main():
    dat_path = 'game/FDOTHER.DAT'
    
    # 分析调色板
    offsets = load_dat_offsets(dat_path)
    if not offsets:
        return
    
    print('=== 调色板分析 ===')
    pal_data = read_resource(dat_path, offsets, 7)
    
    print('\n原始调色板数据 (BGR顺序):')
    print('  索引30-35 (常见游戏UI颜色):')
    for i in range(30, 36):
        b = pal_data[i*3]
        g = pal_data[i*3+1]
        r = pal_data[i*3+2]
        print(f'    [{i:3d}] B={b:02X} G={g:02X} R={r:02X}')
    
    print('\nRGB转换后 (错误):')
    pal_rgb = palette_6bit_to_8bit_rgb(pal_data)
    for i in range(30, 36):
        r = pal_rgb[i*3]
        g = pal_rgb[i*3+1]
        b = pal_rgb[i*3+2]
        print(f'    [{i:3d}] R={r:02X} G={g:02X} B={b:02X}')
    
    print('\nBGR→RGB转换后 (正确):')
    pal_bgr = palette_6bit_to_8bit_bgr(pal_data)
    for i in range(30, 36):
        r = pal_bgr[i*3]
        g = pal_bgr[i*3+1]
        b = pal_bgr[i*3+2]
        print(f'    [{i:3d}] R={r:02X} G={g:02X} B={b:02X}')
    
    print('\n=== 生成对比截图 ===')
    
    # 对比标题 (资源99)
    print('\n标题画面 (FDOTHER[99] + 调色板[100]):')
    create_comparison_png(dat_path, 99, 100)
    
    # 对比菜单 (资源9)
    print('\n菜单 (FDOTHER[9] + 调色板[7]):')
    create_comparison_png(dat_path, 9, 7)
    
    # 对比效果 (资源99 overlay)
    print('\n效果 (FDOTHER[99] overlay + 调色板[100]):')
    create_comparison_png(dat_path, 99, 100)
    
    print('\n对比图已保存到 output/compare/ 目录')
    print('左侧是RGB顺序（错误），右侧是BGR→RGB转换（正确）')

if __name__ == '__main__':
    main()