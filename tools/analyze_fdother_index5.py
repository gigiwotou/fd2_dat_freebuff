#!/usr/bin/env python3
"""
分析FDOTHER索引5的tile数据结构（窗口tile集）
"""

import struct
import sys
import os

def analyze_fdother_index5(dat_path):
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
        
        # Get index 5 data range
        start = offsets[5]
        end = offsets[6] if 6 < resource_count else os.path.getsize(dat_path)
        size = end - start
        
        print(f"\nIndex 5 data (window tile set):")
        print(f"  Start: {start} (0x{start:X})")
        print(f"  End: {end} (0x{end:X})")
        print(f"  Size: {size} bytes")
        
        # Read index 5 data
        f.seek(start)
        data = f.read(size)
        
        # Parse header
        if len(data) < 6:
            print("  Data too small")
            return
        
        # According to sub_1685C: tile数据指针 = FDOTHER_DAT__7 + *(DWORD *)(FDOTHER_DAT__7 + 4 * tile_index + 6)
        # The structure is:
        # Offset 0-1: unknown (maybe width/height of tile grid?)
        # Offset 2-3: unknown
        # Offset 4-5: tile count (WORD)
        # Offset 6+: offset table (DWORD array)
        
        word0 = struct.unpack('<H', data[0:2])[0]
        word1 = struct.unpack('<H', data[2:4])[0]
        tile_count = struct.unpack('<H', data[4:6])[0]
        
        print(f"\n  Header: word0={word0}, word1={word1}, tile_count={tile_count}")
        
        # Parse tile offsets
        print(f"\n  Tile offsets (from offset 6):")
        for i in range(min(tile_count, 30)):
            offset_addr = 6 + i * 4
            if offset_addr + 4 > len(data):
                break
            tile_offset = struct.unpack('<I', data[offset_addr:offset_addr+4])[0]
            
            if tile_offset < len(data) and tile_offset >= 6:
                # Read tile header (width, height)
                if tile_offset + 4 <= len(data):
                    w, h = struct.unpack('<HH', data[tile_offset:tile_offset+4])
                    # Calculate tile data size
                    next_offset_addr = 6 + (i + 1) * 4
                    if next_offset_addr + 4 <= len(data):
                        next_tile_offset = struct.unpack('<I', data[next_offset_addr:next_offset_addr+4])[0]
                        tile_data_size = next_tile_offset - tile_offset
                    else:
                        tile_data_size = len(data) - tile_offset
                    
                    expected_pixels = w * h
                    actual_data = tile_data_size - 4  # subtract 4 bytes header
                    
                    print(f"    Tile {i:2d}: offset={tile_offset:5d}, w={w:3d}, h={h:3d}, expected={expected_pixels:5d}, actual_data={actual_data:5d}")
                    
                    # Check first bytes
                    if tile_offset + 4 < len(data):
                        first_bytes = data[tile_offset+4:tile_offset+24]
                        # Check if it's raw pixel data or RLE
                        control_count = sum(1 for b in first_bytes if b >= 64 and b < 192)
                        raw_count = sum(1 for b in first_bytes if b < 64)
                        print(f"           First bytes: {list(first_bytes[:10])}")
                        
                        # If tile size matches expected pixels, it's raw data
                        if actual_data == expected_pixels or actual_data == expected_pixels + 1:
                            print(f"           [RAW] Data size matches expected pixels")
                        else:
                            print(f"           [RLE?] Data size ({actual_data}) != expected ({expected_pixels})")
            else:
                print(f"    Tile {i:2d}: offset={tile_offset:5d} [OUT OF RANGE or INVALID]")

if __name__ == '__main__':
    dat_path = 'bin/FDOTHER.DAT'
    if len(sys.argv) > 1:
        dat_path = sys.argv[1]
    
    if not os.path.exists(dat_path):
        print(f"File not found: {dat_path}")
        sys.exit(1)
    
    analyze_fdother_index5(dat_path)
