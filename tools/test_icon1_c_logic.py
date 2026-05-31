#!/usr/bin/env python3
"""测试索引1图标 - 验证当前C代码fd_decompress_rle的实现是否正确"""
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

def fd_decompress_rle_exact(src, src_size, dst_width, dst_height, value_param):
    """1:1复制fd_decompress_rle的C代码逻辑"""
    expected = dst_width * dst_height
    dst = [0] * expected
    dst_idx = 0
    src_idx = 0
    
    ah = 0
    prev_al = 0
    
    for row in range(dst_height):
        for col in range(dst_width):
            if dst_idx >= expected:
                break
            
            if ah > 0:
                ah -= 1
            else:
                if src_idx >= src_size:
                    break
                
                al = src[src_idx]
                src_idx += 1
                
                if al > 0xC0:
                    ah = al - 0xC1
                    if src_idx < src_size:
                        al = src[src_idx]
                        src_idx += 1
                    prev_al = al
                else:
                    ah = 0
                    prev_al = al
            
            pixel = prev_al
            if value_param != -1:
                pixel = (value_param + prev_al) & 0xFF
            
            dst[dst_idx] = pixel
            dst_idx += 1
    
    return dst

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
    
    # 测试图标0 - 使用当前C代码的逻辑
    icon_idx = 0
    rel_off = icon_offsets[icon_idx]
    next_rel = icon_offsets[icon_idx + 1] if icon_idx + 1 < len(icon_offsets) else len(res_data)
    icon_data = res_data[rel_off:next_rel]
    
    print(f"\n图标{icon_idx}: {len(icon_data)}字节")
    print(f"前8字节: {' '.join(f'{b:02X}' for b in icon_data[:8])}")
    
    # 当前C代码逻辑：直接解码图标数据（没有跳过4字节）
    pixels = fd_decompress_rle_exact(
        icon_data, len(icon_data),
        outer_w, outer_h,
        pal_win  # value_param = palette_window
    )
    
    print(f"前24像素: {' '.join(f'{p:02X}' for p in pixels[:24])}")
    
    # 渲染图像（注意：C代码中draw_pixels直接使用像素值，不应用palette_window）
    img = Image.new('RGB', (outer_w, outer_h))
    pix = img.load()
    for y in range(outer_h):
        for x in range(outer_w):
            idx = pixels[y * outer_w + x] & 0xFF
            pix[x, y] = palette[idx]
    img.save('output/icon0_c_logic.png')
    print(f"已保存: output/icon0_c_logic.png")
    
    # 对比：如果fd_decompress_rle不应用palette_window，让draw_pixels来应用
    print("\n对比：fd_decompress_rle不应用palette_window")
    pixels_no_pal = fd_decompress_rle_exact(
        icon_data, len(icon_data),
        outer_w, outer_h,
        -1  # 不应用palette_window
    )
    
    print(f"前24像素(原始): {' '.join(f'{p:02X}' for p in pixels_no_pal[:24])}")
    print(f"前24像素(应用pal_win): {' '.join(f'{(p+pal_win)&0xFF:02X}' for p in pixels_no_pal[:24])}")
    
    # 渲染（应用palette_window）
    img2 = Image.new('RGB', (outer_w, outer_h))
    pix2 = img2.load()
    for y in range(outer_h):
        for x in range(outer_w):
            idx = (pixels_no_pal[y * outer_w + x] + pal_win) & 0xFF
            pix2[x, y] = palette[idx]
    img2.save('output/icon0_no_pal_in_decode.png')
    print(f"已保存: output/icon0_no_pal_in_decode.png")

if __name__ == '__main__':
    main()
