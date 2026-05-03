#!/usr/bin/env python3
"""尝试不同的解码方式"""

import struct
from PIL import Image

def try_different_formats():
    with open('game/FDOTHER.DAT', 'rb') as f:
        data = f.read()
    
    # 资源5
    res5_offset = struct.unpack('<I', data[10+5*4:10+5*4+4])[0]
    res5_data = data[res5_offset:]
    
    # 索引130
    cursor_table_offset = 6 + 130 * 4
    cursor_offset = struct.unpack('<I', res5_data[cursor_table_offset:cursor_table_offset+4])[0]
    
    # 光标数据
    cursor_data = res5_data[cursor_offset:]
    width = struct.unpack('<H', cursor_data[0:2])[0]
    height = struct.unpack('<H', cursor_data[2:4])[0]
    
    print(f"尺寸: {width}x{height}")
    print(f"前32字节: {' '.join(f'{b:02X}' for b in cursor_data[4:36])}")
    
    # 尝试1: 直接作为8位调色板索引（无RLE）
    print(f"\n=== 尝试1: 直接8位索引 ===")
    pixel_data = cursor_data[4:4+width*height]
    print(f"像素数据长度: {len(pixel_data)}")
    if len(pixel_data) == width * height:
        img = Image.new('RGBA', (width, height))
        pixels = []
        for px in pixel_data:
            if px == 0:
                pixels.append((0, 0, 0, 0))
            else:
                r = (px * 3) % 256
                g = (px * 5) % 256
                b = (px * 7) % 256
                pixels.append((r, g, b, 255))
        img.putdata(pixels)
        img.save('output/cursor_raw.png')
        print(f"已保存: output/cursor_raw.png")
        
        # 打印前几行
        for row in range(min(5, height)):
            row_pixels = pixel_data[row*width:(row+1)*width]
            print(f"  {row:2d}: {' '.join(f'{px:02X}' for px in row_pixels)}")
    
    # 尝试2: 16-bit values
    print(f"\n=== 尝试2: 16-bit values ===")
    pixel_data_16 = cursor_data[4:4+width*height*2]
    if len(pixel_data_16) == width * height * 2:
        img = Image.new('RGBA', (width, height))
        pixels = []
        for i in range(0, len(pixel_data_16), 2):
            val = struct.unpack('<H', pixel_data_16[i:i+2])[0]
            if val == 0:
                pixels.append((0, 0, 0, 0))
            else:
                r = (val * 3) % 256
                g = (val * 5) % 256
                b = (val * 7) % 256
                pixels.append((r, g, b, 255))
        img.putdata(pixels)
        img.save('output/cursor_16bit.png')
        print(f"已保存: output/cursor_16bit.png")

if __name__ == '__main__':
    try_different_formats()
