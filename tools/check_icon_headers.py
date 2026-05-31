#!/usr/bin/env python3
"""
检查索引1的每个图标是否有自己的4字节宽高头
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

def main():
    filepath = 'game/FDOTHER.DAT'
    data, offsets = load_fdother(filepath)
    
    # 索引1
    res_start = offsets[1]
    res_end = offsets[2]
    res_data = data[res_start:res_end]
    
    # 外头
    outer_w = struct.unpack_from('<H', res_data, 0)[0]
    outer_h = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4]
    
    print(f"外头: {outer_w}x{outer_h}, pal_window={pal_win}")
    
    # 相对偏移表
    icon_offsets = []
    pos = 6
    while pos + 4 <= len(res_data):
        rel_off = struct.unpack_from('<I', res_data, pos)[0]
        if rel_off >= len(res_data):
            break
        icon_offsets.append(rel_off)
        pos += 4
        if len(icon_offsets) >= 20:
            break
    
    print(f"图标数量: {len(icon_offsets)}\n")
    
    # 检查每个图标的前4字节
    print("=== 检查每个图标的前4字节 ===")
    for i, rel_off in enumerate(icon_offsets):
        next_rel = icon_offsets[i + 1] if i + 1 < len(icon_offsets) else len(res_data)
        icon_size = next_rel - rel_off
        icon_data = res_data[rel_off:rel_off+min(20, icon_size)]
        
        # 尝试解析为宽高
        w_le = struct.unpack_from('<H', icon_data, 0)[0]
        h_le = struct.unpack_from('<H', icon_data, 2)[0]
        
        print(f"图标{i}: 偏移0x{rel_off:X}, 大小{icon_size}")
        print(f"  前8字节: {' '.join(f'{b:02X}' for b in icon_data[:8])}")
        print(f"  作为LE宽高: {w_le}x{h_le}")
        
        # 如果宽高在合理范围内（比如<=200），可能是正确的
        if w_le <= 200 and h_le <= 200 and w_le > 0 and h_le > 0:
            print(f"  >>> 合理的宽高！")
        print()

if __name__ == '__main__':
    main()
