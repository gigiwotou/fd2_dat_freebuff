#!/usr/bin/env python3
"""
Verify Map 0 Part 2 character info structure (19 bytes per unit)

From documentation screenshot:
- faction: 1 byte (00=enemy, 01=NPC, 02=friendly)
- portrait: 1 byte
- race: 1 byte  
- job: 1 byte
- level: 1 byte
- items: 8 bytes
- spells: 4 bytes (not 8!)
- spawn_turn: 1 byte
- drop_item: 2 bytes (not 4!)
Total: 19 bytes

Total control size for map 0: 0x3A9 = 937 bytes
Map info: 3 bytes
Turn events: 0x50 = 80 bytes
Reserved: 0x20 = 32 bytes
Treasure: 0x30 = 48 bytes
Character info: total_units * 19 bytes

Check: 3 + 80 + 32 + 48 + (total_units * 19) = 937?
"""

import struct

filepath = r'd:\testworkspace\fd2_dat_freebuff\bin\FDFIELD.DAT'

with open(filepath, 'rb') as f:
    data = f.read()

# Map 0 control data
control_offset = 0x0A9A
control_size = 0x3A9  # 937 bytes

control_data = data[control_offset:control_offset + control_size]

# Parse header
map_number = control_data[0]
max_friendly = control_data[1]
total_units = control_data[2]

print("Map 0 Control Data Analysis")
print("=" * 60)
print("Map number: {}".format(map_number))
print("Max friendly: {}".format(max_friendly))
print("Total enemies/NPCs: {}".format(total_units))
print()

# Calculate expected sizes
header_size = 3
turn_events_size = 0x50  # 80 bytes
reserved_size = 0x20     # 32 bytes
treasure_size = 0x30     # 48 bytes

char_info_start = header_size + turn_events_size + reserved_size + treasure_size
char_info_size = control_size - char_info_start

print("Size breakdown:")
print("  Header:        {} bytes".format(header_size))
print("  Turn events:   {} bytes (0x{:02X})".format(turn_events_size, turn_events_size))
print("  Reserved:      {} bytes (0x{:02X})".format(reserved_size, reserved_size))
print("  Treasure:      {} bytes (0x{:02X})".format(treasure_size, treasure_size))
print("  Character info starts at offset: 0x{:02X} ({})".format(char_info_start, char_info_start))
print("  Character info size: {} bytes".format(char_info_size))
print()

# Check if 19 bytes per unit fits
if total_units > 0:
    bytes_per_unit_19 = char_info_size // total_units
    remainder_19 = char_info_size % total_units
    print("If 19 bytes per unit:")
    print("  {} * 19 = {} bytes".format(total_units, total_units * 19))
    print("  Actual: {} bytes".format(char_info_size))
    print("  Difference: {} bytes".format(char_info_size - total_units * 19))
    print()

# Check if 26 bytes per unit fits (old assumption)
if total_units > 0:
    bytes_per_unit_26 = char_info_size // total_units
    remainder_26 = char_info_size % total_units
    print("If 26 bytes per unit:")
    print("  {} * 26 = {} bytes".format(total_units, total_units * 26))
    print("  Actual: {} bytes".format(char_info_size))
    print("  Difference: {} bytes".format(char_info_size - total_units * 26))
    print()

# Try different byte sizes
print("Testing different unit sizes:")
for unit_size in range(15, 30):
    expected = header_size + turn_events_size + reserved_size + treasure_size + (total_units * unit_size)
    if expected == control_size:
        print("  [MATCH] {} bytes per unit: {} total bytes".format(unit_size, expected))
    elif abs(expected - control_size) < 10:
        print("  {} bytes per unit: {} total (diff: {})".format(unit_size, expected, control_size - expected))

print()
print("=" * 60)
print("PARSE CHARACTER INFO WITH CORRECT SIZE")
print("=" * 60)
print()

# Find correct unit size
correct_unit_size = None
for unit_size in range(15, 30):
    expected = header_size + turn_events_size + reserved_size + treasure_size + (total_units * unit_size)
    if expected == control_size:
        correct_unit_size = unit_size
        break

if correct_unit_size:
    print("Correct unit size: {} bytes".format(correct_unit_size))
    print()
    
    for i in range(min(5, total_units)):
        offset = char_info_start + i * correct_unit_size
        
        faction = control_data[offset]
        portrait = control_data[offset + 1]
        race = control_data[offset + 2]
        job = control_data[offset + 3]
        level = control_data[offset + 4]
        items = control_data[offset + 5:offset + 13]
        
        # Spells depends on unit size
        if correct_unit_size == 19:
            spells = control_data[offset + 13:offset + 17]  # 4 bytes
            spawn_turn = control_data[offset + 17]
            drop_item = struct.unpack_from('<H', control_data, offset + 18)[0]  # 2 bytes
        elif correct_unit_size == 26:
            spells = control_data[offset + 13:offset + 21]  # 8 bytes
            spawn_turn = control_data[offset + 21]
            drop_item = struct.unpack_from('<I', control_data, offset + 22)[0]  # 4 bytes
        else:
            spells = []
            spawn_turn = 0
            drop_item = 0
        
        faction_str = {0: "Enemy", 1: "NPC", 2: "Friendly"}.get(faction, "Unknown")
        
        print("Char {}:".format(i))
        print("  Faction: {} ({})".format(faction, faction_str))
        print("  Portrait: {}, Race: {}, Job: {}, Level: {}".format(portrait, race, job, level))
        print("  Items: {}".format(' '.join('{:02X}'.format(x) for x in items)))
        print("  Spells: {}".format(' '.join('{:02X}'.format(x) for x in spells)))
        print("  Spawn turn: {}".format(spawn_turn))
        print("  Drop item: 0x{:04X}".format(drop_item))
        print()
else:
    print("[ERROR] Could not determine correct unit size!")
