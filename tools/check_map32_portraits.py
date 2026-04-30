import struct

with open('game/FDFIELD.DAT', 'rb') as f:
    data = f.read()

# Parse index table
count = (len(data) - 6) // 4
offsets = []
for i in range(count):
    pos = 6 + i * 4
    offset = struct.unpack_from('<I', data, pos)[0]
    offsets.append(offset)

# Map 32
map_id = 32
charpos_idx = 3 * map_id + 2

charpos_start = offsets[charpos_idx]
charpos_end = offsets[charpos_idx + 1]
charpos_data = data[charpos_start:charpos_end]

total_chars = struct.unpack_from('<H', charpos_data, 0)[0]
print(f"Map 32: {total_chars} characters")
print()

# Enemy info from control data
control_idx = 3 * map_id + 1
control_start = offsets[control_idx]
control_end = offsets[control_idx + 1]
control_data = data[control_start:control_end]

total_units = control_data[2]  # 30 enemies
print(f"total_units (enemies) = {total_units}")
print()

print("Character positions vs Enemy info:")
print("=" * 80)

for i in range(total_chars):
    offset = 2 + i * 6
    if offset + 6 > len(charpos_data):
        break
    
    x = charpos_data[offset]
    y = charpos_data[offset + 2]
    portrait = charpos_data[offset + 4]
    
    # Get enemy portrait from control data
    if i < total_units:
        enemy_offset = 0x83 + i * 26
        enemy_portrait = control_data[enemy_offset + 1]
        char_type = f"Enemy {i}"
    else:
        enemy_portrait = "N/A"
        char_type = f"Friendly {i - total_units}"
    
    skip = "SKIP (0,0)" if (x == 0 and y == 0) else ""
    match = "MATCH" if (portrait == enemy_portrait) else f"MISMATCH! (pos={portrait}, enemy={enemy_portrait})" if isinstance(enemy_portrait, int) else ""
    
    print(f"Char {i:2d} ({char_type:12s}): pos=({x:2d},{y:2d}), portrait_id={portrait:3d}, enemy_portrait={str(enemy_portrait):5s} {match} {skip}")
