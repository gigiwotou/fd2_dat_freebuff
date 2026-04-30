"""Analyze FDFIELD.DAT structure for map 30 (first story map)"""
import struct

data = open('../game/FDFIELD.DAT', 'rb').read()

# Parse offsets (Format 2: no count, offsets from byte 6)
offsets = []
pos = 6
while pos + 4 <= len(data):
    offset = struct.unpack('<I', data[pos:pos+4])[0]
    if offset > len(data):
        break
    offsets.append(offset)
    pos += 4

print(f"FDFIELD.DAT: {len(offsets)} resources total")

# Map 30 resources
map_id = 30
layout_idx = map_id * 3
control_idx = map_id * 3 + 1
spawn_idx = map_id * 3 + 2

print(f"\n=== Map {map_id} Resources ===")
print(f"Layout index: {layout_idx}, offset={offsets[layout_idx]}")
print(f"Control index: {control_idx}, offset={offsets[control_idx]}")
print(f"Spawn index: {spawn_idx}, offset={offsets[spawn_idx]}")

# Layout data
layout_start = offsets[layout_idx]
layout_end = offsets[control_idx]
layout_data = data[layout_start:layout_end]
w = struct.unpack('<H', layout_data[0:2])[0]
h = struct.unpack('<H', layout_data[2:4])[0]
print(f"\n=== Layout Data ===")
print(f"Width: {w}, Height: {h}")
print(f"Layout size: {len(layout_data)} bytes")
print(f"Tile data starts at offset 4, {len(layout_data) - 4} bytes available")
print(f"Expected tiles: {w * h}")
print(f"Actual tiles possible: {(len(layout_data) - 4) // 4}")

# First row terrain IDs
print(f"\nFirst row terrain IDs:")
for x in range(min(w, 24)):
    offset = 4 + x * 4
    b0 = layout_data[offset]
    b1 = layout_data[offset + 1]
    terrain_id = b0 | ((b1 & 0x03) << 8)
    print(f"  [{x}] byte[0]={b0:02x}, byte[1]={b1:02x} → terrain_id={terrain_id}")

# Control data
control_start = offsets[control_idx]
control_end = offsets[spawn_idx]
control_data = data[control_start:control_end]
terrain_set = control_data[0]
ally_max = control_data[1]
enemy_total = control_data[2]
print(f"\n=== Control Data ===")
print(f"Size: {len(control_data)} bytes")
print(f"byte[0] terrain_set_id: {terrain_set}")
print(f"byte[1] ally_max: {ally_max}")
print(f"byte[2] enemy_total: {enemy_total}")
print(f"byte[3:]: {control_data[3:].hex()}")

# Events (16 events × 3 bytes each)
print(f"\nRound Events (16 events, 3 bytes each):")
for i in range(16):
    offset = 3 + i * 3
    event_round = control_data[offset]
    event_id = struct.unpack('<H', control_data[offset+1:offset+3])[0]
    if event_id != 0xFFFF:
        print(f"  Event {i}: round={event_round}, event_id={event_id}")

# Reserved (16 × 2 bytes)
reserved_start = 3 + 16 * 3
reserved_end = reserved_start + 16 * 2
print(f"\nReserved section ({reserved_end - reserved_start} bytes):")
print(f"  {control_data[reserved_start:reserved_end].hex()}")

# Chests (16 chests × 3 bytes)
chests_start = reserved_end
print(f"\nTreasure Chests (16 chests, 3 bytes each):")
for i in range(16):
    offset = chests_start + i * 3
    chest_type = control_data[offset]
    chest_content = struct.unpack('<H', control_data[offset+1:offset+3])[0]
    if chest_type != 0xFF or chest_content != 0xFFFF:
        print(f"  Chest {i}: type={chest_type} (0=items,1=money), content={chest_content}")

# Characters
chars_start = chests_start + 16 * 3
print(f"\nCharacters ({enemy_total} characters, 26 bytes each):")
chars_remaining = len(control_data) - chars_start
print(f"  Remaining control data: {chars_remaining} bytes")
print(f"  Expected for {enemy_total} chars: {enemy_total * 26} bytes")

if enemy_total > 0 and chars_remaining >= enemy_total * 26:
    for i in range(min(enemy_total, 3)):
        offset = chars_start + i * 26
        faction = control_data[offset]
        portrait = control_data[offset + 1]
        race = control_data[offset + 2]
        profession = control_data[offset + 3]
        level = control_data[offset + 4]
        items = control_data[offset + 5:offset + 13]
        spells = control_data[offset + 13:offset + 21]
        spawn_round = control_data[offset + 21]
        drop_type = control_data[offset + 22]
        drop_content = struct.unpack('<I', control_data[offset + 23:offset + 26] + b'\x00')[0] & 0xFFFFFF
        print(f"  Char {i}: faction={faction}, portrait={portrait}, race={race}, profession={profession}, level={level}")
        print(f"    items: {items.hex()}, spells: {spells.hex()}, spawn_round={spawn_round}")
        print(f"    drop: type={drop_type}, content={drop_content}")

# Spawn data
spawn_start = offsets[spawn_idx]
spawn_end = offsets[spawn_idx + 1] if spawn_idx + 1 < len(offsets) else len(data)
spawn_data = data[spawn_start:spawn_end]
char_count = struct.unpack('<H', spawn_data[0:2])[0]
print(f"\n=== Spawn Data ===")
print(f"Character count: {char_count}")
print(f"Spawn data size: {len(spawn_data)} bytes")

print(f"\nSpawn positions:")
for i in range(min(char_count, 10)):
    offset = 2 + i * 6
    x = struct.unpack('<H', spawn_data[offset:offset+2])[0]
    y = struct.unpack('<H', spawn_data[offset+2:offset+4])[0]
    portrait = struct.unpack('<H', spawn_data[offset+4:offset+6])[0]
    print(f"  Char {i}: x={x}, y={y}, portrait={portrait}")
