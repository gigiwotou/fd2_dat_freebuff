#!/usr/bin/env python3
"""
FD2 FDFIELD.DAT Complete Parser

Parses FDFIELD.DAT file structure based on documentation and IDA verification.

Structure:
- Header: 6 bytes "LLLLLL" (0x4C)
- Per-map index: 12 bytes per map (3x 4-byte offsets)
  - Map layout data offset
  - Map control & treasure data offset
  - Character spawn position data offset

Map layout data:
- Width: 2 bytes (LE)
- Height: 2 bytes (LE)
- Tile data: width*height entries, each 4 bytes
  - Terrain ID: 2 bytes
  - Event/Treasure ID: 2 bytes

Map control & treasure data:
- Map ID: 1 byte
- Max friendly units: 1 byte
- Total enemy/ally units: 1 byte
- Turn events: 16 groups x 3 bytes (FF FF 00 = none)
- Reserved: 16 groups x 2 bytes (FF 00)
- Treasure data: 16 groups x 3 bytes
- Unit info: 26 bytes per unit

Character spawn position data:
- Total characters: 2 bytes
- Position info: 6 bytes per character (X, Y, Portrait ID)
"""

import struct
import json
import argparse
from pathlib import Path


class FDFIELD_Parser:
    def __init__(self, data: bytes):
        self.data = data
        self.magic = data[:6]
        self.map_count = struct.unpack_from("<I", data, 6)[0]
        
    def get_map_offsets(self, map_id: int):
        """Get the 3 offsets for a specific map"""
        if map_id >= self.map_count:
            return None
        
        base = 10 + map_id * 12
        layout_offset = struct.unpack_from("<I", self.data, base)[0]
        control_offset = struct.unpack_from("<I", self.data, base + 4)[0]
        spawn_offset = struct.unpack_from("<I", self.data, base + 8)[0]
        
        return {
            "layout": layout_offset,
            "control": control_offset,
            "spawn": spawn_offset
        }
    
    def parse_map_layout(self, layout_offset: int):
        """Parse map layout data (terrain grid)"""
        pos = layout_offset
        
        # Width and Height
        width = struct.unpack_from("<H", self.data, pos)[0]
        height = struct.unpack_from("<H", self.data, pos + 2)[0]
        pos += 4
        
        # Tile data: width*height entries, each 4 bytes
        tiles = []
        for y in range(height):
            row = []
            for x in range(width):
                terrain_id = struct.unpack_from("<H", self.data, pos)[0]
                event_id = struct.unpack_from("<H", self.data, pos + 2)[0]
                pos += 4
                
                row.append({
                    "terrain": terrain_id,
                    "event": event_id
                })
            tiles.append(row)
        
        return {
            "width": width,
            "height": height,
            "tiles": tiles
        }
    
    def parse_map_control(self, control_offset: int, total_enemy_ally: int):
        """Parse map control & treasure data"""
        pos = control_offset
        
        result = {}
        
        # Basic info
        result["map_id"] = self.data[pos]
        result["max_friendly_units"] = self.data[pos + 1]
        result["total_enemy_ally_units"] = self.data[pos + 2]
        pos += 3
        
        # Turn events: 16 groups x 3 bytes
        result["turn_events"] = []
        for i in range(16):
            turn_num = self.data[pos]
            event_id = struct.unpack_from("<H", self.data, pos + 1)[0]
            pos += 3
            
            if turn_num != 0xFF or event_id != 0xFFFF:
                result["turn_events"].append({
                    "turn": turn_num,
                    "event_id": event_id
                })
        
        # Reserved: 16 groups x 2 bytes (should be FF 00)
        result["reserved"] = []
        for i in range(16):
            val = struct.unpack_from("<H", self.data, pos)[0]
            pos += 2
            result["reserved"].append(val)
        
        # Treasure data: 16 groups x 3 bytes
        result["treasures"] = []
        for i in range(16):
            treasure_type = self.data[pos]  # 00=item, 01=money
            content = struct.unpack_from("<H", self.data, pos + 1)[0]
            pos += 3
            
            if treasure_type != 0xFF:
                result["treasures"].append({
                    "type": "item" if treasure_type == 0 else "money",
                    "content": content
                })
        
        # Unit info: 26 bytes per unit
        result["units"] = []
        for i in range(total_enemy_ally):
            unit = {}
            unit["faction"] = self.data[pos]  # 00=enemy, 01=ally, 02=player
            unit["portrait_id"] = self.data[pos + 1]
            unit["race_id"] = self.data[pos + 2]
            unit["class_id"] = self.data[pos + 3]
            unit["level"] = self.data[pos + 4]
            
            # Items: 8 bytes
            unit["items"] = []
            for j in range(8):
                item_id = self.data[pos + 5 + j]
                if item_id != 0xFF:
                    unit["items"].append(item_id)
            
            # Spells: 8 bytes
            unit["spells"] = []
            for j in range(8):
                spell_id = self.data[pos + 13 + j]
                if spell_id != 0xFF:
                    unit["spells"].append(spell_id)
            
            unit["spawn_turn"] = self.data[pos + 21]
            
            # Drop item: 4 bytes
            drop_type = self.data[pos + 22]
            drop_content = struct.unpack_from("<I", self.data, pos + 22)[0] & 0x00FFFFFF
            unit["drop_item"] = {
                "type": "item" if drop_type == 0 else "money",
                "content": drop_content
            } if drop_type != 0xFF else None
            
            pos += 26
            result["units"].append(unit)
        
        return result
    
    def parse_spawn_positions(self, spawn_offset: int, total_chars: int):
        """Parse character spawn position data"""
        pos = spawn_offset
        
        # Total characters
        total = struct.unpack_from("<H", self.data, pos)[0]
        pos += 2
        
        # Position info: 6 bytes per character
        positions = []
        for i in range(total):
            x = struct.unpack_from("<H", self.data, pos)[0]
            y = struct.unpack_from("<H", self.data, pos + 2)[0]
            portrait_id = struct.unpack_from("<H", self.data, pos + 4)[0]
            pos += 6
            
            positions.append({
                "x": x,
                "y": y,
                "portrait_id": portrait_id,
                "is_player": portrait_id == 0
            })
        
        return {
            "total": total,
            "positions": positions
        }
    
    def parse_map(self, map_id: int):
        """Parse complete map data"""
        offsets = self.get_map_offsets(map_id)
        if not offsets:
            return None
        
        result = {
            "map_id": map_id,
            "offsets": offsets
        }
        
        # Parse layout
        result["layout"] = self.parse_map_layout(offsets["layout"])
        
        # Parse control & treasure
        total_enemy_ally = result["layout"]["height"]  # placeholder
        result["control"] = self.parse_map_control(offsets["control"], 0)
        
        # Update total for parsing
        total_enemy_ally = result["control"]["total_enemy_ally_units"]
        result["control"] = self.parse_map_control(offsets["control"], total_enemy_ally)
        
        # Parse spawn positions
        total_chars = result["control"]["max_friendly_units"] + total_enemy_ally
        result["spawn_positions"] = self.parse_spawn_positions(offsets["spawn"], total_chars)
        
        return result


def export_map_to_editable_json(map_data: dict, output_path: Path):
    """Export map data in editable JSON format"""
    
    editable = {
        "map_id": map_data["map_id"],
        "description": "Map data from FDFIELD.DAT",
        "format": "fdfield_complete",
        "layout": {
            "width": map_data["layout"]["width"],
            "height": map_data["layout"]["height"],
            "tiles": map_data["layout"]["tiles"]
        },
        "control": {
            "map_id": map_data["control"]["map_id"],
            "max_friendly_units": map_data["control"]["max_friendly_units"],
            "total_enemy_ally_units": map_data["control"]["total_enemy_ally_units"],
            "turn_events": map_data["control"]["turn_events"],
            "treasures": map_data["control"]["treasures"],
            "units": map_data["control"]["units"]
        },
        "spawn_positions": map_data["spawn_positions"]
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(editable, indent=2, ensure_ascii=False))
    print(f"Exported to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="FD2 FDFIELD.DAT Parser")
    parser.add_argument("--source", type=Path, default=Path("game"),
                       help="Game directory")
    parser.add_argument("--output", type=Path, default=Path("output/maps"),
                       help="Output directory")
    parser.add_argument("--map", type=int, required=True,
                       help="Map ID to parse (e.g., 97)")
    
    args = parser.parse_args()
    
    # Load FDFIELD.DAT
    fdfield_path = args.source / "FDFIELD.DAT"
    if not fdfield_path.exists():
        print(f"Error: {fdfield_path} not found")
        return 1
    
    data = fdfield_path.read_bytes()
    parser_obj = FDFIELD_Parser(data)
    
    print(f"FDFIELD.DAT: {parser_obj.map_count} maps")
    
    # Parse map
    map_data = parser_obj.parse_map(args.map)
    if not map_data:
        print(f"Error: Map {args.map} not found")
        return 1
    
    print(f"\nMap {args.map}:")
    print(f"  Layout offset: 0x{map_data['offsets']['layout']:X}")
    print(f"  Control offset: 0x{map_data['offsets']['control']:X}")
    print(f"  Spawn offset: 0x{map_data['offsets']['spawn']:X}")
    print(f"  Layout: {map_data['layout']['width']}x{map_data['layout']['height']}")
    print(f"  Max friendly units: {map_data['control']['max_friendly_units']}")
    print(f"  Enemy/ally units: {map_data['control']['total_enemy_ally_units']}")
    print(f"  Turn events: {len(map_data['control']['turn_events'])}")
    print(f"  Treasures: {len(map_data['control']['treasures'])}")
    print(f"  Spawn positions: {map_data['spawn_positions']['total']}")
    
    # Export
    output_path = args.output / f"map_{args.map}_editable.json"
    export_map_to_editable_json(map_data, output_path)
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
