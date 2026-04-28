#!/usr/bin/env python3
"""
FDFIELD.DAT Map 97 Locator

Find the correct resource that contains map 97's layout data.
The documentation says each map has 3 offsets, so maybe we need
to find a meta-resource that contains the index for all maps.
"""

import struct
from pathlib import Path


def analyze_all_resources():
    data = Path("game/FDFIELD.DAT").read_bytes()
    magic = data[:6]
    resource_count = struct.unpack_from("<I", data, 6)[0]
    
    print(f"FDFIELD.DAT: {resource_count} resources\n")
    
    # Look for resources that might be map index tables
    # or resources that look like map layout data (start with width/height)
    
    map_like_resources = []
    
    for i in range(resource_count):
        # Get resource data
        start = struct.unpack_from("<I", data, 10 + i * 4)[0]
        end = struct.unpack_from("<I", data, 10 + (i + 1) * 4)[0] if i + 1 < resource_count else len(data)
        res_data = data[start:end]
        
        if len(res_data) >= 4:
            w = struct.unpack_from("<H", res_data, 0)[0]
            h = struct.unpack_from("<H", res_data, 2)[0]
            
            # Check if width/height are reasonable (5-50)
            if 5 <= w <= 50 and 5 <= h <= 50:
                # Check if remaining data matches w*h*4 or w*h*2
                remaining = len(res_data) - 4
                if remaining == w * h * 4:
                    map_like_resources.append({
                        "index": i,
                        "width": w,
                        "height": h,
                        "format": "4_bytes/tile",
                        "size": len(res_data)
                    })
                elif remaining == w * h * 2:
                    map_like_resources.append({
                        "index": i,
                        "width": w,
                        "height": h,
                        "format": "2_bytes/tile",
                        "size": len(res_data)
                    })
                elif remaining > 0:
                    # Check if it's object list format
                    if remaining % 4 == 0:
                        obj_count = remaining // 4
                        map_like_resources.append({
                            "index": i,
                            "width": w,
                            "height": h,
                            "format": f"object_list ({obj_count} objs)",
                            "size": len(res_data)
                        })
    
    print(f"Found {len(map_like_resources)} resources that look like map data:\n")
    
    # Show all map-like resources
    for res in map_like_resources:
        print(f"  Resource {res['index']:3d}: {res['width']:2d}x{res['height']:2d}, format={res['format']}, size={res['size']}")
    
    # Show resources 90-110 (around map 97)
    print(f"\n=== Resources 90-110 ===")
    for i in range(90, min(111, resource_count)):
        start = struct.unpack_from("<I", data, 10 + i * 4)[0]
        end = struct.unpack_from("<I", data, 10 + (i + 1) * 4)[0] if i + 1 < resource_count else len(data)
        res_data = data[start:end]
        
        if len(res_data) >= 4:
            w = struct.unpack_from("<H", res_data, 0)[0]
            h = struct.unpack_from("<H", res_data, 2)[0]
            print(f"  Resource {i:3d}: offset=0x{start:X}, size={len(res_data):5d}, first 4 bytes: {res_data[:4].hex()}, W/H: {w}x{h}")
        else:
            print(f"  Resource {i:3d}: offset=0x{start:X}, size={len(res_data):5d}, too small")


if __name__ == "__main__":
    analyze_all_resources()
