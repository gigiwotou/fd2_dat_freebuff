#!/usr/bin/env python3
"""详细分析索引1的图标数据偏移"""
import struct

def main():
    with open('game/FDOTHER.DAT', 'rb') as f:
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
    
    print(f"总索引数: {len(offsets)-1}")
    
    # 索引1的资源数据
    res_start = offsets[1]
    res_end = offsets[2]
    res_data = data[res_start:res_end]
    
    print(f"\n=== 索引1 资源 ===")
    print(f"偏移: {res_start} - {res_end}")
    print(f"大小: {len(res_data)}")
    print(f"前20字节: {' '.join(f'{b:02X}' for b in res_data[:20])}")
    
    # 解析头部
    outer_w = struct.unpack_from('<H', res_data, 0)[0]
    outer_h = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4]
    
    print(f"\n外头: {outer_w}x{outer_h}, pal_window={pal_win}")
    
    # 解析偏移表
    icon_offsets = []
    pos = 6
    while pos + 4 <= len(res_data):
        rel_off = struct.unpack_from('<I', res_data, pos)[0]
        if rel_off >= len(res_data):
            break
        icon_offsets.append(rel_off)
        pos += 4
    
    print(f"\n图标数量: {len(icon_offsets)}")
    print(f"偏移表位置: 6 - {6 + len(icon_offsets)*4}")
    
    # 检查每个图标的偏移和大小
    print(f"\n=== 图标数据详情 ===")
    for i in range(len(icon_offsets)):
        rel_off = icon_offsets[i]
        next_rel = icon_offsets[i+1] if i+1 < len(icon_offsets) else len(res_data)
        icon_data = res_data[rel_off:next_rel]
        
        # 检查前4字节
        if len(icon_data) >= 4:
            w = struct.unpack_from('<H', icon_data, 0)[0]
            h = struct.unpack_from('<H', icon_data, 2)[0]
            print(f"图标{i}: 偏移={rel_off}, 大小={len(icon_data)}, 前4字节={w}x{h}")
            if w <= 320 and h <= 200:
                print(f"  -> 宽高合理")
            else:
                print(f"  -> 宽高异常")
        else:
            print(f"图标{i}: 偏移={rel_off}, 大小={len(icon_data)}, 数据不足")

if __name__ == '__main__':
    main()
