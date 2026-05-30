#!/usr/bin/env python3
"""检查索引1是否是连续TILE数据"""
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
    
    print("=== 索引1 连续TILE解析 ===")
    start = offsets[1]
    end = offsets[2]
    res_data = data[start:end]
    
    print(f"总大小: {len(res_data)} 字节")
    print(f"前10字节: {' '.join(f'{b:02X}' for b in res_data[:10])}")
    
    # 头5字节: w=24, h=24, pal_window=20
    w = struct.unpack_from('<H', res_data, 0)[0]
    h = struct.unpack_from('<H', res_data, 2)[0]
    pal_window = res_data[4]
    print(f"头: {w}x{h}, 调色板窗口={pal_window}")
    
    # 剩余数据
    tile_data = res_data[5:]
    expected_pixels = w * h  # 24*24 = 576
    print(f"数据区大小: {len(tile_data)} 字节")
    print(f"每个图标像素数: {expected_pixels}")
    print(f"可能的图标数 (如果是原始像素): {len(tile_data) / expected_pixels:.2f}")
    
    # 但数据是EC66编码的，所以实际图标数需要解码
    # 尝试解码整个数据为一个大图像
    print(f"\n尝试1: 解码整个数据为 {w}x{h} 图像")
    decoded = ec66_decode(tile_data, w, h)
    
    img = Image.new('RGB', (w, h))
    pixels = img.load()
    for y in range(h):
        for x in range(w):
            idx = decoded[y * w + x]
            # 应用调色板窗口
            idx = (idx + pal_window) & 0xFF
            pixels[x, y] = palette[idx]
    
    img.save('output/icon1_single.png')
    print(f"  保存到: output/icon1_single.png")
    
    # 打印统计
    non_zero = sum(1 for b in decoded if b != 0)
    unique = len(set(decoded))
    print(f"  非零像素: {non_zero}/{w*h}, 唯一值: {unique}")
    
    # 尝试2: 也许索引1包含多个24x24图标，需要分块解码
    print(f"\n尝试2: 分析前200字节数据模式")
    for i in range(0, min(200, len(tile_data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in tile_data[i:i+16])
        print(f"  偏移{i}: {hex_str}")
    
    # 尝试3: 直接解码前576字节
    print(f"\n尝试3: 只解码前{expected_pixels}字节为24x24")
    if len(tile_data) >= expected_pixels:
        decoded_first = ec66_decode(tile_data[:expected_pixels], w, h)
        
        img = Image.new('RGB', (w, h))
        pixels = img.load()
        for y in range(h):
            for x in range(w):
                idx = decoded_first[y * w + x]
                idx = (idx + pal_window) & 0xFF
                pixels[x, y] = palette[idx]
        
        img.save('output/icon1_first576.png')
        print(f"  保存到: output/icon1_first576.png")

if __name__ == '__main__':
    main()
