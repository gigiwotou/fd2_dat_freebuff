#!/usr/bin/env python3
"""测试索引1图标的正确渲染方式 - 使用sub_4EBFF的pitch逻辑"""
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
    
    # 解析相对偏移表
    icon_offsets = []
    pos = 6
    while pos + 4 <= len(res_data):
        rel_off = struct.unpack_from('<I', res_data, pos)[0]
        if rel_off >= len(res_data):
            break
        icon_offsets.append(rel_off)
        pos += 4
    
    print(f"图标数量: {len(icon_offsets)}")
    
    # 测试图标0 - 使用sub_4EBFF的pitch逻辑
    icon_idx = 0
    rel_off = icon_offsets[icon_idx]
    next_rel = icon_offsets[icon_idx + 1] if icon_idx + 1 < len(icon_offsets) else len(res_data)
    icon_data = res_data[rel_off:next_rel]
    
    print(f"\n图标{icon_idx}: {len(icon_data)}字节")
    print(f"前8字节: {' '.join(f'{b:02X}' for b in icon_data[:8])}")
    
    global ec66_ah, ec66_prev_al, ec66_src_pos
    
    # 方法A: 简单线性解码 + palette_window
    print("\n方法A: 简单线性解码 + palette_window")
    ec66_ah = ec66_prev_al = 0
    ec66_src_pos = 0
    
    pixels = []
    for _ in range(outer_w * outer_h):
        p = sub_4ec66_step(icon_data, len(icon_data))
        pixels.append((p + pal_win) & 0xFF)
    
    # 保存图像
    img = Image.new('RGB', (outer_w, outer_h))
    pix = img.load()
    for y in range(outer_h):
        for x in range(outer_w):
            idx = pixels[y * outer_w + x]
            pix[x, y] = palette[idx]
    img.save('output/icon0_methodA.png')
    print(f"已保存: output/icon0_methodA.png")
    
    # 方法B: sub_4EBFF方式 - 渲染到320x200缓冲区，然后提取
    print("\n方法B: sub_4EBFF方式（pitch=320）")
    ec66_ah = ec66_prev_al = 0
    ec66_src_pos = 0
    
    # 创建320x200的缓冲区
    screen_buf = [0] * (320 * 200)
    dst_pos = 0
    
    for row in range(outer_h):
        row_start = dst_pos
        
        for col in range(outer_w):
            pixel = sub_4ec66_step(icon_data, len(icon_data))
            # 应用palette_window
            pixel = (pixel + pal_win) & 0xFF
            screen_buf[dst_pos] = pixel
            dst_pos += 1
        
        # sub_4EBFF: pop edi + add edi, ebx
        dst_pos = row_start + 320
    
    # 提取图标区域
    pixels_b = []
    for row in range(outer_h):
        for col in range(outer_w):
            pixels_b.append(screen_buf[row * 320 + col])
    
    # 保存图像
    img = Image.new('RGB', (outer_w, outer_h))
    pix = img.load()
    for y in range(outer_h):
        for x in range(outer_w):
            idx = pixels_b[y * outer_w + x]
            pix[x, y] = palette[idx]
    img.save('output/icon0_methodB.png')
    print(f"已保存: output/icon0_methodB.png")
    
    # 方法C: sub_4EBFF方式 - 不应用palette_window（让draw_pixels应用）
    print("\n方法C: sub_4EBFF方式（不在解码时应用palette_window）")
    ec66_ah = ec66_prev_al = 0
    ec66_src_pos = 0
    
    # 创建320x200的缓冲区
    screen_buf = [0] * (320 * 200)
    dst_pos = 0
    
    for row in range(outer_h):
        row_start = dst_pos
        
        for col in range(outer_w):
            pixel = sub_4ec66_step(icon_data, len(icon_data))
            # 不应用palette_window
            screen_buf[dst_pos] = pixel
            dst_pos += 1
        
        dst_pos = row_start + 320
    
    # 提取图标区域
    pixels_c = []
    for row in range(outer_h):
        for col in range(outer_w):
            pixels_c.append(screen_buf[row * 320 + col])
    
    # 保存图像（应用palette_window）
    img = Image.new('RGB', (outer_w, outer_h))
    pix = img.load()
    for y in range(outer_h):
        for x in range(outer_w):
            idx = (pixels_c[y * outer_w + x] + pal_win) & 0xFF
            pix[x, y] = palette[idx]
    img.save('output/icon0_methodC.png')
    print(f"已保存: output/icon0_methodC.png")
    
    print("\n请对比三个图像，哪个是正确的？")

ec66_ah = 0
ec66_prev_al = 0
ec66_src_pos = 0

if __name__ == '__main__':
    main()
