#!/usr/bin/env python3
"""对比Python和C解码结果"""
import struct

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

def decode_icon(icon_data, width, height, pal_window):
    global ec66_ah, ec66_prev_al, ec66_src_pos
    
    ec66_ah = 0
    ec66_prev_al = 0
    ec66_src_pos = 0
    
    pixels = []
    for row in range(height):
        for col in range(width):
            pixel = sub_4ec66_step(icon_data, len(icon_data))
            # 应用调色板窗口（与C代码一致）
            pixel = (pixel + pal_window) & 0xFF
            pixels.append(pixel)
    
    return pixels

def main():
    filepath = 'game/FDOTHER.DAT'
    data, offsets = load_fdother(filepath)
    
    # 索引1
    res_start = offsets[1]
    res_end = offsets[2]
    res_data = data[res_start:res_end]
    
    outer_w = struct.unpack_from('<H', res_data, 0)[0]
    outer_h = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4]
    
    print("=== Python解码结果（含调色板窗口） ===")
    print(f"外头: {outer_w}x{outer_h}, pal_window={pal_win}\n")
    
    # 解析相对偏移表
    icon_offsets = []
    pos = 6
    while pos + 4 <= len(res_data):
        rel_off = struct.unpack_from('<I', res_data, pos)[0]
        if rel_off >= len(res_data):
            break
        icon_offsets.append(rel_off)
        pos += 4
        if len(icon_offsets) >= 5:
            break
    
    # 解码前5个图标
    for icon_idx in range(len(icon_offsets)):
        rel_off = icon_offsets[icon_idx]
        next_rel = icon_offsets[icon_idx + 1] if icon_idx + 1 < len(icon_offsets) else len(res_data)
        icon_data = res_data[rel_off:next_rel]
        
        pixels = decode_icon(icon_data, outer_w, outer_h, pal_win)
        
        print(f"图标{icon_idx}:")
        print(f"  前3行像素: ")
        for row in range(3):
            row_pixels = pixels[row * outer_w:(row + 1) * outer_w]
            hex_str = ' '.join(f'{p:02X}' for p in row_pixels[:24])
            print(f"  行{row}: {hex_str}")
        print()

ec66_ah = 0
ec66_prev_al = 0
ec66_src_pos = 0

if __name__ == '__main__':
    main()
