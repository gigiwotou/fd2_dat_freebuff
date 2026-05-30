#!/usr/bin/env python3
"""分析LMI1资源的tile结构和尺寸"""
import struct

def analyze_lmi1(filepath, index):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # 读取索引表
    table_start = 6
    offsets = []
    offset = table_start
    while offset + 4 <= len(data):
        off = struct.unpack_from('<I', data, offset)[0]
        if off == 0 or off >= len(data):
            break
        offsets.append(off)
        offset += 4
    
    if index >= len(offsets):
        print(f"索引{index}不存在")
        return
    
    start = offsets[index]
    end = offsets[index + 1] if index + 1 < len(offsets) else len(data)
    res_data = data[start:end]
    
    print(f"索引{index}: LMI1资源")
    print(f"  偏移: 0x{start:X} - 0x{end:X}")
    print(f"  大小: {len(res_data)} 字节")
    print(f"  Magic: {res_data[:4]}")
    
    if res_data[:4] != b'LMI1':
        print("  不是LMI1格式")
        return
    
    tile_count = struct.unpack_from('<H', res_data, 4)[0]
    print(f"  Tile数量: {tile_count}")
    
    # 读取tile偏移
    tile_offsets = []
    for i in range(tile_count):
        off = struct.unpack_from('<I', res_data, 6 + i * 4)[0]
        tile_offsets.append(off)
    
    print(f"\nTile偏移:")
    for i, off in enumerate(tile_offsets[:10]):
        next_off = tile_offsets[i + 1] if i + 1 < len(tile_offsets) else len(res_data)
        size = next_off - off
        print(f"  Tile {i}: 偏移 0x{off:X}, 大小 {size} 字节")
    
    # 分析tile尺寸
    if len(tile_offsets) >= 2:
        sizes = []
        for i in range(min(5, len(tile_offsets) - 1)):
            size = tile_offsets[i + 1] - tile_offsets[i]
            sizes.append(size)
        
        print(f"\nTile尺寸分析:")
        print(f"  常见尺寸: {sizes}")
        
        # 找到最常见的尺寸
        from collections import Counter
        most_common = Counter(sizes).most_common(3)
        print(f"  最常见的3个尺寸: {most_common}")
        
        # 分析可能的宽高组合
        for size in set(sizes):
            print(f"\n  尺寸 {size} 的可能宽高组合:")
            for w in range(1, min(size + 1, 256)):
                if size % w == 0:
                    h = size // w
                    if h <= 256:
                        print(f"    {w}x{h}")
                        if w * h == size and w <= 32 and h <= 32:
                            break  # 只打印合理的组合
    
    # 解码第一个tile测试
    if tile_count > 0:
        tile_data_start = tile_offsets[0]
        tile_data_end = tile_offsets[1] if len(tile_offsets) > 1 else len(res_data)
        tile_data = res_data[tile_data_start:tile_data_end]
        
        print(f"\n第一个tile数据 (大小: {len(tile_data)} 字节):")
        print(f"  前32字节: {' '.join(f'{b:02X}' for b in tile_data[:32])}")
        
        # 尝试sub_4EC66解码
        def ec66_decode(src, width, height):
            dst = bytearray(width * height)
            src_pos = 0
            ah = 0
            prev_al = 0
            dst_pos = 0
            
            while dst_pos < len(dst) and src_pos < len(src):
                if ah > 0:
                    ah -= 1
                    pixel = prev_al
                else:
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
        
        # 尝试不同尺寸
        for size in [16, 24, 32, 48, 64, 128, 256]:
            if len(tile_data) >= size:
                w = h = int(size ** 0.5)
                if w * w == size:
                    decoded = ec66_decode(tile_data, w, h)
                    non_zero = sum(1 for b in decoded if b != 0)
                    unique = len(set(decoded))
                    print(f"\n  尝试 {w}x{h} (size={size}):")
                    print(f"    非零像素: {non_zero}, 唯一值: {unique}")
                    print(f"    前64像素: {' '.join(f'{decoded[i]:02X}' for i in range(min(64, len(decoded))))}")

if __name__ == '__main__':
    analyze_lmi1('game/FDOTHER.DAT', 3)
