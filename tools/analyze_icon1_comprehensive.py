#!/usr/bin/env python3
"""
详细分析索引1图标数据格式
测试所有可能的解码组合
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

def decode_simple(icon_data, width, height):
    """简单解码，不跳过任何头"""
    global ec66_ah, ec66_prev_al, ec66_src_pos
    
    ec66_ah = 0
    ec66_prev_al = 0
    ec66_src_pos = 0
    
    pixels = []
    for _ in range(height * width):
        pixel = sub_4ec66_step(icon_data, len(icon_data))
        pixels.append(pixel)
    
    return pixels

def decode_skip_4(icon_data, width, height):
    """跳过前4字节后解码"""
    global ec66_ah, ec66_prev_al, ec66_src_pos
    
    ec66_ah = 0
    ec66_prev_al = 0
    ec66_src_pos = 0
    
    # 跳过前4字节
    pixel_data = icon_data[4:]
    
    pixels = []
    for _ in range(height * width):
        pixel = sub_4ec66_step(pixel_data, len(pixel_data))
        pixels.append(pixel)
    
    return pixels

def render_and_save(pixels, width, height, palette, filename, apply_pal_win=0):
    """渲染像素并保存为PNG"""
    img = Image.new('RGB', (width, height))
    pix = img.load()
    
    for y in range(height):
        for x in range(width):
            idx = pixels[y * width + x]
            idx = (idx + apply_pal_win) & 0xFF
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
    
    # 外头
    outer_w = struct.unpack_from('<H', res_data, 0)[0]
    outer_h = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4]
    
    print(f"外头: {outer_w}x{outer_h}, pal_window={pal_win}")
    print(f"外头5字节: {' '.join(f'{b:02X}' for b in res_data[:5])}")
    
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
    
    # 测试图标0
    icon_idx = 0
    rel_off = icon_offsets[icon_idx]
    next_rel = icon_offsets[icon_idx + 1] if icon_idx + 1 < len(icon_offsets) else len(res_data)
    icon_data = res_data[rel_off:next_rel]
    
    print(f"=== 图标{icon_idx} 详细分析 ===")
    print(f"大小: {len(icon_data)}字节")
    print(f"前24字节: {' '.join(f'{b:02X}' for b in icon_data[:24])}")
    
    # 分析前4字节
    w_le = struct.unpack_from('<H', icon_data, 0)[0]
    h_le = struct.unpack_from('<H', icon_data, 2)[0]
    w_be = struct.unpack_from('>H', icon_data, 0)[0]
    h_be = struct.unpack_from('>H', icon_data, 2)[0]
    
    print(f"\n前4字节作为宽高:")
    print(f"  LE: {w_le}x{h_le}")
    print(f"  BE: {w_be}x{h_be}")
    
    # 统计前4字节
    print(f"\n前4字节统计:")
    for i in range(4):
        b = icon_data[i]
        print(f"  [{i}] 0x{b:02X} = {b} (>{'是' if b > 0xC0 else '否'} 0xC0)")
    
    # 测试不同解码方式
    print(f"\n=== 测试不同解码方式 ===")
    
    # 方式1: 简单解码，不应用palette_window
    pixels1 = decode_simple(icon_data, outer_w, outer_h)
    print(f"\n方式1: 简单解码，无palette_window")
    print(f"  前24像素: {' '.join(f'{p:02X}' for p in pixels1[:24])}")
    render_and_save(pixels1, outer_w, outer_h, palette, f'output/test1_simple_no_win.png', 0)
    
    # 方式2: 简单解码，应用palette_window
    render_and_save(pixels1, outer_w, outer_h, palette, f'output/test2_simple_with_win.png', pal_win)
    
    # 方式3: 跳过4字节，无palette_window
    pixels3 = decode_skip_4(icon_data, outer_w, outer_h)
    print(f"\n方式3: 跳过4字节，无palette_window")
    print(f"  前24像素: {' '.join(f'{p:02X}' for p in pixels3[:24])}")
    render_and_save(pixels3, outer_w, outer_h, palette, f'output/test3_skip4_no_win.png', 0)
    
    # 方式4: 跳过4字节，应用palette_window
    render_and_save(pixels3, outer_w, outer_h, palette, f'output/test4_skip4_with_win.png', pal_win)
    
    print(f"\n=== 已生成测试图像 ===")
    print(f"  output/test1_simple_no_win.png")
    print(f"  output/test2_simple_with_win.png")
    print(f"  output/test3_skip4_no_win.png")
    print(f"  output/test4_skip4_with_win.png")

ec66_ah = 0
ec66_prev_al = 0
ec66_src_pos = 0

if __name__ == '__main__':
    main()
