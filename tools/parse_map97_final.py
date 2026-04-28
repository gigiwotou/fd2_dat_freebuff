#!/usr/bin/env python3
"""
FDFIELD.DAT Resource 97 Parser

Parses the actual map 97 data from FDFIELD.DAT using standard DAT format.
"""

import struct
from pathlib import Path
import json


def parse_dat_file(data: bytes):
    """Parse standard DAT file format"""
    magic = data[:6]
    resource_count = struct.unpack_from("<I", data, 6)[0]
    
    offsets = []
    for i in range(resource_count):
        offset = struct.unpack_from("<I", data, 10 + i * 4)[0]
        offsets.append(offset)
    
    resources = []
    for i in range(resource_count):
        start = offsets[i]
        end = offsets[i + 1] if i + 1 < resource_count else len(data)
        size = end - start
        resources.append({
            "index": i,
            "offset": start,
            "size": size,
            "data": data[start:end]
        })
    
    return resources


def parse_map_layout(res_data: bytes):
    """Parse map layout data"""
    if len(res_data) < 4:
        return None
    
    width = struct.unpack_from("<H", res_data, 0)[0]
    height = struct.unpack_from("<H", res_data, 2)[0]
    
    print(f"Map dimensions: {width}x{height}")
    print(f"Expected tile data size: {width * height * 4} bytes (if 4 bytes/tile)")
    print(f"Actual remaining data: {len(res_data) - 4} bytes")
    print()
    
    # Parse tile data
    tile_data = res_data[4:]
    
    # Try interpretation 1: Each tile is 4 bytes (terrain_id:2 + event_id:2)
    if width * height * 4 == len(tile_data):
        print("Interpretation 1: 4 bytes per tile (terrain:2 + event:2)")
        tiles = []
        pos = 0
        for y in range(height):
            row = []
            for x in range(width):
                terrain_id = struct.unpack_from("<H", tile_data, pos)[0]
                event_id = struct.unpack_from("<H", tile_data, pos + 2)[0]
                pos += 4
                row.append({"terrain": terrain_id, "event": event_id})
            tiles.append(row)
        
        # Print first few rows
        for y in range(min(3, height)):
            print(f"  Row {y}: ", end="")
            for x in range(min(10, width)):
                t = tiles[y][x]
                print(f"({t['terrain']:3d},{t['event']:3d}) ", end="")
            print()
        
        return {"width": width, "height": height, "tiles": tiles, "format": "4_bytes_per_tile"}
    
    # Try interpretation 2: Each tile is 2 bytes (just terrain or tile index)
    elif width * height * 2 == len(tile_data):
        print("Interpretation 2: 2 bytes per tile (tile index)")
        tiles = []
        pos = 0
        for y in range(height):
            row = []
            for x in range(width):
                tile_idx = struct.unpack_from("<H", tile_data, pos)[0]
                pos += 2
                row.append(tile_idx)
            tiles.append(row)
        
        for y in range(min(3, height)):
            print(f"  Row {y}: ", end="")
            for x in range(min(15, width)):
                print(f"{tiles[y][x]:3d} ", end="")
            print()
        
        return {"width": width, "height": height, "tiles": tiles, "format": "2_bytes_per_tile"}
    
    # Try interpretation 3: It's a list of objects (like previous analysis)
    else:
        print(f"Interpretation 3: List of objects ({len(tile_data)} bytes)")
        print(f"  As 16-bit pairs: {len(tile_data) // 2} pairs")
        print(f"  As 32-bit entries: {len(tile_data) // 4} entries")
        
        # Parse as 16-bit pairs
        pairs = []
        pos = 0
        while pos + 3 < len(tile_data):
            val1 = struct.unpack_from("<H", tile_data, pos)[0]
            val2 = struct.unpack_from("<H", tile_data, pos + 2)[0]
            pos += 4
            pairs.append({"val1": val1, "val2": val2})
        
        print(f"  First 10 pairs:")
        for i, p in enumerate(pairs[:10]):
            print(f"    [{i}] val1={p['val1']:5d} (0x{p['val1']:04X}), val2={p['val2']:5d} (0x{p['val2']:04X})")
        
        return {"width": width, "height": height, "objects": pairs, "format": "object_list"}


def main():
    data = Path("game/FDFIELD.DAT").read_bytes()
    resources = parse_dat_file(data)
    
    print(f"FDFIELD.DAT: {len(resources)} resources\n")
    
    # Find resource 97
    res97 = resources[97]
    print(f"Resource 97:")
    print(f"  Offset: 0x{res97['offset']:X} ({res97['offset']})")
    print(f"  Size: {res97['size']} bytes")
    print(f"  First 20 bytes: {res97['data'][:20].hex()}")
    print()
    
    # Parse as map layout
    layout = parse_map_layout(res97['data'])
    
    # Export to JSON
    if layout:
        export_data = {
            "map_id": 97,
            "description": "Battlefield map - First story level",
            "format": layout["format"],
            "width": layout["width"],
            "height": layout["height"],
        }
        
        if "tiles" in layout:
            export_data["tiles"] = layout["tiles"]
        elif "objects" in layout:
            export_data["objects"] = layout["objects"]
        
        output_path = Path("output/maps/map_97_final.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(export_data, indent=2, ensure_ascii=False))
        print(f"\nExported to {output_path}")


if __name__ == "__main__":
    main()
