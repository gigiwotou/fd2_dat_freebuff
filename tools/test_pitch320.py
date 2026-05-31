#!/usr/bin/env python3
"""测试：使用pitch=320渲染，不应用palette_window"""
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

def test_with_pitch(icon_data, width, height, pitch, pal_window):
    """使用pitch渲染，应用palette_window"""
    global ec66_ah, ec66_prev_al, ec66_src_pos
    
    # 创建pitch*height的缓冲区
    dst = [0] * (pitch * height)
    
    ec66_ah = 0
    ec66_prev_al = 0
    ec66_src_pos = 0
    
    for row in range(height):
        dst_pos = row * pitch  # 行起始位置
        
        for col in range(width):
            pixel = sub_4ec66_step(icon_data, len(icon_data))
            pixel = (pixel + pal_window) & 0xFF
            dst[dst_pos + col] = pixel
    
    # 提取图标区域（去除pitch的padding）
    pixels = []
    for row in range(height):
        for col in range(width):
            pixels.append(dst[row * pitch + col])
    
    return pixels

def load_palette(data, offsets):
    pal_start = offsets[0]
    pal_data = data[pal_start:pal_start+768]
    palette = []
    for i in range(256):
        r = pal_data[i*3]
        g = pal_data[i*3+1]
        b = pal_data[i*3+2]
        r = (r << 2) | (r >> 4)
        g = (g << 2) | (g >> 4)
        b = (b << 2) | (b >> 4)
        palette.append((r, g, b))
    return palette

def main():
    filepath = 'game/FDOTHER.DAT'
    data, offsets = load_fdother(filepath)
    
    palette = load_palette(data, offsets)
    
    # 索引1
    res_start = offsets[1]
    res_end = offsets[2]
    res_data = data[res_start:res_end]
    
    outer_w = struct.unpack_from('<H', res_data, 0)[0]
    outer_h = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4]
    
    print(f"外头: {outer_w}x{outer_h}, pal_window={pal_win}")
    
    # 相对偏移表
    icon_offsets = []
    pos = 6
    while pos + 4 <= len(res_data):
        rel_off = struct.unpack_from('<I', res_data, pos)[0]
        if rel_off >= len(res_data):
            break
        icon_offsets.append(rel_off)
        pos += 4
        if len(icon_offsets) >= 20:
            break
    
    print(f"图标数量: {len(icon_offsets)}\n")
    
    # 测试方法：使用pitch=320，应用palette_window
    print("=== 方法：pitch=320，应用palette_window ===")
    for icon_idx in range(min(5, len(icon_offsets))):
        rel_off = icon_offsets[icon_idx]
        next_rel = icon_offsets[icon_idx + 1] if icon_idx + 1 < len(icon_offsets) else len(res_data)
        icon_data = res_data[rel_off:next_rel]
        
        print(f"图标{icon_idx}: {len(icon_data)}字节")
        
        # 使用pitch=320渲染
        pixels = test_with_pitch(icon_data, outer_w, outer_h, pitch=320, pal_window=pal_win)
        
        img = Image.new('RGB', (outer_w, outer_h))
        pix = img.load()
        
        for y in range(outer_h):
            for x in range(outer_w):
                pal_idx = pixels[y * outer_w + x]
                if pal_idx < 256:
                    pix[x, y] = palette[pal_idx]
                else:
                    pix[x, y] = (255, 0, 0)
        
        output_path = f'output/icon1_pitch320_{icon_idx}.png'
        img.save(output_path)
        print(f"  保存到: {output_path}\n")

ec66_ah = 0
ec66_prev_al = 0
ec66_src_pos = 0

if __name__ == '__main__':
    main()
