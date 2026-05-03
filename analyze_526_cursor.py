"""
验证偏移526和8960处的数据

根据IDA:
- dword_53A81 + 526 处读取4字节 = 8960 (0x2300)
- 然后: raw_data + 8960 得到光标数据
- 直接传给sub_4E98D

但之前解析为19018x19786，这不对。

也许8960处的数据已经是RLE像素数据，不需要宽高头部？
或者宽高位是单独存储的？
"""

import struct
from PIL import Image

def verify_offset_526():
    with open('game/FDOTHER.DAT', 'rb') as f:
        data = f.read()
    
    print(f"FDOTHER.DAT 大小: {len(data)}")
    
    # 偏移526处的值
    offset_526 = struct.unpack('<I', data[526:530])[0]
    print(f"\n偏移526处的值: {offset_526} (0x{offset_526:04X})")
    
    # 读取8960处的数据
    cursor_data = data[offset_526:offset_526+64]
    print(f"偏移{offset_526}处前64字节:")
    for i in range(0, 64, 16):
        hex_str = ' '.join(f'{b:02X}' for b in cursor_data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in cursor_data[i:i+16])
        print(f"  {offset_526+i:04X}: {hex_str}  {ascii_str}")
    
    # 分析可能的格式
    print(f"\n=== 假设是图像头 ===")
    w1 = struct.unpack('<H', cursor_data[0:2])[0]
    h1 = struct.unpack('<H', cursor_data[2:4])[0]
    print(f"前4字节作为width/height: {w1}x{h1}")
    
    w2 = struct.unpack('<H', cursor_data[1:3])[0]
    h2 = struct.unpack('<H', cursor_data[3:5])[0]
    print(f"偏移1开始作为width/height: {w2}x{h2}")
    
    # 尝试假设是24x24图像，直接作为RLE数据解码
    print(f"\n=== 假设是24x24 RLE数据（无头部）===")
    rle_data = cursor_data[0:256]  # 取前256字节
    
    # 根据IDA 4E98D的RLE解码
    pixels = [0] * (24 * 24)
    p = 0
    col = 0
    row = 0
    
    while row < 24 and p < len(rle_data):
        opcode = rle_data[p]
        p += 1
        
        bit7 = (opcode >> 7) & 1
        bit6 = (opcode >> 6) & 1
        count = (opcode & 0x3F) + 1
        
        if bit7 and bit6:
            # SKIP - 跳过像素
            col += count
        elif bit7 and not bit6:
            # COPY - 复制原始像素
            for i in range(count):
                if col < 24 and row < 24:
                    pixels[row * 24 + col] = rle_data[p]
                    p += 1
                    col += 1
        elif not bit7 and bit6:
            # ALTERNATE - 间隔填充
            color = rle_data[p]
            p += 1
            for i in range(count):
                col += 1  # skip even
                if col < 24 and row < 24:
                    pixels[row * 24 + col] = color
                col += 1
        else:
            # FILL - 连续填充
            color = rle_data[p]
            p += 1
            for i in range(count):
                if col < 24 and row < 24:
                    pixels[row * 24 + col] = color
                col += 1
        
        # 换行
        while col >= 24:
            col -= 24
            row += 1
            if row >= 24:
                break
    
    # 统计非零像素
    non_zero = sum(1 for px in pixels if px != 0)
    print(f"非零像素: {non_zero}/576")
    
    # 打印像素网格
    print(f"\n像素网格 (前24行):")
    for row in range(24):
        row_pixels = pixels[row*24:(row+1)*24]
        print(f"  {row:2d}: {' '.join(f'{px:02X}' for px in row_pixels)}")
    
    # 保存为PNG
    img = Image.new('RGBA', (24, 24))
    pixels_rgba = []
    for px in pixels:
        if px == 0:
            pixels_rgba.append((0, 0, 0, 0))  # 透明
        else:
            # 简单映射
            r = (px * 3) % 256
            g = (px * 5) % 256
            b = (px * 7) % 256
            pixels_rgba.append((r, g, b, 255))
    img.putdata(pixels_rgba)
    img.save('output/cursor_from_526_raw.png')
    print(f"\n已保存: output/cursor_from_526_raw.png")

if __name__ == '__main__':
    verify_offset_526()
