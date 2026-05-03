import struct

def analyze_fdother_index1():
    """直接从FDOTHER.DAT的索引1解析图像数据"""
    
    with open('game/FDOTHER.DAT', 'rb') as f:
        data = f.read()
    
    print(f"FDOTHER.DAT 总大小: {len(data)} 字节")
    
    # FDOTHER资源索引结构：前4字节是资源数量
    # 然后是资源偏移表，每个资源4字节偏移
    num_resources = struct.unpack('<I', data[0:4])[0]
    print(f"资源数量: {num_resources}")
    
    # 读取索引1的偏移
    if num_resources > 1:
        index1_offset = struct.unpack('<I', data[4:8])[0]
        print(f"\n索引1偏移: {index1_offset} (0x{index1_offset:04X})")
        
        # 查看索引1处的数据
        index1_data = data[index1_offset:]
        print(f"索引1前64字节: {' '.join(f'{b:02X}' for b in index1_data[:64])}")
        
        # 尝试解析为图像：前2字节宽，接着2字节高
        width = struct.unpack('<H', index1_data[0:2])[0]
        height = struct.unpack('<H', index1_data[2:4])[0]
        print(f"\n假设为图像: 宽={width}, 高={height}")
        
        if width > 0 and height > 0 and width < 256 and height < 256:
            # 图像数据从偏移4开始
            img_data = index1_data[4:]
            print(f"图像数据长度: {len(img_data)}")
            print(f"图像数据前64字节: {' '.join(f'{b:02X}' for b in img_data[:64])}")
            
            # 保存原始数据供分析
            with open('output/cursor_index1_raw.bin', 'wb') as f:
                f.write(img_data)
            print(f"\n保存原始数据: output/cursor_index1_raw.bin")
            
            # 尝试直接作为调色板索引图像
            from PIL import Image
            img = Image.new('RGBA', (width, height))
            pixels = []
            for i in range(min(width * height, len(img_data))):
                px = img_data[i]
                if px == 0:
                    pixels.append((0, 0, 0, 0))  # 透明
                else:
                    # 简单颜色映射
                    r = (px * 7) % 256
                    g = (px * 13) % 256
                    b = (px * 17) % 256
                    pixels.append((r, g, b, 255))
            
            # 填充剩余像素
            while len(pixels) < width * height:
                pixels.append((0, 0, 0, 0))
                
            img.putdata(pixels)
            img.save('output/cursor_index1_raw.png')
            print(f"保存原始图像: output/cursor_index1_raw.png")
            
            # 尝试RLE解码
            print(f"\n=== 尝试RLE解码 ===")
            rle_data = img_data
            pixels_rle = [0] * (width * height)
            p = 0
            for row in range(height):
                col = 0
                while col < width and p < len(rle_data):
                    opcode = rle_data[p]
                    p += 1
                    
                    # RLE模式：bit7=SKIP, bit6=COPY/FILL/ALTERNATE
                    bit7 = (opcode >> 7) & 1
                    bit6 = (opcode >> 6) & 1
                    count = (opcode & 0x3F) + 1
                    
                    if bit7 and bit6:
                        # SKIP: 跳过count个像素
                        col += count
                    elif bit7 and not bit6:
                        # COPY: 复制count个像素
                        for i in range(count):
                            if col < width:
                                pixels_rle[row * width + col] = rle_data[p]
                                p += 1
                                col += 1
                    elif not bit7 and bit6:
                        # FILL: 填充count个像素为相同颜色
                        color = rle_data[p]
                        p += 1
                        for i in range(count):
                            if col < width:
                                pixels_rle[row * width + col] = color
                            col += 1
                    else:
                        # ALTERNATE: 交替填充
                        color = rle_data[p]
                        p += 1
                        for i in range(count):
                            if col < width:
                                pixels_rle[row * width + col] = color
                            col += 1
            
            non_zero = sum(1 for px in pixels_rle if px != 0)
            print(f"RLE解码后非零像素: {non_zero}/{width*height}")
            
            # 保存RLE解码图像
            pixels_rle_rgba = []
            for px in pixels_rle:
                if px == 0:
                    pixels_rle_rgba.append((0, 0, 0, 0))
                else:
                    r = (px * 7) % 256
                    g = (px * 13) % 256
                    b = (px * 17) % 256
                    pixels_rle_rgba.append((r, g, b, 255))
            
            img_rle = Image.new('RGBA', (width, height))
            img_rle.putdata(pixels_rle_rgba)
            img_rle.save('output/cursor_index1_rle.png')
            print(f"保存RLE图像: output/cursor_index1_rle.png")
            
            # 打印像素网格
            print(f"\n像素网格 (RLE解码):")
            for row in range(height):
                row_pixels = pixels_rle[row*width:(row+1)*width]
                print(f"  {row:2d}: {' '.join(f'{px:02X}' for px in row_pixels)}")
        else:
            print(f"尺寸无效: {width}x{height}")
    else:
        print("资源数量不足")

if __name__ == '__main__':
    analyze_fdother_index1()
