import sys

def verify_rle_vs_raw(fdother_path):
    """验证索引5的tile数据是RLE压缩还是原始数据"""
    with open(fdother_path, 'rb') as f:
        data = f.read()
    
    if data[:6] != b'LLLLLL':
        print(f"无效的FDOTHER文件")
        return
    
    resource_count = int.from_bytes(data[6:10], 'little')
    
    # 索引5的偏移
    start = int.from_bytes(data[10 + 5*4:10 + 5*4 + 4], 'little')
    end = int.from_bytes(data[10 + 6*4:10 + 6*4 + 4], 'little') if 6 < resource_count else len(data)
    
    tile_count = int.from_bytes(data[start+4:start+6], 'little')
    print(f"索引5: tile数量={tile_count}\n")
    
    # 检查前20个tile
    print("验证RLE vs 原始数据:")
    for i in range(min(tile_count, 20)):
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
            next_offset = end - start
        
        compressed_size = next_offset - tile_offset - 4
        expected_raw_size = w * h
        
        ratio = compressed_size / expected_raw_size if expected_raw_size > 0 else 0
        
        print(f"  Tile {i:2d}: {w:2d}x{h:2d}, 实际数据={compressed_size:4d}字节, 预期原始={expected_raw_size:4d}字节, 压缩比={ratio:.2f}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <FDOTHER.DAT路径>")
        sys.exit(1)
    
    verify_rle_vs_raw(sys.argv[1])
