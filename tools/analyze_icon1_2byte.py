#!/usr/bin/env python3
"""用2字节偏移解析索引1"""
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
    
    print("=== 索引1 2字节偏移表解析 ===")
    
    # 头5字节
    w = struct.unpack_from('<H', res_data, 0)[0]
    h = struct.unpack_from('<H', res_data, 2)[0]
    pal_window = res_data[4]
    print(f"头: {w}x{h}, 调色板窗口={pal_window}")
    
    # 尝试2字节偏移 (从偏移5开始)
    print(f"\n从偏移5开始解析2字节偏移:")
    icon_offsets = []
    pos = 5
    
    # 读取偏移直到遇到不合理值
    while pos + 2 <= len(res_data):
        off = struct.unpack_from('<H', res_data, pos)[0]
        
        if len(icon_offsets) == 0:
            # 第一个偏移应该是5 (数据区开始) 或 0 (相对于数据区)
            print(f"  第一个偏移: {off} (0x{off:X})")
            if off == 0 or off == 5:
                icon_offsets.append(5 + off if off != 0 else 5)
            elif off < len(res_data):
                icon_offsets.append(off)
            else:
                print(f"  第一个偏移不合理，停止")
                break
        else:
            if off < len(res_data):
                icon_offsets.append(off)
            else:
                print(f"  偏移 {off} 超出范围，停止")
                break
        
        pos += 2
        
        if len(icon_offsets) > 50:
            break
    
    print(f"\n找到 {len(icon_offsets)} 个偏移")
    for i in range(min(20, len(icon_offsets))):
        off = icon_offsets[i]
        if i + 1 < len(icon_offsets):
            size = icon_offsets[i + 1] - off
            print(f"  图标{i}: 偏移 0x{off:X} ({off}), 大小 {size} 字节")
        else:
            size = len(res_data) - off
            print(f"  图标{i}: 偏移 0x{off:X} ({off}), 大小 {size} 字节 (到末尾)")
    
    # 渲染图标
    if len(icon_offsets) > 0:
        print(f"\n渲染前10个图标:")
        for i in range(min(10, len(icon_offsets))):
            start_off = icon_offsets[i]
            end_off = icon_offsets[i + 1] if i + 1 < len(icon_offsets) else len(res_data)
            icon_data = res_data[start_off:end_off]
            
            # 24x24图标
            decoded = ec66_decode(icon_data, 24, 24)
            
            img = Image.new('RGB', (24, 24))
            pixels = img.load()
            
            for y in range(24):
                for x in range(24):
                    idx = decoded[y * 24 + x]
                    pixels[x, y] = palette[idx]
            
            output_path = f'output/icon1_2byte_item_{i}.png'
            img.save(output_path)
            print(f"  图标{i} ({len(icon_data)}字节): {output_path}")

if __name__ == '__main__':
    main()
