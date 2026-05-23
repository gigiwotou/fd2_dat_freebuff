import sys

def analyze_index5_uncompressed(fdother_path):
    """分析索引5，找出所有未压缩的tile（数据大小 == w*h）"""
    with open(fdother_path, 'rb') as f:
        data = f.read()
    
    if data[:6] != b'LLLLLL':
        print(f"无效的FDOTHER文件")
        return
    
    resource_count = int.from_bytes(data[6:10], 'little')
    start = int.from_bytes(data[10 + 5*4:10 + 5*4 + 4], 'little')
    end = int.from_bytes(data[10 + 6*4:10 + 6*4 + 4], 'little') if 6 < resource_count else len(data)
    
    tile_count = int.from_bytes(data[start+4:start+6], 'little')
    print(f"索引5: {tile_count}个tile\n")
    
    # 找出所有未压缩的tile
    uncompressed = []
    compressed = []
    
    for i in range(tile_count):
        offset_addr = start + 6 + i * 4
        tile_offset = int.from_bytes(data[offset_addr:offset_addr+4], 'little')
        tile_addr = start + tile_offset
        
        if tile_addr + 4 > end:
            continue
        
        w = int.from_bytes(data[tile_addr:tile_addr+2], 'little')
        h = int.from_bytes(data[tile_addr+2:tile_addr+4], 'little')
        
        # 跳过异常尺寸
        if w > 100 or h > 100:
            continue
        
        if i + 1 < tile_count:
            next_offset = int.from_bytes(data[start + 6 + (i+1)*4:start + 6 + (i+1)*4 + 4], 'little')
        else:
            next_offset = end - start
        
        actual_size = next_offset - tile_offset - 4
        expected_size = w * h
        
        # 读取前8字节像素数据
        pixels = data[tile_addr+4:tile_addr+4+min(8, actual_size)]
        pixel_hex = ' '.join(f'{b:02X}' for b in pixels)
        
        if actual_size == expected_size:
            uncompressed.append((i, w, h, pixel_hex))
        else:
            compressed.append((i, w, h, actual_size, expected_size, pixel_hex))
    
    print(f"未压缩tile: {len(uncompressed)}个")
    print(f"压缩tile: {len(compressed)}个\n")
    
    if uncompressed:
        print("未压缩tile列表:")
        for i, w, h, pixel_hex in uncompressed:
            print(f"  Tile {i:2d}: {w:2d}x{h:2d}, 像素数据={pixel_hex}")
    
    if compressed:
        print("\n压缩tile列表 (前20个):")
        for i, w, h, actual, expected, pixel_hex in compressed[:20]:
            ratio = actual / expected if expected > 0 else 0
            print(f"  Tile {i:2d}: {w:2d}x{h:2d}, 实际={actual}, 预期={expected}, 压缩比={ratio:.2f}, 像素数据={pixel_hex}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <FDOTHER.DAT路径>")
        sys.exit(1)
    
    analyze_index5_uncompressed(sys.argv[1])
