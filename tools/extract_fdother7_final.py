"""
直接使用已知尺寸(320x200)解压缩嵌套DAT的tile资源图片
1:1 实现 fd2_decoder.c 的 fd2_rle_decompress
"""
import struct
import os
from PIL import Image

fdother_path = r"D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT"
output_dir = r"D:\workspace\fd2_dat_freebuff\output\fdother_7_tiles_final\scene_0"
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
    """1:1 实现 fd2_decoder.c 的 fd2_rle_decompress (palette_offset=-1 模式)"""
    output = bytearray(width * height)
    src_pos = 0
    src_end = len(src_data)
    dst_end = width * height
    
    for row in range(height):
        dst_pos = row * width
        count = width
        
        while count > 0 and src_pos < src_end:
            ctrl = src_data[src_pos]
            src_pos += 1
            
            count_1 = (ctrl & 0x3F) + 1
            bit7 = (ctrl >> 7) & 1
            bit6 = (ctrl >> 6) & 1
            
            if bit7 and bit6:
                # Skip
                if dst_pos + count_1 > dst_end:
                    break
                dst_pos += count_1
                count -= count_1
            elif bit7 and not bit6:
                # Copy
                if src_pos + count_1 > src_end:
                    break
                if dst_pos + count_1 > dst_end:
                    break
                for i in range(count_1):
                    output[dst_pos] = src_data[src_pos]
                    dst_pos += 1
                    src_pos += 1
                count -= count_1
            elif not bit7 and bit6:
                # Interleaved fill
                if src_pos >= src_end:
                    break
                if dst_pos + count_1 * 2 > dst_end:
                    break
                fill = src_data[src_pos]
                src_pos += 1
                for i in range(count_1):
                    output[dst_pos + 1] = fill
                    dst_pos += 2
                count = count - count_1 - count_1
            else:
                # Fill
                if src_pos >= src_end:
                    break
                if dst_pos + count_1 > dst_end:
                    break
                fill = src_data[src_pos]
                src_pos += 1
                for i in range(count_1):
                    output[dst_pos] = fill
                    dst_pos += 1
                count -= count_1
    
    return bytes(output)

def save_tile(pixels, width, height, palette_rgb, filename):
    img = Image.new("RGB", (width, height))
    px = img.load()
    
    for y in range(height):
        for x in range(width):
            idx = y * width + x
            if idx < len(pixels):
                pal_idx = pixels[idx]
                if pal_idx < len(palette_rgb):
                    px[x, y] = palette_rgb[pal_idx]
    
    filepath = os.path.join(output_dir, filename)
    img.save(filepath)
    
    non_zero = sum(1 for p in pixels if p != 0)
    total = width * height
    print(f"  非零像素: {non_zero}/{total} ({non_zero/total*100:.1f}%)")
    print(f"  [OK] 已保存 {filepath}")

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
    
    tile0_offset = struct.unpack("<I", resource_data[10:14])[0]
    tile1_offset = struct.unpack("<I", resource_data[14:18])[0]
    tile2_offset = struct.unpack("<I", resource_data[18:22])[0]
    file_end = struct.unpack("<I", resource_data[22:26])[0]
    
    tiles = [
        (0, tile0_offset, tile1_offset),
        (1, tile1_offset, tile2_offset),
        (2, tile2_offset, min(file_end, len(resource_data)))
    ]
    
    dimensions = [(320, 200), (160, 100), (160, 200), (80, 80), (64, 64), (32, 32)]
    
    for tile_idx, tile_start, tile_end in tiles:
        tile_data = resource_data[tile_start:tile_end]
        print(f"\nTile {tile_idx}: 偏移 {tile_start}-{tile_end}, 大小 {len(tile_data)}")
        print(f"  前 20 字节: {tile_data[:20].hex()}")
        
        for width, height in dimensions:
            try:
                pixels = decompress_rle(tile_data, width, height)
                non_zero = sum(1 for p in pixels if p != 0)
                total = width * height
                ratio = non_zero / total if total > 0 else 0
                
                # 保存所有结果
                print(f"  尺寸 {width}x{height}: ", end="")
                save_tile(pixels, width, height, palette_rgb, f"tile_{tile_idx}_{width}x{height}.png")
                
            except Exception as e:
                print(f"  尺寸 {width}x{height}: 错误 {e}")
