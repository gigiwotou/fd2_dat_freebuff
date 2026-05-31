#!/usr/bin/env python3
"""根据sub_4EBFF汇编，索引1每个图标应该是: [width:2][height:2][pixel_data]"""
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
    """sub_4EC66解码"""
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
    
    # 索引1
    res_start = offsets[1]
    res_end = offsets[2]
    res_data = data[res_start:res_end]
    
    print("=== 索引1 按sub_4EBFF格式解析 ===")
    print(f"资源大小: {len(res_data)} 字节")
    
    # 外头5字节
    w_outer = struct.unpack_from('<H', res_data, 0)[0]
    h_outer = struct.unpack_from('<H', res_data, 2)[0]
    pal_window = res_data[4]
    print(f"外头: {w_outer}x{h_outer}, 调色板窗口={pal_window}")
    
    # 偏移6开始是4字节偏移表
    offset_table_start = 6
    icon_offsets = []
    pos = offset_table_start
    
    while pos + 4 <= len(res_data):
        off = struct.unpack_from('<I', res_data, pos)[0]
        if off > len(res_data):
            break
        icon_offsets.append(off)
        pos += 4
        if len(icon_offsets) > 50:
            break
    
    print(f"找到 {len(icon_offsets)} 个偏移")
    
    # 根据sub_4EBFF，每个图标格式: [width:2][height:2][pixel_data]
    if len(icon_offsets) > 0:
        print(f"\n解析前5个图标:")
        for i in range(min(5, len(icon_offsets))):
            start_off = icon_offsets[i]
            end_off = icon_offsets[i + 1] if i + 1 < len(icon_offsets) else len(res_data)
            icon_data = res_data[start_off:end_off]
            
            print(f"\n图标{i}:")
            print(f"  偏移: 0x{start_off:X} - 0x{end_off:X}")
            print(f"  大小: {len(icon_data)} 字节")
            print(f"  前4字节: {' '.join(f'{b:02X}' for b in icon_data[:4])}")
            
            # 解析宽高
            w = struct.unpack_from('<H', icon_data, 0)[0]
            h = struct.unpack_from('<H', icon_data, 2)[0]
            print(f"  宽高: {w}x{h}")
            
            if w > 0 and w <= 320 and h > 0 and h <= 200:
                # 像素数据从偏移4开始
                pixel_data = icon_data[4:]
                expected_pixels = w * h
                print(f"  像素数据: {len(pixel_data)} 字节 (预期: {expected_pixels})")
                
                # 解码
                decoded = ec66_decode(pixel_data, w, h)
                
                non_zero = sum(1 for b in decoded if b != 0)
                unique = len(set(decoded))
                print(f"  非零像素: {non_zero}/{expected_pixels}")
                print(f"  唯一值: {unique}")
                
                # 渲染
                img = Image.new('RGB', (w, h))
                pixels = img.load()
                
                for y in range(h):
                    for x in range(w):
                        idx = decoded[y * w + x]
                        # 应用调色板窗口
                        idx = (idx + pal_window) & 0xFF
                        pixels[x, y] = palette[idx]
                
                output_path = f'output/icon1_sub4ebff_{i}.png'
                img.save(output_path)
                print(f"  保存到: {output_path}")
                
                # 打印前3行
                print(f"  前3行:")
                for row in range(min(3, h)):
                    row_pixels = decoded[row*w:(row+1)*w]
                    hex_str = ' '.join(f'{p:02X}' for p in row_pixels)
                    print(f"    行{row}: {hex_str}")
            else:
                print(f"  宽高不合理")

if __name__ == '__main__':
    main()
