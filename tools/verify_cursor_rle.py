#!/usr/bin/env python3
"""验证光标RLE解码 - 严格按照IDA 4E98D汇编逻辑"""

import struct
from PIL import Image

def decode_cursor_rle():
    with open('game/FDOTHER.DAT', 'rb') as f:
        data = f.read()
    
    # 资源5
    res5_offset = struct.unpack('<I', data[10+5*4:10+5*4+4])[0]
    res5_data = data[res5_offset:]
    
    # 索引130（光标）
    cursor_table_offset = 6 + 130 * 4
    cursor_offset = struct.unpack('<I', res5_data[cursor_table_offset:cursor_table_offset+4])[0]
    
    # 光标数据
    cursor_data = res5_data[cursor_offset:]
    width = struct.unpack('<H', cursor_data[0:2])[0]
    height = struct.unpack('<H', cursor_data[2:4])[0]
    print(f"光标尺寸: {width}x{height}")
    print(f"RLE前16字节: {' '.join(f'{b:02X}' for b in cursor_data[4:20])}")
    
    # RLE数据
    rle_data = cursor_data[4:]
    pixels = [0] * (width * height)
    
    # 严格按照IDA 4E98D汇编逻辑解码
    # 正确的模式映射（根据汇编分析）:
    # bit7=0, bit6=0 (0x00-0x3F): FILL - rep stosb
    # bit7=0, bit6=1 (0x40-0x7F): ALTERNATE - 间隔填充
    # bit7=1, bit6=0 (0x80-0xBF): SKIP - dst += count
    # bit7=1, bit6=1 (0xC0-0xFF): ALTERNATE - 间隔填充
    
    src = 0
    
    for row in range(height):
        col = 0
        while col < width and src < len(rle_data):
            opcode = rle_data[src]
            src += 1
            
            count = (opcode & 0x3F) + 1
            
            bit7 = (opcode >> 7) & 1
            bit6 = (opcode >> 6) & 1
            
            if bit7 and bit6:
                # 0xC0-0xFF: ALTERNATE - 间隔填充（奇数位置）
                color = rle_data[src]
                src += 1
                for i in range(count):
                    col += 1  # 跳过偶数位置
                    if col < width:
                        pixels[row * width + col] = color
                    col += 1  # 前进
            elif bit7 and not bit6:
                # 0x80-0xBF: SKIP - 跳过像素（透明）
                col += count
            elif not bit7 and bit6:
                # 0x40-0x7F: ALTERNATE - 间隔填充（奇数位置）
                color = rle_data[src]
                src += 1
                for i in range(count):
                    col += 1  # 跳过偶数位置
                    if col < width:
                        pixels[row * width + col] = color
                    col += 1  # 前进
            else:
                # 0x00-0x3F: FILL - 连续填充
                color = rle_data[src]
                src += 1
                for i in range(count):
                    if col < width:
                        pixels[row * width + col] = color
                    col += 1
    
    # 统计
    non_zero = sum(1 for px in pixels if px != 0)
    print(f"\n非零像素: {non_zero}/{width*height}")
    
    # 打印所有行
    print(f"\n像素网格:")
    for row in range(height):
        row_pixels = pixels[row*width:(row+1)*width]
        print(f"  {row:2d}: {' '.join(f'{px:02X}' for px in row_pixels)}")
    
    # 保存为PNG
    img = Image.new('RGBA', (width, height))
    pixels_rgba = []
    for px in pixels:
        if px == 0:
            pixels_rgba.append((0, 0, 0, 0))
        else:
            r = (px * 3) % 256
            g = (px * 5) % 256
            b = (px * 7) % 256
            pixels_rgba.append((r, g, b, 255))
    img.putdata(pixels_rgba)
    img.save('output/cursor_verify.png')
    print(f"\n已保存: output/cursor_verify.png")

if __name__ == '__main__':
    decode_cursor_rle()
