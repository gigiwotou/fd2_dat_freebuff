#!/usr/bin/env python3
"""Parse FDFIELD.DAT to extract per-map data

From IDA sub_10010:
  - FDFIELD.DAT loaded with size 3 * n17 + 2
  - n17 = FD2SAV[12485] (map/level index)
  - First 2 bytes (offset 0-1): some metadata
  - Next (3 * n17) bytes: offset table for maps
  
From IDA sub_10652:
  - Processes map data based on map index (n17)
  - Different maps have different sizes:
    - Map 9,24,25: 462x226, tile_size=16
    - Map 17: 462x226, tile_size=16
    - Map 21: 408x276, tile_size=35
    - Map 22: 408x256, tile_size=40
    - Map 27: 462x244, tile_size=46
    - Map 23: 312x?, tile_size=?
    - Map 28,29: same as 9,24,25

FDFIELD.DAT structure:
  [2 bytes: map_count or header]
  [3 * map_count bytes: offset table]
  [data blocks for each map]
"""

import struct
import sys
import os

def parse_fdfield(filepath, map_index=32):
    """Parse FDFIELD.DAT and extract data for specific map"""
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"FDFIELD.DAT file size: {len(data)} bytes")
    print()
    
    # Header: first 2 bytes
    map_count = struct.unpack_from('<H', data, 0)[0]
    print(f"Header (first 2 bytes): {map_count} (0x{map_count:04X})")
    print(f"  This could be: number of maps, or just a magic value")
    print()
    
    # The file might have a different structure
    # Let's try reading it as: [header] + [per-map entries]
    
    # First, dump first 100 bytes in hex
    print("First 100 bytes (hex):")
    for i in range(0, min(100, len(data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"  {i:04X}: {hex_str:<48} {ascii_str}")
    print()
    
    # Try interpreting first few bytes differently
    # 0x4C4C = 19532, but 0x4C = 'L', could be magic "LLLLLL"
    if data[0:6] == b'LLLLLL':
        print("Magic header: 'LL' repeated 3 times")
        print()
        
        # After magic, read 2-byte map count or similar
        # Then offset table
        
        # Skip first 6 bytes (magic)
        # Next might be 2-byte values
        
        pos = 6
        print(f"Data after magic (starting at offset {pos}):")
        
        # Read as 2-byte values
        for i in range(10):
            if pos + 2 <= len(data):
                val = struct.unpack_from('<H', data, pos)[0]
                print(f"  16-bit[{i}] at {pos}: {val} (0x{val:04X})")
                pos += 2
    else:
        print(f"Magic: {data[0:6].hex()}")
    
    print()
    print("=" * 60)
    print("Analyzing map data blocks...")
    print("=" * 60)
    
    # Map sizes from IDA sub_10652
    map_sizes = {
        9: (462, 226, 16),
        17: (462, 226, 16),
        21: (408, 276, 35),
        22: (408, 256, 40),
        23: (312, None, None),
        24: (462, 226, 16),
        25: (462, 226, 16),
        27: (462, 244, 46),
        28: (462, 226, 16),
        29: (462, 226, 16),
    }
    
    # Search for patterns that might be character data
    # Characters have: icon_id (0-140), position, direction
    # Look for sequences of small values
    
    print("\nSearching for character-like data patterns...")
    print("Looking for: icon_id(0-140), position_x, position_y, direction...")
    
    # Try scanning with different strides
    for stride in [80, 64, 48, 40, 32, 24, 20, 16, 12, 8, 6, 4]:
        valid_sequences = 0
        for start in range(0, len(data) - stride * 3, stride):
            # Check if this could be a character record
            record = data[start:start+stride]
            
            # Heuristic: some bytes should be small (icon IDs, positions)
            small_bytes = sum(1 for b in record[:min(8, len(record))] if b < 140)
            if small_bytes >= 3:  # At least 3 small bytes
                valid_sequences += 1
        
        if valid_sequences > 0 and valid_sequences < 1000:
            print(f"  Stride {stride:3d}: {valid_sequences} potential character records")

def main():
    fdfield_path = sys.argv[1] if len(sys.argv) > 1 else 'FDFIELD.DAT'
    map_index = int(sys.argv[2]) if len(sys.argv) > 2 else 32
    
    if not os.path.exists(fdfield_path):
        print(f"Error: {fdfield_path} not found")
        return 1
    
    parse_fdfield(fdfield_path, map_index)
    return 0

if __name__ == '__main__':
    sys.exit(main())
