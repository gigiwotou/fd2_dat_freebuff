#!/usr/bin/env python3
"""Parse FDFIELD.DAT using correct structure from IDA sub_111BA

Structure:
  Bytes 0-5: Header/magic
  Bytes 6+: Index table (8 bytes per entry: start_offset, end_offset)
  
  To load map N:
    - Read index at offset (4 * N + 6)
    - This gives (start, end) DWORDs
    - Data size = end - start
    - Read data from start_offset
"""

import struct
import sys
import os

def parse_fdfield_entry(filepath, map_index):
    """Load one map entry from FDFIELD.DAT using sub_111BA logic"""
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"FDFIELD.DAT file size: {len(data)} bytes")
    print(f"Loading map index: {map_index}")
    print()
    
    # Calculate index table offset
    idx_offset = 4 * map_index + 6
    print(f"Index table offset for map {map_index}: {idx_offset} (0x{idx_offset:X})")
    
    if idx_offset + 8 > len(data):
        print(f"  ERROR: Index offset out of range")
        return
    
    # Read 8 bytes (start_offset, end_offset)
    start_offset = struct.unpack_from('<I', data, idx_offset)[0]
    end_offset = struct.unpack_from('<I', data, idx_offset + 4)[0]
    data_size = end_offset - start_offset
    
    print(f"  Start offset: {start_offset} (0x{start_offset:X})")
    print(f"  End offset:   {end_offset} (0x{end_offset:X})")
    print(f"  Data size:    {data_size} bytes")
    print()
    
    if start_offset >= len(data) or start_offset + data_size > len(data):
        print(f"  ERROR: Data offset out of range")
        return
    
    # Read the map data block
    map_data = data[start_offset:start_offset + data_size]
    
    print(f"First 100 bytes of map data:")
    for i in range(0, min(100, len(map_data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in map_data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in map_data[i:i+16])
        print(f"  {start_offset + i:05X}: {hex_str:<48} {ascii_str}")
    print()
    
    # Analyze structure
    print("Analyzing map data structure:")
    
    # First 4 bytes might be metadata
    if len(map_data) >= 4:
        val16_0 = struct.unpack_from('<H', map_data, 0)[0]
        val16_2 = struct.unpack_from('<H', map_data, 2)[0]
        print(f"  Bytes 0-1: {val16_0} (0x{val16_0:04X})")
        print(f"  Bytes 2-3: {val16_2} (0x{val16_2:04X})")
    
    # Look for character data patterns
    # Characters might be at a specific offset in the map data
    # Search for sequences of bytes where byte[7] is an icon ID (0-140)
    
    print(f"\nSearching for character data (80-byte records with icon_id at offset+7):")
    char_candidates = []
    for start in range(0, len(map_data) - 80, 1):
        record = map_data[start:start+80]
        icon_id = record[7]
        # Check if icon_id is valid and some other bytes are small
        if 0 <= icon_id <= 140:
            # Check if first 8 bytes have several small values
            small_count = sum(1 for b in record[:8] if b < 150)
            if small_count >= 4:
                char_candidates.append((start, icon_id, record[:16]))
    
    if char_candidates:
        print(f"  Found {len(char_candidates)} potential character records:")
        for pos, icon_id, sample in char_candidates[:10]:
            print(f"    Position {start_offset + pos:6d} (0x{start_offset + pos:05X}): icon_id={icon_id}, bytes={' '.join(f'{b:02X}' for b in sample)}")
    else:
        print(f"  No character data found with this pattern")
    
    # Try other record sizes
    print(f"\nSearching with different record sizes:")
    for stride in [64, 48, 40, 32, 24, 20, 16, 12, 10, 8]:
        count = 0
        for start in range(0, len(map_data) - stride, 1):
            record = map_data[start:start+stride]
            if stride >= 8:
                icon_id = record[7]
                if 0 <= icon_id <= 140:
                    count += 1
        
        if 0 < count < 100:
            print(f"  Stride {stride:3d}: {count} potential records")

def main():
    fdfield_path = sys.argv[1] if len(sys.argv) > 1 else 'FDFIELD.DAT'
    map_index = int(sys.argv[2]) if len(sys.argv) > 2 else 32
    
    if not os.path.exists(fdfield_path):
        print(f"Error: {fdfield_path} not found")
        return 1
    
    parse_fdfield_entry(fdfield_path, map_index)
    return 0

if __name__ == '__main__':
    sys.exit(main())
