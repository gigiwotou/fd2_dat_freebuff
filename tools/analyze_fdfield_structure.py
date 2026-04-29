"""Analyze FDFIELD.DAT resource structure to understand the layout"""
import struct
from pathlib import Path

fdfield_path = Path("game/FDFIELD.DAT")
data = fdfield_path.read_bytes()

# Parse format 1 (count at byte 6)
count = struct.unpack_from('<I', data, 6)[0]
offsets = []
for i in range(count):
    offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(offset)

print(f"FDFIELD.DAT: {count} resources\n")

# Calculate sizes
sizes = []
for i in range(count):
    start = offsets[i]
    end = offsets[i+1] if i+1 < count else len(data)
    sizes.append(end - start)

# Group into potential map structures
# Try: 3 resources per map (layout, control, spawn)
print("=== Assuming 3 resources per map ===")
print("Map | Resource Indices | Layout Size | Ctrl Size | Spawn Size")
print("-" * 65)

num_maps = count // 3
for map_id in range(min(5, num_maps)):
    layout_idx = map_id * 3
    ctrl_idx = map_id * 3 + 1
    spawn_idx = map_id * 3 + 2
    
    if spawn_idx >= count:
        break
    
    layout_size = sizes[layout_idx]
    ctrl_size = sizes[ctrl_idx]
    spawn_size = sizes[spawn_idx]
    
    # Try to parse layout dimensions
    if layout_size >= 4:
        start = offsets[layout_idx]
        w = data[start] | (data[start+1] << 8)
        h = data[start+2] | (data[start+3] << 8)
    else:
        w, h = 0, 0
    
    # Try to parse terrain_set_id from control
    if ctrl_size >= 1:
        start = offsets[ctrl_idx]
        ts_id = data[start]
    else:
        ts_id = 0
    
    print(f"{map_id:3d} | {layout_idx:3d}, {ctrl_idx:3d}, {spawn_idx:3d}   | {layout_size:5d}      | {ctrl_size:5d}    | {spawn_size:5d}      | {w}x{h} (ts_id={ts_id})")

# Check if resources follow pattern: Layout(size varies), Control(~200 bytes), Spawn(~2000 bytes)
print(f"\n=== Resource sizes pattern ===")
print("Index | Size  | Possible Type")
print("-" * 40)
for i in range(15):
    size = sizes[i]
    if size < 300:
        possible_type = "Control (small, ~200 bytes)"
    elif size < 3000:
        possible_type = "Layout or Spawn"
    else:
        possible_type = "Spawn (large)"
    print(f"{i:5d} | {size:5d} | {possible_type}")
