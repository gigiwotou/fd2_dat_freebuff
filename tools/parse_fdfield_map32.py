#!/usr/bin/env python3
"""Parse FDFIELD.DAT to find map 32 character/sprite data

Structure from analysis:
  - Bytes 0-5: Magic "LLLLLL"
  - Bytes 6+: 3-byte little-endian offsets (point to map data blocks)
  - Each map has a data block containing:
    - Map dimensions
    - Tile data
    - Character/sprite positions
"""

import struct
import sys
import os

def parse_fdfield_for_map(filepath, target_map=32):
    """Parse FDFIELD.DAT and find data for specific map"""
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"FDFIELD.DAT file size: {len(data)} bytes")
    print()
    
    # Read offset table (3-byte offsets starting at offset 6)
    pos = 6
    offsets = []
    while pos + 3 <= len(data):
        offset = data[pos] | (data[pos+1] << 8) | (data[pos+2] << 16)
        offsets.append(offset)
        pos += 3
        
        # Stop when we hit unreasonable offsets
        if offset > len(data) or (len(offsets) > 5 and offset == 0):
            break
    
    print(f"Found {len(offsets)} map entries in offset table")
    print()
    
    # The offset table might not be 1:1 with map IDs
    # Map 32 might be at a different index
    # Let's examine several offsets to find map 32
    
    print("Examining data blocks:")
    for i in range(min(40, len(offsets))):
        off = offsets[i]
        if 0 < off < len(data):
            block = data[off:off+80]
            
            # Look for patterns that might indicate map number
            # or character data (icon IDs 0-140)
            
            # Check if first few bytes could be map metadata
            byte0 = block[0]
            byte1 = block[1] if len(block) > 1 else 0
            byte2 = block[2] if len(block) > 2 else 0
            
            # Try to find map number or character count
            print(f"  Map[{i:2d}] at offset {off:6d} (0x{off:05X}):")
            print(f"    First 20 bytes: {' '.join(f'{b:02X}' for b in block[:20])}")
            
            # Check for small values that could be icon IDs
            small_vals = [(j, block[j]) for j in range(min(20, len(block))) if block[j] < 140]
            if small_vals:
                print(f"    Small values (<140): {[(j, v) for j, v in small_vals[:10]]}")
            
            print()

def main():
    fdfield_path = sys.argv[1] if len(sys.argv) > 1 else 'FDFIELD.DAT'
    map_id = int(sys.argv[2]) if len(sys.argv) > 2 else 32
    
    if not os.path.exists(fdfield_path):
        print(f"Error: {fdfield_path} not found")
        return 1
    
    parse_fdfield_for_map(fdfield_path, map_id)
    return 0

if __name__ == '__main__':
    sys.exit(main())
