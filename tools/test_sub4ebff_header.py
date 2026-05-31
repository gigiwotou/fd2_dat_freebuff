#!/usr/bin/env python3
"""
分析sub_4EBFF汇编代码，验证索引1图标的正确渲染方式

关键发现：sub_4EBFF从源数据读取宽高（前4字节）
- 4ec0c  lodsw    ; 从ESI读取width
- 4ec11  lodsw    ; 从ESI读取height

但索引1的图标数据不带宽高头！
所以需要构建临时缓冲区：[width:2][height:2][icon_data...]
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

def sub_4ec66_decode_with_header(src_data, width, height):
    """
    1:1模拟sub_4EBFF + sub_4EC66：
    1. sub_4EBFF从源数据读取宽高（前4字节）
    2. 但我们的数据不带宽高头，所以传入width/height
    3. 模拟sub_4EC66解码逻辑
    """
    dst = [0] * (width * height)
    dst_idx = 0
    src_idx = 0
    src_size = len(src_data)
    
    ah = 0
    al = 0
    
    # sub_4EBFF循环：width * height次
    for _ in range(width * height):
        # sub_4EC66逻辑
        if ah == 0:
            # 读取新字节
            if src_idx >= src_size:
                break
            al = src_data[src_idx]
            src_idx += 1
            
            if al > 0xC0:
                # 运行长度编码
                ah = al - 0xC1
                if src_idx < src_size:
                    al = src_data[src_idx]
                    src_idx += 1
            else:
                ah = 0
        else:
            ah -= 1
            # AL保持不变
        
        dst[dst_idx] = al
        dst_idx += 1
    
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
    
    print(f"\nIcon {icon_idx}: {len(icon_data)} bytes")
    print(f"First 32 bytes: {' '.join(f'{b:02X}' for b in icon_data[:32])}")
    
    # 关键修复：构建带宽高头的临时缓冲区
    # 这样sub_4EBFF可以正确读取宽高
    temp_buffer = struct.pack('<HH', outer_w, outer_h) + icon_data
    
    print(f"临时缓冲区大小: {len(temp_buffer)} bytes")
    print(f"临时缓冲区前8字节: {' '.join(f'{b:02X}' for b in temp_buffer[:8])}")
    
    # 从临时缓冲区的第4字节开始解码（跳过宽高头）
    pixel_data = temp_buffer[4:]
    pixels = sub_4ec66_decode_with_header(pixel_data, outer_w, outer_h)
    
    print(f"\n解码结果: {len(pixels)} 像素")
    print(f"前24像素: {' '.join(f'{p:02X}' for p in pixels[:24])}")
    
    if len(pixels) == outer_w * outer_h:
        print(f"OK 像素数量匹配")
        
        # 渲染图像（应用palette_window）
        img = Image.new('RGB', (outer_w, outer_h))
        pix = img.load()
        for y in range(outer_h):
            for x in range(outer_w):
                idx = (pixels[y * outer_w + x] + pal_win) & 0xFF
                pix[x, y] = palette[idx]
        img.save('output/icon0_with_header_fix.png')
        print(f"已保存: output/icon0_with_header_fix.png")

if __name__ == '__main__':
    main()
