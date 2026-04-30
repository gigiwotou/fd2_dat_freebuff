#!/usr/bin/env python3
"""Parse FDFIELD.DAT using correct structure from documentation

Structure:
  Bytes 0-5: Magic "LLLLLL" (6 bytes of 0x4C)
  Per map (12 bytes each):
    - DWORD[0]: Map tile data offset
    - DWORD[1]: Map control & treasure data offset
    - DWORD[2]: Character spawn position data offset

Map tile data:
  - Width: 2 bytes
  - Height: 2 bytes
  - Tile data: (width * height) * 4 bytes (two 16-bit values per tile)

Map control & treasure data:
  - Map number: 1 byte
  - Max friendly units: 1 byte
  - Total enemy/friendly units: 1 byte
  - Turn events: 16 groups * 3 bytes
  - Reserved: 16 groups * 2 bytes (FF 00)
  - Treasure data: 16 groups * 3 bytes
  - Character info: (total units) * 26 bytes

Character spawn position data:
  - Total characters: 2 bytes (max_friendly + total_units)
  - Position info: (total characters) * 6 bytes (3 * 16-bit values)
    - X coordinate: 2 bytes
    - Y coordinate: 2 bytes
    - Portrait ID: 2 bytes (00 = player character)
"""

import struct
import sys
import os

def parse_fdfield_map(filepath, map_index):
    """Parse FDFIELD.DAT for specific map"""
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"FDFIELD.DAT file size: {len(data)} bytes")
    print(f"Parsing map index: {map_index}")
    print()
    
    # Check magic header
    magic = data[0:6]
    if magic == b'LLLLLL':
        print("Magic header: 'LLLLLL' (correct)")
    else:
        print(f"Magic header: {magic.hex()}")
    print()
    
    # Calculate index table offset (12 bytes per map)
    idx_offset = 6 + map_index * 12
    print(f"Map {map_index} index table offset: {idx_offset} (0x{idx_offset:X})")
    
    if idx_offset + 12 > len(data):
        print(f"  ERROR: Index offset out of range")
        return
    
    # Read 3 DWORDs
    tile_data_offset = struct.unpack_from('<I', data, idx_offset)[0]
    control_data_offset = struct.unpack_from('<I', data, idx_offset + 4)[0]
    char_pos_offset = struct.unpack_from('<I', data, idx_offset + 8)[0]
    
    print(f"  Tile data offset:      {tile_data_offset} (0x{tile_data_offset:X})")
    print(f"  Control data offset:   {control_data_offset} (0x{control_data_offset:X})")
    print(f"  Character pos offset:  {char_pos_offset} (0x{char_pos_offset:X})")
    print()
    
    # Parse map control data (to get character counts)
    if 0 < control_data_offset < len(data):
        print("=" * 60)
        print("MAP CONTROL DATA")
        print("=" * 60)
        
        ctrl_data = data[control_data_offset:]
        
        map_number = ctrl_data[0]
        max_friendly = ctrl_data[1]
        total_units = ctrl_data[2]
        
        print(f"  Map number:          {map_number}")
        print(f"  Max friendly units:  {max_friendly}")
        print(f"  Total enemy/friendly: {total_units}")
        
        total_chars = max_friendly + total_units
        print(f"  Total characters:    {total_chars}")
        print()
        
        # Turn events (16 groups * 3 bytes)
        print("  Turn events (16 groups):")
        for i in range(16):
            offset = 3 + i * 3
            turn = ctrl_data[offset]
            event_id = struct.unpack_from('<H', ctrl_data, offset + 1)[0]
            if turn != 0xFF or event_id != 0xFFFF:
                print(f"    Group {i:2d}: turn={turn:3d}, event={event_id}")
        print()
        
        # Treasure data (16 groups * 3 bytes)
        treasure_offset = 3 + 16 * 3 + 16 * 2  # after turn events and reserved
        print("  Treasure data (16 groups):")
        for i in range(16):
            offset = treasure_offset + i * 3
            type_byte = ctrl_data[offset]
            content = struct.unpack_from('<H', ctrl_data, offset + 1)[0]
            if type_byte != 0xFF:
                type_str = "item" if type_byte == 0 else "money"
                print(f"    Group {i:2d}: type={type_str}, content={content}")
        print()
        
        # Character info (total_units * 26 bytes)
        char_info_offset = treasure_offset + 16 * 3
        print(f"  Character info ({total_units} units * 26 bytes):")
        print(f"    Start offset: {control_data_offset + char_info_offset}")
        
        for i in range(total_units):
            offset = char_info_offset + i * 26
            if offset + 26 > len(ctrl_data):
                break
            
            faction = ctrl_data[offset]
            portrait = ctrl_data[offset + 1]
            race = ctrl_data[offset + 2]
            job = ctrl_data[offset + 3]
            level = ctrl_data[offset + 4]
            items = ctrl_data[offset + 5:offset + 13]
            spells = ctrl_data[offset + 13:offset + 21]
            spawn_turn = ctrl_data[offset + 21]
            drop_type = ctrl_data[offset + 22]
            drop_content = struct.unpack_from('<I', ctrl_data, offset + 22)[0] & 0xFFFFFF
            
            faction_str = {0: "enemy", 1: "friendly", 2: "player"}.get(faction, f"unknown({faction})")
            
            print(f"    Unit {i:2d}: faction={faction_str}, portrait={portrait:2d}, race={race:2d}, job={job:2d}, level={level:2d}")
            print(f"             spawn_turn={spawn_turn:2d}, items=[{', '.join(f'{x:02X}' for x in items)}]")
        
        print()
    
    # Parse character spawn positions
    if 0 < char_pos_offset < len(data):
        print("=" * 60)
        print("CHARACTER SPAWN POSITIONS")
        print("=" * 60)
        
        pos_data = data[char_pos_offset:]
        total_pos = struct.unpack_from('<H', pos_data, 0)[0]
        
        print(f"  Total characters: {total_pos}")
        print()
        
        for i in range(total_pos):
            offset = 2 + i * 6
            if offset + 6 > len(pos_data):
                break
            
            x = struct.unpack_from('<H', pos_data, offset)[0]
            y = struct.unpack_from('<H', pos_data, offset + 2)[0]
            portrait = struct.unpack_from('<H', pos_data, offset + 4)[0]
            
            char_type = "player" if portrait == 0 else f"NPC(portrait={portrait})"
            print(f"  Character {i:2d}: X={x:3d}, Y={y:3d}, {char_type}")
        
        print()
        
        # These are the positions we need to draw sprites at!
        print("SPRITE POSITIONS FOR MAP RENDERING:")
        for i in range(total_pos):
            offset = 2 + i * 6
            if offset + 6 > len(pos_data):
                break
            
            x = struct.unpack_from('<H', pos_data, offset)[0]
            y = struct.unpack_from('<H', pos_data, offset + 2)[0]
            portrait = struct.unpack_from('<H', pos_data, offset + 4)[0]
            
            print(f"  Draw sprite at map tile ({x}, {y}), portrait={portrait}")

def main():
    fdfield_path = sys.argv[1] if len(sys.argv) > 1 else 'FDFIELD.DAT'
    map_index = int(sys.argv[2]) if len(sys.argv) > 2 else 32
    
    if not os.path.exists(fdfield_path):
        print(f"Error: {fdfield_path} not found")
        return 1
    
    parse_fdfield_map(fdfield_path, map_index)
    return 0

if __name__ == '__main__':
    sys.exit(main())
