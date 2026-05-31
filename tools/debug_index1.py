#!/usr/bin/env python3
"""Debug index 1 resource structure"""
import sys

def read_dword(data, offset):
    return data[offset] | (data[offset + 1] << 8) | (data[offset + 2] << 16) | (data[offset + 3] << 24)

def read_word(data, offset):
    return data[offset] | (data[offset + 1] << 8)

def main():
    filepath = "game/FDOTHER.DAT"
    with open(filepath, "rb") as f:
        data = f.read()
    
    # Parse index 1 resource
    # Read offset table from FDOTHER.DAT
    magic = data[0:6]
    print(f"Magic: {magic}")
    
    # Count resources
    count = 0
    pos = 6
    while pos + 4 <= len(data):
        off = read_dword(data, pos)
        if off == 0 or off > len(data):
            break
        count += 1
        pos += 4
    
    print(f"Total resources: {count}")
    
    # Get index 1 resource
    res1_start = read_dword(data, 6 + 0 * 4)
    res1_end = read_dword(data, 6 + 1 * 4)
    res1_size = res1_end - res1_start
    
    print(f"\nIndex 1 resource:")
    print(f"  Start offset: 0x{res1_start:X}")
    print(f"  End offset: 0x{res1_end:X}")
    print(f"  Size: {res1_size} bytes")
    
    # Read index 1 data
    res1 = data[res1_start:res1_end]
    
    # Parse header
    w = read_word(res1, 0)
    h = read_word(res1, 2)
    print(f"\n  Width: {w}")
    print(f"  Height: {h}")
    print(f"  Byte[4]: {res1[4]} (0x{res1[4]:02X})")
    print(f"  Byte[5]: {res1[5]} (0x{res1[5]:02X})")
    print(f"  Byte[6]: {res1[6]} (0x{res1[6]:02X})")
    print(f"  Byte[7]: {res1[7]} (0x{res1[7]:02X})")
    
    # Check if header is 8 bytes (2-byte palette window) or 6 bytes (1-byte)
    if res1[5] != 0:
        pw = read_word(res1, 4)
        offset_table_start = 8
        print(f"\n  Palette window (2-byte): {pw} (0x{pw:04X})")
        print(f"  Offset table starts at: {offset_table_start}")
    else:
        pw = res1[4]
        offset_table_start = 6
        print(f"\n  Palette window (1-byte): {pw} (0x{pw:02X})")
        print(f"  Offset table starts at: {offset_table_start}")
    
    # Parse offset table
    offsets = []
    pos = offset_table_start
    while pos + 4 <= len(res1):
        off = read_dword(res1, pos)
        if off > res1_size:
            break
        offsets.append(off)
        pos += 4
        if len(offsets) > 100:
            break
    
    print(f"\n  Offset count: {len(offsets)}")
    print(f"  First 10 offsets:")
    for i in range(min(10, len(offsets))):
        size = offsets[i+1] - offsets[i] if i+1 < len(offsets) else res1_size - offsets[i]
        print(f"    [{i}] offset={offsets[i]}, size={size}")

if __name__ == "__main__":
    main()
