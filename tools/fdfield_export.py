#!/usr/bin/env python3
"""
FDFIELD.DAT Complete Map Exporter

Exports map data from FDFIELD.DAT using the verified structure:
- Map N layout: resource index 2 + N*3
- Map N control: resource index 3 + N*3
- Map N spawn: resource index 4 + N*3
"""

import struct
import json
import argparse
from pathlib import Path


class FDFIELD_Parser:
    def __init__(self, filepath: Path):
        self.data = filepath.read_bytes()
        self.magic = self.data[:6]
        self.resource_count = struct.unpack_from("<I", self.data, 6)[0]
        
    def get_resource(self, idx: int) -> bytes:
        """Get raw resource data by index"""
        if idx >= self.resource_count:
            return b""
        start = struct.unpack_from("<I", self.data, 10 + idx * 4)[0]
        end = struct.unpack_from("<I", self.data, 10 + (idx + 1) * 4)[0] if idx + 1 < self.resource_count else len(self.data)
        return self.data[start:end]
    
    def get_map_resources(self, map_id: int) -> dict:
        """Get the 3 resource indices for a map"""
        layout_idx = 2 + map_id * 3
        control_idx = 3 + map_id * 3
        spawn_idx = 4 + map_id * 3
        
        return {
            "layout_idx": layout_idx,
            "control_idx": control_idx,
            "spawn_idx": spawn_idx,
            "layout_data": self.get_resource(layout_idx),
            "control_data": self.get_resource(control_idx),
            "spawn_data": self.get_resource(spawn_idx)
        }
    
    def parse_layout(self, data: bytes) -> dict:
        """Parse map layout data"""
        if len(data) < 4:
            return None
        
        width = struct.unpack_from("<H", data, 0)[0]
        height = struct.unpack_from("<H", data, 2)[0]
        
        if width <= 0 or width > 100 or height <= 0 or height > 100:
            return None
        
        tile_data = data[4:]
        expected_size = width * height * 4
        
        if len(tile_data) != expected_size:
            return None
        
        # Parse tiles
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
        
        return {
            "width": width,
            "height": height,
            "tiles": tiles
        }
    
    def parse_control(self, data: bytes) -> dict:
        """Parse map control and treasure data"""
        if len(data) < 3:
            return None
        
        result = {}
        pos = 0
        
        # Basic info
        result["map_id"] = data[pos]
        result["max_friendly_units"] = data[pos + 1]
        result["total_enemy_ally_units"] = data[pos + 2]
        pos += 3
        
        # Turn events: 16 groups x 3 bytes
        result["turn_events"] = []
        for i in range(16):
            if pos + 3 > len(data):
                break
            turn_num = data[pos]
            event_id = struct.unpack_from("<H", data, pos + 1)[0]
            pos += 3
            if turn_num != 0xFF or event_id != 0xFFFF:
                result["turn_events"].append({"turn": turn_num, "event_id": event_id})
        
        # Reserved: 16 groups x 2 bytes
        pos += 32
        
        # Treasure data: 16 groups x 3 bytes
        result["treasures"] = []
        for i in range(16):
            if pos + 3 > len(data):
                break
            treasure_type = data[pos]
            content = struct.unpack_from("<H", data, pos + 1)[0]
            pos += 3
            if treasure_type != 0xFF:
                result["treasures"].append({
                    "type": "item" if treasure_type == 0 else "money",
                    "content": content
                })
        
        # Unit info: 26 bytes per unit
        total_units = result["total_enemy_ally_units"]
        result["units"] = []
        for i in range(total_units):
            if pos + 26 > len(data):
                break
            
            unit = {}
            unit["faction"] = data[pos]
            unit["portrait_id"] = data[pos + 1]
            unit["race_id"] = data[pos + 2]
            unit["class_id"] = data[pos + 3]
            unit["level"] = data[pos + 4]
            
            # Items (8 bytes)
            unit["items"] = []
            for j in range(8):
                item_id = data[pos + 5 + j]
                if item_id != 0xFF:
                    unit["items"].append(item_id)
            
            # Spells (8 bytes)
            unit["spells"] = []
            for j in range(8):
                spell_id = data[pos + 13 + j]
                if spell_id != 0xFF:
                    unit["spells"].append(spell_id)
            
            unit["spawn_turn"] = data[pos + 21]
            
            # Drop item (4 bytes)
            drop_type = data[pos + 22]
            drop_content = struct.unpack_from("<I", data, pos + 22)[0] & 0x00FFFFFF
            unit["drop_item"] = {
                "type": "item" if drop_type == 0 else "money",
                "content": drop_content
            } if drop_type != 0xFF else None
            
            pos += 26
            result["units"].append(unit)
        
        return result
    
    def parse_spawn(self, data: bytes) -> dict:
        """Parse character spawn positions"""
        if len(data) < 2:
            return None
        
        total_chars = struct.unpack_from("<H", data, 0)[0]
        pos = 2
        
        positions = []
        for i in range(total_chars):
            if pos + 6 > len(data):
                break
            
            x = struct.unpack_from("<H", data, pos)[0]
            y = struct.unpack_from("<H", data, pos + 2)[0]
            portrait_id = struct.unpack_from("<H", data, pos + 4)[0]
            pos += 6
            
            positions.append({
                "x": x,
                "y": y,
                "portrait_id": portrait_id,
                "is_player": portrait_id == 0
            })
        
        return {
            "total": total_chars,
            "positions": positions
        }
    
    def parse_map(self, map_id: int) -> dict:
        """Parse complete map data"""
        resources = self.get_map_resources(map_id)
        
        result = {
            "map_id": map_id,
            "resource_indices": {
                "layout": resources["layout_idx"],
                "control": resources["control_idx"],
                "spawn": resources["spawn_idx"]
            }
        }
        
        # Parse layout
        layout = self.parse_layout(resources["layout_data"])
        if layout:
            result["layout"] = layout
        else:
            result["error"] = f"Invalid layout data (resource {resources['layout_idx']})"
            return result
        
        # Parse control
        control = self.parse_control(resources["control_data"])
        if control:
            result["control"] = control
        
        # Parse spawn positions
        spawn = self.parse_spawn(resources["spawn_data"])
        if spawn:
            result["spawn_positions"] = spawn
        
        return result
    
    def get_map_count(self) -> int:
        """Get total number of maps"""
        # Count valid map layouts
        count = 0
        for i in range(200):  # Try up to 200 maps
            resources = self.get_map_resources(i)
            layout = self.parse_layout(resources["layout_data"])
            if layout:
                count = i + 1
            else:
                break
        return count


def main():
    parser = argparse.ArgumentParser(description="FD2 FDFIELD.DAT Map Exporter")
    parser.add_argument("--source", type=Path, default=Path("game"),
                       help="Game directory")
    parser.add_argument("--output", type=Path, default=Path("output/maps"),
                       help="Output directory")
    parser.add_argument("--map", type=int,
                       help="Map ID to export (e.g., 0 for first map)")
    parser.add_argument("--list", action="store_true",
                       help="List all available maps")
    
    args = parser.parse_args()
    
    fdfield_path = args.source / "FDFIELD.DAT"
    if not fdfield_path.exists():
        print(f"Error: {fdfield_path} not found")
        return 1
    
    fdfield = FDFIELD_Parser(fdfield_path)
    
    if args.list:
        # List all maps
        map_count = fdfield.get_map_count()
        print(f"Total maps: {map_count}\n")
        
        for i in range(map_count):
            resources = fdfield.get_map_resources(i)
            layout = fdfield.parse_layout(resources["layout_data"])
            control = fdfield.parse_control(resources["control_data"])
            
            if layout:
                print(f"Map {i:2d}: {layout['width']:2d}x{layout['height']:2d}, "
                      f"resources: {resources['layout_idx']},{resources['control_idx']},{resources['spawn_idx']}")
                
                if control:
                    print(f"         Control: max_friendly={control['max_friendly_units']}, "
                          f"enemy_ally={control['total_enemy_ally_units']}, "
                          f"treasures={len(control['treasures'])}")
        return 0
    
    if args.map is None:
        print("Error: Specify --map <id> or --list")
        return 1
    
    # Parse and export specific map
    map_data = fdfield.parse_map(args.map)
    
    if "error" in map_data:
        print(f"Error: {map_data['error']}")
        return 1
    
    print(f"Map {args.map}:")
    print(f"  Layout: {map_data['layout']['width']}x{map_data['layout']['height']}")
    
    if "control" in map_data:
        control = map_data["control"]
        print(f"  Control: max_friendly={control['max_friendly_units']}, "
              f"enemy_ally={control['total_enemy_ally_units']}, "
              f"turn_events={len(control['turn_events'])}, "
              f"treasures={len(control['treasures'])}")
    
    if "spawn_positions" in map_data:
        spawn = map_data["spawn_positions"]
        print(f"  Spawn positions: {spawn['total']} characters")
    
    # Export
    output_path = args.output / f"map_{args.map}_complete.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(map_data, indent=2, ensure_ascii=False))
    print(f"\nExported to {output_path}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
