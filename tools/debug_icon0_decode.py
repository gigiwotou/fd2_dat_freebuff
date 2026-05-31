#!/usr/bin/env python3
"""
分析图标0的解码过程，逐步检查每个像素值
"""
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

def sub_4ec66_step_debug(src_data, src_size, step_num):
    global ec66_ah, ec66_prev_al, ec66_src_pos
    
    if ec66_ah > 0:
        ec66_ah -= 1
        print(f"  Step {step_num}: AH>0, 返回prev_al=0x{ec66_prev_al:02X} ({ec66_prev_al}), AH={ec66_ah}")
        return ec66_prev_al
    
    if ec66_src_pos >= src_size:
        print(f"  Step {step_num}: src_idx超出范围")
        return 0
    
    al = src_data[ec66_src_pos]
    old_pos = ec66_src_pos
    ec66_src_pos += 1
    
    print(f"  Step {step_num}: 读取[0x{old_pos:X}] = 0x{al:02X} ({al})", end='')
    
    if al > 0xC0:
        ec66_ah = al - 0xC1
        if ec66_src_pos < src_size:
            al = src_data[ec66_src_pos]
            ec66_src_pos += 1
            print(f" -> RLE: ah={ec66_ah}, 读取像素=0x{al:02X} ({al})")
        else:
            print(f" -> RLE: ah={ec66_ah}, 但src_idx超出")
        ec66_prev_al = al
        return al
    else:
        ec66_ah = 0
        ec66_prev_al = al
        print(f" -> 直接像素")
        return al

def main():
    filepath = 'game/FDOTHER.DAT'
    data, offsets = load_fdother(filepath)
    
    # 索引1
    res_start = offsets[1]
    res_end = offsets[2]
    res_data = data[res_start:res_end]
    
    # 相对偏移表
    pos = 6
    icon_offsets = []
    while pos + 4 <= len(res_data):
        rel_off = struct.unpack_from('<I', res_data, pos)[0]
        if rel_off >= len(res_data):
            break
        icon_offsets.append(rel_off)
        pos += 4
        if len(icon_offsets) >= 1:
            break
    
    # 图标0
    rel_off = icon_offsets[0]
    icon_data = res_data[rel_off:]
    
    print(f"图标0起始偏移: 0x{rel_off:X}")
    print(f"图标数据前32字节: {' '.join(f'{b:02X}' for b in icon_data[:32])}")
    print()
    
    # 重置EC66状态
    global ec66_ah, ec66_prev_al, ec66_src_pos
    ec66_ah = 0
    ec66_prev_al = 0
    ec66_src_pos = 0
    
    # 解码前50个像素
    print("=== 解码前50个像素 ===")
    pixels = []
    for i in range(50):
        pixel = sub_4ec66_step_debug(icon_data, len(icon_data), i)
        pixels.append(pixel)
    
    print(f"\n前50像素值: {' '.join(f'{p:02X}' for p in pixels)}")
    print(f"前50像素值(十进制): {' '.join(str(p) for p in pixels)}")

ec66_ah = 0
ec66_prev_al = 0
ec66_src_pos = 0

if __name__ == '__main__':
    main()
