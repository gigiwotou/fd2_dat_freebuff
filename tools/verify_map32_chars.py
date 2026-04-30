#!/usr/bin/env python3
"""
Verify map 32 character position data parsing against raw hex dump.
"""
import struct

def main():
    with open('game/FDFIELD.DAT', 'rb') as f:
        data = f.read()
    
    # Parse index table
    count = (len(data) - 6) // 4
    offsets = []
    for i in range(count):
        pos = 6 + i * 4
        offset = struct.unpack_from('<I', data, pos)[0]
        offsets.append(offset)
    
    # Map 32
    map_id = 32
    charpos_idx = 3 * map_id + 2  # 98
    
    charpos_start = offsets[charpos_idx]
    charpos_end = offsets[charpos_idx + 1]
    charpos_data = data[charpos_start:charpos_end]
    
    print("=" * 80)
    print(f"Map {map_id} Character Position Data Verification")
    print("=" * 80)
    print(f"\nFile offset: 0x{charpos_start:06X} ({charpos_start})")
    print(f"Resource size: {len(charpos_data)} bytes")
    print()
    
    # Print full hex dump
    print("Full hex dump:")
    for i in range(0, len(charpos_data), 16):
        hex_str = ' '.join(f'{b:02x}' for b in charpos_data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in charpos_data[i:i+16])
        print(f"  +{i:04x}: {hex_str:<48s} {ascii_str}")
    print()
    
    # Parse total count
    total_count = struct.unpack_from('<H', charpos_data, 0)[0]
    print(f"Total count (bytes 0-1): {total_count} (0x{total_count:04X})")
    print()
    
    # Parse all characters
    print("Parsing all characters (6 bytes each):")
    print(f"  Expected: {total_count} characters")
    print(f"  Data size: {len(charpos_data) - 2} bytes for character data")
    print(f"  Calculated: {(len(charpos_data) - 2) // 6} characters")
    print()
    
    # Parse and display
    for i in range(total_count):
        offset = 2 + i * 6
        if offset + 6 > len(charpos_data):
            print(f"  Char {i}: ERROR - insufficient data")
            break
        
        x = charpos_data[offset]
        b1 = charpos_data[offset + 1]
        y = charpos_data[offset + 2]
        portrait = charpos_data[offset + 3]
        b4 = charpos_data[offset + 4]
        b5 = charpos_data[offset + 5]
        
        hex_bytes = f"{x:02x} {b1:02x} {y:02x} {portrait:02x} {b4:02x} {b5:02x}"
        
        print(f"  Char {i:2d}: [{hex_bytes}] X={x:3d}, Y={y:3d}, portrait={portrait:3d}, b1=0x{b1:02x}, b4=0x{b4:02x}, b5=0x{b5:02x}")

if __name__ == '__main__':
    main()
