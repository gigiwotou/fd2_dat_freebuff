#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
FDOTHER资源解码验证脚本
将C程序输出的.raw文件转换为PNG图像用于验证

格式:
  [4字节: 宽度 (little-endian)]
  [4字节: 高度 (little-endian)]
  [768字节: 调色板 (RGB, 6-bit to 8-bit)]
  [width*height字节: 像素数据 (调色板索引)]

用法:
  python3 decode_to_png.py <input.raw> [output.png]
'''

import sys
import struct
import os

try:
    from PIL import Image
except ImportError:
    print('错误: 需要PIL库 (pip install Pillow)')
    sys.exit(1)

def read_raw_file(filepath):
    '''读取.raw文件并返回(宽度, 高度, 调色板, 像素数据)'''
    with open(filepath, 'rb') as f:
        # 读取宽度和高度
        w = struct.unpack('<I', f.read(4))[0]
        h = struct.unpack('<I', f.read(4))[0]
        
        # 读取调色板 (768 bytes = 256 colors * 3 channels)
        palette_6bit = f.read(768)
        
        # 转换为8-bit调色板 (PIL需要256*3字节)
        palette_8bit = bytearray(256 * 3)
        for i in range(256):
            for c in range(3):
                v6 = palette_6bit[i * 3 + c] & 0x3F
                # 转换公式: value_8bit = (value_6bit << 2) | (value_6bit >> 4)
                palette_8bit[i * 3 + c] = ((v6 << 2) | (v6 >> 4)) & 0xFF
        
        # 读取像素数据
        pixels = f.read(w * h)
        
    return w, h, palette_8bit, pixels

def create_png(input_path, output_path=None):
    '''从.raw文件创建PNG图像'''
    print(f'读取: {input_path}')
    
    if not os.path.exists(input_path):
        print(f'错误: 文件不存在 {input_path}')
        return False
    
    w, h, palette, pixels = read_raw_file(input_path)
    print(f'  尺寸: {w}x{h}')
    print(f'  调色板: 256色 (6-bit -> 8-bit)')
    print(f'  像素: {len(pixels)} bytes')
    
    # 创建图像
    # PIL的putpalette需要256*3字节的调色板
    img = Image.frombytes('P', (w, h), pixels)
    img.putpalette(palette)
    
    # 设置输出路径
    if output_path is None:
        # 从输入文件名生成PNG文件名
        base = os.path.splitext(input_path)[0]
        output_path = f'{base}.png'
    
    # 保存PNG
    img.save(output_path)
    print(f'已保存: {output_path}')
    
    return True

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if create_png(input_path, output_path):
        print('转换完成!')
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()