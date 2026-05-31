#!/usr/bin/env python3
"""对比分析：检查当前C代码的RLE解码逻辑是否与汇编一致"""
import struct

def main():
    filepath = 'game/FDOTHER.DAT'
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # 获取索引1资源
    res1_start = struct.unpack_from('<I', data, 6 + 4)[0]
    res1_end = struct.unpack_from('<I', data, 6 + 8)[0]
    res_data = data[res1_start:res1_end]
    
    # 解析头部
    outer_w = struct.unpack_from('<H', res_data, 0)[0]
    outer_h = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4]
    
    # 解析偏移表
    icon_offsets = []
    pos = 6
    while pos + 4 <= len(res_data):
        rel_off = struct.unpack_from('<I', res_data, pos)[0]
        if rel_off >= len(res_data):
            break
        icon_offsets.append(rel_off)
        pos += 4
    
    # 获取第一个图标数据
    icon_data = res_data[icon_offsets[0]:icon_offsets[1]]
    
    print(f"图标0数据 ({len(icon_data)} bytes):")
    print(f"  前32字节: {' '.join(f'{b:02X}' for b in icon_data[:32])}")
    
    # 手动解码前20个字节
    print(f"\n手动解码前20个像素:")
    src_idx = 0
    ah = 0
    al = 0
    
    for i in range(20):
        if ah == 0:
            al = icon_data[src_idx]
            src_idx += 1
            if al > 0xC0:
                ah = al - 0xC1
                al = icon_data[src_idx]
                src_idx += 1
            else:
                ah = 0
        else:
            ah -= 1
        
        print(f"  像素[{i:2d}] = 0x{al:02X} ({al:3d}), AH={ah}")
    
    print(f"\n像素值 (十进制): {[0x81, 0x60, 0xBE, 0x04, 0xBD, 0x82, 0xBC, 0xBB, 0xBF, 0x82, 0x82, 0x82, 0xBC, 0xBB, 0xBF, 0x04, 0xBD, 0x81, 0xBE, 0x60]}")

if __name__ == '__main__':
    main()
