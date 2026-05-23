import sys

def analyze_index7(fdother_path):
    with open(fdother_path, 'rb') as f:
        data = f.read()
    
    if data[:6] != b'LLLLLL':
        print(f"无效的FDOTHER文件")
        return
    
    resource_count = int.from_bytes(data[6:10], 'little')
    
    # 索引7的偏移
    start = int.from_bytes(data[10 + 7*4:10 + 7*4 + 4], 'little')
    end = int.from_bytes(data[10 + 8*4:10 + 8*4 + 4], 'little') if 8 < resource_count else len(data)
    size = end - start
    
    print(f"索引7: start=0x{start:X}, end=0x{end:X}, size={size}")
    
    # 检查魔术字节
    magic = data[start:start+4]
    print(f"魔术字节: {magic}")
    
    if magic == b'LMI1':
        tile_count = int.from_bytes(data[start+4:start+6], 'little')
        print(f"Tile数量: {tile_count}")
        
        # 分析每个tile
        print(f"\n前30个Tile信息:")
        for i in range(min(tile_count, 30)):
            offset_addr = start + 6 + i * 4
            tile_offset = int.from_bytes(data[offset_addr:offset_addr+4], 'little')
            tile_addr = start + tile_offset
            
            if tile_addr + 4 > end:
                continue
            
            w = int.from_bytes(data[tile_addr:tile_addr+2], 'little')
            h = int.from_bytes(data[tile_addr+2:tile_addr+4], 'little')
            
            # 下一个tile的偏移
            if i + 1 < tile_count:
                next_offset = int.from_bytes(data[offset_addr+4:offset_addr+8], 'little')
            else:
                next_offset = size
            
            compressed_size = next_offset - tile_offset - 4
            
            # 检查像素数据
            pixel_start = tile_addr + 4
            pixel_end = start + next_offset
            if pixel_end <= end:
                pixels = data[pixel_start:pixel_end]
                unique_colors = len(set(pixels[:min(len(pixels), 50)]))
            else:
                unique_colors = 0
            
            print(f"  Tile {i:2d}: offset=0x{tile_offset:04X}, {w:2d}x{h:2d}, 压缩={compressed_size:3d}字节, 颜色数={unique_colors}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <FDOTHER.DAT路径>")
        sys.exit(1)
    
    analyze_index7(sys.argv[1])
