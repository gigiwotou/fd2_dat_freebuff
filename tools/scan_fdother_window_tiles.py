#!/usr/bin/env python3
"""
扫描FDOTHER.DAT所有LMI1资源，查找哪个索引包含适合窗口边框的tile（tile 1-17接近16x16）
"""

import struct
import os

def scan_fdother_for_window_tiles():
    fdother_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'FDOTHER.DAT')
    
    if not os.path.exists(fdother_path):
        print(f"错误: 找不到FDOTHER.DAT文件")
        return
    
    print(f"分析文件: {fdother_path}")
    
    with open(fdother_path, 'rb') as f:
        f.seek(6)
        resource_count = struct.unpack('<I', f.read(4))[0]
        print(f"资源数量: {resource_count}")
        
        f.seek(10)
        offsets = []
        for i in range(resource_count):
            offset = struct.unpack('<I', f.read(4))[0]
            offsets.append(offset)
        
        # 扫描前50个索引
        print(f"\n扫描索引0-49，查找LMI1格式的tile集:")
        print(f"{'索引':>4} | {'大小':>6} | {'Tile数':>5} | {'Tile0':>8} | {'Tile1':>8} | {'Tile2':>8} | {'Tile13':>8}")
        print("-" * 75)
        
        for idx in range(min(50, resource_count)):
            start = offsets[idx]
            end = offsets[idx + 1] if idx + 1 < resource_count else os.path.getsize(fdother_path)
            size = end - start
            
            if size < 10:
                continue
            
            f.seek(start)
            data = f.read(min(size, 1000))
            
            # 检查是否是LMI1格式
            if data[0:4] != b'LMI1':
                continue
            
            tile_count = struct.unpack('<H', data[4:6])[0]
            if tile_count < 17:
                continue
            
            # 读取tile 0, 1, 2, 13的尺寸
            tile_sizes = {}
            for t in [0, 1, 2, 13]:
                if t < tile_count:
                    offset_addr = 6 + t * 4
                    tile_offset = struct.unpack('<I', data[offset_addr:offset_addr+4])[0]
                    if tile_offset < size - 4:
                        w = struct.unpack('<H', data[tile_offset:tile_offset+2])[0]
                        h = struct.unpack('<H', data[tile_offset+2:tile_offset+4])[0]
                        tile_sizes[t] = f"{w}x{h}"
                    else:
                        tile_sizes[t] = "N/A"
                else:
                    tile_sizes[t] = "N/A"
            
            print(f"{idx:4d} | {size:6d} | {tile_count:5d} | {tile_sizes.get(0, 'N/A'):>8} | {tile_sizes.get(1, 'N/A'):>8} | {tile_sizes.get(2, 'N/A'):>8} | {tile_sizes.get(13, 'N/A'):>8}")

if __name__ == '__main__':
    scan_fdother_for_window_tiles()
