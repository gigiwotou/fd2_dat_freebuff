#!/usr/bin/env python3
"""验证修复后的索引1解码逻辑：1:1复现sub_4EBFF + sub_4EC66"""
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

def sub_4ec66_decode(src_data, width, height):
    """1:1复现sub_4EC66 RLE解码，不应用palette_window"""
    dst = [0] * (width * height)
    dst_idx = 0
    src_idx = 0
    src_size = len(src_data)
    
    # sub_4EC66状态变量
    ah = 0
    prev_al = 0
    
    for row in range(height):
        for col in range(width):
            if dst_idx >= width * height:
                break
            
            # sub_4EC66逻辑
            if ah > 0:
                # AH > 0: 重复之前的像素值
                ah -= 1
            else:
                # AH == 0: 读取新字节
                if src_idx >= src_size:
                    break
                
                al = src_data[src_idx]
                src_idx += 1
                
                if al > 0xC0:
                    # AL > 0xC0: 运行长度编码
                    ah = al - 0xC1
                    if src_idx < src_size:
                        al = src_data[src_idx]
                        src_idx += 1
                    prev_al = al
                else:
                    # AL <= 0xC0: 直接像素值
                    ah = 0
                    prev_al = al
            
            # sub_4EC66返回prev_al，不应用palette_window
            dst[dst_idx] = prev_al
            dst_idx += 1
    
    return dst

def render_with_palette_window(pixels, width, height, palette, palette_window):
    """渲染时应用palette_window"""
    img = Image.new('RGB', (width, height))
    pix = img.load()
    for y in range(height):
        for x in range(width):
            # 应用palette_window
            idx = (pixels[y * width + x] + palette_window) & 0xFF
            pix[x, y] = palette[idx]
    return img

def main():
    filepath = 'game/FDOTHER.DAT'
    data, offsets = load_fdother(filepath)
    palette = load_palette(data, offsets)
    
    # Index 1 resource
    res_start = offsets[1]
    res_end = offsets[2]
    res_data = data[res_start:res_end]
    
    # Parse header: [w:2][h:2][pw:1][pad:1][offsets...]
    outer_w = struct.unpack_from('<H', res_data, 0)[0]
    outer_h = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4]
    
    print(f"Header: {outer_w}x{outer_h}, palette_window={pal_win}")
    
    # Parse offset table from byte 6
    icon_offsets = []
    pos = 6
    while pos + 4 <= len(res_data):
        rel_off = struct.unpack_from('<I', res_data, pos)[0]
        if rel_off >= len(res_data):
            break
        icon_offsets.append(rel_off)
        pos += 4
    
    print(f"Icon count: {len(icon_offsets)}")
    
    # Test first 5 icons with FIXED logic
    for icon_idx in range(min(5, len(icon_offsets))):
        rel_off = icon_offsets[icon_idx]
        next_rel = icon_offsets[icon_idx + 1] if icon_idx + 1 < len(icon_offsets) else len(res_data)
        icon_data = res_data[rel_off:next_rel]
        
        print(f"\nIcon {icon_idx}: {len(icon_data)} bytes")
        print(f"  First 16 bytes: {' '.join(f'{b:02X}' for b in icon_data[:16])}")
        
        # 1:1 sub_4EC66 decode (NO palette window)
        pixels = sub_4ec66_decode(icon_data, outer_w, outer_h)
        
        # Render WITH palette window (fixed logic)
        img = render_with_palette_window(pixels, outer_w, outer_h, palette, pal_win)
        img.save(f'output/icon{icon_idx}_fixed.png')
        print(f"  Saved: output/icon{icon_idx}_fixed.png")
        
        # Show first row pixels (after palette window applied)
        first_row = [(pixels[x] + pal_win) & 0xFF for x in range(min(24, outer_w))]
        print(f"  First row (with window): {' '.join(f'{p:02X}' for p in first_row)}")

if __name__ == '__main__':
    main()
