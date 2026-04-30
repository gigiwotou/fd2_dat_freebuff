#!/usr/bin/env python3
"""Parse FDOTHER.DAT to find map character/sprite data

From IDA sub_10652, FDOTHER.DAT is loaded for specific maps.
Map 32 might use FDOTHER.DAT data for scene characters.

FDOTHER.DAT structure:
  - Bytes 0-5: Magic "LLLLLL"
  - Bytes 6+: 3-byte offsets pointing to map scene data
"""

import struct
import sys
import os

def parse_fdother_for_map(filepath):
    """Parse FDOTHER.DAT looking for character data"""
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"FDOTHER.DAT file size: {len(data)} bytes")
    print()
    
    # Read all 3-byte offsets
    offsets = []
    pos = 6
    while pos + 3 <= len(data):
        offset = data[pos] | (data[pos+1] << 8) | (data[pos+2] << 16)
        if offset > len(data):
            break
        offsets.append(offset)
        pos += 3
    
    print(f"Found {len(offsets)} offsets in FDOTHER.DAT")
    print()
    
    # FDOTHER.DAT offsets point to RLE-compressed data
    # Let's find offsets that could contain character data
    
    # Look for data blocks with small values (possible icon IDs)
    for i in range(min(50, len(offsets))):
        off = offsets[i]
        if 0 < off < len(data) - 40:
            block = data[off:off+80]
            
            # Check if this could be character data
            # icon_id should be 0-140
            icon_id = block[7] if len(block) > 7 else -1
            
            # Check if first 16 bytes have reasonable values
            small_count = sum(1 for b in block[:16] if b < 150)
            
            if small_count >= 8 and 0 <= icon_id <= 140:
                print(f"Offset[{i:3d}] at {off:7d} (0x{off:06X}): icon_id={icon_id}, small_count={small_count}")
                print(f"  Data: {' '.join(f'{b:02X}' for b in block[:20])}")
                print()

def main():
    fdother_path = sys.argv[1] if len(sys.argv) > 1 else 'FDOTHER.DAT'
    
    if not os.path.exists(fdother_path):
        print(f"Error: {fdother_path} not found")
        return 1
    
    parse_fdother_for_map(fdother_path)
    return 0

if __name__ == '__main__':
    sys.exit(main())
