#!/usr/bin/env python3
"""
Verify Map 0 Part 2 (Control Data) structure according to documentation

Structure:
- Bytes 0-2: Map info (map_number, max_friendly, total_units)
- Next 0x50 bytes (80 bytes): Turn events (16 groups * 3 bytes each)
- Next 0x20 bytes (32 bytes): Reserved (16 groups * 2 bytes, FF 00)
- Next 0x30 bytes (48 bytes): Treasure data (16 groups * 3 bytes)
- Next: Character info (19 bytes per enemy/NPC)

Total control size for map 0: 0x3A9 = 937 bytes
Map number should be 0, max_friendly should be some value, total_units = enemy count
"""

import struct

filepath = r'd:\testworkspace\fd2_dat_freebuff\bin\FDFIELD.DAT'

with open(filepath, 'rb') as f:
    data = f.read()

# Map 0 control data at 0x0A9A
control_offset = 0x0A9A
control_size = 0x3A9

print("Map 0 Control Data (Part 2)")
print("=" * 60)
print("Start offset: 0x{:04X} ({})".format(control_offset, control_offset))
print("Size: 0x{:04X} ({}) bytes".format(control_size, control_size))
print()

control_data = data[control_offset:control_offset + control_size]

# First 3 bytes: map info
map_number = control_data[0]
max_friendly = control_data[1]
total_units = control_data[2]

print("Map Info (first 3 bytes):")
print("  Map number:      {}".format(map_number))
print("  Max friendly:    {}".format(max_friendly))
print("  Total enemies:   {}".format(total_units))
print()

# Next 0x50 bytes: Turn events (16 * 3 bytes)
turn_events_offset = 3
print("Turn Events (16 groups * 3 bytes, starting at offset 3):")
print("{:<6} {:<8} {:<8}".format("Group", "Turn", "Event"))
print("-" * 25)

for i in range(16):
    offset = turn_events_offset + i * 3
    turn = control_data[offset]
    event = struct.unpack_from('<H', control_data, offset + 1)[0]
    print("{:<6} {:<8} {:<8}".format(i, turn, event))

print()

# Next 0x20 bytes: Reserved (16 * 2 bytes)
reserved_offset = 3 + 0x50
print("Reserved Data (16 groups * 2 bytes, starting at offset 0x53):")
for i in range(16):
    offset = reserved_offset + i * 2
    val = struct.unpack_from('<H', control_data, offset)[0]
    if val != 0xFF00:
        print("  Group {}: 0x{:04X} (expected FF 00)".format(i, val))

print("  (All should be 0xFF00)")
print()

# Next 0x30 bytes: Treasure data (16 * 3 bytes)
treasure_offset = reserved_offset + 0x20
print("Treasure Data (16 groups * 3 bytes, starting at offset 0x73):")
print("{:<6} {:<8} {:<12} {:<12}".format("Group", "Type", "Content", "Description"))
print("-" * 45)

for i in range(16):
    offset = treasure_offset + i * 3
    box_type = control_data[offset]
    content = struct.unpack_from('<H', control_data, offset + 1)[0]
    
    if box_type == 0x00:
        desc = "Item #{}".format(content)
    elif box_type == 0x01:
        desc = "Gold: {}".format(content)
    elif box_type == 0xFF:
        desc = "(empty)"
        content = 0
    else:
        desc = "Unknown type {}".format(box_type)
    
    if box_type != 0xFF:
        print("{:<6} {:<8} {:<12} {:<12}".format(i, box_type, content, desc))

print()

# Character info starts after treasure data
char_info_offset = treasure_offset + 0x30
print("Character Info (19 bytes per unit, starting at offset 0xA3):")
print("Total enemy/NPC units: {}".format(total_units))
print()

# Parse character info
for i in range(min(5, total_units)):
    offset = char_info_offset + i * 19
    if offset + 19 > len(control_data):
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
    drop_content = struct.unpack_from('<H', control_data, offset + 19)[0] if offset + 21 <= len(control_data) else 0
    
    faction_str = {0: "Enemy", 1: "NPC", 2: "Friendly"}.get(faction, "Unknown")
    
    print("Char {}:".format(i))
    print("  Faction: {} ({})".format(faction, faction_str))
    print("  Portrait: {}, Race: {}, Job: {}, Level: {}".format(portrait, race, job, level))
    print("  Items: {}".format(' '.join('{:02X}'.format(x) for x in items)))
    print("  Spells: {}".format(' '.join('{:02X}'.format(x) for x in spells)))
    print("  Spawn turn: {}".format(spawn_turn))
    print("  Drop: type={}, content={}".format(drop_type, drop_content))
    print()
