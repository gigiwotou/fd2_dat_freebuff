"""Check map 32 control data to verify terrain_set_id"""
import struct

data = open('../game/FDFIELD.DAT', 'rb').read()

# Parse offsets (Format 2)
offsets = []
pos = 6
while pos + 4 <= len(data):
    offset = struct.unpack('<I', data[pos:pos+4])[0]
    if offset > len(data):
        break
    offsets.append(offset)
    pos += 4

print(f"FDFIELD.DAT: {len(offsets)} resources total")

# Map 32 resources
map_id = 32
layout_idx = map_id * 3
control_idx = map_id * 3 + 1

print(f"\n=== Map {map_id} Resources ===")
print(f"Layout index: {layout_idx}, offset={offsets[layout_idx]}")
print(f"Control index: {control_idx}, offset={offsets[control_idx]}")

# Control data
control_start = offsets[control_idx]
control_end = offsets[control_idx + 1] if control_idx + 1 < len(offsets) else len(data)
control_data = data[control_start:control_end]
terrain_set = control_data[0]
ally_max = control_data[1]
enemy_total = control_data[2]

print(f"\n=== Control Data ===")
print(f"Size: {len(control_data)} bytes")
print(f"terrain_set_id: {terrain_set} (0x{terrain_set:02x})")
print(f"ally_max: {ally_max}")
print(f"enemy_total: {enemy_total}")
print(f"tileset index needed: {terrain_set * 2}")
print(f"palette index needed: {terrain_set * 2 + 1}")

# Check FDSHAP.DAT
fdshap_data = open('../game/FDSHAP.DAT', 'rb').read()
fdshap_offsets = []
pos = 6
while pos + 4 <= len(fdshap_data):
    offset = struct.unpack('<I', fdshap_data[pos:pos+4])[0]
    if offset > len(fdshap_data):
        break
    fdshap_offsets.append(offset)
    pos += 4

print(f"\n=== FDSHAP.DAT ===")
print(f"Total resources: {len(fdshap_offsets)}")
print(f"Max tileset index: {len(fdshap_offsets) - 1}")
print(f"Max terrain_set_id possible: {(len(fdshap_offsets) - 1) // 2}")

if terrain_set * 2 >= len(fdshap_offsets):
    print(f"\n*** ERROR: terrain_set_id={terrain_set} requires tileset index {terrain_set * 2}, but FDSHAP.DAT only has {len(fdshap_offsets)} resources! ***")
