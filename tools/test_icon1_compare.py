#!/usr/bin/env python3
"""对比索引1图标的不同解码方式，找出正确的实现"""
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

def sub_4ec66_decode(src_data):
    """1:1复现sub_4EC66，返回所有解码后的像素值"""
    dst = []
    src_idx = 0
    src_size = len(src_data)
    ah = 0
    prev_al = 0
    
    while src_idx < src_size:
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
        dst.append(prev_al)
    
    return dst

def main():
    filepath = 'game/FDOTHER.DAT'
    data, offsets = load_fdother(filepath)
    palette = load_palette(data, offsets)
    
    # Index 1 resource
    res_start = offsets[1]
    res_end = offsets[2]
    res_data = data[res_start:res_end]
    
    outer_w = struct.unpack_from('<H', res_data, 0)[0]
    outer_h = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4]
    
    print(f"Header: {outer_w}x{outer_h}, palette_window={pal_win}")
    
    # Parse offset table
    icon_offsets = []
    pos = 6
    while pos + 4 <= len(res_data):
        rel_off = struct.unpack_from('<I', res_data, pos)[0]
        if rel_off >= len(res_data):
            break
        icon_offsets.append(rel_off)
        pos += 4
    
    print(f"Icon count: {len(icon_offsets)}")
    
    # 测试图标0
    icon_idx = 0
    rel_off = icon_offsets[icon_idx]
    next_rel = icon_offsets[icon_idx + 1] if icon_idx + 1 < len(icon_offsets) else len(res_data)
    icon_data = res_data[rel_off:next_rel]
    
    print(f"\nIcon {icon_idx}: {len(icon_data)} bytes")
    print(f"First 32 bytes: {' '.join(f'{b:02X}' for b in icon_data[:32])}")
    
    # 方式1: 不跳过任何字节，直接解码
    pixels_direct = sub_4ec66_decode(icon_data)
    print(f"\n方式1 (直接解码): {len(pixels_direct)} 像素")
    print(f"  前24像素: {' '.join(f'{p:02X}' for p in pixels_direct[:24])}")
    
    # 检查像素数量是否匹配24x24=576
    if len(pixels_direct) == outer_w * outer_h:
        print(f"  OK 像素数量匹配 {outer_w}x{outer_h}={outer_w*outer_h}")
        # 渲染
        img = Image.new('RGB', (outer_w, outer_h))
        pix = img.load()
        for y in range(outer_h):
            for x in range(outer_w):
                idx = (pixels_direct[y * outer_w + x] + pal_win) & 0xFF
                pix[x, y] = palette[idx]
        img.save('output/icon0_method1_direct.png')
        print(f"  已保存: output/icon0_method1_direct.png")
    else:
        print(f"  ERROR 像素数量不匹配 (期望{outer_w*outer_h}, 实际{len(pixels_direct)})")
    
    # 方式2: 跳过前4字节
    if len(icon_data) > 4:
        pixels_skip4 = sub_4ec66_decode(icon_data[4:])
        print(f"\n方式2 (跳过4字节): {len(pixels_skip4)} 像素")
        print(f"  前24像素: {' '.join(f'{p:02X}' for p in pixels_skip4[:24])}")
        
        if len(pixels_skip4) == outer_w * outer_h:
            print(f"  OK 像素数量匹配 {outer_w}x{outer_h}={outer_w*outer_h}")
            img = Image.new('RGB', (outer_w, outer_h))
            pix = img.load()
            for y in range(outer_h):
                for x in range(outer_w):
                    idx = (pixels_skip4[y * outer_w + x] + pal_win) & 0xFF
                    pix[x, y] = palette[idx]
            img.save('output/icon0_method2_skip4.png')
            print(f"  已保存: output/icon0_method2_skip4.png")
        else:
            print(f"  ERROR 像素数量不匹配 (期望{outer_w*outer_h}, 实际{len(pixels_skip4)})")

if __name__ == '__main__':
    main()
