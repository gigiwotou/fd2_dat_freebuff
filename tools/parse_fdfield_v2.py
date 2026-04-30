#!/usr/bin/env python3
"""Parse FDFIELD.DAT to find map and character data

From IDA sub_10010:
  - FDFIELD.DAT loaded with size 3 * n17 + 2 or 3 * n17
  - n17 = FD2SAV[12485] (map/level index)
  - dword_53AC1 = *(int16*)FDFIELD.DAT[0]  (first 2 bytes)
  - dword_53AC5 = *(int16*)FDFIELD.DAT[2]  (next 2 bytes)
  - n6 = FDFIELD.DAT_header[1] (byte at offset 1)
  - dword_53BE3 = FDFIELD.DAT_header[2] (byte at offset 2)

Structure appears to be:
  - Header: contains map count, metadata
  - Per-map data: offset table (3 bytes per entry)
"""

import struct
import sys
import os

def parse_fdfield(filepath):
    """Parse FDFIELD.DAT structure"""
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"FDFIELD.DAT file size: {len(data)} bytes")
    print()
    
    # From IDA:
    # dword_53AC1 = *(int16*)dword_53A51  (first 16-bit value)
    # dword_53AC5 = *(int16*)(dword_53A51 + 2)  (second 16-bit value)
    
    header_val1 = struct.unpack_from('<H', data, 0)[0]
    header_val2 = struct.unpack_from('<H', data, 2)[0]
    
    print(f"Header (first 4 bytes as two 16-bit values):")
    print(f"  Offset 0-1: {header_val1} (0x{header_val1:04X})")
    print(f"  Offset 2-3: {header_val2} (0x{header_val2:04X})")
    print()
    
    # The file seems to have a structure like:
    # [4 bytes header] + [offset table] + [data blocks]
    # Offsets are 3 bytes each (little-endian)
    
    # Check if first 4 bytes are header
    # Then 3-byte offsets follow
    
    # Read all 3-byte offsets
    offset_start = 4
    offsets = []
    pos = offset_start
    while pos + 3 <= min(400, len(data)):
        # 3-byte little-endian offset
        offset = data[pos] | (data[pos+1] << 8) | (data[pos+2] << 16)
        offsets.append(offset)
        pos += 3
        
        # Stop if we hit a pattern break (zeros or repeating)
        if len(offsets) > 50 and offset == 0:
            break
    
    print(f"Found {len(offsets)} 3-byte offsets in header area:")
    for i, off in enumerate(offsets[:30]):
        print(f"  Offset[{i:2d}] at {offset_start + i*3:4d}: {off:6d} (0x{off:06X})")
    print()
    
    # These offsets likely point to per-map data blocks
    # Let's examine what's at the first few offsets
    print("Examining data at first few offsets:")
    for i in range(min(5, len(offsets))):
        off = offsets[i]
        if off < len(data):
            block = data[off:off+40]
            print(f"\n  Block at offset {off} (0x{off:X}):")
            print(f"    Hex: {' '.join(f'{b:02X}' for b in block[:20])}")
            
            # Try interpreting as different structures
            if len(block) >= 4:
                val16_0 = struct.unpack_from('<H', block, 0)[0]
                val16_2 = struct.unpack_from('<H', block, 2)[0]
                print(f"    16-bit[0]: {val16_0} (0x{val16_0:04X})")
                print(f"    16-bit[2]: {val16_2} (0x{val16_2:04X})")
            
            if len(block) >= 8:
                print(f"    Byte[0]: {block[0]}")
                print(f"    Byte[1]: {block[1]}")
                print(f"    Byte[2]: {block[2]}")
                print(f"    Byte[3]: {block[3]}")
                print(f"    Byte[4]: {block[4]}")
                print(f"    Byte[5]: {block[5]}")
                print(f"    Byte[6]: {block[6]}")
                print(f"    Byte[7]: {block[7]}")
    
    # Search for character-like patterns (icon IDs 0-140)
    print(f"\n\nSearching for character data patterns:")
    print(f"Looking for sequences of bytes in range 0-140 (possible icon IDs)...")
    
    # Scan for 80-byte records
    for stride in [80, 40, 32, 24, 20, 16, 12, 8]:
        count = 0
        valid_records = 0
        for start in range(0, len(data) - stride, stride):
            record = data[start:start+stride]
            # Check if byte 7 is a valid icon ID (0-140)
            if 0 <= record[7] <= 140:
                valid_records += 1
        
        print(f"  Stride {stride:3d}: {valid_records} records with valid icon_id at offset+7")

def main():
    fdfield_path = sys.argv[1] if len(sys.argv) > 1 else 'FDFIELD.DAT'
    
    if not os.path.exists(fdfield_path):
        print(f"Error: {fdfield_path} not found")
        return 1
    
    parse_fdfield(fdfield_path)
    return 0

if __name__ == '__main__':
    sys.exit(main())
