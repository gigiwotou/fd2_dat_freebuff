#!/usr/bin/env python3
"""索引1图标正确解码 - 使用外部宽高，图标数据不含宽高头"""
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
    """sub_4EC66: 获取下一个像素值"""
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

def decode_icon_with_external_wh(icon_data, width, height, pal_window):
    """使用外部宽高解码图标数据（图标数据不含宽高头）"""
    global ec66_ah, ec66_prev_al, ec66_src_pos
    
    ec66_ah = 0
    ec66_prev_al = 0
    ec66_src_pos = 0
    
    pixels = []
    for row in range(height):
        row_pixels = []
        for col in range(width):
            pixel = sub_4ec66_step(icon_data, len(icon_data))
            # 应用调色板窗口
            pixel = (pixel + pal_window) & 0xFF
            row_pixels.append(pixel)
        pixels.append(row_pixels)
    
    return pixels

def main():
    filepath = 'game/FDOTHER.DAT'
    data, offsets = load_fdother(filepath)
    
    # 索引1
    res_start = offsets[1]
    res_end = offsets[2]
    res_data = data[res_start:res_end]
    
    print("=== 索引1 使用外部宽高解码 ===")
    print(f"资源大小: {len(res_data)} 字节")
    
    # 外头
    outer_w = struct.unpack_from('<H', res_data, 0)[0]
    outer_h = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4]
    print(f"外头宽高: {outer_w}x{outer_h}")
    print(f"调色板窗口: {pal_win}")
    
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
    
    print(f"图标数量: {len(icon_offsets)}")
    
    # 渲染前5个图标
    print(f"\n渲染前5个图标（使用外部宽高 {outer_w}x{outer_h}）:")
    for icon_idx in range(min(5, len(icon_offsets))):
        rel_off = icon_offsets[icon_idx]
        next_rel = icon_offsets[icon_idx + 1] if icon_idx + 1 < len(icon_offsets) else len(res_data)
        icon_data = res_data[rel_off:next_rel]
        
        print(f"\n{'='*60}")
        print(f"图标{icon_idx}: {len(icon_data)}字节")
        print(f"前16字节: {' '.join(f'{b:02X}' for b in icon_data[:16])}")
        
        # 使用外部宽高解码
        pixels = decode_icon_with_external_wh(icon_data, outer_w, outer_h, pal_win)
        
        # 统计
        flat_pixels = [p for row in pixels for p in row]
        non_zero = sum(1 for p in flat_pixels if p != 0)
        unique = len(set(flat_pixels))
        print(f"  非零像素: {non_zero}/{outer_w*outer_h}")
        print(f"  唯一值: {unique}")
        
        # 渲染到图像
        img = Image.new('RGB', (outer_w, outer_h))
        pix = img.load()
        
        # 简单调色板（灰度）
        for y in range(outer_h):
            for x in range(outer_w):
                idx = pixels[y][x]
                gray = idx
                pix[x, y] = (gray, gray, gray)
        
        output_path = f'output/icon1_external_wh_{icon_idx}.png'
        img.save(output_path)
        print(f"  保存到: {output_path}")

# 全局EC66状态
ec66_ah = 0
ec66_prev_al = 0
ec66_src_pos = 0

if __name__ == '__main__':
    main()
