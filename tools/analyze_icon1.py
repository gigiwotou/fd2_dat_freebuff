#!/usr/bin/env python3
"""详细分析索引1的结构 - 可能包含多个24x24图标"""
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
    
    # 索引1: 2235字节, 可能包含多个24x24图标
    print("=== 索引1 详细分析 ===")
    start = offsets[1]
    end = offsets[2]
    icon_data = data[start:end]
    print(f"总大小: {len(icon_data)} 字节")
    print(f"前5字节: {icon_data[:5].hex()}")
    
    # 解析头
    w = struct.unpack_from('<H', icon_data, 0)[0]
    h = struct.unpack_from('<H', icon_data, 2)[0]
    pal_window = icon_data[4]
    print(f"头: {w}x{h}, 调色板窗口={pal_window}")
    
    # 数据区从偏移5开始
    tile_data = icon_data[5:]
    print(f"数据区大小: {len(tile_data)} 字节")
    
    # 24x24 = 576像素
    icon_size = 24 * 24
    num_icons = len(tile_data) // icon_size
    remaining = len(tile_data) % icon_size
    
    print(f"\n每个图标: 24x24 = {icon_size} 像素")
    print(f"可能的图标数: {num_icons}")
    print(f"剩余字节: {remaining}")
    
    # 渲染前几个图标
    print(f"\n渲染前{min(10, num_icons)}个图标:")
    for i in range(min(10, num_icons)):
        offset = i * icon_size
        icon_pixels = tile_data[offset:offset + icon_size]
        
        decoded = ec66_decode(icon_pixels, 24, 24)
        
        img = Image.new('RGB', (24, 24))
        pixels = img.load()
        
        for y in range(24):
            for x in range(24):
                idx = decoded[y * 24 + x]
                pixels[x, y] = palette[idx]
        
        output_path = f'output/icon1_item_{i}.png'
        img.save(output_path)
        print(f"  图标 {i}: 保存到 {output_path}")
    
    # 检查数据的前100字节模式
    print(f"\n数据前100字节:")
    for i in range(0, min(100, len(tile_data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in tile_data[i:i+16])
        print(f"  {i:04X}: {hex_str}")

if __name__ == '__main__':
    main()
