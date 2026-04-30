#!/usr/bin/env python3
"""Parse FDFIELD.DAT using correct structure from documentation

FDFIELD.DAT Structure:
  Bytes 0-5: Magic "LLLLLL" (6 bytes of 0x4C)
  Per map (12 bytes each):
    - DWORD[0]: Map tile data offset
    - DWORD[1]: Map control & treasure data offset  
    - DWORD[2]: Character spawn position data offset
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
    
    # Calculate index table offset (12 bytes per map, starting at offset 6)
    idx_offset = 6 + map_index * 12
    print(f"Map {map_index} index table offset: {idx_offset} (0x{idx_offset:X})")
    
    if idx_offset + 12 > len(data):
        print(f"  ERROR: Index offset out of range (file size: {len(data)})")
        # Try to find valid map indices
        max_maps = (len(data) - 6) // 12
        print(f"  Maximum map index possible: {max_maps}")
        return
    
    # Read 3 DWORDs
    tile_data_offset = struct.unpack_from('<I', data, idx_offset)[0]
    control_data_offset = struct.unpack_from('<I', data, idx_offset + 4)[0]
    char_pos_offset = struct.unpack_from('<I', data, idx_offset + 8)[0]
    
    print(f"  Tile data offset:      {tile_data_offset} (0x{tile_data_offset:X})")
    print(f"  Control data offset:   {control_data_offset} (0x{control_data_offset:X})")
    print(f"  Character pos offset:  {char_pos_offset} (0x{char_pos_offset:X})")
    print()
    
    # Parse character spawn positions
    if char_pos_offset > 0 and char_pos_offset < len(data):
        print("=" * 60)
        print("CHARACTER SPAWN POSITIONS")
        print("=" * 60)
        
        pos_data = data[char_pos_offset:]
        total_pos = struct.unpack_from('<H', pos_data, 0)[0]
        
        print(f"  Total characters: {total_pos}")
        print()
        
        # C code output format
        print(f"  // C code array for map {map_index}:")
        print(f"  fd2_map_char_pos_t map_{map_index}_chars[] = {{")
        
        for i in range(total_pos):
            offset = 2 + i * 6
            if offset + 6 > len(pos_data):
                break
            
            x = struct.unpack_from('<H', pos_data, offset)[0]
            y = struct.unpack_from('<H', pos_data, offset + 2)[0]
            portrait = struct.unpack_from('<H', pos_data, offset + 4)[0]
            
            char_type = "player" if portrait == 0 else f"NPC(portrait={portrait})"
            print(f"    Char {i:2d}: X={x:3d}, Y={y:3d}, {char_type}")
            
            if i < 50:  # Limit output for C array
                print(f"    {{{x}, {y}, {portrait}}},")
        
        print(f"  }};")
        print()
    else:
        print(f"  ERROR: Character position offset invalid: {char_pos_offset}")

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
