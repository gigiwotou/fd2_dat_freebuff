"""
根据sub_2EB9F的汇编，tile数据访问是：
v8 = a5 + 4*a6
v13 = *(DWORD *)(v8 + 6) + a5       # tile_data_ptr = base + offset
v9 = *(DWORD *)(v8 + 10) - *(DWORD *)(v8 + 6)  # tile_size = end - start

但sub_2EB9F调用sub_4E98D时：
v9 = *(DWORD *)(a5 + 4*a6 + 8) + a5
sub_4E98D(v9+9, *v9, v9[1], a7, a8, value)

这里v9是指向tile数据的指针：
- *v9 = width
- v9[1] = height
- v9+9 = RLE数据起始

所以tile数据格式是:
[width:2][height:2][?:4][?:2][RLE数据] = 10字节头

但我们的数据前4字节是32637x32384，说明数据不对。

让我重新检查：也许嵌套DAT的count=26不是tile数量，而是资源数量。
实际上，嵌套DAT可能只包含1个tile（索引0），其他数据不是tile。

让我查看sub_2EB9F被调用时传入的a6值...
"""
import struct
from PIL import Image
import os

fdother_path = r"D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT"
output_dir = r"D:\workspace\fd2_dat_freebuff\output\fdother_7_tiles_v7\scene_0"
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
    print(f"偏移数量字段: {offset_count}")
    
    # 偏移表后到第一个tile的数据
    offset_table_end = 10 + offset_count * 4
    first_tile_offset = struct.unpack("<I", resource_data[10:14])[0]
    
    inline_data = resource_data[offset_table_end:first_tile_offset]
    print(f"\n内联数据大小: {len(inline_data)} (从 {offset_table_end} 到 {first_tile_offset})")
    print(f"内联数据前 16 字节: {inline_data[:16].hex()}")
    
    # 尝试解析内联数据为tile元数据
    # 每个条目可能是: [width:2][height:2][offset:4] = 8字节
    entry_size = 8
    tile_count = len(inline_data) // entry_size
    print(f"可能的tile元数据条目数: {tile_count}")
    
    for i in range(min(tile_count, 10)):
        entry_start = i * entry_size
        if entry_start + entry_size > len(inline_data):
            break
        
        w = struct.unpack("<H", inline_data[entry_start:entry_start+2])[0]
        h = struct.unpack("<H", inline_data[entry_start+2:entry_start+4])[0]
        offset = struct.unpack("<I", inline_data[entry_start+4:entry_start+8])[0]
        
        print(f"  条目 {i}: w={w}, h={h}, offset={offset}")
        
        # 检查是否是合理的宽高
        if 0 < w <= 320 and 0 < h <= 200 and offset < len(resource_data):
            print(f"    [合理的宽高!]")
            # 提取tile数据 (从offset开始)
            tile_data = resource_data[offset:]
            print(f"    Tile数据大小: {len(tile_data)}")
            print(f"    Tile数据前 16 字节: {tile_data[:16].hex()}")
            
            # 尝试直接解压缩 (假设没有额外头)
            try:
                pixels = decompress_rle(tile_data, w, h)
                non_zero = sum(1 for p in pixels if p != 0)
                total = w * h
                ratio = non_zero / total if total > 0 else 0
                print(f"    非零像素: {non_zero}/{total} ({ratio*100:.1f}%)")
                
                if 0.01 <= ratio <= 0.95:
                    img = Image.new("RGB", (w, h))
                    px = img.load()
                    for y in range(h):
                        for x in range(w):
                            idx = y * w + x
                            pal_idx = pixels[idx]
                            if pal_idx < len(palette_rgb):
                                px[x, y] = palette_rgb[pal_idx]
                    
                    filepath = os.path.join(output_dir, f"tile_{i}_{w}x{h}.png")
                    img.save(filepath)
                    print(f"    [OK] 已保存 {filepath}")
            except Exception as e:
                print(f"    错误: {e}")
