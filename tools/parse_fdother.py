#!/usr/bin/env python3
"""Parse FDOTHER.DAT to find map character data

From IDA sub_10652:
  - FDOTHER.DAT loaded with different offsets based on map index
  - Map 9,24,25: offset 15
  - Map 17: offset 15
  - Map 21: offset 35
  - Map 22: offset 40
  - Map 23: offset 42
  - Map 27: offset 46
  - Map 28,29: offset 55
  
  - sub_4E98D used to decode RLE data from FDOTHER.DAT
  - This is the SAME RLE decoder used for FDICON.B24!

FDOTHER.DAT likely contains:
  - RLE-compressed map data
  - Character positions and sprites
  - Scene data
"""

import struct
import sys
import os

def parse_fdother(filepath):
    """Parse FDOTHER.DAT structure"""
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"FDOTHER.DAT file size: {len(data)} bytes")
    print()
    
    # First, check the header/offset table structure
    print("First 200 bytes (hex):")
    for i in range(0, min(200, len(data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"  {i:04X}: {hex_str:<48} {ascii_str}")
    print()
    
    # Check if it has 'LLLLLL' header like FDFIELD.DAT
    if data[0:6] == b'LLLLLL':
        print("Magic header: 'LL' repeated 3 times (same as FDFIELD.DAT)")
        print()
        
        # Read 3-byte offsets after header
        pos = 6
        offsets = []
        for i in range(100):
            if pos + 3 > len(data):
                break
            offset = data[pos] | (data[pos+1] << 8) | (data[pos+2] << 16)
            offsets.append(offset)
            pos += 3
        
        print(f"Found {len(offsets)} 3-byte offsets:")
        for i in range(min(30, len(offsets))):
            print(f"  Offset[{i:3d}] at {6 + i*3:5d}: {offsets[i]:6d} (0x{offsets[i]:06X})")
        
        # Examine data at first few offsets
        print("\n\nExamining data at first few offsets:")
        for i in range(min(5, len(offsets))):
            off = offsets[i]
            if 0 < off < len(data):
                block = data[off:off+80]
                print(f"\n  Block at offset {off} (0x{off:X}):")
                print(f"    Hex: {' '.join(f'{b:02X}' for b in block[:40])}")
                
                # Check if this contains character-like data
                # icon_id at byte 7, position bytes elsewhere
                if len(block) >= 8:
                    print(f"    Byte[0]: {block[0]:3d} (0x{block[0]:02X})")
                    print(f"    Byte[1]: {block[1]:3d} (0x{block[1]:02X})")
                    print(f"    Byte[2]: {block[2]:3d} (0x{block[2]:02X})")
                    print(f"    Byte[3]: {block[3]:3d} (0x{block[3]:02X})")
                    print(f"    Byte[4]: {block[4]:3d} (0x{block[4]:02X})")
                    print(f"    Byte[5]: {block[5]:3d} (0x{block[5]:02X})")
                    print(f"    Byte[6]: {block[6]:3d} (0x{block[6]:02X})")
                    print(f"    Byte[7]: {block[7]:3d} (0x{block[7]:02X}) {'<-- icon_id?' if 0 <= block[7] <= 140 else ''}")
    else:
        print(f"Magic: {data[0:6].hex()}")
    
    # Search for character position patterns
    print("\n\nSearching for character/position data patterns...")
    print("Looking for sequences that might contain: icon_id, pos_x, pos_y, direction...")
    
    # Scan for patterns where multiple consecutive bytes are small values
    for window_size in [80, 64, 48, 40, 32, 24, 20, 16, 12, 8]:
        count = 0
        for start in range(0, len(data) - window_size, 4):
            window = data[start:start+window_size]
            # Count bytes in valid ranges
            small_count = sum(1 for b in window[:16] if b < 150)
            if small_count >= 8:  # Most bytes are small
                count += 1
        
        if 0 < count < 5000:
            print(f"  Window {window_size:3d}: {count} potential blocks")

def main():
    fdother_path = sys.argv[1] if len(sys.argv) > 1 else 'FDOTHER.DAT'
    
    if not os.path.exists(fdother_path):
        print(f"Error: {fdother_path} not found")
        return 1
    
    parse_fdother(fdother_path)
    return 0

if __name__ == '__main__':
    sys.exit(main())
