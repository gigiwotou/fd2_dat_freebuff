#!/usr/bin/env python3
"""
Verify map tile data structure from FDFIELD.DAT

Documentation says tile data starts with:
  1. Map width: 2 bytes
  2. Map height: 2 bytes
  3. Map data: width * height * 4 bytes (2 WORDs per tile)
"""

import struct
import sys

def verify_tile_data(filepath, map_index=32):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"FDFIELD.DAT file size: {len(data)} bytes")
    print(f"Verifying map {map_index} tile data")
    print()
    
    # Get offset from documentation structure (12 bytes per map)
    offset = 6 + map_index * 12
    tile_off, ctrl_off, char_off = struct.unpack_from('<III', data, offset)
    
    print(f"Map {map_index} offsets:")
    print(f"  Tile data:      {tile_off} (0x{tile_off:06X})")
    print(f"  Control data:   {ctrl_off} (0x{ctrl_off:06X})")
    print(f"  Character pos:  {char_off} (0x{char_off:06X})")
    print()
    
    # Verify tile data structure
    if 0 < tile_off < len(data):
        print(f"Tile data at offset {tile_off}:")
        
        # Read width and height
        if tile_off + 4 <= len(data):
            width = struct.unpack_from('<H', data, tile_off)[0]
            height = struct.unpack_from('<H', data, tile_off + 2)[0]
            print(f"  Map width:  {width}")
            print(f"  Map height: {height}")
            print(f"  Expected tile data size: {width * height * 4} bytes")
            print()
            
            # Read first few tiles
            print("  First 5 tiles (terrain_id, event_id):")
            tile_data_offset = tile_off + 4
            for i in range(min(5, width * height)):
                pos = tile_data_offset + i * 4
                if pos + 4 <= len(data):
                    terrain_id = struct.unpack_from('<H', data, pos)[0]
                    event_id = struct.unpack_from('<H', data, pos + 2)[0]
                    print(f"    Tile {i}: terrain={terrain_id}, event={event_id}")
            
            print()
            
            # Verify control data starts after tile data
            expected_ctrl_off = tile_off + 4 + (width * height * 4)
            print(f"Expected control data offset: {expected_ctrl_off} (0x{expected_ctrl_off:06X})")
            print(f"Actual control data offset:   {ctrl_off} (0x{ctrl_off:06X})")
            
            if expected_ctrl_off == ctrl_off:
                print("✓ Offsets match! Documentation structure is CORRECT")
            else:
                print(f"✗ Offset mismatch (difference: {ctrl_off - expected_ctrl_off})")
    else:
        print(f"ERROR: Invalid tile offset {tile_off}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <FDFIELD.DAT> [map_index]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    map_index = int(sys.argv[2]) if len(sys.argv) > 2 else 32
    
    verify_tile_data(filepath, map_index)
