"""Verify FDFIELD.DAT format - check byte 6-9"""
import struct
from pathlib import Path

fdfield_path = Path("game/FDFIELD.DAT")
data = fdfield_path.read_bytes()

print(f"FDFIELD.DAT size: {len(data)} bytes")
print(f"Magic (0-6): {data[0:6]}")

# Check byte 6-9 as potential count (format 1)
count_format1 = struct.unpack_from('<I', data, 6)[0]
print(f"\nIf format 1 (byte 6-9 = count):")
print(f"  count = {count_format1}")

# Try parsing as format 1
if count_format1 < 5000 and count_format1 > 0:
    print(f"  Possible valid count")
    # Check if offset table from byte 10 makes sense
    offset0 = struct.unpack_from('<I', data, 10)[0]
    offset1 = struct.unpack_from('<I', data, 14)[0]
    print(f"  offset[0] from byte 10: {offset0}")
    print(f"  offset[1] from byte 14: {offset1}")
    if offset0 < len(data) and offset1 < len(data):
        print(f"  Offsets look valid")
else:
    print(f"  Count looks invalid (too large or zero)")

# Try parsing as format 2 (offsets from byte 6)
print(f"\nIf format 2 (offsets from byte 6):")
offset0_v2 = struct.unpack_from('<I', data, 6)[0]
offset1_v2 = struct.unpack_from('<I', data, 10)[0]
offset2_v2 = struct.unpack_from('<I', data, 14)[0]
print(f"  offset[0] = {offset0_v2}")
print(f"  offset[1] = {offset1_v2}")
print(f"  offset[2] = {offset2_v2}")

# Count format 2 offsets
offsets_v2 = []
pos = 6
while pos + 4 <= len(data):
    offset = struct.unpack_from('<I', data, pos)[0]
    if offset > len(data):
        break
    offsets_v2.append(offset)
    pos += 4

print(f"  Total offsets parsed: {len(offsets_v2)}")

# Now check what the game's fd2_dat.c would parse (format 1)
print(f"\n=== Game's fd2_dat.c (format 1) would parse: ===")
if count_format1 < 5000:
    print(f"  Count: {count_format1}")
    print(f"  First offset (byte 10): {struct.unpack_from('<I', data, 10)[0]}")
else:
    print(f"  Count {count_format1} is invalid, would fail to load")

# Verify with Python export tool output
print(f"\n=== Python export_all_maps.py (format 2) parsed: ===")
print(f"  Total resources: {len(offsets_v2)}")
print(f"  offset[0] (layout map 0): {offsets_v2[0] if len(offsets_v2) > 0 else 'N/A'}")
print(f"  offset[1] (control map 0): {offsets_v2[1] if len(offsets_v2) > 1 else 'N/A'}")
print(f"  offset[2] (spawn map 0): {offsets_v2[2] if len(offsets_v2) > 2 else 'N/A'}")
