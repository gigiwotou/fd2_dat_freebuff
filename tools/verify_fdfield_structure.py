#!/usr/bin/env python3
"""
FDFIELD.DAT Structure Verification

Theory: Each map uses 3 consecutive resources:
- Resource N*3: Layout data (width, height, tiles)
- Resource N*3+1: Control & treasure data
- Resource N*3+2: Spawn position data
"""

import struct
from pathlib import Path
import json


def verify_3_resource_per_map():
    data = Path("game/FDFIELD.DAT").read_bytes()
    resource_count = struct.unpack_from("<I", data, 6)[0]
    
    print(f"=== FDFIELD.DAT: 3 Resources Per Map Theory ===")
    print(f"Total resources: {resource_count}")
    print(f"Expected maps: {resource_count // 3}")
    print()
    
    # Show first few maps
    for map_id in range(min(10, resource_count // 3)):
        layout_idx = map_id * 3
        control_idx = map_id * 3 + 1
        spawn_idx = map_id * 3 + 2
        
        # Get resources
        resources = {}
        for idx in [layout_idx, control_idx, spawn_idx]:
            if idx < resource_count:
                start = struct.unpack_from("<I", data, 10 + idx * 4)[0]
                end = struct.unpack_from("<I", data, 10 + (idx + 1) * 4)[0] if idx + 1 < resource_count else len(data)
                res_data = data[start:end]
                resources[idx] = {
                    "offset": start,
                    "size": len(res_data),
                    "data": res_data
                }
        
        # Analyze
        print(f"Map {map_id:2d}:")
        
        # Layout
        if layout_idx in resources:
            res = resources[layout_idx]
            if len(res["data"]) >= 4:
                w = struct.unpack_from("<H", res["data"], 0)[0]
                h = struct.unpack_from("<H", res["data"], 2)[0]
                print(f"  Layout (res {layout_idx:3d}): {w:2d}x{h:2d}, size={res['size']:5d}")
            else:
                print(f"  Layout (res {layout_idx:3d}): too small ({res['size']} bytes)")
        
        # Control
        if control_idx in resources:
            res = resources[control_idx]
            if res["size"] > 3:
                map_id_byte = res["data"][0]
                max_friendly = res["data"][1]
                total_enemy_ally = res["data"][2]
                print(f"  Control (res {control_idx:3d}): map_id={map_id_byte}, max_friendly={max_friendly}, enemy_ally={total_enemy_ally}, size={res['size']}")
            else:
                print(f"  Control (res {control_idx:3d}): too small ({res['size']} bytes)")
        
        # Spawn
        if spawn_idx in resources:
            res = resources[spawn_idx]
            print(f"  Spawn  (res {spawn_idx:3d}): size={res['size']}")
        
        print()
    
    # Check map 97
    print(f"\n=== Map 97 ===")
    layout_idx = 97 * 3  # = 291
    control_idx = 292
    spawn_idx = 293
    
    if layout_idx >= resource_count:
        print(f"Map 97 would need resources {layout_idx}-{spawn_idx}, but file only has {resource_count}")
        print(f"\nConclusion: Map 97 does NOT exist in this file using 3-resources-per-map format")
    else:
        print(f"Map 97 resources: {layout_idx}, {control_idx}, {spawn_idx}")
        
        for idx in [layout_idx, control_idx, spawn_idx]:
            if idx < resource_count:
                start = struct.unpack_from("<I", data, 10 + idx * 4)[0]
                end = struct.unpack_from("<I", data, 10 + (idx + 1) * 4)[0] if idx + 1 < resource_count else len(data)
                res_data = data[start:end]
                print(f"  Resource {idx}: offset=0x{start:X}, size={len(res_data)}, first 20 bytes: {res_data[:20].hex()}")


def check_actual_map_count():
    """Check how many valid maps exist"""
    data = Path("game/FDFIELD.DAT").read_bytes()
    resource_count = struct.unpack_from("<I", data, 6)[0]
    
    print(f"\n=== Checking for valid map layouts ===")
    valid_maps = []
    
    for i in range(0, resource_count, 3):
        if i + 2 >= resource_count:
            break
        
        # Check if resource i looks like a map layout
        start = struct.unpack_from("<I", data, 10 + i * 4)[0]
        end = struct.unpack_from("<I", data, 10 + (i + 1) * 4)[0] if i + 1 < resource_count else len(data)
        res_data = data[start:end]
        
        if len(res_data) >= 4:
            w = struct.unpack_from("<H", res_data, 0)[0]
            h = struct.unpack_from("<H", res_data, 2)[0]
            
            if 5 <= w <= 60 and 5 <= h <= 60:
                # Check if size matches
                remaining = len(res_data) - 4
                if remaining == w * h * 4 or remaining == w * h * 2:
                    valid_maps.append({
                        "map_id": i // 3,
                        "layout_idx": i,
                        "width": w,
                        "height": h
                    })
    
    print(f"Found {len(valid_maps)} valid map layouts:")
    for m in valid_maps[:20]:
        print(f"  Map {m['map_id']:2d} (res {m['layout_idx']:3d}): {m['width']}x{m['height']}")
    
    if len(valid_maps) > 20:
        print(f"  ... and {len(valid_maps) - 20} more")


if __name__ == "__main__":
    verify_3_resource_per_map()
    check_actual_map_count()
