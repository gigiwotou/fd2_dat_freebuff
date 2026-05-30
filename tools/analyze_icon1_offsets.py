#!/usr/bin/env python3
"""重新分析索引1 - 可能有内部偏移表结构"""
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
    
    print("=== 索引1 偏移表结构分析 ===")
    start = offsets[1]
    end = offsets[2]
    res_data = data[start:end]
    
    # 解析头 (5字节)
    w = struct.unpack_from('<H', res_data, 0)[0]
    h = struct.unpack_from('<H', res_data, 2)[0]
    pal_window = res_data[4]
    print(f"头: {w}x{h}, 调色板窗口={pal_window}")
    
    # 数据区从偏移5开始
    data_start = 5
    print(f"\n数据区从偏移 {data_start} 开始")
    
    # 解析偏移表 (每项4字节)
    offset_table = []
    pos = data_start
    count = 0
    while pos + 4 <= len(res_data):
        off = struct.unpack_from('<I', res_data, pos)[0]
        
        # 检查偏移是否合理
        if off > len(res_data):
            print(f"偏移 {off} 超出范围，停止解析")
            break
        
        # 检查是否是递增的
        if offset_table and off < offset_table[-1]:
            print(f"偏移 {off} 不是递增的，停止解析")
            break
        
        # 检查第一个偏移是否为0
        if count == 0 and off != 0:
            print(f"第一个偏移不是0 ({off})，可能不是偏移表")
            break
        
        offset_table.append(off)
        count += 1
        pos += 4
        
        # 安全限制
        if count > 200:
            print("达到最大计数，停止")
            break
    
    print(f"\n找到 {len(offset_table)} 个偏移")
    print(f"前10个偏移: {offset_table[:10]}")
    
    # 计算每个项的大小
    print(f"\n项大小:")
    for i in range(min(10, len(offset_table) - 1)):
        size = offset_table[i + 1] - offset_table[i]
        print(f"  项 {i}: {size} 字节")
    
    # 如果最后一个偏移指向数据末尾，计算项数
    if offset_table:
        last_off = offset_table[-1]
        remaining = len(res_data) - data_start - (len(offset_table) * 4) - last_off
        print(f"\n最后偏移: {last_off}")
        print(f"剩余数据: {remaining} 字节")
        
        # 假设每个图标是24x24 = 576像素
        # 但实际编码后的大小可能不同
        print(f"\n尝试解析为偏移表结构:")
        print(f"  数据区总大小: {len(res_data) - data_start} 字节")
        print(f"  偏移表大小: {len(offset_table) * 4} 字节")
        print(f"  实际数据: {len(res_data) - data_start - len(offset_table) * 4} 字节")

if __name__ == '__main__':
    main()
