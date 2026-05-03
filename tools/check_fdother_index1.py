#!/usr/bin/env python3
"""检查FDOTHER索引1的资源0"""

import struct
from PIL import Image

def check_fdother_index1():
    with open('game/FDOTHER.DAT', 'rb') as f:
        data = f.read()
    
    # FDOTHER.DAT格式：偏移6=资源数量，偏移10开始=资源表
    resource_count = struct.unpack('<I', data[6:10])[0]
    print(f"资源数量: {resource_count}")
    
    # 索引1
    res1_offset = struct.unpack('<I', data[10+1*4:10+1*4+4])[0]
    res2_offset = struct.unpack('<I', data[10+2*4:10+2*4+4])[0]
    res1_size = res2_offset - res1_offset
    
    print(f"\n索引1: 偏移={res1_offset}, 大小={res1_size}")
    print(f"前32字节: {' '.join(f'{b:02X}' for b in data[res1_offset:res1_offset+32])}")
    
    # 检查是否是24x24图像
    width = struct.unpack('<H', data[res1_offset:res1_offset+2])[0]
    height = struct.unpack('<H', data[res1_offset+2:res1_offset+4])[0]
    print(f"宽高: {width}x{height}")
    
    if width == 24 and height == 24:
        print("匹配24x24!")
        # RLE解码
        rle_data = data[res1_offset+4:res1_offset+4+200]
        print(f"RLE前16字节: {' '.join(f'{b:02X}' for b in rle_data[:16])}")

if __name__ == '__main__':
    check_fdother_index1()
