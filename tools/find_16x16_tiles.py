import sys

def find_window_tile_set(fdother_path):
    with open(fdother_path, 'rb') as f:
        data = f.read()
    
    if data[:6] != b'LLLLLL':
        print(f"无效的FDOTHER文件")
        return
    
    resource_count = int.from_bytes(data[6:10], 'little')
    print(f"资源总数: {resource_count}")
    
    offsets = []
    for i in range(resource_count):
        offset = int.from_bytes(data[10 + i*4:10 + i*4 + 4], 'little')
        offsets.append(offset)
    
    print(f"\n查找包含16x16 tile的资源:")
    
    for idx in range(resource_count):
        start = offsets[idx]
        end = offsets[idx + 1] if idx + 1 < resource_count else len(data)
        size = end - start
        
        if size < 6:
            continue
        
        # 检查魔术字节
        magic = data[start:start+4]
        if magic != b'LMI1':
            continue
        
        tile_count = int.from_bytes(data[start+4:start+6], 'little')
        if tile_count == 0 or tile_count > 1000:
            continue
        
        # 检查前几个tile的尺寸
        sixteen_count = 0
        total_tiles = 0
        
        for i in range(min(tile_count, 20)):
            offset_addr = start + 6 + i * 4
            if offset_addr + 4 > end:
                break
            
            tile_offset = int.from_bytes(data[offset_addr:offset_addr+4], 'little')
            tile_addr = start + tile_offset
            
            if tile_addr + 4 > end:
                continue
            
            w = int.from_bytes(data[tile_addr:tile_addr+2], 'little')
            h = int.from_bytes(data[tile_addr+2:tile_addr+4], 'little')
            
            if w == 16 and h == 16:
                sixteen_count += 1
            total_tiles += 1
        
        if sixteen_count > 0:
            print(f"\n  索引 {idx}: tile_count={tile_count}, 16x16数量={sixteen_count}/{total_tiles}")
            
            # 详细输出前几个tile
            for i in range(min(tile_count, 30)):
                offset_addr = start + 6 + i * 4
                if offset_addr + 4 > end:
                    break
                
                tile_offset = int.from_bytes(data[offset_addr:offset_addr+4], 'little')
                tile_addr = start + tile_offset
                
                if tile_addr + 4 > end:
                    continue
                
                w = int.from_bytes(data[tile_addr:tile_addr+2], 'little')
                h = int.from_bytes(data[tile_addr+2:tile_addr+4], 'little')
                
                next_offset = int.from_bytes(data[offset_addr+4:offset_addr+8], 'little') if i + 1 < tile_count else size
                compressed_size = next_offset - tile_offset - 4
                
                if w == 16 and h == 16:
                    print(f"    Tile {i:2d}: {w}x{h}, 压缩={compressed_size}字节, 偏移=0x{tile_offset:X}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <FDOTHER.DAT路径>")
        sys.exit(1)
    
    find_window_tile_set(sys.argv[1])
