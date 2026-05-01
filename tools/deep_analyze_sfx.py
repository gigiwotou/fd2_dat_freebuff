#!/usr/bin/env python3
"""
Deep analysis of LLLLLL nested format in FDOTHER.DAT.
Resource [6] and [11] and [77] use this format.

From the analysis:
- Resource [6]: LLLLLL header, 38 sub-resources
- The sub-resources contain audio sample data with repeating patterns (3F F0, etc.)

Need to understand:
1. What is the offset table structure?
2. What is the audio data format inside each sub?
"""

import struct
from pathlib import Path


def analyze_res6_deep():
    with open("game/FDOTHER.DAT", "rb") as f:
        data = f.read()
    
    offset_table_start = 10
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, offset_table_start + i * 4)[0]
        offsets.append(off)
    
    start = offsets[6]
    end = offsets[7] if 7 < count else len(data)
    res6 = data[start:end]
    
    print("=" * 80)
    print("Resource [6] Deep Analysis")
    print(f"Size: {len(res6)} bytes")
    print(f"Header: {res6[:6]}")
    print(f"First 256 bytes hex dump:")
    print("=" * 80)
    
    for i in range(0, min(256, len(res6)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in res6[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in res6[i:i+16])
        print(f"  {i:04X}: {hex_str:<48s} {ascii_str}")
    
    # Analyze offset table
    sub_count = struct.unpack_from('<I', res6, 6)[0]
    print(f"\nSub-resource count: {sub_count}")
    print("Offset table (first 20):")
    
    for i in range(min(sub_count, 20)):
        sub_off = struct.unpack_from('<I', res6, 10 + i * 4)[0]
        if i + 1 < sub_count:
            sub_end = struct.unpack_from('<I', res6, 10 + (i + 1) * 4)[0]
        else:
            sub_end = len(res6)
        
        sub_size = sub_end - sub_off
        
        if sub_off < len(res6):
            sub_data = res6[sub_off:sub_off + min(32, sub_size)]
            print(f"  [{i:2d}] offset=0x{sub_off:04X}, size={sub_size:5d}, "
                  f"first_bytes={sub_data[:16].hex()}")
        else:
            print(f"  [{i:2d}] offset=0x{sub_off:08X} (out of bounds!)")


def analyze_res78_deep():
    """Resource #78 is used in sub_20421 for lightning sound."""
    with open("game/FDOTHER.DAT", "rb") as f:
        data = f.read()
    
    offset_table_start = 10
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, offset_table_start + i * 4)[0]
        offsets.append(off)
    
    start = offsets[78]
    end = offsets[79] if 79 < count else len(data)
    res78 = data[start:end]
    
    print("=" * 80)
    print("Resource [78] Deep Analysis (used in sub_20421 for lightning)")
    print(f"Size: {len(res78)} bytes")
    print("=" * 80)
    
    # Full hex dump
    for i in range(0, len(res78), 16):
        hex_str = ' '.join(f'{b:02X}' for b in res78[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in res78[i:i+16])
        print(f"  {start+i-start:04X}: {hex_str:<48s} {ascii_str}")


def analyze_res9_deep():
    """Resource [9] - 274 bytes, used for some sound effect."""
    with open("game/FDOTHER.DAT", "rb") as f:
        data = f.read()
    
    offset_table_start = 10
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, offset_table_start + i * 4)[0]
        offsets.append(off)
    
    start = offsets[9]
    end = offsets[10] if 10 < count else len(data)
    res9 = data[start:end]
    
    print("\n" + "=" * 80)
    print("Resource [9] Deep Analysis (274 bytes)")
    print("=" * 80)
    
    # Analyze header
    if len(res9) >= 4:
        val1 = struct.unpack_from('<H', res9, 0)[0]
        val2 = struct.unpack_from('<H', res9, 2)[0]
        print(f"First 4 bytes: {val1} (0x{val1:04X}), {val2} (0x{val2:04X})")
    
    # Full hex dump
    for i in range(0, len(res9), 16):
        hex_str = ' '.join(f'{b:02X}' for b in res9[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in res9[i:i+16])
        print(f"  {start+i-start:04X}: {hex_str:<48s} {ascii_str}")


def analyze_res0_deep():
    """Resource [0] - 2235 bytes, first resource."""
    with open("game/FDOTHER.DAT", "rb") as f:
        data = f.read()
    
    offset_table_start = 10
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, offset_table_start + i * 4)[0]
        offsets.append(off)
    
    start = offsets[0]
    end = offsets[1] if 1 < count else len(data)
    res0 = data[start:end]
    
    print("\n" + "=" * 80)
    print("Resource [0] Deep Analysis (2235 bytes)")
    print("=" * 80)
    
    # Full hex dump
    for i in range(0, min(256, len(res0)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in res0[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in res0[i:i+16])
        print(f"  {start+i-start:04X}: {hex_str:<48s} {ascii_str}")


def try_find_voc_headers():
    """Search for Creative Voice File headers in FDOTHER.DAT."""
    with open("game/FDOTHER.DAT", "rb") as f:
        data = f.read()
    
    print("\n" + "=" * 80)
    print("Searching for VOC headers...")
    print("=" * 80)
    
    # VOC files start with "Creative Voice File" or 0x1A followed by version info
    pos = 0
    while pos < len(data):
        pos = data.find(b'\x1A', pos)
        if pos < 0:
            break
        
        if pos + 20 < len(data):
            # Check for VOC header pattern
            if data[pos+1:pos+4] in [b'\x01\x01', b'\x00\x00', b'\x00\x01', b'\x01\x00']:
                print(f"  Found potential VOC header at offset 0x{pos:06X}")
                print(f"    Bytes: {data[pos:pos+20].hex()}")
        
        pos += 1


def try_find_sample_boundaries():
    """Try to find sample boundaries by looking for repeating patterns."""
    with open("game/FDOTHER.DAT", "rb") as f:
        data = f.read()
    
    # Resource [6] sub-resource [0] analysis
    offset_table_start = 10
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, offset_table_start + i * 4)[0]
        offsets.append(off)
    
    res6_start = offsets[6]
    res6_end = offsets[7]
    res6 = data[res6_start:res6_end]
    
    print("\n" + "=" * 80)
    print("Resource [6] Sub [0] Analysis")
    print("=" * 80)
    
    # The first 10 bytes + 38*4 = 162 bytes is the header + offset table
    # So sub[0] starts at offset 162 in the resource
    sub0_start = 10 + 38 * 4  # = 162
    sub1_off = struct.unpack_from('<I', res6, 10 + 1 * 4)[0]
    sub0_size = sub1_off - sub0_start
    
    print(f"Sub[0] offset in resource: 0x{sub0_start:04X}")
    print(f"Sub[1] offset: 0x{sub1_off:04X}")
    print(f"Sub[0] size: {sub0_size}")
    
    if sub0_start < len(res6):
        sub0 = res6[sub0_start:sub0_start + min(sub0_size, len(res6) - sub0_start)]
        print(f"First 128 bytes:")
        for i in range(0, min(128, len(sub0)), 16):
            hex_str = ' '.join(f'{b:02X}' for b in sub0[i:i+16])
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in sub0[i:i+16])
            print(f"  {i:04X}: {hex_str:<48s} {ascii_str}")


if __name__ == "__main__":
    analyze_res6_deep()
    analyze_res78_deep()
    analyze_res9_deep()
    analyze_res0_deep()
    try_find_voc_headers()
    try_find_sample_boundaries()
