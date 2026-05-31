#!/usr/bin/env python3
"""测试：每个图标包含完整的外头（宽高+pal_window+保留字节）"""
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

def test_icon_with_own_header(icon_data):
    """每个图标包含自己的外头"""
    global ec66_ah, ec66_prev_al, ec66_src_pos
    
    # 解析图标的外头
    icon_w = struct.unpack_from('<H', icon_data, 0)[0]
    icon_h = struct.unpack_from('<H', icon_data, 2)[0]
    icon_pal_win = icon_data[4]
    
    print(f"  图标外头: {icon_w}x{icon_h}, pal_window={icon_pal_win}")
    
    if icon_w <= 0 or icon_w > 320 or icon_h <= 0 or icon_h > 200:
        print(f"  宽高不合理")
        return None, 0, 0
    
    # 像素数据从第6字节开始（跳过宽高+pal_window+保留字节）
    # 或者从第5字节开始（跳过宽高+pal_window）
    pixel_data = icon_data[6:]  # 尝试从第6字节开始
    
    ec66_ah = 0
    ec66_prev_al = 0
    ec66_src_pos = 0
    
    pixels = []
    for row in range(icon_h):
        for col in range(icon_w):
            pixel = sub_4ec66_step(pixel_data, len(pixel_data))
            pixel = (pixel + icon_pal_win) & 0xFF
            pixels.append(pixel)
    
    return pixels, icon_w, icon_h

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
    
    print(f"资源外头: {outer_w}x{outer_h}, pal_window={pal_win}")
    
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
    
    # 渲染前5个图标
    for icon_idx in range(min(5, len(icon_offsets))):
        rel_off = icon_offsets[icon_idx]
        next_rel = icon_offsets[icon_idx + 1] if icon_idx + 1 < len(icon_offsets) else len(res_data)
        icon_data = res_data[rel_off:next_rel]
        
        print(f"图标{icon_idx}: {len(icon_data)}字节")
        print(f"  前12字节: {' '.join(f'{b:02X}' for b in icon_data[:12])}")
        
        pixels, w, h = test_icon_with_own_header(icon_data)
        
        if pixels:
            img = Image.new('RGB', (w, h))
            pix = img.load()
            
            for y in range(h):
                for x in range(w):
                    pal_idx = pixels[y * w + x]
                    if pal_idx < 256:
                        pix[x, y] = palette[pal_idx]
                    else:
                        pix[x, y] = (255, 0, 0)
            
            output_path = f'output/icon1_with_own_header_{icon_idx}.png'
            img.save(output_path)
            print(f"  保存到: {output_path}\n")
        else:
            print()

ec66_ah = 0
ec66_prev_al = 0
ec66_src_pos = 0

if __name__ == '__main__':
    main()
