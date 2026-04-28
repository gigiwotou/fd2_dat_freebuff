#!/usr/bin/env python3
"""
FDFIELD.DAT Complete Map 97 Parser

Map 97 uses resources 291, 292, 293 (map_id * 3 + 0/1/2)
"""

import struct
import json
from pathlib import Path


def parse_fdfield():
    data = Path("game/FDFIELD.DAT").read_bytes()
    resource_count = struct.unpack_from("<I", data, 6)[0]
    
    print(f"FDFIELD.DAT: {resource_count} resources\n")
    
    # Get map 97 resources
    map_id = 97
    layout_idx = map_id * 3      # 291
    control_idx = map_id * 3 + 1 # 292
    spawn_idx = map_id * 3 + 2   # 293
    
    print(f"Map 97 resources: {layout_idx}, {control_idx}, {spawn_idx}\n")
    
    # Helper to get resource
    def get_resource(idx):
        start = struct.unpack_from("<I", data, 10 + idx * 4)[0]
        end = struct.unpack_from("<I", data, 10 + (idx + 1) * 4)[0] if idx + 1 < resource_count else len(data)
        return data[start:end]
    
    # Parse layout
    layout_data = get_resource(layout_idx)
    print(f"=== Layout Data (Resource {layout_idx}) ===")
    print(f"Size: {len(layout_data)} bytes")
    print(f"First 20 bytes: {layout_data[:20].hex()}\n")
    
    if len(layout_data) >= 4:
        width = struct.unpack_from("<H", layout_data, 0)[0]
        height = struct.unpack_from("<H", layout_data, 2)[0]
        print(f"Dimensions: {width}x{height}")
        print(f"Expected tile data: {width * height * 4} bytes")
        print(f"Actual remaining: {len(layout_data) - 4} bytes\n")
        
        if len(layout_data) - 4 == width * height * 4:
            print("Format: 4 bytes per tile (terrain_id:2 + event_id:2)")
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
                for x in range(min(10, width)):
                    t = tiles[y][x]
                    print(f"({t['terrain']:3d},{t['event']:3d}) ", end="")
                print()
            
            layout = {"width": width, "height": height, "tiles": tiles}
        else:
            print("Format: Not 4 bytes per tile, checking other formats...")
            layout = {"width": width, "height": height}
    else:
        layout = {}
    
    # Parse control & treasure
    control_data = get_resource(control_idx)
    print(f"\n=== Control Data (Resource {control_idx}) ===")
    print(f"Size: {len(control_data)} bytes")
    print(f"First 20 bytes: {control_data[:20].hex()}\n")
    
    control = {}
    if len(control_data) >= 3:
        control["map_id"] = control_data[0]
        control["max_friendly_units"] = control_data[1]
        control["total_enemy_ally_units"] = control_data[2]
        print(f"Map ID: {control['map_id']}")
        print(f"Max friendly units: {control['max_friendly_units']}")
        print(f"Total enemy/ally units: {control['total_enemy_ally_units']}")
        
        pos = 3
        
        # Turn events: 16 groups x 3 bytes
        print(f"\nTurn events:")
        control["turn_events"] = []
        for i in range(16):
            if pos + 3 > len(control_data):
                break
            turn_num = control_data[pos]
            event_id = struct.unpack_from("<H", control_data, pos + 1)[0]
            pos += 3
            if turn_num != 0xFF or event_id != 0xFFFF:
                control["turn_events"].append({"turn": turn_num, "event_id": event_id})
                print(f"  Turn {turn_num}: event {event_id}")
        
        # Reserved: 16 groups x 2 bytes
        pos += 32  # Skip reserved
        control["reserved"] = control_data[pos-32:pos].hex()
        
        # Treasure data: 16 groups x 3 bytes
        print(f"\nTreasures:")
        control["treasures"] = []
        for i in range(16):
            if pos + 3 > len(control_data):
                break
            treasure_type = control_data[pos]
            content = struct.unpack_from("<H", control_data, pos + 1)[0]
            pos += 3
            if treasure_type != 0xFF:
                control["treasures"].append({
                    "type": "item" if treasure_type == 0 else "money",
                    "content": content
                })
                print(f"  {treasure_type}: {content}")
        
        # Unit info: 26 bytes per unit
        total_units = control["total_enemy_ally_units"]
        print(f"\nUnits ({total_units} units):")
        control["units"] = []
        for i in range(total_units):
            if pos + 26 > len(control_data):
                break
            
            unit = {}
            unit["faction"] = control_data[pos]
            unit["portrait_id"] = control_data[pos + 1]
            unit["race_id"] = control_data[pos + 2]
            unit["class_id"] = control_data[pos + 3]
            unit["level"] = control_data[pos + 4]
            
            # Items (8 bytes)
            unit["items"] = []
            for j in range(8):
                item_id = control_data[pos + 5 + j]
                if item_id != 0xFF:
                    unit["items"].append(item_id)
            
            # Spells (8 bytes)
            unit["spells"] = []
            for j in range(8):
                spell_id = control_data[pos + 13 + j]
                if spell_id != 0xFF:
                    unit["spells"].append(spell_id)
            
            unit["spawn_turn"] = control_data[pos + 21]
            
            # Drop item (4 bytes)
            drop_type = control_data[pos + 22]
            drop_content_bytes = control_data[pos + 22:pos + 26]
            drop_content = struct.unpack_from("<I", control_data, pos + 22)[0] & 0x00FFFFFF
            
            unit["drop_item"] = {
                "type": "item" if drop_type == 0 else "money",
                "content": drop_content
            } if drop_type != 0xFF else None
            
            pos += 26
            control["units"].append(unit)
            print(f"  Unit {i}: faction={unit['faction']}, portrait={unit['portrait_id']}, level={unit['level']}, items={unit['items']}, spells={unit['spells']}")
    
    # Parse spawn positions
    spawn_data = get_resource(spawn_idx)
    print(f"\n=== Spawn Positions (Resource {spawn_idx}) ===")
    print(f"Size: {len(spawn_data)} bytes")
    print(f"First 20 bytes: {spawn_data[:20].hex()}\n")
    
    spawn = {}
    if len(spawn_data) >= 2:
        total_chars = struct.unpack_from("<H", spawn_data, 0)[0]
        spawn["total"] = total_chars
        print(f"Total characters: {total_chars}")
        
        spawn["positions"] = []
        pos = 2
        for i in range(total_chars):
            if pos + 6 > len(spawn_data):
                break
            
            x = struct.unpack_from("<H", spawn_data, pos)[0]
            y = struct.unpack_from("<H", spawn_data, pos + 2)[0]
            portrait_id = struct.unpack_from("<H", spawn_data, pos + 4)[0]
            pos += 6
            
            spawn["positions"].append({
                "x": x,
                "y": y,
                "portrait_id": portrait_id,
                "is_player": portrait_id == 0
            })
            print(f"  Char {i}: x={x}, y={y}, portrait={portrait_id}")
    
    # Export to JSON
    export_data = {
        "map_id": 97,
        "description": "Battlefield map - First story level",
        "format": "fdfield_complete",
        "layout": layout,
        "control": control,
        "spawn_positions": spawn
    }
    
    output_path = Path("output/maps/map_97_complete.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(export_data, indent=2, ensure_ascii=False))
    print(f"\n=== Exported to {output_path} ===")


if __name__ == "__main__":
    parse_fdfield()
