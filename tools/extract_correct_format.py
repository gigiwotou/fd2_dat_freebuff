"""
根据sub_111BA分析，嵌套DAT访问tile的方式是：
- 读取 4*index + 6 处的 8 字节 (start, end)
- tile数据 = data[start:end]

但我们的问题是如何确定每个tile的宽高？
查看sub_2EB9F:
  v9 = *(DWORD *)(a5 + 4*a6 + 8) + a5
  sub_4E98D(v9+9, *v9, v9[1], a7, a8, value)

这里:
- v9[0] = width
- v9[1] = height
- v9+9 = RLE数据 (跳过9字节头)

所以tile数据格式是:
[width:2][height:2][? :4][? :2][RLE数据]
总共 10 字节头，其中前4字节是宽高

让我们重新解析：
嵌套DAT结构:
- LLLLLL (6)
- count (4)
- offsets[count*4] - 每个条目是4字节的资源起始偏移
- 但实际tile访问是通过 4*index + 6 读取 8 字节

等等，让我重新理解：
fseek(4*a7+6) 读取 8 字节
所以从字节 6 开始，每 4 字节一个偏移
但 sub_2EB9F 使用 a5 + 4*a6 + 8，说明tile数据有8字节头

让我尝试：
嵌套DAT偏移表指向的是tile数据块
每个tile数据块格式: [width:2][height:2][unknown:4][RLE数据]
"""
import struct
from PIL import Image
import os

fdother_path = r"D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT"
output_dir = r"D:\workspace\fd2_dat_freebuff\output\fdother_7_tiles_v5\scene_0"
os.makedirs(output_dir, exist_ok=True)

def load_palette(fdother_path):
    with open(fdother_path, "rb") as f:
        f.read(6)
        count = struct.unpack("<I", f.read(4))[0]
        offsets = struct.unpack(f"<{count}I", f.read(count * 4))
        start = offsets[75]
        end = offsets[76] if 76 < count else None
        f.seek(start)
        pal_data = f.read(768) if end is None else f.read(end - start)
    
    palette_rgb = []
    for i in range(256):
        r = (pal_data[i * 3] << 2) | (pal_data[i * 3] >> 4)
        g = (pal_data[i * 3 + 1] << 2) | (pal_data[i * 3 + 1] >> 4)
        b = (pal_data[i * 3 + 2] << 2) | (pal_data[i * 3 + 2] >> 4)
        palette_rgb.append((r, g, b))
    
    return palette_rgb

def decompress_rle(src_data, width, height):
    output = bytearray(width * height)
    src_pos = 0
    dst_pos = 0
    src_end = len(src_data)
    
    for row in range(height):
        count = width
        while count > 0 and src_pos < src_end:
            ctrl = src_data[src_pos]
            src_pos += 1
            
            count_1 = (ctrl & 0x3F) + 1
            bit7 = (ctrl >> 7) & 1
            bit6 = (ctrl >> 6) & 1
            
            if bit7 and bit6:
                dst_pos += count_1
                count -= count_1
            elif bit7 and not bit6:
                if src_pos + count_1 > src_end:
                    break
                for i in range(count_1):
                    output[dst_pos] = src_data[src_pos]
                    dst_pos += 1
                    src_pos += 1
                count -= count_1
            elif not bit7 and bit6:
                if src_pos >= src_end:
                    break
                fill = src_data[src_pos]
                src_pos += 1
                for i in range(count_1):
                    output[dst_pos + 1] = fill
                    dst_pos += 2
                count = count - count_1 - count_1
            else:
                if src_pos >= src_end:
                    break
                fill = src_data[src_pos]
                src_pos += 1
                for i in range(count_1):
                    output[dst_pos] = fill
                    dst_pos += 1
                count -= count_1
        dst_pos = row * width + width
    
    return bytes(output)

palette_rgb = load_palette(fdother_path)

with open(fdother_path, "rb") as f:
    f.read(6)
    count = struct.unpack("<I", f.read(4))[0]
    offsets = struct.unpack(f"<{count}I", f.read(count * 4))
    
    index = 82
    start = offsets[index]
    end = offsets[index + 1]
    f.seek(start)
    resource_data = f.read(end - start)
    
    print(f"资源大小: {len(resource_data)}")
    offset_count = struct.unpack("<I", resource_data[6:10])[0]
    print(f"偏移数量: {offset_count}")
    
    # 根据sub_2EB9F的访问方式:
    # v9 = *(DWORD *)(a5 + 4*a6 + 8) + a5
    # 这意味着从字节 8 开始，每 4 字节一个偏移，但这是tile数据块的相对偏移
    
    # 实际上嵌套DAT的偏移表结构可能是:
    # [count:4][offset0:4][offset1:4][offset2:4]...[tile_count:4]
    # tile_count后是tile元数据表
    
    # 但根据我们之前的分析，偏移表只有3个有效值
    # 让我们尝试直接解析tile数据，假设每个tile有8字节头
    
    # 第一个tile偏移
    tile0_offset = struct.unpack("<I", resource_data[10:14])[0]
    tile1_offset = struct.unpack("<I", resource_data[14:18])[0]
    tile2_offset = struct.unpack("<I", resource_data[18:22])[0]
    file_end = struct.unpack("<I", resource_data[22:26])[0]
    
    print(f"\n偏移表:")
    print(f"  Tile 0 起始: {tile0_offset}")
    print(f"  Tile 1 起始: {tile1_offset}")
    print(f"  Tile 2 起始: {tile2_offset}")
    print(f"  文件结束: {file_end}")
    
    # 提取每个tile数据
    tiles = [
        (0, tile0_offset, tile1_offset),
        (1, tile1_offset, tile2_offset),
        (2, tile2_offset, file_end if file_end < len(resource_data) else len(resource_data))
    ]
    
    for tile_idx, tile_start, tile_end in tiles:
        tile_data = resource_data[tile_start:tile_end]
        print(f"\nTile {tile_idx}: 偏移 {tile_start}-{tile_end}, 大小 {len(tile_data)}")
        
        # 尝试解析宽高头 (前4字节)
        if len(tile_data) >= 4:
            w, h = struct.unpack("<HH", tile_data[:4])
            print(f"  前4字节宽高: {w} x {h}")
            
            if 0 < w <= 640 and 0 < h <= 480:
                print(f"  [有效尺寸!]")
                # 根据sub_2EB9F，RLE数据从字节9开始
                rle_data = tile_data[9:]
                print(f"  RLE数据大小: {len(rle_data)}")
                
                # 解压缩
                pixels = decompress_rle(rle_data, w, h)
                
                # 创建图像
                img = Image.new("RGB", (w, h))
                px = img.load()
                for y in range(h):
                    for x in range(w):
                        idx = y * w + x
                        pal_idx = pixels[idx]
                        if pal_idx < len(palette_rgb):
                            px[x, y] = palette_rgb[pal_idx]
                
                filepath = os.path.join(output_dir, f"tile_{tile_idx}_{w}x{h}.png")
                img.save(filepath)
                print(f"  [OK] 已保存 {filepath}")
                
                # 放大
                if min(w, h) < 100:
                    zoom = max(4, 100 // min(w, h))
                    zoomed = img.resize((w * zoom, h * zoom), Image.NEAREST)
                    zoomed.save(filepath.replace(".png", f"_zoom{zoom}x.png"))
            else:
                # 尝试不同的宽高头位置
                for header_size in [4, 6, 8, 10]:
                    if len(tile_data) >= header_size + 4:
                        w, h = struct.unpack("<HH", tile_data[header_size:header_size+4])
                        if 0 < w <= 640 and 0 < h <= 480:
                            print(f"  尝试header_size={header_size}: {w} x {h} [有效!]")
                            rle_data = tile_data[header_size+9:] if header_size+9 < len(tile_data) else tile_data[header_size+4:]
                            print(f"  RLE数据大小: {len(rle_data)}")
                            
                            pixels = decompress_rle(rle_data, w, h)
                            img = Image.new("RGB", (w, h))
                            px = img.load()
                            for y in range(h):
                                for x in range(w):
                                    idx = y * w + x
                                    pal_idx = pixels[idx]
                                    if pal_idx < len(palette_rgb):
                                        px[x, y] = palette_rgb[pal_idx]
                            
                            filepath = os.path.join(output_dir, f"tile_{tile_idx}_{w}x{h}_hdr{header_size}.png")
                            img.save(filepath)
                            print(f"  [OK] 已保存 {filepath}")
                            break
