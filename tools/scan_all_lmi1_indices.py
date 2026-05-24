#!/usr/bin/env python3
"""
扫描FDOTHER.DAT所有LMI1格式的索引，查找包含16x16窗口边框tile的索引
"""

import struct
import os

fdother_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'FDOTHER.DAT')

with open(fdother_path, 'rb') as f:
    f.seek(6)
    resource_count = struct.unpack('<I', f.read(4))[0]
    print(f"资源总数: {resource_count}")
    
    f.seek(10)
    offsets = []
    for i in range(resource_count):
        offset = struct.unpack('<I', f.read(4))[0]
        offsets.append(offset)
    
    print(f"\n{'='*60}")
    print(f"扫描所有LMI1格式的索引:")
    print(f"{'='*60}")
    
    lmi1_indices = []
    
    for idx in range(resource_count):
        start = offsets[idx]
        end = offsets[idx + 1] if idx + 1 < resource_count else os.path.getsize(fdother_path)
        size = end - start
        
        if size < 10:
            continue
            
        f.seek(start)
        header = f.read(6)
        
        if header[:4] == b'LMI1':
            tile_count = struct.unpack('<H', header[4:6])[0]
            
            # 读取前几个tile的尺寸
            tile_sizes = []
            for i in range(min(5, tile_count)):
                offset_addr = 6 + i * 4
                if offset_addr + 4 > size:
                    break
                    
                tile_offset = struct.unpack('<I', header if offset_addr < 6 else f.read(4))[0]
                # 需要重新读取
                f.seek(start + 6 + i * 4)
                tile_offset_data = f.read(4)
                if len(tile_offset_data) < 4:
                    break
                tile_offset = struct.unpack('<I', tile_offset_data)[0]
                
                if tile_offset < size:
                    f.seek(start + tile_offset)
                    wh = f.read(4)
                    if len(wh) == 4:
                        w = struct.unpack('<H', wh[0:2])[0]
                        h = struct.unpack('<H', wh[2:4])[0]
                        tile_sizes.append((w, h))
            
            lmi1_indices.append({
                'index': idx,
                'tile_count': tile_count,
                'sizes': tile_sizes[:5],
                'start': start,
                'size': size
            })
            
            # 检查是否包含16x16左右的tile
            has_window_tiles = any(10 <= w <= 20 and 10 <= h <= 20 for w, h in tile_sizes[:5])
            
            print(f"\n索引{idx}: {tile_count}个tile")
            print(f"  前5个tile尺寸: {tile_sizes[:5]}")
            print(f"  大小: {size}字节")
            if has_window_tiles:
                print(f"  >>> 可能包含窗口tile <<<")
    
    print(f"\n{'='*60}")
    print(f"总结: 找到{lmi1_indices}个LMI1格式的索引")
    print(f"{'='*60}")
    
    # 特别检查包含16x16 tile的索引
    print(f"\n包含接近16x16 tile的索引:")
    for info in lmi1_indices:
        for w, h in info['sizes']:
            if 14 <= w <= 18 and 14 <= h <= 18:
                print(f"  索引{info['index']}: tile尺寸{w}x{h}")
                break
