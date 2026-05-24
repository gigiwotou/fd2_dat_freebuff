#!/usr/bin/env python3
"""
可视化FDOTHER索引5解压后的tile数据
用于验证RLE解压是否正确，以及tile 1-17的窗口边框内容
"""

import struct
import os
from PIL import Image

def decompress_rle(src_data, width, height):
    """1:1实现fd2_decode_fdother_resource的RLE解压算法"""
    compressed = src_data[4:]
    comp_size = len(compressed)
    
    dst = [0] * (width * height)
    
    num4 = 0
    num3 = comp_size - 1
    num7 = 0
    num8 = 0
    num9 = 0
    b = 0
    num10 = 0
    num11 = 0
    
    pixel_idx = 0
    expected = width * height
    
    while num4 <= num3 and pixel_idx < expected:
        flag = (num8 != 0)
        
        if not flag:
            num7 = 0
            num8 = 0
            num9 = 0
            
            if num4 < comp_size:
                b = compressed[num4]
                if b >= 192:
                    num7 = b - 192 + 1
                elif b >= 128:
                    num8 = b - 128 + 1
                elif b >= 64:
                    num9 = b - 64
                    num8 = 1
                else:
                    num8 = 1
                    num9 = b
            
            num10 += num7
            if num10 >= width:
                num10 = 0
                num11 += 1
        else:
            num12 = num9
            num13 = 0
            while num13 <= num12:
                if b >= 64 and b < 128:
                    num10 += 1
                
                if num4 < comp_size:
                    index = compressed[num4]
                    if num10 >= 0 and num10 < width and num11 >= 0 and num11 < height:
                        if pixel_idx < expected:
                            dst[pixel_idx] = index
                            pixel_idx += 1
                
                num10 += 1
                if num10 >= width:
                    num10 = 0
                    num11 += 1
                
                num13 += 1
            
            num8 -= 1
        
        num4 += 1
        
        if num11 >= height:
            break
    
    return bytes(dst)

def load_palette():
    """加载FDOTHER索引75的调色板"""
    fdother_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'FDOTHER.DAT')
    
    with open(fdother_path, 'rb') as f:
        f.seek(6)
        resource_count = struct.unpack('<I', f.read(4))[0]
        
        f.seek(10)
        offsets = []
        for i in range(resource_count):
            offset = struct.unpack('<I', f.read(4))[0]
            offsets.append(offset)
        
        start = offsets[75]
        end = offsets[76] if 76 < resource_count else os.path.getsize(fdother_path)
        size = end - start
        
        f.seek(start)
        pal_data = f.read(size)
        
        palette = []
        for i in range(256):
            r = (pal_data[i * 3 + 0] << 2) | (pal_data[i * 3 + 0] >> 4)
            g = (pal_data[i * 3 + 1] << 2) | (pal_data[i * 3 + 1] >> 4)
            b = (pal_data[i * 3 + 2] << 2) | (pal_data[i * 3 + 2] >> 4)
            palette.append((r, g, b))
        
        return palette

def visualize_tiles():
    fdother_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'FDOTHER.DAT')
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    palette = load_palette()
    
    with open(fdother_path, 'rb') as f:
        f.seek(6)
        resource_count = struct.unpack('<I', f.read(4))[0]
        
        f.seek(10)
        offsets = []
        for i in range(resource_count):
            offset = struct.unpack('<I', f.read(4))[0]
            offsets.append(offset)
        
        start = offsets[5]
        end = offsets[6] if 6 < resource_count else os.path.getsize(fdother_path)
        size = end - start
        
        f.seek(start)
        index5_data = f.read(size)
        
        tile_count = struct.unpack('<H', index5_data[4:6])[0]
        print(f"Tile总数: {tile_count}")
        
        tiles = []
        
        for i in range(min(tile_count, 20)):
            offset_addr = 6 + i * 4
            tile_offset = struct.unpack('<I', index5_data[offset_addr:offset_addr+4])[0]
            
            tile_addr = tile_offset
            w = struct.unpack('<H', index5_data[tile_addr:tile_addr+2])[0]
            h = struct.unpack('<H', index5_data[tile_addr+2:tile_addr+4])[0]
            
            if i + 1 < tile_count:
                next_tile_offset = struct.unpack('<I', index5_data[6 + (i+1)*4:6 + (i+1)*4+4])[0]
                compressed_size = next_tile_offset - tile_offset
            else:
                compressed_size = size - tile_offset
            
            compressed_data = index5_data[tile_addr:tile_addr+compressed_size]
            
            decompressed = decompress_rle(compressed_data, w, h)
            
            non_zero = sum(1 for p in decompressed if p != 0)
            print(f"Tile {i}: {w}x{h}, 非零像素={non_zero}/{w*h}")
            
            img = Image.new('RGB', (w, h))
            pixels = img.load()
            
            for y in range(h):
                for x in range(w):
                    idx = decompressed[y * w + x]
                    pixels[x, y] = palette[idx]
            
            tile_path = os.path.join(output_dir, f'tile_{i:03d}_{w}x{h}.png')
            img.save(tile_path)
            tiles.append((img, w, h))
        
        print(f"\n已保存前20个tile到 {output_dir}")
        
        combined_width = sum(w for _, w, _ in tiles[:10])
        max_height = max(h for _, _, h in tiles[:10])
        
        combined = Image.new('RGB', (combined_width, max_height), (0, 0, 0))
        
        x_offset = 0
        for img, w, h in tiles[:10]:
            combined.paste(img, (x_offset, 0))
            x_offset += w
        
        combined_path = os.path.join(output_dir, 'tiles_0_9_combined.png')
        combined.save(combined_path)
        print(f"已保存组合图: {combined_path}")

if __name__ == '__main__':
    visualize_tiles()
