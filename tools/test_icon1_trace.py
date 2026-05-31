#!/usr/bin/env python3
"""手动跟踪sub_4EC66的解码过程，验证RLE逻辑"""
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
    
    # 测试图标0
    icon_idx = 0
    rel_off = icon_offsets[icon_idx]
    next_rel = icon_offsets[icon_idx + 1] if icon_idx + 1 < len(icon_offsets) else len(res_data)
    icon_data = res_data[rel_off:next_rel]
    
    print(f"\n图标{icon_idx}: {len(icon_data)}字节")
    print(f"完整数据: {' '.join(f'{b:02X}' for b in icon_data[:min(50, len(icon_data))])}")
    print()
    
    # 手动跟踪sub_4EC66解码过程
    print("=== 手动跟踪sub_4EC66解码过程 ===")
    print(f"需要解码 {outer_w}x{outer_h} = {outer_w*outer_h} 像素\n")
    
    ah = 0  # 运行长度计数器
    prev_al = 0  # 上次读取的像素值
    src_idx = 0
    
    pixels = []
    src_idx_at_pixel = []  # 记录每个像素对应的源数据位置
    
    for pixel_num in range(outer_w * outer_h):
        src_idx_at_pixel.append(src_idx)
        
        if ah > 0:
            # AH > 0: 重复之前的像素值
            print(f"像素{pixel_num:3d}: AH={ah}>0, 重复prev_al=0x{prev_al:02X}")
            ah -= 1
        else:
            # AH == 0: 读取新字节
            if src_idx >= len(icon_data):
                print(f"像素{pixel_num:3d}: 源数据不足!")
                break
            
            al = icon_data[src_idx]
            src_idx += 1
            print(f"像素{pixel_num:3d}: 读取AL=0x{al:02X}", end='')
            
            if al > 0xC0:
                # AL > 0xC0: 运行长度编码
                ah = al - 0xC1
                print(f" (RLE: ah=0x{ah:02X}={ah})", end='')
                if src_idx < len(icon_data):
                    al = icon_data[src_idx]
                    src_idx += 1
                    prev_al = al
                    print(f", 像素值=0x{al:02X}")
                else:
                    print(", 源数据不足!")
                    break
            else:
                # AL <= 0xC0: 直接像素值
                ah = 0
                prev_al = al
                print(f" (直接像素)")
        
        pixels.append(prev_al)
        
        # 只显示前40个像素的详细过程
        if pixel_num >= 39:
            if pixel_num == 40:
                print("... (省略中间像素的详细信息) ...")
            continue
    
    print(f"\n共解码 {len(pixels)} 像素")
    print(f"前24像素: {' '.join(f'{p:02X}' for p in pixels[:24])}")
    print(f"应用pal_win={pal_win}后: {' '.join(f'{(p+pal_win)&0xFF:02X}' for p in pixels[:24])}")
    
    # 渲染图像
    img = Image.new('RGB', (outer_w, outer_h))
    pix = img.load()
    for y in range(outer_h):
        for x in range(outer_w):
            idx = (pixels[y * outer_w + x] + pal_win) & 0xFF
            pix[x, y] = palette[idx]
    img.save('output/icon0_trace.png')
    print(f"\n已保存: output/icon0_trace.png")
    
    # 尝试另一种方法：不应用palette_window
    img2 = Image.new('RGB', (outer_w, outer_h))
    pix2 = img2.load()
    for y in range(outer_h):
        for x in range(outer_w):
            idx = pixels[y * outer_w + x] & 0xFF
            pix2[x, y] = palette[idx]
    img2.save('output/icon0_trace_no_pal.png')
    print(f"已保存: output/icon0_trace_no_pal.png")

if __name__ == '__main__':
    main()
