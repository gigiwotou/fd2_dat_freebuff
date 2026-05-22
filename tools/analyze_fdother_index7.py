#!/usr/bin/env python3
"""
分析FDOTHER索引7的tile数据结构

根据IDA MCP反编译代码:
- sub_1685C: tile数据指针 = FDOTHER_DAT__7 + *(DWORD *)(FDOTHER_DAT__7 + 4 * tile_index + 6)
- sub_4ED0B: 读取宽度(WORD) + 高度(WORD) + 像素数据
"""

import struct
import sys
import os

def analyze_fdother_index7(dat_path):
    with open(dat_path, 'rb') as f:
        # Read DAT header
        magic = f.read(6)
        if magic != b'LLLLLL':
            print("Invalid DAT file")
            return
        
        resource_count = struct.unpack('<I', f.read(4))[0]
        print(f"Resource count: {resource_count}")
        
        # Read offset table
        offsets = []
        for i in range(resource_count):
            offset = struct.unpack('<I', f.read(4))[0]
            offsets.append(offset)
        
        # Get index 7 data range
        start = offsets[7]
        end = offsets[8] if 8 < resource_count else os.path.getsize(dat_path)
        size = end - start
        
        print(f"\nIndex 7 data:")
        print(f"  Start: {start} (0x{start:X})")
        print(f"  End: {end} (0x{end:X})")
        print(f"  Size: {size} bytes")
        
        # Read index 7 data
        f.seek(start)
        data = f.read(size)
        
        # Parse header
        if len(data) < 6:
            print("  Data too small")
            return
        
        # The structure starts at offset 0
        # Offset 0-1: unknown
        # Offset 2-3: unknown
        # Offset 4-5: tile count (WORD)
        # Offset 6+: offset table (DWORD array)
        
        tile_count = struct.unpack('<H', data[4:6])[0]
        print(f"\n  Tile count: {tile_count}")
        
        # Parse tile offsets
        print(f"\n  Tile offsets (from offset 6):")
        for i in range(min(tile_count, 30)):
            offset_addr = 6 + i * 4
            if offset_addr + 4 > len(data):
                break
            tile_offset = struct.unpack('<I', data[offset_addr:offset_addr+4])[0]
            
            if tile_offset < len(data):
                # Read tile header (width, height)
                if tile_offset + 4 <= len(data):
                    w, h = struct.unpack('<HH', data[tile_offset:tile_offset+4])
                    tile_size = len(data) - tile_offset if i == tile_count - 1 else \
                               (struct.unpack('<I', data[6 + (i+1) * 4:6 + (i+1) * 4 + 4])[0] if (i+1) * 4 + 6 <= len(data) else len(data)) - tile_offset
                    
                    print(f"    Tile {i:2d}: offset={tile_offset:5d} (0x{tile_offset:04X}), w={w:3d}, h={h:3d}")
                    
                    # Check if it's RLE compressed
                    if tile_offset + 4 < len(data):
                        first_bytes = data[tile_offset+4:tile_offset+24]
                        # Check for RLE control bytes (>= 64)
                        control_count = sum(1 for b in first_bytes if b >= 64)
                        is_rle = control_count > len(first_bytes) * 0.5
                        print(f"           First 20 bytes: {list(first_bytes)}")
                        print(f"           RLE likely: {is_rle} (control bytes: {control_count}/20)")
            else:
                print(f"    Tile {i:2d}: offset={tile_offset:5d} (0x{tile_offset:04X}) [OUT OF RANGE]")

if __name__ == '__main__':
    dat_path = 'bin/FDOTHER.DAT'
    if len(sys.argv) > 1:
        dat_path = sys.argv[1]
    
    if not os.path.exists(dat_path):
        print(f"File not found: {dat_path}")
        sys.exit(1)
    
    analyze_fdother_index7(dat_path)
