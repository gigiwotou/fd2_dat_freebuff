#!/usr/bin/env python3
"""验证索引1图标的正确解码方式"""
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
    
    # 测试所有图标
    for icon_idx in range(min(3, len(icon_offsets)-1)):
        rel_off = icon_offsets[icon_idx]
        next_rel = icon_offsets[icon_idx + 1] if icon_idx + 1 < len(icon_offsets) else len(res_data)
        icon_data = res_data[rel_off:next_rel]
        
        print(f"\n=== 图标{icon_idx}: {len(icon_data)}字节 ===")
        print(f"前8字节: {' '.join(f'{b:02X}' for b in icon_data[:8])}")
        
        # 解析图标内部的宽高头
        inner_w = struct.unpack_from('<H', icon_data, 0)[0]
        inner_h = struct.unpack_from('<H', icon_data, 2)[0]
        print(f"内部宽高: {inner_w}x{inner_h}")
        
        # 跳过4字节头,解码像素数据
        pixel_data = icon_data[4:]
        print(f"像素数据大小: {len(pixel_data)}字节")
        
        # 解码
        global ec66_ah, ec66_prev_al, ec66_src_pos
        ec66_ah = 0
        ec66_prev_al = 0
        ec66_src_pos = 0
        
        # 使用外层宽高解码(24x24)
        pixels = []
        for _ in range(outer_w * outer_h):
            pixels.append(sub_4ec66_step(pixel_data, len(pixel_data)))
        
        # 应用调色板窗口
        pixels_with_pal = [(p + pal_win) & 0xFF for p in pixels]
        
        print(f"前24像素(原始): {' '.join(f'{p:02X}' for p in pixels[:24])}")
        print(f"前24像素(应用pal_win): {' '.join(f'{p:02X}' for p in pixels_with_pal[:24])}")
        
        # 渲染
        render_image(pixels_with_pal, outer_w, outer_h, palette, 
                    f'output/icon{icon_idx}_final.png')
        print(f"已保存: output/icon{icon_idx}_final.png")

ec66_ah = 0
ec66_prev_al = 0
ec66_src_pos = 0

if __name__ == '__main__':
    main()
