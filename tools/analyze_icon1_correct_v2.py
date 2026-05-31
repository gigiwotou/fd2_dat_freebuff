#!/usr/bin/env python3
"""正确解析索引1：偏移6开始的值是相对于资源的偏移"""
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
    res_start = offsets[1]  # 0x4A6 - 文件偏移
    res_end = offsets[2]    # 0xD61 - 文件偏移
    res_data = data[res_start:res_end]
    res_size = len(res_data)
    
    print("=== 索引1 正确解析 ===")
    print(f"文件偏移: 0x{res_start:X} - 0x{res_end:X}")
    print(f"资源大小: {res_size} 字节")
    
    # 外头5字节
    w_outer = struct.unpack_from('<H', res_data, 0)[0]
    h_outer = struct.unpack_from('<H', res_data, 2)[0]
    pal_window = res_data[4]
    print(f"外头: {w_outer}x{h_outer}, 调色板窗口={pal_window}")
    
    # 偏移6开始是相对偏移表（相对于资源开始）
    offset_table_start = 6
    icon_offsets = []
    pos = offset_table_start
    
    while pos + 4 <= res_size:
        rel_off = struct.unpack_from('<I', res_data, pos)[0]
        
        # 转换为文件偏移
        file_off = res_start + rel_off
        
        if file_off > res_end:
            print(f"相对偏移0x{rel_off:X}超出资源范围，停止")
            break
        
        icon_offsets.append((rel_off, file_off))
        pos += 4
        
        if len(icon_offsets) > 50:
            break
    
    print(f"\n找到 {len(icon_offsets)} 个图标:")
    for i in range(min(21, len(icon_offsets))):
        rel_off, file_off = icon_offsets[i]
        if i + 1 < len(icon_offsets):
            _, next_file_off = icon_offsets[i + 1]
            size = next_file_off - file_off
            print(f"  图标{i}: 相对0x{rel_off:X} = 文件0x{file_off:X}, 大小{size}字节")
        else:
            print(f"  图标{i}: 相对0x{rel_off:X} = 文件0x{file_off:X}")
    
    # 解析图标
    if len(icon_offsets) > 0:
        print(f"\n解析前5个图标:")
        for i in range(min(5, len(icon_offsets))):
            rel_off, file_off = icon_offsets[i]
            _, next_file_off = icon_offsets[i + 1] if i + 1 < len(icon_offsets) else (0, res_end)
            
            # 图标数据
            icon_data = data[file_off:next_file_off]
            
            print(f"\n图标{i}:")
            print(f"  文件偏移: 0x{file_off:X} - 0x{next_file_off:X}")
            print(f"  大小: {len(icon_data)} 字节")
            print(f"  前8字节: {' '.join(f'{b:02X}' for b in icon_data[:8])}")
            
            # 根据sub_4EBFF，前4字节是宽高
            if len(icon_data) >= 4:
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
                    
                    output_path = f'output/icon1_correct_{i}.png'
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
