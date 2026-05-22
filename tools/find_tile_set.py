#!/usr/bin/env python3
"""
查找真正的窗口tile数据集
"""

import struct
import sys
import os

def find_tile_set(dat_path):
    with open(dat_path, 'rb') as f:
        magic = f.read(6)
        resource_count = struct.unpack('<I', f.read(4))[0]
        
        offsets = []
        for i in range(resource_count):
            offset = struct.unpack('<I', f.read(4))[0]
            offsets.append(offset)
    
    print(f"Checking resources for tile set structure...")
    print(f"Looking for: header(6 bytes) + offset_table(N*4) + tile_data\n")
    
    # Check resources that might be tile sets
    # Tile set should have:
    # - Header with tile count at offset 4-5
    # - Offset table starting at offset 6
    # - Multiple tiles with w,h headers
    
    candidates = [7, 13, 17, 19, 21, 23, 25]
    
    for idx in candidates:
        if idx >= resource_count:
            continue
            
        start = offsets[idx]
        end = offsets[idx+1] if idx+1 < resource_count else os.path.getsize(dat_path)
        size = end - start
        
        with open(dat_path, 'rb') as f:
            f.seek(start)
            data = f.read(min(size, 200))
        
        if len(data) < 6:
            continue
        
        # Check if it has tile set structure
        word0 = struct.unpack('<H', data[0:2])[0]
        word1 = struct.unpack('<H', data[2:4])[0]
        tile_count = struct.unpack('<H', data[4:6])[0]
        
        print(f"Index {idx}: size={size}")
        print(f"  Header: [{word0}, {word1}, tile_count={tile_count}]")
        
        # If tile_count is reasonable, check offset table
        if 5 <= tile_count <= 100:
            print(f"  Possible tile set! Checking offset table...")
            
            # Read full data
            with open(dat_path, 'rb') as f:
                f.seek(start)
                full_data = f.read(size)
            
            # Check offset table
            valid_offsets = 0
            for i in range(min(tile_count, 10)):
                offset_addr = 6 + i * 4
                if offset_addr + 4 > len(full_data):
                    break
                tile_offset = struct.unpack('<I', full_data[offset_addr:offset_addr+4])[0]
                
                if tile_offset < len(full_data) and tile_offset >= 6:
                    # Check tile header
                    if tile_offset + 4 <= len(full_data):
                        tw, th = struct.unpack('<HH', full_data[tile_offset:tile_offset+4])
                        if 0 < tw <= 320 and 0 < th <= 200:
                            valid_offsets += 1
                            print(f"    Tile {i}: offset={tile_offset}, w={tw}, h={th}")
            
            print(f"  Valid tiles: {valid_offsets}/{tile_count}")
            if valid_offsets > tile_count * 0.5:
                print(f"  [FOUND] This looks like the tile set!")
        
        print()

if __name__ == '__main__':
    dat_path = 'bin/FDOTHER.DAT'
    if len(sys.argv) > 1:
        dat_path = sys.argv[1]
    
    if not os.path.exists(dat_path):
        print(f"File not found: {dat_path}")
        sys.exit(1)
    
    find_tile_set(dat_path)
