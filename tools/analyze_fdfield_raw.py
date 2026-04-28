#!/usr/bin/env python3
"""
FDFIELD.DAT Raw Structure Analyzer
Examines the actual binary structure to understand the format.
"""

import struct
from pathlib import Path


def analyze_fdfield():
    data = Path("game/FDFIELD.DAT").read_bytes()
    
    print(f"=== FDFIELD.DAT Raw Analysis ===")
    print(f"File size: {len(data)} bytes ({len(data)/1024:.1f} KB)\n")
    
    # Check header
    print(f"Header (first 10 bytes):")
    print(f"  Bytes 0-5: {data[0:6]}")
    print(f"  Bytes 6-9: {data[6:10].hex()} = {struct.unpack_from('<I', data, 6)[0]}")
    
    # Check if this is standard DAT format or custom map format
    # Standard DAT: offset 6 has resource_count, then 10 + i*4 has offsets
    # Custom map: offset 6 has map_count, then 10 + i*12 has 3 offsets per map
    
    resource_count = struct.unpack_from("<I", data, 6)[0]
    print(f"\nValue at offset 6: {resource_count}")
    
    # Test standard DAT format (4 bytes per entry)
    print(f"\n--- Test 1: Standard DAT format (4 bytes per entry) ---")
    if resource_count < 10000:
        print(f"  Resource count: {resource_count}")
        print(f"  Expected index table size: {resource_count * 4} bytes")
        print(f"  Expected data start: {10 + resource_count * 4}")
        
        # Read first few offsets
        for i in range(min(5, resource_count)):
            offset = struct.unpack_from("<I", data, 10 + i * 4)[0]
            next_offset = struct.unpack_from("<I", data, 10 + (i+1) * 4)[0] if i + 1 < resource_count else len(data)
            size = next_offset - offset
            print(f"  Resource {i:3d}: offset=0x{offset:X}, size={size}")
        
        # Check resource 97
        if resource_count > 97:
            offset97 = struct.unpack_from("<I", data, 10 + 97 * 4)[0]
            offset98 = struct.unpack_from("<I", data, 10 + 98 * 4)[0] if resource_count > 98 else len(data)
            size97 = offset98 - offset97
            print(f"\n  Resource 97: offset=0x{offset97:X} ({offset97}), size={size97}")
            
            # Read first 20 bytes of resource 97
            print(f"  First 20 bytes: {data[offset97:offset97+20].hex()}")
            
            # Try to interpret as width/height
            if size97 >= 4:
                w = struct.unpack_from("<H", data, offset97)[0]
                h = struct.unpack_from("<H", data, offset97 + 2)[0]
                print(f"  If interpreted as WxH: {w}x{h}")
    
    # Test custom map format (12 bytes per entry)
    print(f"\n--- Test 2: Custom map format (12 bytes per entry) ---")
    # If value at offset 6 is actually map_count
    map_count_candidate = resource_count
    if map_count_candidate < 1000 and map_count_candidate * 12 < len(data):
        print(f"  Possible map count: {map_count_candidate}")
        print(f"  Index table size: {map_count_candidate * 12} bytes")
        print(f"  Data start: {10 + map_count_candidate * 12}")
        
        # Read first map's 3 offsets
        for i in range(min(3, map_count_candidate)):
            base = 10 + i * 12
            off1 = struct.unpack_from("<I", data, base)[0]
            off2 = struct.unpack_from("<I", data, base + 4)[0]
            off3 = struct.unpack_from("<I", data, base + 8)[0]
            print(f"  Map {i:3d}: layout=0x{off1:X}, control=0x{off2:X}, spawn=0x{off3:X}")
        
        # Check map 97
        if map_count_candidate > 97:
            base97 = 10 + 97 * 12
            off1 = struct.unpack_from("<I", data, base97)[0]
            off2 = struct.unpack_from("<I", data, base97 + 4)[0]
            off3 = struct.unpack_from("<I", data, base97 + 8)[0]
            print(f"\n  Map 97: layout=0x{off1:X} ({off1}), control=0x{off2:X} ({off2}), spawn=0x{off3:X} ({off3})")
            
            # Check if these offsets make sense
            if off1 < len(data):
                print(f"  Layout data (first 20 bytes): {data[off1:off1+20].hex()}")
                if off1 + 4 <= len(data):
                    w = struct.unpack_from("<H", data, off1)[0]
                    h = struct.unpack_from("<H", data, off1 + 2)[0]
                    print(f"  If interpreted as WxH: {w}x{h}")
    
    # Also check what fd2_resources.c says about FDFIELD.DAT
    print(f"\n--- Test 3: Check FDFIELD.DAT resource count consistency ---")
    # FDFIELD.DAT is 243169 bytes
    # If standard DAT with 406 resources: 10 + 406*4 = 1634 (reasonable)
    # If custom map with X maps: 10 + X*12 = ?
    
    # Try to find a reasonable map count
    for candidate_count in range(50, 500):
        data_start = 10 + candidate_count * 12
        if data_start > len(data):
            break
        # Check if the data at that position looks reasonable
        # (should be start of actual map data, not random offsets)
        pass
    
    print(f"\n=== Raw hex dump of first 200 bytes ===")
    for i in range(0, min(200, len(data)), 16):
        hex_str = data[i:i+16].hex()
        hex_formatted = ' '.join(hex_str[j:j+2] for j in range(0, len(hex_str), 2))
        print(f"  {i:04X}: {hex_formatted}")


if __name__ == "__main__":
    analyze_fdfield()
