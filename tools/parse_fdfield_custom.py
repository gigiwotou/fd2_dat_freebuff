#!/usr/bin/env python3
"""
FDFIELD.DAT Custom Format Analyzer

Per documentation:
- Header: 6 bytes of 0x4C ("LLLLLL")
- Map count: 4 bytes at offset 6 (value = 406)
- Map index table: 12 bytes per map (3 x 4-byte offsets)
  - (1) Map layout data offset
  - (2) Map control & treasure data offset
  - (3) Character spawn position data offset
"""

import struct
import json
from pathlib import Path


def parse_custom_format():
    data = Path("game/FDFIELD.DAT").read_bytes()
    
    print(f"=== FDFIELD.DAT Custom Format Analysis ===")
    print(f"File size: {len(data)} bytes")
    print(f"Magic: {data[:6]}")
    
    # Read map count
    map_count = struct.unpack_from("<I", data, 6)[0]
    print(f"Map count: {map_count}")
    print(f"Index table size: {map_count * 12} bytes")
    print(f"Index table ends at: {10 + map_count * 12}")
    print()
    
    # Show first 10 maps
    print("=== First 10 Maps ===")
    for map_id in range(min(10, map_count)):
        base = 10 + map_id * 12
        layout_offset = struct.unpack_from("<I", data, base)[0]
        control_offset = struct.unpack_from("<I", data, base + 4)[0]
        spawn_offset = struct.unpack_from("<I", data, base + 8)[0]
        
        print(f"Map {map_id:2d}: layout=0x{layout_offset:X} ({layout_offset:6d}), control=0x{control_offset:X} ({control_offset:6d}), spawn=0x{spawn_offset:X} ({spawn_offset:6d})")
    
    # Check map 97
    print(f"\n=== Map 97 ===")
    map_id = 97
    base = 10 + map_id * 12
    
    layout_offset = struct.unpack_from("<I", data, base)[0]
    control_offset = struct.unpack_from("<I", data, base + 4)[0]
    spawn_offset = struct.unpack_from("<I", data, base + 8)[0]
    
    print(f"Index table entry at offset 0x{base:X} ({base}):")
    print(f"  Layout offset:  0x{layout_offset:X} ({layout_offset})")
    print(f"  Control offset: 0x{control_offset:X} ({control_offset})")
    print(f"  Spawn offset:   0x{spawn_offset:X} ({spawn_offset})")
    
    # Parse layout data
    print(f"\n--- Layout Data ---")
    if layout_offset < len(data):
        # Find next offset to get size
        next_layout_base = 10 + (map_id + 1) * 12
        if next_layout_base + 4 <= len(data):
            next_layout_offset = struct.unpack_from("<I", data, next_layout_base)[0]
            layout_size = next_layout_offset - layout_offset if next_layout_offset > layout_offset else 1000
        else:
            layout_size = 1000
        
        # Read layout data
        layout_data = data[layout_offset:layout_offset+layout_size]
        print(f"Size: {len(layout_data)} bytes")
        print(f"First 40 bytes: {layout_data[:40].hex()}")
        
        if len(layout_data) >= 4:
            width = struct.unpack_from("<H", layout_data, 0)[0]
            height = struct.unpack_from("<H", layout_data, 2)[0]
            print(f"Dimensions: {width}x{height}")
            print(f"Expected tile data: {width * height * 4} bytes")
            print(f"Actual remaining: {len(layout_data) - 4} bytes")
            
            if len(layout_data) - 4 == width * height * 4:
                print("Format: 4 bytes per tile (terrain:2 + event:2)")
                
                # Parse tiles
                tiles = []
                pos = 4
                for y in range(height):
                    row = []
                    for x in range(width):
                        terrain_id = struct.unpack_from("<H", layout_data, pos)[0]
                        event_id = struct.unpack_from("<H", layout_data, pos + 2)[0]
                        pos += 4
                        row.append({"terrain": terrain_id, "event": event_id})
                    tiles.append(row)
                
                # Print first 5 rows
                print("\nTile grid (terrain, event):")
                for y in range(min(5, height)):
                    print(f"  Row {y:2d}: ", end="")
                    for x in range(min(15, width)):
                        t = tiles[y][x]
                        print(f"({t['terrain']:3d},{t['event']:3d}) ", end="")
                    print()
                
                layout = {"width": width, "height": height, "tiles": tiles}
            else:
                layout = {"width": width, "height": height}
        else:
            layout = {}
    
    # Parse control data
    print(f"\n--- Control Data ---")
    if control_offset < len(data):
        control_data = data[control_offset:control_offset+200]
        print(f"First 50 bytes: {control_data[:50].hex()}")
        
        if len(control_data) >= 3:
            map_id_byte = control_data[0]
            max_friendly = control_data[1]
            total_enemy_ally = control_data[2]
            print(f"Map ID: {map_id_byte}")
            print(f"Max friendly units: {max_friendly}")
            print(f"Total enemy/ally units: {total_enemy_ally}")
            
            control = {
                "map_id": map_id_byte,
                "max_friendly_units": max_friendly,
                "total_enemy_ally_units": total_enemy_ally
            }
        else:
            control = {}
    
    # Parse spawn data
    print(f"\n--- Spawn Position Data ---")
    if spawn_offset < len(data):
        spawn_data = data[spawn_offset:spawn_offset+100]
        print(f"First 30 bytes: {spawn_data[:30].hex()}")
        
        if len(spawn_data) >= 2:
            total_chars = struct.unpack_from("<H", spawn_data, 0)[0]
            print(f"Total characters: {total_chars}")
            
            spawn = {"total": total_chars}
        else:
            spawn = {}
    
    # Export
    print(f"\n=== Exporting ===")
    # ... export code


if __name__ == "__main__":
    parse_custom_format()
