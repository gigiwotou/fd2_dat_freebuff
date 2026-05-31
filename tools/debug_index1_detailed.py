#!/usr/bin/env python3
"""Debug index 1 resource structure - detailed byte dump"""
import struct

def read_dword(data, offset):
    return data[offset] | (data[offset + 1] << 8) | (data[offset + 2] << 16) | (data[offset + 3] << 24)

def read_word(data, offset):
    return data[offset] | (data[offset + 1] << 8)

def main():
    filepath = "game/FDOTHER.DAT"
    with open(filepath, "rb") as f:
        data = f.read()
    
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
    
    # Get index 0 resource
    res0_start = read_dword(data, 6 + 0 * 4)
    res0_end = read_dword(data, 6 + 1 * 4)
    print(f"Index 0 (palette): 0x{res0_start:X} - 0x{res0_end:X}, size={res0_end - res0_start}")
    
    # Get index 1 resource
    res1_start = read_dword(data, 6 + 1 * 4)
    res1_end = read_dword(data, 6 + 2 * 4)
    res1_size = res1_end - res1_start
    
    print(f"\nIndex 1 resource:")
    print(f"  Start offset: 0x{res1_start:X}")
    print(f"  End offset: 0x{res1_end:X}")
    print(f"  Size: {res1_size} bytes")
    
    # Read index 1 data
    res1 = data[res1_start:res1_end]
    
    # Dump first 100 bytes in hex
    print(f"\n  First 100 bytes (hex):")
    for i in range(0, min(100, len(res1)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in res1[i:i+16])
        print(f"    {i:04X}: {hex_str}")
    
    # Parse assuming: [w:2][h:2][pw:1][pad:1][offsets...]
    w = read_word(res1, 0)
    h = read_word(res1, 2)
    pw = res1[4]
    
    print(f"\n  Option A (6-byte header):")
    print(f"    Width: {w}")
    print(f"    Height: {h}")
    print(f"    Palette window: {pw}")
    
    # Try parsing offsets from byte 6
    offsets_from_6 = []
    pos = 6
    while pos + 4 <= len(res1):
        off = read_dword(res1, pos)
        if off > res1_size:
            break
        offsets_from_6.append(off)
        pos += 4
    
    print(f"    Offsets from byte 6: {len(offsets_from_6)} found")
    for i in range(min(5, len(offsets_from_6))):
        end = offsets_from_6[i+1] if i+1 < len(offsets_from_6) else res1_size
        print(f"      [{i}] {offsets_from_6[i]} (size: {end - offsets_from_6[i]})")
    
    # Parse assuming: [pw:2][count:2][offsets...] (no width/height)
    pw2 = read_word(res1, 0)
    count2 = read_word(res1, 2)
    
    print(f"\n  Option B (palette window first):")
    print(f"    Word[0]: {pw2} (0x{pw2:04X})")
    print(f"    Word[2]: {count2}")
    
    # Try parsing offsets from byte 4
    offsets_from_4 = []
    pos = 4
    while pos + 4 <= len(res1):
        off = read_dword(res1, pos)
        if off > res1_size:
            break
        offsets_from_4.append(off)
        pos += 4
    
    print(f"    Offsets from byte 4: {len(offsets_from_4)} found")
    for i in range(min(5, len(offsets_from_4))):
        end = offsets_from_4[i+1] if i+1 < len(offsets_from_4) else res1_size
        print(f"      [{i}] {offsets_from_4[i]} (size: {end - offsets_from_4[i]})")
    
    # Check first icon data
    if len(offsets_from_6) > 0:
        first_icon = res1[offsets_from_6[0]:]
        print(f"\n  First icon data (from offset table @6):")
        print(f"    Size: {len(first_icon)} bytes")
        print(f"    First 32 bytes: {' '.join(f'{b:02X}' for b in first_icon[:32])}")
        
        icon_w = read_word(first_icon, 0)
        icon_h = read_word(first_icon, 2)
        print(f"    Icon internal: {icon_w}x{icon_h}")
    
    if len(offsets_from_4) > 0:
        first_icon = res1[offsets_from_4[0]:]
        print(f"\n  First icon data (from offset table @4):")
        print(f"    Size: {len(first_icon)} bytes")
        print(f"    First 32 bytes: {' '.join(f'{b:02X}' for b in first_icon[:32])}")
        
        icon_w = read_word(first_icon, 0)
        icon_h = read_word(first_icon, 2)
        print(f"    Icon internal: {icon_w}x{icon_h}")

if __name__ == "__main__":
    main()
