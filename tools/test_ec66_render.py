#!/usr/bin/env python3
"""测试sub_4EC66解码并渲染图像"""
import struct
from PIL import Image

def load_fdother(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # 读取索引表
    offsets = []
    offset = 6
    while offset + 4 <= len(data):
        off = struct.unpack_from('<I', data, offset)[0]
        if off == 0 or off >= len(data):
            break
        offsets.append(off)
        offset += 4
    
    offsets.append(len(data))  # 文件末尾
    return data, offsets

def ec66_decode(src, width, height):
    """sub_4EC66解码"""
    dst = bytearray(width * height)
    src_pos = 0
    ah = 0
    prev_al = 0
    dst_pos = 0
    
    for row in range(height):
        for col in range(width):
            if dst_pos >= len(dst):
                break
            
            if ah > 0:
                ah -= 1
                pixel = prev_al
            else:
                if src_pos >= len(src):
                    break
                al = src[src_pos]
                src_pos += 1
                
                if al > 0xC0:
                    ah = al - 0xC1
                    if src_pos < len(src):
                        al = src[src_pos]
                        src_pos += 1
                    prev_al = al
                    pixel = al
                else:
                    ah = 0
                    prev_al = al
                    pixel = al
            
            dst[dst_pos] = pixel
            dst_pos += 1
    
    return dst

def load_palette(filepath, pal_index=0):
    """加载调色板"""
    data, offsets = load_fdother(filepath)
    start = offsets[pal_index]
    end = offsets[pal_index + 1]
    pal_data = data[start:end]
    
    # 6bit -> 8bit
    rgb = []
    for i in range(256):
        r = (pal_data[i * 3] << 2) | (pal_data[i * 3] >> 4)
        g = (pal_data[i * 3 + 1] << 2) | (pal_data[i * 3 + 1] >> 4)
        b = (pal_data[i * 3 + 2] << 2) | (pal_data[i * 3 + 2] >> 4)
        rgb.append((r, g, b))
    
    return rgb

def render_tile(tile_data, width, height, palette_rgb, output_path):
    """渲染tile到图像"""
    decoded = ec66_decode(tile_data, width, height)
    
    img = Image.new('RGB', (width, height))
    pixels = img.load()
    
    for y in range(height):
        for x in range(width):
            idx = decoded[y * width + x]
            pixels[x, y] = palette_rgb[idx]
    
    img.save(output_path)
    print(f"  保存到: {output_path}")
    
    # 打印统计
    non_zero = sum(1 for b in decoded if b != 0)
    unique = len(set(decoded))
    print(f"  非零像素: {non_zero}/{width*height}, 唯一值: {unique}")

def main():
    filepath = 'game/FDOTHER.DAT'
    
    # 加载主调色板 (索引0)
    print("加载调色板...")
    palette = load_palette(filepath, 0)
    
    # 加载索引3 (LMI1, 23 tiles, 16x16)
    print("\n分析索引3 (LMI1)...")
    data, offsets = load_fdother(filepath)
    start = offsets[3]
    end = offsets[4]
    lmi1_data = data[start:end]
    
    tile_count = struct.unpack_from('<H', lmi1_data, 4)[0]
    print(f"  Tile数量: {tile_count}")
    
    # 读取tile偏移
    tile_offsets = []
    for i in range(tile_count):
        off = struct.unpack_from('<I', lmi1_data, 6 + i * 4)[0]
        tile_offsets.append(off)
    
    # 渲染前5个tile
    for i in range(min(5, tile_count)):
        tile_start = tile_offsets[i]
        tile_end = tile_offsets[i + 1] if i + 1 < len(tile_offsets) else len(lmi1_data)
        tile_data = lmi1_data[tile_start:tile_end]
        
        print(f"\nTile {i}: 大小 {len(tile_data)} 字节")
        render_tile(tile_data, 16, 16, palette, f'output/lmi1_tile_{i}.png')
    
    # 分析索引1 (图标24x24)
    print("\n\n分析索引1 (图标24x24)...")
    start = offsets[1]
    end = offsets[2]
    icon_data = data[start:end]
    print(f"  大小: {len(icon_data)} 字节")
    
    # 索引1可能有多个图标，需要解析结构
    # 尝试解析为5字节头的TILE
    if len(icon_data) >= 5:
        w = struct.unpack_from('<H', icon_data, 0)[0]
        h = struct.unpack_from('<H', icon_data, 2)[0]
        pal_window = icon_data[4]
        print(f"  尺寸: {w}x{h}")
        print(f"  调色板窗口: {pal_window}")
        
        if w > 0 and w <= 320 and h > 0 and h <= 200:
            tile_data = icon_data[5:]
            print(f"  数据大小: {len(tile_data)} 字节")
            print(f"  预期大小: {w*h} 字节")
            
            if len(tile_data) >= w * h:
                render_tile(tile_data[:w*h], w, h, palette, 'output/icon1_full.png')
    
    # 分析索引10 (62x26图标)
    print("\n\n分析索引10 (62x26图标)...")
    start = offsets[10]
    end = offsets[11]
    icon10_data = data[start:end]
    print(f"  大小: {len(icon10_data)} 字节")
    
    if len(icon10_data) >= 5:
        w = struct.unpack_from('<H', icon10_data, 0)[0]
        h = struct.unpack_from('<H', icon10_data, 2)[0]
        pal_window = icon10_data[4]
        print(f"  尺寸: {w}x{h}")
        print(f"  调色板窗口: {pal_window}")
        
        if w > 0 and w <= 320 and h > 0 and h <= 200:
            tile_data = icon10_data[5:]
            render_tile(tile_data[:w*h], w, h, palette, 'output/icon10_full.png')

if __name__ == '__main__':
    main()
