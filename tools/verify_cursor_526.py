import struct

def analyze_cursor_at_526():
    """验证FDOTHER.DAT偏移526处的光标数据是否为RLE压缩"""
    
    with open('game/FDOTHER.DAT', 'rb') as f:
        data = f.read()
    
    print(f"FDOTHER.DAT 总大小: {len(data)} 字节")
    
    # 读取偏移526处的相对偏移
    rel_offset = struct.unpack('<I', data[526:530])[0]
    print(f"\n偏移526处的相对偏移: {rel_offset} (0x{rel_offset:04X})")
    
    if rel_offset == 0 or rel_offset >= len(data):
        print(f"错误: 相对偏移 {rel_offset} 超出文件范围")
        return
    
    # 光标图像数据
    cursor_data = data[rel_offset:]
    width = struct.unpack('<H', cursor_data[0:2])[0]
    height = struct.unpack('<H', cursor_data[2:4])[0]
    
    print(f"光标图像: 偏移={rel_offset}, 尺寸={width}x{height}")
    print(f"前32字节: {' '.join(f'{b:02X}' for b in cursor_data[:32])}")
    
    # RLE数据
    rle_data = cursor_data[4:]
    print(f"RLE数据长度: {len(rle_data)}")
    
    # 尝试RLE解码
    print(f"\n=== RLE解码测试 ===")
    pixels = [0] * (width * height)
    p = 0
    for row in range(height):
        col = 0
        while col < width and p < len(rle_data):
            opcode = rle_data[p]
            p += 1
            count = (opcode & 0x3F) + 1
            
            bit7 = (opcode >> 7) & 1
            bit6 = (opcode >> 6) & 1
            
            if bit7 and bit6:
                col += count
            elif bit7 and not bit6:
                for i in range(count):
                    if col < width:
                        pixels[row * width + col] = rle_data[p]
                        p += 1
                        col += 1
            elif not bit7 and bit6:
                color = rle_data[p]
                p += 1
                for i in range(count):
                    col += 1
                    if col < width:
                        pixels[row * width + col] = color
                    col += 1
            else:
                color = rle_data[p]
                p += 1
                for i in range(count):
                    if col < width:
                        pixels[row * width + col] = color
                    col += 1
    
    non_zero = sum(1 for px in pixels if px != 0)
    print(f"非零像素: {non_zero}/{width*height}")
    
    # 打印像素网格
    print(f"\n像素网格 (0=透明):")
    for row in range(height):
        row_pixels = pixels[row*width:(row+1)*width]
        print(f"  {row:2d}: {' '.join(f'{px:02X}' for px in row_pixels)}")
    
    # 保存为PNG
    from PIL import Image
    img = Image.new('RGBA', (width, height))
    pixels_rgba = []
    for px in pixels:
        if px == 0:
            pixels_rgba.append((0, 0, 0, 0))
        else:
            # 简单调色板映射
            r = (px * 3) % 256
            g = (px * 5) % 256
            b = (px * 7) % 256
            pixels_rgba.append((r, g, b, 255))
    img.putdata(pixels_rgba)
    img.save('output/cursor_from_526.png')
    print(f"\n保存: output/cursor_from_526.png")

if __name__ == '__main__':
    analyze_cursor_at_526()
