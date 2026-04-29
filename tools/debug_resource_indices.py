"""Debug: Check which resource index Python export tool actually uses for map 0 control"""
import struct
from pathlib import Path

fdfield_path = Path("game/FDFIELD.DAT")
data = fdfield_path.read_bytes()

# Parse format 1 (count at byte 6)
count = struct.unpack_from('<I', data, 6)[0]
print(f"FDFIELD.DAT count: {count}")

offsets = []
for i in range(count):
    offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(offset)

print(f"Total offsets: {len(offsets)}")
print(f"\nFirst 10 offsets:")
for i in range(10):
    start = offsets[i]
    end = offsets[i+1] if i+1 < len(offsets) else len(data)
    size = end - start
    print(f"  Resource {i}: offset={start}, size={size}")
    if size < 30:
        print(f"    Data: {data[start:start+size].hex(' ')}")
    else:
        print(f"    First 20 bytes: {data[start:start+20].hex(' ')}")

# Now check what export_all_maps.py does
print(f"\n=== export_all_maps.py for map 0 ===")
print(f"layout_idx = map_id * 3 = 0 * 3 = 0")
print(f"control_idx = map_id * 3 + 1 = 0 * 3 + 1 = 1")
print(f"\nSo it reads:")
print(f"  Layout: resource 0")
print(f"  Control: resource 1")

# But wait! The user said indices are 1, 4, 7, 10 (1-based)
# Converting to 0-based: 0, 3, 6, 9...
# So map 0 layout should be resource 0, control should be resource 3+1=4?
print(f"\n=== User's indices (converted to 0-based) ===")
print(f"User said map data is at: 1, 4, 7, 10 (1-based)")
print(f"Convert to 0-based: 0, 3, 6, 9")
print(f"So for map 0:")
print(f"  Layout: resource 0")
print(f"  Control: resource 3")
print(f"  Spawn: resource 6")

# Check resource 1 vs resource 3
print(f"\n=== Comparing resource 1 vs resource 3 ===")
for idx in [1, 3]:
    start = offsets[idx]
    end = offsets[idx+1] if idx+1 < len(offsets) else len(data)
    size = end - start
    print(f"\nResource {idx}: offset={start}, size={size}")
    print(f"  First 20 bytes: {data[start:start+20].hex(' ')}")
    if size >= 3:
        terrain_set_id = data[start]
        print(f"  terrain_set_id (byte 0) = {terrain_set_id} (0x{terrain_set_id:02x})")
    if size >= 6:
        width, height = struct.unpack_from('<HH', data[start:start+4], 0)
        ally_max = data[start+4]
        enemy_total = data[start+5]
        print(f"  If layout: {width}x{height}")
        print(f"  If control: ally_max={ally_max}, enemy_total={enemy_total}")
