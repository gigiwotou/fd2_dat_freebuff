#!/usr/bin/env python3
"""详细分析索引1图标0的数据结构"""
import struct

def main():
    dat_path = 'game/FDOTHER.DAT'
    with open(dat_path, 'rb') as f:
        data = f.read()
    
    # 解析索引表
    offsets = []
    offset = 6
    while offset + 4 <= len(data):
        off = struct.unpack_from('<I', data, offset)[0]
        if off == 0 or off >= len(data):
            break
        offsets.append(off)
        offset += 4
    offsets.append(len(data))
    
    # 索引1的资源数据
    res_start = offsets[1]
    res_data = data[res_start:]
    
    # 解析头部
    outer_w = struct.unpack_from('<H', res_data, 0)[0]
    outer_h = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4] | (res_data[5] << 8)
    
    print(f"索引1: {outer_w}x{outer_h}, pal_window={pal_win}")
    
    # 解析偏移表
    icon_offsets = []
    pos = 6
    while pos + 4 <= len(res_data):
        rel_off = struct.unpack_from('<I', res_data, pos)[0]
        if rel_off >= len(res_data):
            break
        icon_offsets.append(rel_off)
        pos += 4
    
    print(f"图标数量: {len(icon_offsets)}")
    
    # 图标0的原始数据
    start = icon_offsets[0]
    end = icon_offsets[1] if len(icon_offsets) > 1 else len(res_data)
    icon_raw = res_data[start:end]
    
    print(f"\n图标0 原始数据 ({len(icon_raw)}字节):")
    print(f"偏移={start}, 大小={end-start}")
    
    # 检查前4字节
    if len(icon_raw) >= 4:
        w1 = struct.unpack_from('<H', icon_raw, 0)[0]
        h1 = struct.unpack_from('<H', icon_raw, 2)[0]
        print(f"前4字节作为宽高: {w1}x{h1}")
        if w1 > 1000 or h1 > 1000:
            print(f"  -> 异常，图标数据不包含4字节宽高头")
        else:
            print(f"  -> 正常，图标数据包含4字节宽高头")
    
    # 分析EC66编码数据
    print(f"\n图标0 EC66数据前64字节:")
    for i in range(0, min(64, len(icon_raw)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in icon_raw[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in icon_raw[i:i+16])
        print(f"  {i:3d}: {hex_str:<48s} {ascii_str}")
    
    # 尝试解析EC66编码
    print(f"\nEC66解码分析:")
    src_idx = 0
    ah = 0
    al = 0
    pixel_count = 0
    
    while src_idx < len(icon_raw) and pixel_count < 100:
        if ah > 0:
            ah -= 1
            print(f"  像素{pixel_count}: AH={ah+1}->重复 AL={al}")
            pixel_count += 1
        else:
            if src_idx >= len(icon_raw):
                break
            al = icon_raw[src_idx]
            src_idx += 1
            
            if al > 0xC0:
                run_len = al - 0xC1
                if src_idx < len(icon_raw):
                    al = icon_raw[src_idx]
                    src_idx += 1
                print(f"  像素{pixel_count}: RLE {run_len}次 AL={al} (原始字节: {icon_raw[src_idx-2]:02X} {icon_raw[src_idx-1]:02X})")
                ah = run_len - 1
                pixel_count += 1
            else:
                print(f"  像素{pixel_count}: 直接 AL={al} (原始字节: {al:02X})")
                pixel_count += 1
    
    print(f"\n总像素数: {pixel_count}")
    print(f"源数据消耗: {src_idx}/{len(icon_raw)}")

if __name__ == '__main__':
    main()
