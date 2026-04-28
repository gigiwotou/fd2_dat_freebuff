#!/usr/bin/env python3
"""
FDFIELD.DAT Map 97 Direct Parser

Map 97 uses resource index 97 directly in FDFIELD.DAT.
"""

import struct
import json
from pathlib import Path


def parse_fdfield_map97():
    data = Path("game/FDFIELD.DAT").read_bytes()
    resource_count = struct.unpack_from("<I", data, 6)[0]
    
    print(f"FDFIELD.DAT: {resource_count} resources\n")
    
    # Helper to get resource
    def get_resource(idx):
        if idx >= resource_count:
            return None
        start = struct.unpack_from("<I", data, 10 + idx * 4)[0]
        end = struct.unpack_from("<I", data, 10 + (idx + 1) * 4)[0] if idx + 1 < resource_count else len(data)
        return data[start:end]
    
    # Check resources around 97
    print("=== Resources 94-105 ===")
    for i in range(94, min(106, resource_count)):
        res_data = get_resource(i)
        if res_data:
            print(f"Resource {i:3d}: size={len(res_data):5d}, first 20 bytes: {res_data[:20].hex()}")
            
            if len(res_data) >= 4:
                w = struct.unpack_from("<H", res_data, 0)[0]
                h = struct.unpack_from("<H", res_data, 2)[0]
                if 5 <= w <= 60 and 5 <= h <= 60:
                    print(f"  -> Possible map: {w}x{h}")
        else:
            print(f"Resource {i:3d}: N/A")
        print()
    
    # Try resource 97 as layout
    print("\n=== Resource 97 as Map Layout ===")
    res97 = get_resource(97)
    if res97:
        print(f"Size: {len(res97)} bytes")
        if len(res97) >= 4:
            w = struct.unpack_from("<H", res97, 0)[0]
            h = struct.unpack_from("<H", res97, 2)[0]
            print(f"First 4 bytes: {res97[:4].hex()} -> {w}x{h}")
            print(f"Expected tile data: {w * h * 4} bytes")
            print(f"Actual remaining: {len(res97) - 4} bytes")
            
            if len(res97) - 4 == w * h * 4:
                print("\nFormat: 4 bytes per tile (terrain:2 + event:2)")
            elif len(res97) - 4 == w * h * 2:
                print("\nFormat: 2 bytes per tile (tile index)")
            else:
                print(f"\nFormat: Object list or other format")
                
                # Parse as object list (pairs of 16-bit values)
                tile_data = res97[4:]
                if len(tile_data) % 4 == 0:
                    obj_count = len(tile_data) // 4
                    print(f"  {obj_count} objects (4 bytes each)")
                    
                    for idx in range(min(10, obj_count)):
                        pos = idx * 4
                        val1 = struct.unpack_from("<H", tile_data, pos)[0]
                        val2 = struct.unpack_from("<H", tile_data, pos + 2)[0]
                        print(f"  Object {idx}: val1={val1:3d} (0x{val1:04X}), val2={val2:3d} (0x{val2:04X})")
    
    # Try to find control and spawn data
    # They might be in resources 98 and 99, or stored differently
    print("\n\n=== Looking for Control & Spawn Data ===")
    for i in range(98, min(101, resource_count)):
        res_data = get_resource(i)
        if res_data and len(res_data) > 0:
            print(f"Resource {i}: size={len(res_data)}, first 30 bytes: {res_data[:30].hex()}")
            
            # Check if it looks like control data
            if len(res_data) >= 3:
                map_id = res_data[0]
                max_friendly = res_data[1]
                total_enemy_ally = res_data[2]
                print(f"  Possible control data: map_id={map_id}, max_friendly={max_friendly}, enemy_ally={total_enemy_ally}")
            print()


if __name__ == "__main__":
    parse_fdfield_map97()
