#!/usr/bin/env python3
"""测试sub_4EBFF的pitch逻辑"""
import struct
from PIL import Image

def load_fdother(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    offsets = []
    offset = 6
    while offset + 4 <= len(data):
        off = struct.unpack_from('<I', data, offset)[0]
        if off == 0 or off >= len(data):
            break
        offsets.append(off)
        offset += 4
    
    offsets.append(len(data))
    return data, offsets

def sub_4ec66_step(src_data, src_size):
    global ec66_ah, ec66_prev_al, ec66_src_pos
    
    if ec66_ah > 0:
        ec66_ah -= 1
        return ec66_prev_al
    
    if ec66_src_pos >= src_size:
        return 0
    
    al = src_data[ec66_src_pos]
    ec66_src_pos += 1
    
    if al > 0xC0:
        ec66_ah = al - 0xC1
        if ec66_src_pos < src_size:
            al = src_data[ec66_src_pos]
            ec66_src_pos += 1
        ec66_prev_al = al
        return al
    else:
        ec66_ah = 0
        ec66_prev_al = al
        return al

def test_no_palette_window(icon_data, width, height, pitch=320):
    """不应用调色板窗口，直接使用原始像素值"""
    global ec66_ah, ec66_prev_al, ec66_src_pos
    
    ec66_ah = 0
    ec66_prev_al = 0
    ec66_src_pos = 0
    
    # 创建320x200的缓冲区
    dst = [0] * (320 * 200)
    dst_pos = 0
    
    for row in range(height):
        row_start = dst_pos
        
        for col in range(width):
            pixel = sub_4ec66_step(icon_data, len(icon_data))
            dst[dst_pos] = pixel
            dst_pos += 1
        
        # 恢复到行首，然后移动pitch
        dst_pos = row_start + pitch
    
    # 提取图标区域
    pixels = []
    for row in range(height):
        for col in range(width):
            pixels.append(dst[row * pitch + col])
    
    return pixels

def test_simple_decode(icon_data, width, height):
    """简单解码，不使用pitch"""
    global ec66_ah, ec66_prev_al, ec66_src_pos
    
    ec66_ah = 0
    ec66_prev_al = 0
    ec66_src_pos = 0
    
    pixels = []
    for row in range(height):
        for col in range(width):
            pixel = sub_4ec66_step(icon_data, len(icon_data))
            pixels.append(pixel)
    
    return pixels

def load_palette(data, offsets):
    """加载索引0的调色板"""
    pal_start = offsets[0]
    pal_data = data[pal_start:pal_start+768]
    palette = []
    for i in range(256):
        r = pal_data[i*3]
        g = pal_data[i*3+1]
        b = pal_data[i*3+2]
        # 6bit转8bit
        r = (r << 2) | (r >> 4)
        g = (g << 2) | (g >> 4)
        b = (b << 2) | (b >> 4)
        palette.append((r, g, b))
    return palette

def main():
    filepath = 'game/FDOTHER.DAT'
    data, offsets = load_fdother(filepath)
    
    # 加载调色板
    palette = load_palette(data, offsets)
    
    # 索引1
    res_start = offsets[1]
    res_end = offsets[2]
    res_data = data[res_start:res_end]
    
    outer_w = struct.unpack_from('<H', res_data, 0)[0]
    outer_h = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4]
    
    print(f"外头: {outer_w}x{outer_h}, pal_window={pal_win}")
    
    # 解析相对偏移表
    icon_offsets = []
    pos = 6
    while pos + 4 <= len(res_data):
        rel_off = struct.unpack_from('<I', res_data, pos)[0]
        if rel_off >= len(res_data):
            break
        icon_offsets.append(rel_off)
        pos += 4
        if len(icon_offsets) >= 3:
            break
    
    # 测试图标0
    icon_idx = 0
    rel_off = icon_offsets[icon_idx]
    next_rel = icon_offsets[icon_idx + 1] if icon_idx + 1 < len(icon_offsets) else len(res_data)
    icon_data = res_data[rel_off:next_rel]
    
    print(f"\n图标{icon_idx}: {len(icon_data)}字节")
    print(f"前16字节: {' '.join(f'{b:02X}' for b in icon_data[:16])}")
    
    # 方法1: 不使用pitch，不应用palette_window
    print("\n方法1: 简单解码，不应用palette_window")
    pixels1 = test_simple_decode(icon_data, outer_w, outer_h)
    print(f"前24像素: {' '.join(f'{p:02X}' for p in pixels1[:24])}")
    
    img1 = Image.new('RGB', (outer_w, outer_h))
    pix1 = img1.load()
    for y in range(outer_h):
        for x in range(outer_w):
            pal_idx = pixels1[y * outer_w + x]
            pal_idx = pal_idx & 0xFF  # 确保在0-255范围内
            if pal_idx < 256:
                pix1[x, y] = palette[pal_idx]
            else:
                pix1[x, y] = (255, 0, 0)  # 红色表示错误
    img1.save(f'output/test_method1_{icon_idx}.png')
    
    # 方法2: 使用pitch=320，不应用palette_window
    print("\n方法2: 使用pitch=320，不应用palette_window")
    pixels2 = test_no_palette_window(icon_data, outer_w, outer_h, pitch=320)
    print(f"前24像素: {' '.join(f'{p:02X}' for p in pixels2[:24])}")
    
    img2 = Image.new('RGB', (outer_w, outer_h))
    pix2 = img2.load()
    for y in range(outer_h):
        for x in range(outer_w):
            pal_idx = pixels2[y * outer_w + x]
            pal_idx = pal_idx & 0xFF
            if pal_idx < 256:
                pix2[x, y] = palette[pal_idx]
            else:
                pix2[x, y] = (255, 0, 0)
    img2.save(f'output/test_method2_{icon_idx}.png')
    
    # 方法3: 简单解码，应用palette_window
    print(f"\n方法3: 简单解码，应用palette_window={pal_win}")
    pixels3 = [(p + pal_win) & 0xFF for p in pixels1]
    print(f"前24像素: {' '.join(f'{p:02X}' for p in pixels3[:24])}")
    
    img3 = Image.new('RGB', (outer_w, outer_h))
    pix3 = img3.load()
    for y in range(outer_h):
        for x in range(outer_w):
            pal_idx = pixels3[y * outer_w + x]
            if pal_idx < 256:
                pix3[x, y] = palette[pal_idx]
            else:
                pix3[x, y] = (255, 0, 0)
    img3.save(f'output/test_method3_{icon_idx}.png')
    
    print("\n已生成测试图像:")
    print(f"  output/test_method1_{icon_idx}.png - 简单解码，无palette_window")
    print(f"  output/test_method2_{icon_idx}.png - 使用pitch=320，无palette_window")
    print(f"  output/test_method3_{icon_idx}.png - 简单解码，有palette_window")

ec66_ah = 0
ec66_prev_al = 0
ec66_src_pos = 0

if __name__ == '__main__':
    main()
