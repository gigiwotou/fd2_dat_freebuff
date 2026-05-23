import sys

def analyze_index4(fdother_path):
    """详细分析索引4的tile数据"""
    with open(fdother_path, 'rb') as f:
        data = f.read()
    
    if data[:6] != b'LLLLLL':
        print(f"无效的FDOTHER文件")
        return
    
    resource_count = int.from_bytes(data[6:10], 'little')
    
    # 索引4的偏移
    start = int.from_bytes(data[10 + 4*4:10 + 4*4 + 4], 'little')
    end = int.from_bytes(data[10 + 5*4:10 + 5*4 + 4], 'little') if 5 < resource_count else len(data)
    size = end - start
    
    print(f"索引4: start=0x{start:X}, end=0x{end:X}, size={size}")
    
    # 检查魔术字节
    magic = data[start:start+4]
    print(f"魔术字节: {magic}")
    
    if magic == b'LMI1':
        tile_count = int.from_bytes(data[start+4:start+6], 'little')
        print(f"Tile数量: {tile_count}\n")
        
        # 检查所有tile的压缩比
        compressed_tiles = 0
        raw_tiles = 0
        
        for i in range(tile_count):
            offset_addr = start + 6 + i * 4
            tile_offset = int.from_bytes(data[offset_addr:offset_addr+4], 'little')
            tile_addr = start + tile_offset
            
            if tile_addr + 4 > end:
                continue
            
            w = int.from_bytes(data[tile_addr:tile_addr+2], 'little')
            h = int.from_bytes(data[tile_addr+2:tile_addr+4], 'little')
            
            if w > 100 or h > 100:
                continue  # 跳过异常尺寸
            
            # 下一个tile的偏移
            if i + 1 < tile_count:
                next_offset_addr = start + 6 + (i + 1) * 4
                next_offset = int.from_bytes(data[next_offset_addr:next_offset_addr+4], 'little')
            else:
                next_offset = size
            
            compressed_size = next_offset - tile_offset - 4
            expected_raw_size = w * h
            
            if compressed_size == expected_raw_size:
                raw_tiles += 1
                if raw_tiles <= 5:
                    print(f"  Tile {i:2d}: {w:2d}x{h:2d}, 数据={compressed_size}字节 (未压缩)")
            else:
                compressed_tiles += 1
                if compressed_tiles <= 5:
                    ratio = compressed_size / expected_raw_size if expected_raw_size > 0 else 0
                    print(f"  Tile {i:2d}: {w:2d}x{h:2d}, 压缩={compressed_size}字节, 预期={expected_raw_size}字节, 压缩比={ratio:.2f}")
        
        print(f"\n统计: 未压缩={raw_tiles}, 压缩={compressed_tiles}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <FDOTHER.DAT路径>")
        sys.exit(1)
    
    analyze_index4(sys.argv[1])
