#!/usr/bin/env python3
"""
FDFIELD.DAT Complete Map Parser

Finds all valid map layouts and determines the correct resource mapping.
"""

import struct
import json
from pathlib import Path


def analyze_all_maps():
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
    
    # Find all valid map layouts (4 bytes per tile format)
    valid_maps = []
    
    for i in range(resource_count):
        res_data = get_resource(i)
        if not res_data or len(res_data) < 4:
            continue
        
        width = struct.unpack_from("<H", res_data, 0)[0]
        height = struct.unpack_from("<H", res_data, 2)[0]
        
        # Check reasonable dimensions
        if 5 <= width <= 60 and 5 <= height <= 60:
            remaining = len(res_data) - 4
            
            # Check if it matches 4 bytes per tile
            if remaining == width * height * 4:
                valid_maps.append({
                    "resource_idx": i,
                    "width": width,
                    "height": height,
                    "size": len(res_data),
                    "format": "4_bytes_per_tile"
                })
    
    print(f"Found {len(valid_maps)} valid map layouts (4 bytes/tile format):\n")
    
    # Show all valid maps
    for m in valid_maps[:40]:
        print(f"Resource {m['resource_idx']:3d}: {m['width']:2d}x{m['height']:2d}, size={m['size']:5d}")
    
    if len(valid_maps) > 40:
        print(f"... and {len(valid_maps) - 40} more")
    
    # Try to find pattern
    print(f"\n=== Checking Resource Patterns ===")
    if valid_maps:
        # Check if resources are at regular intervals
        intervals = []
        for i in range(1, len(valid_maps)):
            interval = valid_maps[i]['resource_idx'] - valid_maps[i-1]['resource_idx']
            intervals.append(interval)
        
        print(f"Intervals between map resources: {intervals[:20]}")
        
        # Check for common interval
        from collections import Counter
        interval_counts = Counter(intervals)
        most_common = interval_counts.most_common(3)
        print(f"Most common intervals: {most_common}")
    
    # Check resource 97 specifically
    print(f"\n=== Resource 97 Analysis ===")
    res97 = get_resource(97)
    if res97:
        print(f"Size: {len(res97)} bytes")
        print(f"First 40 bytes hex: {res97[:40].hex()}")
        print(f"First 40 bytes decimal: {list(res97[:40])}")
        
        if len(res97) >= 4:
            w = struct.unpack_from("<H", res97, 0)[0]
            h = struct.unpack_from("<H", res97, 2)[0]
            print(f"\nIf interpreted as WxH: {w}x{h}")
            print(f"Expected size for grid: {4 + w * h * 4} bytes")
            
            # Parse as object list
            tile_data = res97[4:]
            if len(tile_data) % 4 == 0:
                obj_count = len(tile_data) // 4
                print(f"\nAs object list: {obj_count} objects")
                
                # Check if objects follow a pattern
                terrain_values = []
                event_values = []
                for idx in range(obj_count):
                    pos = idx * 4
                    terrain = struct.unpack_from("<H", tile_data, pos)[0]
                    event = struct.unpack_from("<H", tile_data, pos + 2)[0]
                    terrain_values.append(terrain)
                    event_values.append(event)
                
                print(f"Terrain value range: {min(terrain_values)} - {max(terrain_values)}")
                print(f"Event value range: {min(event_values)} - {max(event_values)}")
                
                # Check unique values
                unique_terrain = set(terrain_values)
                unique_events = set(event_values)
                print(f"Unique terrain values: {len(unique_terrain)} - {sorted(unique_terrain)[:20]}")
                print(f"Unique event values: {len(unique_events)} - {sorted(unique_events)[:20]}")


if __name__ == "__main__":
    analyze_all_maps()
