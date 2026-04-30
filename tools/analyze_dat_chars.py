#!/usr/bin/env python3
"""Analyze DAT files to find character position data

From IDA analysis of sub_2B4FB:
- Sprites are placed on a SCREEN GRID (not map tiles):
  - X spacing: 28 pixels
  - Y spacing: 30 pixels
  - Base position varies by context
  
- Characters are indexed (0..n7-1)
- Position = 320 * (30 * (index / 10) + 100) + 28 * (index % 10) + 23

From sub_10010:
- Character data is 80 bytes per character from FD2SAV+4771
- FD2SAV is 22987 bytes, XOR decrypted
- n6_0 = FD2SAV[12484] = character count
- Icon ID at offset+7 of each 80-byte record

Since FD2.SAV (save file) may not exist, we need to check if there's
a DAT file that contains the same data for map 32.
"""

import struct
import sys
import os

def analyze_fdother(filepath):
    """FDOTHER.DAT may contain scene/character metadata"""
    print(f"=== Analyzing {filepath} ===")
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes")
    
    # Show structure
    print("\nFirst 100 bytes:")
    for i in range(0, min(100, len(data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"  {i:04X}: {hex_str:<48} {ascii_str}")
    
    # Look for patterns:
    # - Repeated values that might be icon IDs
    # - Groups of bytes that might be positions
    
    # Check if there's a count byte
    if len(data) > 0:
        print(f"\nByte[0]: {data[0]}")
        if 0 < data[0] < 50:
            print(f"  Could be a count of {data[0]} items")
            item_size = (len(data) - 1) / data[0]
            print(f"  If so, each item is {item_size:.1f} bytes")
    
    print()

def analyze_fdshap(filepath):
    """FDSHAP.DAT contains shape/tileset data"""
    print(f"=== Analyzing {filepath} ===")
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes")
    
    # Look for character-related patterns
    # Scan for small values that could be icon IDs (0-140)
    icon_id_count = 0
    for i in range(len(data)):
        if 0 < data[i] < 140:
            icon_id_count += 1
    
    print(f"Potential icon ID bytes (1-139): {icon_id_count} found")
    
    # Check for 80-byte patterns
    for stride in [80, 40, 20, 16, 12, 8]:
        if len(data) > stride:
            print(f"\nChecking stride {stride} bytes:")
            for offset in [0, stride]:
                if offset + stride <= len(data):
                    record = data[offset:offset+stride]
                    print(f"  Record at {offset}: {' '.join(f'{b:02X}' for b in record[:20])}")
                    if stride >= 8:
                        print(f"    Byte+7 (icon_id?): {record[7]}")
    
    print()

def main():
    bin_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    
    for dat_file in ['FDOTHER.DAT', 'FDSHAP.DAT', 'FDFIELD.DAT', 'FDTXT.DAT']:
        filepath = os.path.join(bin_dir, dat_file)
        if os.path.exists(filepath):
            analyze_fdother(filepath) if dat_file == 'FDOTHER.DAT' else \
            analyze_fdshap(filepath)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
