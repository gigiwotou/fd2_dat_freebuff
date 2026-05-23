import sys

def analyze_tile_format(fdother_path, index=4):
    """分析指定索引的tile数据格式"""
    with open(fdother_path, 'rb') as f:
        data = f.read()
    
    if data[:6] != b'LLLLLL':
        print(f"无效的FDOTHER文件")
        return
    
    resource_count = int.from_bytes(data[6:10], 'little')
    
    # 指定索引的偏移
    start = int.from_bytes(data[10 + index*4:10 + index*4 + 4], 'little')
    end = int.from_bytes(data[10 + (index+1)*4:10 + (index+1)*4 + 4], 'little') if index + 1 < resource_count else len(data)
    size = end - start
    
    print(f"索引{index}: start=0x{start:X}, size={size}")
    
    magic = data[start:start+4]
    print(f"魔术字节: {magic}")
    
    if magic == b'LMI1':
        tile_count = int.from_bytes(data[start+4:start+6], 'little')
        print(f"Tile数量: {tile_count}\n")
        
        # 分析前10个tile
        print("前10个Tile详细分析:")
        for i in range(min(tile_count, 10)):
            offset_addr = start + 6 + i * 4
            tile_offset = int.from_bytes(data[offset_addr:offset_addr+4], 'little')
            tile_addr = start + tile_offset
            
            if tile_addr + 4 > end:
                continue
            
            w = int.from_bytes(data[tile_addr:tile_addr+2], 'little')
            h = int.from_bytes(data[tile_addr+2:tile_addr+4], 'little')
            
            # 下一个tile的偏移
            if i + 1 < tile_count:
                next_offset_addr = start + 6 + (i + 1) * 4
                next_offset = int.from_bytes(data[next_offset_addr:next_offset_addr+4], 'little')
            else:
                next_offset = size
            
            actual_size = next_offset - tile_offset - 4
            expected_size = w * h
            
            # 读取前16字节像素数据
            pixel_start = tile_addr + 4
            if pixel_start + 16 <= end:
                pixels = data[pixel_start:pixel_start+16]
                pixel_hex = ' '.join(f'{b:02X}' for b in pixels)
                
                # 检查是否是RLE格式 (控制字节64-191)
                rle_like = sum(1 for b in pixels if 64 <= b <= 191)
                is_rle = "可能是RLE" if rle_like > 8 else "可能是原始"
            else:
                pixel_hex = "N/A"
                is_rle = "N/A"
            
            match = "OK" if actual_size == expected_size else "DIFF"
            print(f"  Tile {i:2d}: {w:2d}x{h:2d}, 实际={actual_size:4d}, 预期={expected_size:4d} [{match}], 格式={is_rle}")
            print(f"         像素数据: {pixel_hex}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <FDOTHER.DAT路径> [索引]")
        sys.exit(1)
    
    index = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    analyze_tile_format(sys.argv[1], index)
