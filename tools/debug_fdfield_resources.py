"""Debug FDFIELD.DAT resource structure for map 0"""
import struct
from pathlib import Path

fdfield_path = Path("game/FDFIELD.DAT")
data = fdfield_path.read_bytes()

print(f"FDFIELD.DAT size: {len(data)} bytes")
print(f"Magic (0-6): {data[0:6]}")

# Parse format 2 (no count, offsets from byte 6)
offsets = []
pos = 6
while pos + 4 <= len(data):
    offset = struct.unpack_from('<I', data, pos)[0]
    if offset > len(data):
        break
    offsets.append(offset)
    pos += 4
    if len(offsets) > 500:
        break

print(f"Total resources: {len(offsets)}")

# Map 0 uses resources 0, 1, 2
print("\n=== Map 0 Resources ===")
for i in range(3):
    start = offsets[i]
    end = offsets[i+1] if i+1 < len(offsets) else len(data)
    size = end - start
    print(f"Resource {i}: offset={start}, size={size}")
    print(f"  First 16 bytes: {data[start:start+16].hex(' ')}")

# Layout (resource 0)
layout_start = offsets[0]
layout_end = offsets[1]
layout_data = data[layout_start:layout_end]
width, height = struct.unpack_from('<HH', layout_data, 0)
print(f"\nLayout (resource 0): {width}x{height} = {width*height} tiles")

# Control (resource 1)  
control_start = offsets[1]
control_end = offsets[2]
control_data = data[control_start:control_end]
terrain_set_id = control_data[0]
print(f"\nControl (resource 1): size={len(control_data)}")
print(f"  terrain_set_id = {terrain_set_id}")
print(f"  First 20 bytes: {control_data[:20].hex(' ')}")

# Verify with map 1 (resources 3, 4, 5)
print("\n=== Map 1 Resources ===")
for i in range(3, 6):
    start = offsets[i]
    end = offsets[i+1] if i+1 < len(offsets) else len(data)
    size = end - start
    print(f"Resource {i}: offset={start}, size={size}")
    if i == 4:  # Control for map 1
        ctrl = data[start:start+20]
        ts_id = ctrl[0]
        print(f"  terrain_set_id = {ts_id}")
        print(f"  First 20 bytes: {ctrl.hex(' ')}")
