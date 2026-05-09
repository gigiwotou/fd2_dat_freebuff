import struct
from PIL import Image

data = open('game/FDOTHER.DAT', 'rb').read()

# 读取索引4
off4 = struct.unpack('<I', data[10 + 4*4:10 + 4*4 + 4])[0]
off5 = struct.unpack('<I', data[10 + 5*4:10 + 5*4 + 4])[0]
res4 = data[off4:off5]

print(f'索引4总大小: {len(res4)}')
print(f'魔数: {res4[:4]}')

if res4[:4] == b'LMI1':
    count = struct.unpack('<H', res4[4:6])[0]
    print(f'子资源数量: {count}')
    
    base_offset = 6
    
    # 分析所有16x16子资源
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
            
            if w == 16 and h == 16:
                data_size = len(sub_data) - 4
                expected_size = w * h  # 16x16 = 256
                print(f'\n子资源{i}: {w}x{h}, 数据大小={data_size}, 预期={expected_size}')
                
                if data_size == expected_size:
                    # 这是标准16x16字体
                    pixel_data = sub_data[4:4+expected_size]
                    
                    # 创建图像
                    img = Image.new('RGB', (16, 16))
                    for y in range(16):
                        for x in range(16):
                            val = pixel_data[y * 16 + x]
                            if val > 0:
                                img.putpixel((x, y), (255, 255, 255))
                            else:
                                img.putpixel((x, y), (0, 0, 0))
                    
                    img.save(f'output/fdother_font_char_{i}.png')
                    print(f'已导出: output/fdother_font_char_{i}.png')
                    
                    # 打印前4行像素数据
                    print(f'像素数据(前4行):')
                    for y in range(4):
                        row = pixel_data[y*16:(y+1)*16]
                        print(f'  行{y}: {row.hex(" ")}')
