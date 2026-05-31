#!/usr/bin/env python3
"""验证索引1的sub_4EC66解码是否正确"""
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
    """sub_4EC66解码 - 严格按照MCP汇编实现"""
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
    start = offsets[1]
    end = offsets[2]
    res_data = data[start:end]
    
    print("=== 索引1 详细分析 ===")
    print(f"总大小: {len(res_data)} 字节")
    
    # 头5字节
    w = struct.unpack_from('<H', res_data, 0)[0]
    h = struct.unpack_from('<H', res_data, 2)[0]
    pal_window = res_data[4]
    print(f"头: {w}x{h}, 调色板窗口={pal_window}")
    
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
    
    # 显示第一个图标
    if len(icon_offsets) > 0:
        start_off = icon_offsets[0]
        end_off = icon_offsets[1] if len(icon_offsets) > 1 else len(res_data)
        icon_data = res_data[start_off:end_off]
        
        print(f"\n图标0:")
        print(f"  偏移: 0x{start_off:X} - 0x{end_off:X}")
        print(f"  大小: {len(icon_data)} 字节")
        print(f"  预期像素: {w*h}")
        
        # 尝试解码
        decoded = ec66_decode(icon_data, w, h)
        
        # 统计
        non_zero = sum(1 for b in decoded if b != 0)
        unique = len(set(decoded))
        print(f"  非零像素: {non_zero}/{w*h}")
        print(f"  唯一值: {unique}")
        
        # 打印前50个像素
        print(f"  前50像素: {' '.join(f'{decoded[i]:02X}' for i in range(min(50, len(decoded))))}")
        
        # 渲染
        img = Image.new('RGB', (w, h))
        pixels = img.load()
        
        for y in range(h):
            for x in range(w):
                idx = decoded[y * w + x]
                # 应用调色板窗口
                idx = (idx + pal_window) & 0xFF
                pixels[x, y] = palette[idx]
        
        img.save('output/icon1_python_test.png')
        print(f"\n保存到: output/icon1_python_test.png")
        
        # 尝试不使用palette_window
        img2 = Image.new('RGB', (w, h))
        pixels2 = img2.load()
        
        for y in range(h):
            for x in range(w):
                idx = decoded[y * w + x]
                pixels2[x, y] = palette[idx]
        
        img2.save('output/icon1_python_no_palwin.png')
        print(f"保存到 (无palette_window): output/icon1_python_no_palwin.png")

if __name__ == '__main__':
    main()
