import sys

def find_all_tile_sets(fdother_path):
    """扫描所有资源，找出所有LMI1格式的tile集"""
    with open(fdother_path, 'rb') as f:
        data = f.read()
    
    if data[:6] != b'LLLLLL':
        print(f"无效的FDOTHER文件")
        return
    
    resource_count = int.from_bytes(data[6:10], 'little')
    
    print(f"扫描{resource_count}个资源，查找LMI1格式的tile集:\n")
    
    for idx in range(resource_count):
        start = int.from_bytes(data[10 + idx*4:10 + idx*4 + 4], 'little')
        end = int.from_bytes(data[10 + (idx+1)*4:10 + (idx+1)*4 + 4], 'little') if idx + 1 < resource_count else len(data)
        size = end - start
        
        if size < 6:
            continue
        
        # 检查魔术字节
        magic = data[start:start+4]
        if magic != b'LMI1':
            continue
        
        tile_count = int.from_bytes(data[start+4:start+6], 'little')
        if tile_count == 0 or tile_count > 2000:
            continue
        
        # 分析tile尺寸分布
        sizes = {}
        for i in range(min(tile_count, 50)):
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
        
        print(f"索引 {idx:3d}: 大小={size:6d}, tile数={tile_count:4d}, 尺寸分布={dict(list(sizes.items())[:5])}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <FDOTHER.DAT路径>")
        sys.exit(1)
    
    find_all_tile_sets(sys.argv[1])
