#!/usr/bin/env python3
"""严格遵循sub_4EBFF + sub_4EC66汇编代码的1:1实现"""
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

def sub_4ec66_decode_exact(src_data, num_pixels):
    """严格1:1复现sub_4EC66，解码指定数量的像素"""
    dst = []
    src_idx = 0
    src_size = len(src_data)
    
    # sub_4EC66状态变量（对应寄存器）
    ah = 0
    al = 0
    
    # sub_4EBFF循环 num_pixels 次
    for i in range(num_pixels):
        # sub_4EC66逻辑开始
        # or ah, ah; jz loc_4EC6D
        if ah == 0:
            # loc_4EC6D: lodsb
            if src_idx >= src_size:
                break
            al = src_data[src_idx]
            src_idx += 1
            
            # cmp al, 0C0h; ja loc_4EC75
            if al > 0xC0:
                # loc_4EC75: mov ah, al; sub ah, 0C1h
                ah = al - 0xC1
                
                # lodsb
                if src_idx < src_size:
                    al = src_data[src_idx]
                    src_idx += 1
            else:
                # xor ah, ah
                ah = 0
        else:
            # dec ah
            ah -= 1
            # AL保持不变，重复使用
        
        # sub_4EC66返回，AL就是像素值
        dst.append(al)
    
    return dst

def main():
    filepath = 'game/FDOTHER.DAT'
    data, offsets = load_fdother(filepath)
    palette = load_palette(data, offsets)
    
    # Index 1 resource
    res_start = offsets[1]
    res_end = offsets[2]
    res_data = data[res_start:res_end]
    
    # Parse header
    outer_w = struct.unpack_from('<H', res_data, 0)[0]
    outer_h = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4]
    
    print(f"Header: {outer_w}x{outer_h}, palette_window={pal_win}")
    
    # Parse offset table from byte 6
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
    
    num_pixels = outer_w * outer_h
    print(f"\nIcon {icon_idx}: {len(icon_data)} bytes")
    print(f"First 32 bytes: {' '.join(f'{b:02X}' for b in icon_data[:32])}")
    print(f"需要解码 {num_pixels} 个像素 ({outer_w}x{outer_h})")
    
    # 1:1 sub_4EC66 decode
    pixels = sub_4ec66_decode_exact(icon_data, num_pixels)
    print(f"\n解码结果: {len(pixels)} 像素")
    print(f"前24像素: {' '.join(f'{p:02X}' for p in pixels[:24])}")
    print(f"像素值范围: {min(pixels)} - {max(pixels)}")
    
    if len(pixels) == num_pixels:
        print(f"OK 像素数量匹配")
        
        # 渲染图像（应用palette_window）
        img = Image.new('RGB', (outer_w, outer_h))
        pix = img.load()
        for y in range(outer_h):
            for x in range(outer_w):
                idx = (pixels[y * outer_w + x] + pal_win) & 0xFF
                pix[x, y] = palette[idx]
        img.save('output/icon0_exact.png')
        print(f"已保存: output/icon0_exact.png")
        
        # 也生成不应用palette_window的图像用于对比
        img2 = Image.new('RGB', (outer_w, outer_h))
        pix2 = img2.load()
        for y in range(outer_h):
            for x in range(outer_w):
                idx = pixels[y * outer_w + x]
                pix2[x, y] = palette[idx]
        img2.save('output/icon0_no_window.png')
        print(f"已保存: output/icon0_no_window.png")
    else:
        print(f"ERROR 像素数量不匹配 (期望{num_pixels}, 实际{len(pixels)})")

if __name__ == '__main__':
    main()
