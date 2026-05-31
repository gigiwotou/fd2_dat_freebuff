#!/usr/bin/env python3
"""根据sub_4EBFF汇编重新分析索引1图标0的结构"""
import struct

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

def main():
    filepath = 'game/FDOTHER.DAT'
    data, offsets = load_fdother(filepath)
    
    # 索引1资源
    start = offsets[1]
    end = offsets[2]
    res_data = data[start:end]
    
    print("=== 索引1 根据sub_4EBFF重新分析 ===")
    print(f"总大小: {len(res_data)} 字节")
    
    # 根据sub_4EBFF，数据格式应该是:
    # [width:2][height:2][pixel_data...]
    # 所以偏移6开始的4字节偏移表指向的是包含宽高的tile数据
    
    # 头5字节
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
    for i in range(min(5, len(icon_offsets))):
        print(f"  偏移{i}: 0x{icon_offsets[i]:X} = {icon_offsets[i]}")
    
    # 分析图标0 (根据sub_4EBFF，每个图标内部有宽高头)
    if len(icon_offsets) > 0:
        start_off = icon_offsets[0]
        end_off = icon_offsets[1] if len(icon_offsets) > 1 else len(res_data)
        icon_data = res_data[start_off:end_off]
        
        print(f"\n=== 图标0 内部结构 ===")
        print(f"大小: {len(icon_data)} 字节")
        print(f"前4字节: {' '.join(f'{b:02X}' for b in icon_data[:4])}")
        
        # 根据sub_4EBFF，前4字节是宽高
        w = struct.unpack_from('<H', icon_data, 0)[0]
        h = struct.unpack_from('<H', icon_data, 2)[0]
        print(f"内部头: {w}x{h}")
        
        if w > 0 and w <= 320 and h > 0 and h <= 200:
            print(f"  看起来是有效的宽高!")
            pixel_data = icon_data[4:]
            print(f"  像素数据: {len(pixel_data)} 字节")
            print(f"  预期像素: {w * h}")
            
            # 解码
            decoded = ec66_decode(pixel_data, w, h)
            
            non_zero = sum(1 for b in decoded if b != 0)
            unique = len(set(decoded))
            print(f"  非零像素: {non_zero}/{w*h}")
            print(f"  唯一值: {unique}")
            
            # 前50像素
            print(f"  前50像素: {' '.join(f'{decoded[i]:02X}' for i in range(min(50, len(decoded))))}")
            
            # 按行打印前3行
            print(f"\n  前3行像素:")
            for row in range(min(3, h)):
                row_pixels = decoded[row*w:(row+1)*w]
                hex_str = ' '.join(f'{p:02X}' for p in row_pixels)
                print(f"    行{row}: {hex_str}")
        else:
            print(f"  宽高不合理，可能不是这种格式")

if __name__ == '__main__':
    main()
