#!/usr/bin/env python3
"""正确解析索引1：图标是纯EC66像素数据，使用外头宽高"""
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
    res_start_file = offsets[1]
    res_end_file = offsets[2]
    res_data = data[res_start_file:res_end_file]
    
    print("=== 索引1 正确解析 ===")
    print(f"文件偏移: 0x{res_start_file:X}")
    print(f"资源大小: {len(res_data)} 字节")
    
    # 外头
    w = struct.unpack_from('<H', res_data, 0)[0]
    h = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4]
    print(f"外头: {w}x{h}, pal_window={pal_win}")
    
    # 偏移6开始是相对偏移表
    icon_offsets = []
    pos = 6
    while pos + 4 <= len(res_data):
        rel_off = struct.unpack_from('<I', res_data, pos)[0]
        
        # 检查是否合理（相对偏移不应超过资源大小）
        if rel_off >= len(res_data):
            print(f"相对偏移0x{rel_off:X}超出范围，停止")
            break
        
        icon_offsets.append(rel_off)
        pos += 4
        
        if len(icon_offsets) >= 20:
            break
    
    print(f"找到 {len(icon_offsets)} 个图标")
    
    # 解码并渲染前5个图标
    print(f"\n解码前5个图标:")
    for i in range(min(5, len(icon_offsets))):
        rel_off = icon_offsets[i]
        # 下一个偏移或资源末尾
        next_rel = icon_offsets[i + 1] if i + 1 < len(icon_offsets) else len(res_data)
        
        # 图标像素数据
        pixel_data = res_data[rel_off:next_rel]
        
        print(f"\n图标{i}:")
        print(f"  相对偏移: 0x{rel_off:X} - 0x{next_rel:X}")
        print(f"  像素数据大小: {len(pixel_data)} 字节")
        print(f"  预期像素: {w*h}")
        print(f"  前20字节: {' '.join(f'{b:02X}' for b in pixel_data[:20])}")
        
        # EC66解码
        decoded = ec66_decode(pixel_data, w, h)
        
        non_zero = sum(1 for b in decoded if b != 0)
        unique = len(set(decoded))
        print(f"  非零像素: {non_zero}/{w*h}")
        print(f"  唯一值: {unique}")
        
        # 打印前3行
        print(f"  前3行:")
        for row in range(min(3, h)):
            row_pixels = decoded[row*w:(row+1)*w]
            hex_str = ' '.join(f'{p:02X}' for p in row_pixels)
            print(f"    行{row}: {hex_str}")
        
        # 渲染
        img = Image.new('RGB', (w, h))
        pixels = img.load()
        
        for y in range(h):
            for x in range(w):
                idx = decoded[y * w + x]
                # 应用调色板窗口
                idx = (idx + pal_win) & 0xFF
                pixels[x, y] = palette[idx]
        
        output_path = f'output/icon1_final_{i}.png'
        img.save(output_path)
        print(f"  保存到: {output_path}")

if __name__ == '__main__':
    main()
