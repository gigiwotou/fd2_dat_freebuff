import struct
from PIL import Image

data = open('game/FDOTHER.DAT', 'rb').read()
off4 = struct.unpack('<I', data[10 + 4*4:10 + 4*4 + 4])[0]
off5 = struct.unpack('<I', data[10 + 5*4:10 + 5*4 + 4])[0]
res4 = data[off4:off5]

if res4[:4] == b'LMI1':
    count = struct.unpack('<H', res4[4:6])[0]
    print(f'子资源数量: {count}')
    
    base_offset = 6
    
    # 查找所有可能包含字体的子资源
    # 字体应该是多个字符的集合，大小应该是 字符数 * (16*16 或 8*16)
    for i in range(count):
        off = struct.unpack('<I', res4[base_offset + i*4:base_offset + i*4 + 4])[0]
        if i + 1 < count:
            next_off = struct.unpack('<I', res4[base_offset + (i+1)*4:base_offset + (i+1)*4 + 4])[0]
        else:
            next_off = len(res4)
        
        sub_data = res4[off:next_off]
        if len(sub_data) >= 4:
            w = struct.unpack('<H', sub_data[0:2])[0]
            h = struct.unpack('<H', sub_data[2:4])[0]
            
            # 检查是否是字体集（大尺寸，包含多个字符）
            if w >= 16 and h >= 16 and len(sub_data) > 260:
                pixel_size = len(sub_data) - 4  # 减去4字节头
                print(f'\n子资源{i}: {w}x{h}, 数据大小={len(sub_data)}, 像素大小={pixel_size}')
                
                # 尝试解码为图像
                # 假设是16x16字符，每个字符256像素
                if pixel_size % 256 == 0:
                    char_count = pixel_size // 256
                    print(f'  -> 可能包含{char_count}个16x16字符')
                    
                    # 导出前几个字符为图像
                    chars_to_export = min(16, char_count)
                    img = Image.new('P', (16 * chars_to_export, 16))
                    
                    for c in range(chars_to_export):
                        char_data = sub_data[4 + c*256:4 + (c+1)*256]
                        for y in range(16):
                            for x in range(16):
                                pixel = char_data[y * 16 + x]
                                img.putpixel((c * 16 + x, y), pixel)
                    
                    img.save(f'output/font_chars_{i}.png')
                    print(f'  -> 已导出到 output/font_chars_{i}.png')
