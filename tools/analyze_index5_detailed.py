import sys

def analyze_index5_detailed(fdother_path):
    """详细分析索引5的tile数据"""
    with open(fdother_path, 'rb') as f:
        data = f.read()
    
    if data[:6] != b'LLLLLL':
        print(f"无效的FDOTHER文件")
        return
    
    resource_count = int.from_bytes(data[6:10], 'little')
    
    # 索引5的偏移
    start = int.from_bytes(data[10 + 5*4:10 + 5*4 + 4], 'little')
    end = int.from_bytes(data[10 + 6*4:10 + 6*4 + 4], 'little') if 6 < resource_count else len(data)
    size = end - start
    
    print(f"索引5: start=0x{start:X}, end=0x{end:X}, size={size}")
    
    # 检查魔术字节
    magic = data[start:start+4]
    print(f"魔术字节: {magic}")
    
    if magic == b'LMI1':
        tile_count = int.from_bytes(data[start+4:start+6], 'little')
        print(f"Tile数量: {tile_count}\n")
        
        # 分析前30个tile
        print("前30个Tile详细信息:")
        for i in range(min(tile_count, 30)):
            offset_addr = start + 6 + i * 4
            tile_offset = int.from_bytes(data[offset_addr:offset_addr+4], 'little')
            tile_addr = start + tile_offset
            
            if tile_addr + 4 > end:
                print(f"  Tile {i:2d}: offset=0x{tile_offset:04X} (超出范围)")
                continue
            
            w = int.from_bytes(data[tile_addr:tile_addr+2], 'little')
            h = int.from_bytes(data[tile_addr+2:tile_addr+4], 'little')
            
            # 下一个tile的偏移
            if i + 1 < tile_count:
                next_offset_addr = start + 6 + (i + 1) * 4
                next_offset = int.from_bytes(data[next_offset_addr:next_offset_addr+4], 'little')
            else:
                next_offset = size
            
            compressed_size = next_offset - tile_offset - 4
            
            # 检查像素数据的前几个字节
            pixel_start = tile_addr + 4
            if pixel_start + 8 <= end:
                pixels = data[pixel_start:pixel_start+8]
                pixel_hex = ' '.join(f'{b:02X}' for b in pixels)
            else:
                pixel_hex = "N/A"
            
            print(f"  Tile {i:2d}: offset=0x{tile_offset:04X}, {w:2d}x{h:2d}, 压缩={compressed_size:4d}字节, 像素数据={pixel_hex}")
        
        # 统计所有尺寸
        print("\n所有tile尺寸统计:")
        sizes = {}
        for i in range(tile_count):
            offset_addr = start + 6 + i * 4
            if offset_addr + 4 > end:
                break
            
            tile_offset = int.from_bytes(data[offset_addr:offset_addr+4], 'little')
            tile_addr = start + tile_offset
            
            if tile_addr + 4 > end:
                continue
            
            w = int.from_bytes(data[tile_addr:tile_addr+2], 'little')
            h = int.from_bytes(data[tile_addr+2:tile_addr+4], 'little')
            size_key = f"{w}x{h}"
            sizes[size_key] = sizes.get(size_key, 0) + 1
        
        for size_key, count in sorted(sizes.items(), key=lambda x: -x[1]):
            print(f"  {size_key}: {count}个")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <FDOTHER.DAT路径>")
        sys.exit(1)
    
    analyze_index5_detailed(sys.argv[1])
