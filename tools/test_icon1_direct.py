#!/usr/bin/env python3
"""Test direct RLE decoding for index 1 icons (no 4-byte header skip)"""
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

def decompress_rle(src_data, width, height, palette_window):
    """sub_4EC66 RLE decompression with palette window"""
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
    
    # Test first 5 icons
    for icon_idx in range(min(5, len(icon_offsets))):
        rel_off = icon_offsets[icon_idx]
        next_rel = icon_offsets[icon_idx + 1] if icon_idx + 1 < len(icon_offsets) else len(res_data)
        icon_data = res_data[rel_off:next_rel]
        
        print(f"\nIcon {icon_idx}: {len(icon_data)} bytes")
        
        # Direct RLE decode (no header skip)
        pixels = decompress_rle(icon_data, outer_w, outer_h, pal_win)
        
        # Render image
        img = Image.new('RGB', (outer_w, outer_h))
        pix = img.load()
        for y in range(outer_h):
            for x in range(outer_w):
                idx = pixels[y * outer_w + x]
                pix[x, y] = palette[idx]
        
        img.save(f'output/icon{icon_idx}_direct.png')
        print(f"  Saved: output/icon{icon_idx}_direct.png")

if __name__ == '__main__':
    main()
