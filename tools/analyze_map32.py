#!/usr/bin/env python3
"""
Analyze map 32 from FDFIELD.DAT using IDA-verified parsing logic.
"""
import struct

def main():
    # Load FDFIELD.DAT
    with open('game/FDFIELD.DAT', 'rb') as f:
        data = f.read()
    
    print("=" * 80)
    print("Map 32 Analysis - IDA-Verified Parsing Logic")
    print("=" * 80)
    
    # Parse index table (99 entries)
    count = (len(data) - 6) // 4
    offsets = []
    for i in range(count):
        pos = 6 + i * 4
        offset = struct.unpack_from('<I', data, pos)[0]
        offsets.append(offset)
    
    print(f"\nFDFIELD.DAT: {len(data)} bytes, {count} index entries\n")
    
    # Map 32 indices
    map_id = 32
    layout_idx = 3 * map_id      # 96
    control_idx = 3 * map_id + 1 # 97
    charpos_idx = 3 * map_id + 2 # 98
    
    print(f"Index Calculation (IDA formula):")
    print(f"  layout_idx  = 3 * {map_id} + 0 = {layout_idx}")
    print(f"  control_idx = 3 * {map_id} + 1 = {control_idx}")
    print(f"  charpos_idx = 3 * {map_id} + 2 = {charpos_idx}")
    print()
    
    # Get data ranges
    layout_start = offsets[layout_idx]
    layout_end = offsets[layout_idx + 1]
    layout_data = data[layout_start:layout_end]
    
    control_start = offsets[control_idx]
    control_end = offsets[control_idx + 1]
    control_data = data[control_start:control_end]
    
    charpos_start = offsets[charpos_idx]
    charpos_end = offsets[charpos_idx + 1]
    charpos_data = data[charpos_start:charpos_end]
    
    print(f"Resource Offsets:")
    print(f"  layout:  0x{layout_start:06X} ({layout_start}) -> 0x{layout_end:06X} ({layout_end}), size={layout_end-layout_start}")
    print(f"  control: 0x{control_start:06X} ({control_start}) -> 0x{control_end:06X} ({control_end}), size={control_end-control_start}")
    print(f"  charpos: 0x{charpos_start:06X} ({charpos_start}) -> 0x{charpos_end:06X} ({charpos_end}), size={charpos_end-charpos_start}")
    print()
    
    # Parse layout data
    map_width = struct.unpack_from('<H', layout_data, 0)[0]
    map_height = struct.unpack_from('<H', layout_data, 2)[0]
    
    print(f"Map Dimensions (from layout_data):")
    print(f"  Width:  {map_width} tiles")
    print(f"  Height: {map_height} tiles")
    print(f"  Total tiles: {map_width * map_height}")
    print()
    
    # Parse control data (IDA sub_1088D lines 1098b-10995)
    terrain_set_id = control_data[0]
    max_friendly = control_data[1]  # ::n6
    total_units = control_data[2]   # dword_53BE3
    
    print(f"Control Data (IDA parsing):")
    print(f"  terrain_set_id (byte[0]) = {terrain_set_id}")
    print(f"  max_friendly    (byte[1]) = {max_friendly} (::n6)")
    print(f"  total_units     (byte[2]) = {total_units} (dword_53BE3)")
    print()
    
    # Print first 32 bytes of control data
    print(f"Control Data First 32 bytes (hex):")
    for i in range(0, min(32, len(control_data)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in control_data[i:i+16])
        print(f"  +{i:04x}: {hex_str}")
    print()
    
    # Parse enemy info from control data (offset 0x83)
    char_info_offset = 0x83
    print(f"Enemy/NPC Character Info (from control_data + 0x{char_info_offset:X}):")
    print(f"  Each unit: 26 bytes")
    print(f"  Expected units: {total_units}")
    print()
    
    enemy_count = 0
    for i in range(total_units):
        offset = char_info_offset + i * 26
        if offset + 26 > len(control_data):
            print(f"  Warning: insufficient data for enemy {i}")
            break
        
        faction = control_data[offset]
        portrait = control_data[offset + 1]
        race = control_data[offset + 2]
        job = control_data[offset + 3]
        level = control_data[offset + 4]
        items = control_data[offset + 5:offset + 13]
        spells = control_data[offset + 13:offset + 17]
        spawn_turn = control_data[offset + 17]
        drop_type = control_data[offset + 18]
        drop_content = control_data[offset + 19:offset + 22]
        reserved = control_data[offset + 22:offset + 26]
        
        if i < 10 or faction != 0:  # Show first 10 and any non-enemy
            print(f"  Enemy {i:2d}: faction={faction}, portrait={portrait}, race={race}, "
                  f"job={job}, level={level}, spawn_turn={spawn_turn}")
            print(f"           items: {' '.join(f'{x:02x}' for x in items)}")
            print(f"           spells: {' '.join(f'{x:02x}' for x in spells)}")
            print(f"           drop: type={drop_type}, content={' '.join(f'{x:02x}' for x in drop_content)}")
        
        enemy_count += 1
    
    print(f"  Total enemies parsed: {enemy_count}")
    print()
    
    # Parse character positions
    total_chars = struct.unpack_from('<H', charpos_data, 0)[0]
    
    print(f"Character Position Data:")
    print(f"  Total characters: {total_chars}")
    print(f"  First 16 bytes (hex): {' '.join(f'{b:02x}' for b in charpos_data[:16])}")
    print()
    
    # IDA v4 offset calculation
    v4_offset = 6 * total_units + 2
    
    print(f"Friendly Character Positions (IDA logic):")
    print(f"  v4_offset = 6 * {total_units} + 2 = {v4_offset}")
    print(f"  Reading {max_friendly} friendly characters")
    print()
    
    friendly_count = 0
    for i in range(max_friendly):
        offset = v4_offset + i * 6
        if offset + 6 > len(charpos_data):
            print(f"  Warning: insufficient data for char {i}")
            break
        
        x = charpos_data[offset]
        y = charpos_data[offset + 2]
        portrait = charpos_data[offset + 3]
        unknown1 = charpos_data[offset + 1]
        unknown2 = charpos_data[offset + 4:offset + 6]
        
        print(f"  Friendly {i}: X={x:3d}, Y={y:3d}, portrait={portrait}, "
              f"unknown1=0x{unknown1:02x}, unknown2=[{unknown2[0]:02x}, {unknown2[1]:02x}]")
        friendly_count += 1
    
    print(f"  Total friendly chars: {friendly_count}")
    print()
    
    # Also show enemy positions (first total_units entries)
    print(f"Enemy/NPC Positions (first {total_units} entries):")
    for i in range(min(5, total_units)):  # Show first 5
        offset = 2 + i * 6
        if offset + 6 > len(charpos_data):
            break
        x = charpos_data[offset]
        y = charpos_data[offset + 2]
        portrait = charpos_data[offset + 3]
        print(f"  Enemy {i:2d}: X={x:3d}, Y={y:3d}, portrait={portrait}")
    
    if total_units > 5:
        print(f"  ... ({total_units - 5} more enemies)")
    
    print()
    print("=" * 80)
    print("Summary:")
    print(f"  Map {map_id}: {map_width}x{map_height} tiles, terrain_set={terrain_set_id}")
    print(f"  {enemy_count} enemies/NPCs, {friendly_count} friendly characters")
    print(f"  Character positions: {total_chars} total ({total_units} enemies + {friendly_count} friendly)")
    print("=" * 80)

if __name__ == '__main__':
    main()
