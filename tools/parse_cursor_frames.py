import struct
from PIL import Image
import os

def parse_fdother_res1():
    """解析FDOTHER.DAT资源1中的子资源"""
    
    dat_path = 'game/FDOTHER.DAT'
    output_dir = 'cursor_frames'
    os.makedirs(output_dir, exist_ok=True)
    
    with open(dat_path, 'rb') as f:
        # 解析DAT文件头
        f.seek(6)
        count = struct.unpack('<I', f.read(4))[0]
        print(f"FDOTHER.DAT 资源总数: {count}")
        
        # 读取资源偏移表
        offsets = []
        for i in range(count):
            offsets.append(struct.unpack('<I', f.read(4))[0])
        
        # 资源1
        res1_start = offsets[1]
        res1_end = offsets[2] if len(offsets) > 2 else offsets[1] + 100000
        res1_size = res1_end - res1_start
        
        print(f"\n资源1:")
        print(f"  文件偏移: {res1_start} (0x{res1_start:04X})")
        print(f"  文件大小: {res1_size}")
        
        # 读取资源1数据
        f.seek(res1_start)
        res1_data = f.read(res1_size)
        
        # 解析32位偏移表
        num_offsets = 0
        sub_offsets = []
        pos = 0
        while pos + 4 <= len(res1_data):
            off = struct.unpack('<I', res1_data[pos:pos+4])[0]
            if off >= res1_size:
                break
            sub_offsets.append(off)
            num_offsets += 1
            pos += 4
            if num_offsets >= 100:
                break
        
        print(f"  子资源数量: {num_offsets}")
        
        # 解析前20个子资源
        print(f"\n解析前20个子资源:")
        for i in range(min(20, num_offsets)):
            sub_off = sub_offsets[i]
            sub_data = res1_data[sub_off:]
            
            if len(sub_data) < 4:
                print(f"  子资源{i}: 数据不足")
                continue
            
            # 读取宽度和高度
            width = struct.unpack('<H', sub_data[0:2])[0]
            height = struct.unpack('<H', sub_data[2:4])[0]
            
            # RLE数据在4字节头之后
            rle_data = sub_data[4:]
            print(f"  子资源{i}: offset={sub_off} (0x{sub_off:04X}), 尺寸={width}x{height}, RLE长度={len(rle_data)}")
            
            # 解码RLE数据
            if width > 0 and height > 0 and width < 256 and height < 256:
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
                            # SKIP
                            col += count
                        elif bit7 and not bit6:
                            # COPY
                            for j in range(count):
                                if col < width:
                                    pixels[row * width + col] = rle_data[p]
                                    p += 1
                                    col += 1
                        elif not bit7 and bit6:
                            # ALTERNATE
                            color = rle_data[p]
                            p += 1
                            for j in range(count):
                                col += 1
                                if col < width:
                                    pixels[row * width + col] = color
                                col += 1
                        else:
                            # FILL
                            color = rle_data[p]
                            p += 1
                            for j in range(count):
                                if col < width:
                                    pixels[row * width + col] = color
                                col += 1
                
                non_zero = sum(1 for px in pixels if px != 0)
                print(f"    非零像素: {non_zero}/{width*height}")
                
                # 保存图片
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
                filename = os.path.join(output_dir, f'sub_{i:02d}_{width}x{height}.png')
                img.save(filename)
                print(f"    保存: {filename}")
            else:
                print(f"    无效尺寸: {width}x{height}")

if __name__ == '__main__':
    parse_fdother_res1()
