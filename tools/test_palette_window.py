#!/usr/bin/env python3
"""Test all palette window application scenarios for index 1"""
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

def decompress_rle_raw(src_data, width, height):
    """sub_4EC66 RLE decompression WITHOUT palette window"""
    dst = [0] * (width * height)
    dst_idx = 0
    src_idx = 0
    src_size = len(src_data)
    
    ah = 0
    prev_al = 0
    
    for row in range(height):
        for col in range(width):
            if dst_idx >= width * height:
                break
            
            if ah > 0:
                ah -= 1
            else:
                if src_idx >= src_size:
                    break
                
                al = src_data[src_idx]
                src_idx += 1
                
                if al > 0xC0:
                    ah = al - 0xC1
                    if src_idx < src_size:
                        al = src_data[src_idx]
                        src_idx += 1
                    prev_al = al
                else:
                    ah = 0
                    prev_al = al
            
            # NO palette window applied
            dst[dst_idx] = prev_al
            dst_idx += 1
    
    return dst

def decompress_rle_with_window(src_data, width, height, palette_window):
    """sub_4EC66 RLE decompression WITH palette window"""
    dst = [0] * (width * height)
    dst_idx = 0
    src_idx = 0
    src_size = len(src_data)
    
    ah = 0
    prev_al = 0
    
    for row in range(height):
        for col in range(width):
            if dst_idx >= width * height:
                break
            
            if ah > 0:
                ah -= 1
            else:
                if src_idx >= src_size:
                    break
                
                al = src_data[src_idx]
                src_idx += 1
                
                if al > 0xC0:
                    ah = al - 0xC1
                    if src_idx < src_size:
                        al = src_data[src_idx]
                        src_idx += 1
                    prev_al = al
                else:
                    ah = 0
                    prev_al = al
            
            # Apply palette window
            pixel = prev_al
            if palette_window != -1:
                pixel = (palette_window + prev_al) & 0xFF
            
            dst[dst_idx] = pixel
            dst_idx += 1
    
    return dst

def render_image(pixels, width, height, palette, apply_window=None):
    """Render image with optional palette window at render time"""
    img = Image.new('RGB', (width, height))
    pix = img.load()
    for y in range(height):
        for x in range(width):
            idx = pixels[y * width + x]
            if apply_window is not None:
                idx = (idx + apply_window) & 0xFF
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
    
    # Parse header
    outer_w = struct.unpack_from('<H', res_data, 0)[0]
    outer_h = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4]
    
    print(f"Header: {outer_w}x{outer_h}, palette_window={pal_win}")
    
    # Parse offset table
    icon_offsets = []
    pos = 6
    while pos + 4 <= len(res_data):
        rel_off = struct.unpack_from('<I', res_data, pos)[0]
        if rel_off >= len(res_data):
            break
        icon_offsets.append(rel_off)
        pos += 4
    
    print(f"Icon count: {len(icon_offsets)}")
    
    # Test icon 0
    icon_idx = 0
    rel_off = icon_offsets[icon_idx]
    next_rel = icon_offsets[icon_idx + 1] if icon_idx + 1 < len(icon_offsets) else len(res_data)
    icon_data = res_data[rel_off:next_rel]
    
    print(f"\nIcon {icon_idx}: {len(icon_data)} bytes")
    print(f"First 32 bytes: {' '.join(f'{b:02X}' for b in icon_data[:32])}")
    
    # Test 1: RLE with window applied during decode, no window at render
    pixels1 = decompress_rle_with_window(icon_data, outer_w, outer_h, pal_win)
    img1 = render_image(pixels1, outer_w, outer_h, palette, apply_window=None)
    img1.save('output/icon0_decode_with_window.png')
    print(f"Saved: output/icon0_decode_with_window.png (window in decode)")
    
    # Test 2: RLE without window in decode, window at render
    pixels2 = decompress_rle_raw(icon_data, outer_w, outer_h)
    img2 = render_image(pixels2, outer_w, outer_h, palette, apply_window=pal_win)
    img2.save('output/icon0_render_with_window.png')
    print(f"Saved: output/icon0_render_with_window.png (window in render)")
    
    # Test 3: Window applied both times (wrong)
    img3 = render_image(pixels1, outer_w, outer_h, palette, apply_window=pal_win)
    img3.save('output/icon0_double_window.png')
    print(f"Saved: output/icon0_double_window.png (double window - wrong)")
    
    # Test 4: No window at all
    img4 = render_image(pixels2, outer_w, outer_h, palette, apply_window=None)
    img4.save('output/icon0_no_window.png')
    print(f"Saved: output/icon0_no_window.png (no window)")

if __name__ == '__main__':
    main()
