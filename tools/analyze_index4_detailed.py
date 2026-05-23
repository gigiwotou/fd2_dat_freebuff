import sys

def analyze_index4_tiles(fdother_path):
    """详细分析索引4的所有tile，找出角、边框、内容区域tile"""
    with open(fdother_path, 'rb') as f:
        data = f.read()
    
    if data[:6] != b'LLLLLL':
        print(f"无效的FDOTHER文件")
        return
    
    resource_count = int.from_bytes(data[6:10], 'little')
    start = int.from_bytes(data[10 + 4*4:10 + 4*4 + 4], 'little')
    end = int.from_bytes(data[10 + 5*4:10 + 5*4 + 4], 'little') if 5 < resource_count else len(data)
    
    tile_count = int.from_bytes(data[start+4:start+6], 'little')
    print(f"索引4: {tile_count}个tile\n")
    
    # 分析所有tile的尺寸和内容
    tiles_info = []
    for i in range(tile_count):
        offset_addr = start + 6 + i * 4
        tile_offset = int.from_bytes(data[offset_addr:offset_addr+4], 'little')
        tile_addr = start + tile_offset
        
        if tile_addr + 4 > end:
            continue
        
        w = int.from_bytes(data[tile_addr:tile_addr+2], 'little')
        h = int.from_bytes(data[tile_addr+2:tile_addr+4], 'little')
        
        # 获取像素数据
        if i + 1 < tile_count:
            next_offset = int.from_bytes(data[start + 6 + (i+1)*4:start + 6 + (i+1)*4 + 4], 'little')
        else:
            next_offset = end - start
        
        pixel_data_size = next_offset - tile_offset - 4
        expected_size = w * h
        
        # 读取前8字节像素数据
        pixels = data[tile_addr+4:tile_addr+4+min(8, pixel_data_size)]
        pixel_hex = ' '.join(f'{b:02X}' for b in pixels)
        
        # 统计唯一颜色
        all_pixels = data[tile_addr+4:tile_addr+4+pixel_data_size] if pixel_data_size <= 256 else data[tile_addr+4:tile_addr+4+256]
        unique_colors = len(set(all_pixels))
        
        # 判断tile类型
        tile_type = "未知"
        if w == 24 and h == 24:
            if i == 0:
                tile_type = "可能是角tile"
            else:
                tile_type = "大方块"
        elif w <= 4 and h <= 4:
            tile_type = "小角tile候选"
        elif w == 16 and h == 3:
            tile_type = "水平边框候选"
        elif w == 3 and h == 16:
            tile_type = "垂直边框候选"
        
        tiles_info.append((i, w, h, unique_colors, tile_type, pixel_hex))
    
    # 按尺寸分类显示
    print("按尺寸分类:")
    sizes = {}
    for i, w, h, colors, ttype, _ in tiles_info:
        key = f"{w}x{h}"
        if key not in sizes:
            sizes[key] = []
        sizes[key].append((i, colors, ttype))
    
    for size, tiles in sorted(sizes.items(), key=lambda x: -len(x[1])):
        print(f"\n  {size}: {len(tiles)}个")
        for i, colors, ttype in tiles[:10]:
            print(f"    Tile {i:2d}: {colors}种颜色, {ttype}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <FDOTHER.DAT路径>")
        sys.exit(1)
    
    analyze_index4_tiles(sys.argv[1])
