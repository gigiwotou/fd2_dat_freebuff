#!/usr/bin/env python3
"""Parse map 32 data from FDFIELD.DAT

Data at offset 0xDCD9, size 320 bytes:
  Bytes 0-1: 0x0035 = 53
  Bytes 2-3: 0x0011 = 17
  
Pattern looks like 16-bit values, possibly:
  - Event records
  - Sprite positions
  - Tile metadata
"""

import struct
import sys
import os

def parse_map32_data(filepath, map_index=32):
    """Parse map data and look for character/sprite positions"""
    
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
    
    # First 4 bytes: metadata
    meta1 = struct.unpack_from('<H', map_data, 0)[0]
    meta2 = struct.unpack_from('<H', map_data, 2)[0]
    print(f"Header metadata:")
    print(f"  Bytes 0-1: {meta1} (0x{meta1:04X})")
    print(f"  Bytes 2-3: {meta2} (0x{meta2:04X})")
    print()
    
    # Remaining data: 320 - 4 = 316 bytes
    remaining = map_data[4:]
    print(f"Remaining data: {len(remaining)} bytes")
    print()
    
    # Try interpreting as different record sizes
    # Common sizes: 6 bytes (icon_id + x + y + direction?), 8 bytes, 10 bytes
    
    print("Trying to parse as event/sprite records:")
    
    for record_size in [6, 8, 10, 12, 16, 20]:
        if len(remaining) % record_size == 0:
            num_records = len(remaining) // record_size
            print(f"\n  Record size: {record_size} bytes, Count: {num_records}")
            
            # Parse first few records
            for i in range(min(10, num_records)):
                record = remaining[i * record_size:(i + 1) * record_size]
                
                # Try different interpretations
                if record_size >= 6:
                    # Interpret as: icon_id(byte) + x(16-bit) + y(16-bit) + direction(byte)
                    icon_id = record[0]
                    pos_x = struct.unpack_from('<H', record, 1)[0]
                    pos_y = struct.unpack_from('<H', record, 3)[0]
                    direction = record[5] if record_size >= 6 else 0
                    
                    print(f"    Record[{i:2d}]: icon_id={icon_id:3d}, x={pos_x:3d}, y={pos_y:3d}, dir={direction:2d} | hex={' '.join(f'{b:02X}' for b in record)}")
                else:
                    print(f"    Record[{i:2d}]: {' '.join(f'{b:02X}' for b in record)}")

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
