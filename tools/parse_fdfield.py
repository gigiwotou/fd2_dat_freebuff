#!/usr/bin/env python3
"""Parse FDFIELD.DAT to find character position data

From IDA sub_10010:
  - FDFIELD.DAT is loaded with size 3 * n17 + 2 or 3 * n17
  - n17 = FD2SAV[12485] (level/map index)
  - Contains map metadata: tileset count, map dimensions, etc.
"""

import struct
import sys
import os

def parse_fdfield(filepath, max_dump=200):
    """Parse FDFIELD.DAT structure"""
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"FDFIELD.DAT file size: {len(data)} bytes")
    print()
    
    # Show first bytes as different interpretations
    print("First bytes analysis:")
    for i in range(min(20, len(data))):
        print(f"  Offset {i:3d}: {data[i]:3d} (0x{data[i]:02X})")
    
    # Try reading as 16-bit values
    print("\n16-bit values (little-endian):")
    for i in range(0, min(40, len(data)-1), 2):
        val = struct.unpack_from('<H', data, i)[0]
        print(f"  Offset {i:3d}: {val:5d} (0x{val:04X})")
    
    # Try reading as 32-bit values
    print("\n32-bit values (little-endian):")
    for i in range(0, min(40, len(data)-3), 4):
        val = struct.unpack_from('<I', data, i)[0]
        print(f"  Offset {i:3d}: {val:10d} (0x{val:08X})")
    
    # Dump raw hex for inspection
    print(f"\nRaw hex (first {max_dump} bytes):")
    for i in range(0, min(max_dump, len(data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"  {i:04X}: {hex_str:<48} {ascii_str}")

def main():
    fdfield_path = sys.argv[1] if len(sys.argv) > 1 else 'FDFIELD.DAT'
    
    if not os.path.exists(fdfield_path):
        print(f"Error: {fdfield_path} not found")
        return 1
    
    parse_fdfield(fdfield_path)
    return 0

if __name__ == '__main__':
    sys.exit(main())
