#!/usr/bin/env python3
"""
详细测试索引1图标的各种解码方式
"""
import struct
from PIL import Image

def load_fdother(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # 解析索引表
    index_count = struct.unpack_from('<H', data, 4)[0]
    index_start = 6
    
    offsets = []
    for i in range(index_count):
        off = struct.unpack_from('<I', data, index_start + i * 4)[0]
        offsets.append(off)
    offsets.append(len(data))
    
    return data, offsets

def sub_4ec66_step(src_data, src_size):
    """sub_4EC66: 精确按照MCP汇编实现"""
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

def decode_rle(src_data, width, height):
    """解码RLE数据为像素"""
    global ec66_ah, ec66_prev_al, ec66_src_pos
    
    ec66_ah = 0
    ec66_prev_al = 0
    ec66_src_pos = 0
    
    pixels = []
    for _ in range(width * height):
        pixel = sub_4ec66_step(src_data, len(src_data))
        pixels.append(pixel)
    
    return pixels

def render_pixels(pixels, width, height, palette, pal_window, filename):
    """渲染像素并保存"""
    img = Image.new('RGB', (width, height))
    pix = img.load()
    
    for y in range(height):
        for x in range(width):
            idx = pixels[y * width + x]
            # 应用调色板窗口
            idx = (idx + pal_window) & 0xFF
            if idx < 256:
                pix[x, y] = palette[idx]
            else:
                pix[x, y] = (255, 0, 0)
    
    img.save(filename)
    return img

def main():
    filepath = 'game/FDOTHER.DAT'
    data, offsets = load_fdother(filepath)
    palette = load_palette(data, offsets)
    
    # 索引1
    res_start = offsets[1]
    res_end = offsets[2]
    res_data = data[res_start:res_end]
    
    # 解析外头
    outer_w = struct.unpack_from('<H', res_data, 0)[0]
    outer_h = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4]
    
    print(f"外头: {outer_w}x{outer_h}, pal_window={pal_win}")
    print(f"资源大小: {len(res_data)} 字节\n")
    
    # 解析相对偏移表 (从偏移6开始)
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
    
    # 分析图标0
    icon0_start = icon_offsets[0]
    icon0_end = icon_offsets[1] if len(icon_offsets) > 1 else len(res_data)
    icon0_data = res_data[icon0_start:icon0_end]
    
    print(f"=== 图标0 分析 ===")
    print(f"相对偏移: 0x{icon0_start:X}")
    print(f"图标大小: {len(icon0_data)} 字节")
    print(f"前32字节: {' '.join(f'{b:02X}' for b in icon0_data[:32])}")
    
    # 检查前4字节是否可能是宽高
    w1 = struct.unpack_from('<H', icon0_data, 0)[0]
    h1 = struct.unpack_from('<H', icon0_data, 2)[0]
    print(f"前4字节作为LE宽高: {w1}x{h1}")
    print(f"  -> {'合理' if w1 <= 320 and h1 <= 200 else '不合理'}\n")
    
    # 测试1: 直接解码整个图标数据（不含任何头）
    print("测试1: 直接解码整个图标数据")
    pixels1 = decode_rle(icon0_data, outer_w, outer_h)
    print(f"  前16像素: {' '.join(f'{p:02X}' for p in pixels1[:16])}")
    render_pixels(pixels1, outer_w, outer_h, palette, pal_win, 'output/test1_direct.png')
    
    # 测试2: 跳过前4字节后解码
    print("\n测试2: 跳过前4字节")
    pixels2 = decode_rle(icon0_data[4:], outer_w, outer_h)
    print(f"  前16像素: {' '.join(f'{p:02X}' for p in pixels2[:16])}")
    render_pixels(pixels2, outer_w, outer_h, palette, pal_win, 'output/test2_skip4.png')
    
    # 测试3: 使用图标自己的宽高（如果合理）
    if w1 <= 320 and h1 <= 200:
        print(f"\n测试3: 使用图标自己的宽高 {w1}x{h1}")
        pixels3 = decode_rle(icon0_data[4:], w1, h1)
        render_pixels(pixels3, w1, h1, palette, pal_win, 'output/test3_own_size.png')
    
    # 测试4: 检查是否所有图标数据都有相同的模式
    print(f"\n=== 检查所有图标前8字节 ===")
    for i in range(min(5, len(icon_offsets))):
        start = icon_offsets[i]
        end = icon_offsets[i+1] if i+1 < len(icon_offsets) else len(res_data)
        icon_data = res_data[start:end]
        print(f"图标{i}: {' '.join(f'{b:02X}' for b in icon_data[:8])}")

# 全局EC66状态
ec66_ah = 0
ec66_prev_al = 0
ec66_src_pos = 0

if __name__ == '__main__':
    main()
