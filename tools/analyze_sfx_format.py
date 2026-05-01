#!/usr/bin/env python3
"""
Deep analysis of FDOTHER.DAT audio samples, especially resource [6] and [9].

Resource [6] at offset 0x02CB13:
  - Starts with "LLLLLL" header (nested DAT format)
  - Contains 3F F0 repeating patterns - looks like VOC audio blocks
  
Resource [9] at offset 0x033903:
  - 274 bytes, 3F B7 repeating pattern
  - Possibly raw PCM or ADPCM
"""

import struct
from pathlib import Path

def analyze_resource_6():
    with open("game/FDOTHER.DAT", "rb") as f:
        data = f.read()
    
    # Read resource [6] offsets
    offset_table_start = 10
    offsets = []
    count = struct.unpack_from('<I', data, 6)[0]
    for i in range(count):
        off = struct.unpack_from('<I', data, offset_table_start + i * 4)[0]
        offsets.append(off)
    
    start = offsets[6]
    end = offsets[7] if 7 < count else len(data)
    res6 = data[start:end]
    
    print("=" * 80)
    print("Resource [6] Analysis:")
    print(f"  Offset: 0x{start:06X}")
    print(f"  Size: {len(res6)} bytes")
    print()
    
    # Check LLLLLL header
    if res6[:6] == b'LLLLLL':
        print("  Header: LLLLLL (nested DAT)")
        res_count = struct.unpack_from('<I', res6, 6)[0]
        print(f"  Sub-resource count: {res_count}")
        
        # Read offset table
        for i in range(min(res_count, 20)):
            sub_offset = struct.unpack_from('<I', res6, 10 + i * 4)[0]
            next_off = struct.unpack_from('<I', res6, 10 + (i+1) * 4)[0] if i+1 < res_count else len(res6)
            sub_size = next_off - sub_offset
            
            print(f"\n  Sub-resource [{i}]: offset=0x{sub_offset:04X}, size={sub_size}")
            
            # Dump first bytes of each sub-resource
            if sub_offset + 20 <= len(res6):
                sub_data = res6[sub_offset:sub_offset+32]
                hex_str = ' '.join(f'{b:02X}' for b in sub_data)
                print(f"    Hex: {hex_str}")
                
                # Check for VOC header
                if sub_data[:8] == b'\x00\x01' or sub_data[:4] == b'Creative':
                    print("    -> VOC audio block detected!")
    else:
        print("  No LLLLLL header")
    
    print("\n" + "=" * 80)

def analyze_resource_9():
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
    
    print("=" * 80)
    print("Resource [9] Analysis:")
    print(f"  Offset: 0x{start:06X}")
    print(f"  Size: {len(res9)} bytes")
    print()
    
    # Full hex dump
    print("  Full hex dump:")
    for i in range(0, len(res9), 16):
        hex_str = ' '.join(f'{b:02X}' for b in res9[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in res9[i:i+16])
        print(f"    {start+i:06X}: {hex_str:<48s} {ascii_str}")
    
    print("\n" + "=" * 80)

def analyze_all_small_resources():
    """Analyze resources that could be audio samples (< 5000 bytes)"""
    with open("game/FDOTHER.DAT", "rb") as f:
        data = f.read()
    
    offset_table_start = 10
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, offset_table_start + i * 4)[0]
        offsets.append(off)
    
    print("Small resources (< 5000 bytes) - potential audio samples:")
    for i in range(min(count, 40)):
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else len(data)
        size = end - start
        
        if size < 5000:
            res = data[start:end]
            
            # Check for audio-like patterns
            # VOC typically has blocks with size+data format
            # Check for repeating patterns (silence or tone)
            
            unique_bytes = len(set(res))
            
            print(f"\n  [{i}] size={size}, unique_bytes={unique_bytes}")
            print(f"      First 32 bytes: {res[:32].hex()}")

def extract_sample_0_from_sub20421():
    """
    In sub_20421, when a5==1, it calls sub_25A96(handle, 0, 1).
    The a6 parameter is 0, meaning sample index 0.
    
    The sample data comes from the _FDOTHER.DAT_ buffer passed to sub_25A96.
    In sub_1F894: _FDOTHER.DAT_ = sub_111BA(..., 77) — this loads FDOTHER.DAT resource #77
    
    So the lightning sound is in FDOTHER.DAT resource #77, sample index 0!
    """
    print("=" * 80)
    print("Finding lightning sound sample:")
    print("  From sub_1F894: _FDOTHER.DAT_ = sub_111BA(..., 77)")
    print("  This loads FDOTHER.DAT resource #77")
    print("  Then sub_20421(3, 90, 1) is called with a5=1 (enable sound)")
    print("  Inside sub_20421: sub_25A96(handle, 0, 1) plays sample #0")
    print("  So: lightning sound = FDOTHER.DAT resource #77, sample #0")
    print("=" * 80)
    
    with open("game/FDOTHER.DAT", "rb") as f:
        data = f.read()
    
    offset_table_start = 10
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, offset_table_start + i * 4)[0]
        offsets.append(off)
    
    if count > 77:
        start = offsets[77]
        end = offsets[78] if 78 < count else len(data)
        res77 = data[start:end]
        
        print(f"\nResource [77] analysis:")
        print(f"  Offset: 0x{start:06X}")
        print(f"  Size: {len(res77)} bytes")
        print(f"  First 64 bytes: {res77[:64].hex()}")
        
        # Check header
        if res77[:6] == b'LLLLLL':
            sub_count = struct.unpack_from('<I', res77, 6)[0]
            print(f"  Header: LLLLLL, sub-count: {sub_count}")
            
            for i in range(sub_count):
                sub_off = struct.unpack_from('<I', res77, 10 + i * 4)[0]
                next_off = struct.unpack_from('<I', res77, 10 + (i+1) * 4)[0] if i+1 < sub_count else len(res77)
                sub_size = next_off - sub_off
                
                print(f"  Sub [{i}]: offset=0x{sub_off:04X}, size={sub_size}")
                
                if sub_off + 32 <= len(res77):
                    sub_data = res77[sub_off:sub_off+32]
                    print(f"    Hex: {sub_data.hex()}")

if __name__ == "__main__":
    analyze_resource_6()
    analyze_resource_9()
    analyze_all_small_resources()
    extract_sample_0_from_sub20421()
