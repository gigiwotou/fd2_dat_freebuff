#!/usr/bin/env python3
"""
Parse FDFIELD.DAT to extract all map data including character positions

FDFIELD.DAT Structure (from documentation):
  1. Header = 6 bytes of 0x4C ('LLLLLL')
  2. Per-map data: 12 bytes per map (3 DWORDs)
     - DWORD[0]: Map tile data offset
     - DWORD[1]: Map control & treasure data offset
     - DWORD[2]: Character spawn position data offset
"""

import struct
import sys
import os
import json

def parse_fdfield(filepath, map_index=32):
    """Parse FDFIELD.DAT for specific map"""
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"FDFIELD.DAT file size: {len(data)} bytes")
    print(f"Parsing map index: {map_index}")
    print()
    
    # Verify magic header
    magic = data[0:6]
    if magic != b'LLLLLL':
        print(f"ERROR: Expected 'LLLLLL' header, got {magic}")
        return None
    
    # Calculate index table offset (12 bytes per map, starting at offset 6)
    idx_offset = 6 + map_index * 12
    
    if idx_offset + 12 > len(data):
        print(f"ERROR: Map index {map_index} out of range")
        max_maps = (len(data) - 6) // 12
        print(f"Maximum map index: {max_maps}")
        return None
    
    # Read 3 offsets
    tile_offset = struct.unpack_from('<I', data, idx_offset)[0]
    control_offset = struct.unpack_from('<I', data, idx_offset + 4)[0]
    char_pos_offset = struct.unpack_from('<I', data, idx_offset + 8)[0]
    
    print(f"Map {map_index} offsets:")
    print(f"  Tile data:      {tile_offset} (0x{tile_offset:06X})")
    print(f"  Control data:   {control_offset} (0x{control_offset:06X})")
    print(f"  Character pos:  {char_pos_offset} (0x{char_pos_offset:06X})")
    print()
    
    result = {
        'map_index': map_index,
        'tile_offset': tile_offset,
        'control_offset': control_offset,
        'char_pos_offset': char_pos_offset,
        'characters': []
    }
    
    # Parse character positions
    if 0 < char_pos_offset < len(data):
        pos_data = data[char_pos_offset:]
        
        # Total character count (2 bytes)
        if len(pos_data) < 2:
            print("ERROR: Character position data too short")
            return result
        
        total_chars = struct.unpack_from('<H', pos_data, 0)[0]
        print(f"Total characters in scene: {total_chars}")
        print()
        print(f"{'ID':<4} {'X':<6} {'Y':<6} {'Portrait':<10} {'Type':<10}")
        print("-" * 40)
        
        for i in range(total_chars):
            offset = 2 + i * 6
            if offset + 6 > len(pos_data):
                break
            
            x = struct.unpack_from('<H', pos_data, offset)[0]
            y = struct.unpack_from('<H', pos_data, offset + 2)[0]
            portrait = struct.unpack_from('<H', pos_data, offset + 4)[0]
            
            char_type = "PLAYER" if portrait == 0 else f"NPC"
            
            print(f"{i:<4} {x:<6} {y:<6} {portrait:<10} {char_type:<10}")
            
            result['characters'].append({
                'index': i,
                'x': x,
                'y': y,
                'portrait_id': portrait,
                'type': 'player' if portrait == 0 else 'npc'
            })
        
        print()
        print(f"Parsed {len(result['characters'])} characters with positions")
    
    return result

def generate_c_code(result, map_index):
    """Generate C code for character positions"""
    print("\n" + "="*60)
    print("C CODE FOR CHARACTER POSITIONS")
    print("="*60)
    
    print(f"\n/* Map {map_index} character positions from FDFIELD.DAT */")
    print(f"static const fd2_map_char_pos_t map_{map_index}_chars[] = {{")
    
    for char in result['characters']:
        if char['x'] == 0 and char['y'] == 0:
            continue  # Skip empty positions
        
        print(f"    {{{char['x']:3d}, {char['y']:3d}, {char['portrait_id']:2d}}},  /* Char {char['index']:2d} */")
    
    print("};")
    print(f"static const int map_{map_index}_char_count = {len([c for c in result['characters'] if c['x'] != 0 or c['y'] != 0])};")

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <FDFIELD.DAT> [map_index]")
        return 1
    
    filepath = sys.argv[1]
    map_index = int(sys.argv[2]) if len(sys.argv) > 2 else 32
    
    if not os.path.exists(filepath):
        print(f"ERROR: File not found: {filepath}")
        return 1
    
    result = parse_fdfield(filepath, map_index)
    if result:
        generate_c_code(result, map_index)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
