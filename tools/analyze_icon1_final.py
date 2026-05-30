#!/usr/bin/env python3
"""正确解析索引1: 偏移6开始是4字节偏移表"""
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

def ec66_decode(src, width, height):
    dst = bytearray(width * height)
    src_pos = 0
    ah = 0
    prev_al = 0
    dst_pos = 0
    
    for row in range(height):
        for col in range(width):
            if dst_pos >= len(dst):
                break
            
            if ah > 0:
                ah -= 1
                pixel = prev_al
            else:
                if src_pos >= len(src):
                    break
                al = src[src_pos]
                src_pos += 1
                
                if al > 0xC0:
                    ah = al - 0xC1
                    if src_pos < len(src):
                        al = src[src_pos]
                        src_pos += 1
                    prev_al = al
                    pixel = al
                else:
                    ah = 0
                    prev_al = al
                    pixel = al
            
            dst[dst_pos] = pixel
            dst_pos += 1
    
    return dst

def load_palette(filepath, pal_index=0):
    data, offsets = load_fdother(filepath)
    start = offsets[pal_index]
    end = offsets[pal_index + 1]
    pal_data = data[start:end]
    
    rgb = []
    for i in range(256):
        r = (pal_data[i * 3] << 2) | (pal_data[i * 3] >> 4)
        g = (pal_data[i * 3 + 1] << 2) | (pal_data[i * 3 + 1] >> 4)
        b = (pal_data[i * 3 + 2] << 2) | (pal_data[i * 3 + 2] >> 4)
        rgb.append((r, g, b))
    
    return rgb

def main():
    filepath = 'game/FDOTHER.DAT'
    data, offsets = load_fdother(filepath)
    palette = load_palette(filepath, 0)
    
    start = offsets[1]
    end = offsets[2]
    res_data = data[start:end]
    
    print("=== 索引1 正确解析 ===")
    print(f"总大小: {len(res_data)} 字节")
    
    # 头5字节
    w = struct.unpack_from('<H', res_data, 0)[0]
    h = struct.unpack_from('<H', res_data, 2)[0]
    pal_window = res_data[4]
    print(f"头: {w}x{h}, 调色板窗口={pal_window}")
    
    # 偏移5是填充
    print(f"偏移5 (填充): 0x{res_data[5]:02X}")
    
    # 从偏移6开始解析4字节偏移
    offset_table_start = 6
    icon_offsets = []
    pos = offset_table_start
    
    while pos + 4 <= len(res_data):
        off = struct.unpack_from('<I', res_data, pos)[0]
        
        if off > len(res_data):
            print(f"偏移 {off} 超出范围，停止")
            break
        
        icon_offsets.append(off)
        pos += 4
        
        if len(icon_offsets) > 50:
            break
    
    print(f"\n找到 {len(icon_offsets)} 个偏移")
    for i in range(min(25, len(icon_offsets))):
        off = icon_offsets[i]
        if i + 1 < len(icon_offsets):
            size = icon_offsets[i + 1] - off
            print(f"  图标{i}: 偏移 0x{off:X} ({off}), 大小 {size} 字节")
        else:
            size = len(res_data) - off
            print(f"  图标{i}: 偏移 0x{off:X} ({off}), 大小 {size} 字节 (到末尾)")
    
    # 渲染图标
    if len(icon_offsets) > 0:
        print(f"\n渲染前{min(20, len(icon_offsets))}个图标:")
        for i in range(min(20, len(icon_offsets))):
            start_off = icon_offsets[i]
            end_off = icon_offsets[i + 1] if i + 1 < len(icon_offsets) else len(res_data)
            icon_data = res_data[start_off:end_off]
            
            decoded = ec66_decode(icon_data, w, h)
            
            img = Image.new('RGB', (w, h))
            pixels = img.load()
            
            for y in range(h):
                for x in range(w):
                    idx = decoded[y * w + x]
                    # 应用调色板窗口
                    idx = (idx + pal_window) & 0xFF
                    pixels[x, y] = palette[idx]
            
            output_path = f'output/icon1_correct_{i}.png'
            img.save(output_path)
            non_zero = sum(1 for b in decoded if b != 0)
            print(f"  图标{i} ({len(icon_data)}字节, {non_zero}非零): {output_path}")

if __name__ == '__main__':
    main()
