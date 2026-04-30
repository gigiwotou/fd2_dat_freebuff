#!/usr/bin/env python3
"""Parse map 32 data from FDFIELD.DAT - dump full data"""

import struct
import sys
import os

def parse_map32_data(filepath, map_index=32):
    """Parse map data"""
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # Get map data using sub_111BA logic
    idx_offset = 4 * map_index + 6
    start_offset = struct.unpack_from('<I', data, idx_offset)[0]
    end_offset = struct.unpack_from('<I', data, idx_offset + 4)[0]
    data_size = end_offset - start_offset
    
    map_data = data[start_offset:start_offset + data_size]
    
    print(f"Map {map_index} data:")
    print(f"  File offset: {start_offset} (0x{start_offset:X})")
    print(f"  Data size: {data_size} bytes")
    print()
    
    # Dump all 320 bytes
    print("Full data dump:")
    for i in range(0, len(map_data), 16):
        hex_str = ' '.join(f'{b:02X}' for b in map_data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in map_data[i:i+16])
        print(f"  {start_offset + i:05X}: {hex_str:<48} {ascii_str}")
    
    print()
    print("Interpreting as 16-bit values:")
    for i in range(0, min(len(map_data), 320), 2):
        val = struct.unpack_from('<H', map_data, i)[0]
        print(f"  Offset {i:3d}: {val:5d} (0x{val:04X})")
    
    print()
    print("Analyzing record structure...")
    
    # First 4 bytes: 53, 17
    # Then data from offset 4
    # 316 bytes = 4 * 79 or other combinations
    
    # Let's look for patterns
    # Maybe it's: [count] [records...]
    # Or maybe it's: [width] [height] [tile data...]
    
    # 53 could be map width in some unit
    # 17 could be map height or event count
    
    # If 17 is event count, each event = 316/17 ≈ 18.6 bytes (not even)
    # If we skip first 4 bytes: 316/17 ≈ 18.6 bytes
    
    # Let's try: first 4 bytes are metadata, then look at remaining
    remaining = map_data[4:]
    
    # Maybe it's pairs of 16-bit values
    print("\nPairs of 16-bit values (after header):")
    pair_idx = 0
    for i in range(0, len(remaining) - 1, 4):
        val1 = struct.unpack_from('<H', remaining, i)[0]
        val2 = struct.unpack_from('<H', remaining, i + 2)[0]
        print(f"  Pair[{pair_idx:2d}]: ({val1:5d}, {val2:5d})")
        pair_idx += 1
        if pair_idx >= 40:
            break

def main():
    fdfield_path = sys.argv[1] if len(sys.argv) > 1 else 'FDFIELD.DAT'
    map_index = int(sys.argv[2]) if len(sys.argv) > 2 else 32
    
    if not os.path.exists(fdfield_path):
        print(f"Error: {fdfield_path} not found")
        return 1
    
    parse_map32_data(fdfield_path, map_index)
    return 0

if __name__ == '__main__':
    sys.exit(main())
