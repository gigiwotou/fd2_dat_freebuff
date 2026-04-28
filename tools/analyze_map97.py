#!/usr/bin/env python3
"""
FD2 Map 97 Correct Analyzer

Analyzes the actual structure of map 97 from FDFIELD.DAT.
The data appears to be a list of tile placement commands:
- Header: 4 bytes
- Then pairs of 16-bit values: (tile_index, tile_property)
"""

import struct
import json
from pathlib import Path


def parse_map_97(data: bytes):
    """Parse map 97 data structure"""
    
    if len(data) < 4:
        print("Error: Data too small")
        return None
    
    # Header (first 4 bytes)
    header_val1 = struct.unpack_from("<H", data, 0)[0]
    header_val2 = struct.unpack_from("<H", data, 2)[0]
    
    print(f"=== Map 97 Analysis ===")
    print(f"Total size: {len(data)} bytes")
    print(f"Header: 0x{header_val1:04X} ({header_val1}), 0x{header_val2:04X} ({header_val2})")
    print()
    
    # Remaining data is tile commands
    tile_data = data[4:]
    
    # Parse as pairs of 16-bit values
    tile_commands = []
    pos = 0
    
    while pos + 3 < len(tile_data):
        val1 = struct.unpack_from("<H", tile_data, pos)[0]
        val2 = struct.unpack_from("<H", tile_data, pos + 2)[0]
        pos += 4
        
        tile_commands.append({
            "index": len(tile_commands),
            "offset": pos - 4,
            "value1": val1,
            "value2": val2,
            "hex1": f"0x{val1:04X}",
            "hex2": f"0x{val2:04X}"
        })
    
    print(f"Tile commands: {len(tile_commands)}")
    print(f"Remaining bytes: {len(tile_data) - pos}")
    print()
    
    # Analyze the pattern
    print("=== Tile Command Pattern ===")
    print("Index | Offset | Value1 | Value2 | Interpretation")
    print("-" * 60)
    
    for cmd in tile_commands[:30]:  # First 30 commands
        # Try to interpret
        if cmd["value2"] in [0, 5, 6, 8, 11, 12]:
            interpretation = f"Tile {cmd['value1']}, prop={cmd['value2']}"
        elif cmd["value2"] >= 68 and cmd["value2"] <= 69:
            interpretation = f"Tile {cmd['value1']}, layer={cmd['value2'] - 68}"
        else:
            interpretation = f"Tile {cmd['value1']}, val2={cmd['value2']}"
        
        print(f"  {cmd['index']:3d} | 0x{cmd['offset']:04X} | {cmd['hex1']:6s} | {cmd['hex2']:6s} | {interpretation}")
    
    # Check for repeating pattern
    print("\n=== Value2 Distribution ===")
    value2_counts = {}
    for cmd in tile_commands:
        v2 = cmd["value2"]
        value2_counts[v2] = value2_counts.get(v2, 0) + 1
    
    for v2 in sorted(value2_counts.keys()):
        count = value2_counts[v2]
        print(f"  Value2 = {v2:3d} (0x{v2:02X}): {count:3d} times")
    
    # Try to build map grid
    print("\n=== Attempting Map Grid Reconstruction ===")
    
    # Check if this could be a grid with header values as dimensions
    if header_val1 * header_val2 * 4 + 4 == len(data):
        print(f"Grid fits: {header_val1}x{header_val2} = {header_val1 * header_val2} cells")
        print(f"Each cell: 4 bytes (2x 16-bit values)")
        print(f"Total: {header_val1 * header_val2 * 4} + 4 header = {len(data)} bytes")
        
        # Build 2D grid
        grid = []
        for y in range(header_val2):
            row = []
            for x in range(header_val1):
                idx = y * header_val1 + x
                if idx < len(tile_commands):
                    row.append({
                        "tile": tile_commands[idx]["value1"],
                        "prop": tile_commands[idx]["value2"]
                    })
                else:
                    row.append({"tile": 0, "prop": 0})
            grid.append(row)
        
        # Print grid
        print("\n=== Tile Grid (value1 = tile index) ===")
        for y, row in enumerate(grid):
            print(f"Row {y:2d}: ", end="")
            for cell in row:
                print(f"{cell['tile']:3d} ", end="")
            print()
        
        # Export
        export_data = {
            "map_id": 97,
            "description": "Battlefield map - First story level",
            "format": "fdfield_grid",
            "width": header_val1,
            "height": header_val2,
            "grid": grid,
            "raw_data": [b for b in data]
        }
        
        output_path = Path("output/maps/map_97_grid.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(export_data, indent=2))
        print(f"\nExported to {output_path}")
        
    else:
        print(f"Grid does not match: {header_val1}x{header_val2}*4+4 = {header_val1 * header_val2 * 4 + 4} != {len(data)}")
    
    return tile_commands


def main():
    # Read FDFIELD.DAT
    fdfield_path = Path("game/FDFIELD.DAT")
    if not fdfield_path.exists():
        print(f"Error: {fdfield_path} not found")
        return 1
    
    data = fdfield_path.read_bytes()
    
    # Parse DAT file
    if data[:6] != b"LLLLLL":
        print("Error: Invalid DAT magic")
        return 1
    
    resource_count = struct.unpack_from("<I", data, 6)[0]
    print(f"FDFIELD.DAT: {resource_count} resources")
    
    # Get resource 97
    if resource_count <= 97:
        print("Error: Resource 97 not found")
        return 1
    
    offset = struct.unpack_from("<I", data, 10 + 97 * 4)[0]
    next_offset = struct.unpack_from("<I", data, 10 + 98 * 4)[0] if resource_count > 98 else len(data)
    
    map_97_data = data[offset:next_offset]
    print(f"\nMap 97: offset={offset}, size={len(map_97_data)} bytes")
    print(f"Raw data (hex): {map_97_data[:50].hex()}\n")
    
    parse_map_97(map_97_data)
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
