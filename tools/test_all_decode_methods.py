#!/usr/bin/env python3
"""
综合分析：测试所有可能的索引1解码组合
"""
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

def render_image(pixels, width, height, palette, filename):
    img = Image.new('RGB', (width, height))
    pix = img.load()
    for y in range(height):
        for x in range(width):
            idx = pixels[y * width + x] & 0xFF
            if idx < 256:
                pix[x, y] = palette[idx]
            else:
                pix[x, y] = (255, 0, 0)
    img.save(filename)

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
        if len(icon_offsets) >= 3:
            break
    
    # 测试图标0
    icon_data = res_data[icon_offsets[0]:icon_offsets[1]]
    print(f"\n图标0: {len(icon_data)}字节")
    print(f"前32字节: {' '.join(f'{b:02X}' for b in icon_data[:32])}")
    
    # 测试1: 不应用palette_window
    print("\n=== 测试1: 不应用palette_window ===")
    global ec66_ah, ec66_prev_al, ec66_src_pos
    ec66_ah = ec66_prev_al = 0
    ec66_src_pos = 0
    
    pixels1 = []
    for _ in range(outer_w * outer_h):
        pixels1.append(sub_4ec66_step(icon_data, len(icon_data)))
    
    print(f"前24像素: {' '.join(f'{p:02X}' for p in pixels1[:24])}")
    render_image(pixels1, outer_w, outer_h, palette, 'output/test1_no_palwin.png')
    
    # 测试2: 应用palette_window
    print("\n=== 测试2: 应用palette_window ===")
    pixels2 = [(p + pal_win) & 0xFF for p in pixels1]
    print(f"前24像素: {' '.join(f'{p:02X}' for p in pixels2[:24])}")
    render_image(pixels2, outer_w, outer_h, palette, 'output/test2_with_palwin.png')
    
    # 测试3: 跳过前4字节，不应用palette_window
    print("\n=== 测试3: 跳过前4字节，不应用palette_window ===")
    ec66_ah = ec66_prev_al = 0
    ec66_src_pos = 0
    
    icon_data_skip4 = icon_data[4:]
    pixels3 = []
    for _ in range(outer_w * outer_h):
        pixels3.append(sub_4ec66_step(icon_data_skip4, len(icon_data_skip4)))
    
    print(f"前24像素: {' '.join(f'{p:02X}' for p in pixels3[:24])}")
    render_image(pixels3, outer_w, outer_h, palette, 'output/test3_skip4_no_palwin.png')
    
    # 测试4: 跳过前4字节，应用palette_window
    print("\n=== 测试4: 跳过前4字节，应用palette_window ===")
    pixels4 = [(p + pal_win) & 0xFF for p in pixels3]
    print(f"前24像素: {' '.join(f'{p:02X}' for p in pixels4[:24])}")
    render_image(pixels4, outer_w, outer_h, palette, 'output/test4_skip4_with_palwin.png')
    
    print("\n=== 已生成测试图像 ===")
    print("请查看 output/test1_*.png 到 output/test4_*.png")
    print("对比哪个解码方式是正确的")

ec66_ah = 0
ec66_prev_al = 0
ec66_src_pos = 0

if __name__ == '__main__':
    main()
