import struct
from PIL import Image

dat_path = 'bin/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    magic = f.read(4)
    tile_count = struct.unpack('<H', f.read(2))[0]
    
    offsets = []
    for i in range(tile_count):
        offset = struct.unpack('<I', f.read(4))[0]
        offsets.append(offset)
    
    # 读取索引5
    f.seek(offsets[5])
    res_size = offsets[6] - offsets[5]
    res_data = f.read(res_size)
    
    # 解析LMI1
    inner_count = struct.unpack('<H', res_data[4:6])[0]
    print(f"Tile数量: {inner_count}")
    
    # 可视化关键tile
    tiles_to_check = [0, 1, 2, 3, 4, 5, 9, 10, 13, 14]
    
    for idx in tiles_to_check:
        offset = struct.unpack('<I', res_data[6 + idx*4:10 + idx*4])[0]
        w = struct.unpack('<H', res_data[offset:offset+2])[0]
        h = struct.unpack('<H', res_data[offset+2:offset+4])[0]
        
        print(f"\nTile {idx}: {w}x{h}")
        
        if w > 0 and h > 0 and w * h < 10000:
            pixels = res_data[offset+4:offset+4+w*h]
            
            # 创建图像
            img = Image.new('RGB', (w, h))
            for y in range(h):
                for x in range(w):
                    if y * w + x < len(pixels):
                        p = pixels[y * w + x]
                        # 使用简单颜色映射
                        r = (p * 7) % 256
                        g = (p * 13) % 256
                        b = (p * 17) % 256
                        img.putpixel((x, y), (r, g, b))
            
            # 放大4倍
            img_large = img.resize((w*4, h*4), Image.NEAREST)
            img_large.save(f'output/tile_{idx}_{w}x{h}.png')
            print(f"  已保存到 output/tile_{idx}_{w}x{h}.png")
