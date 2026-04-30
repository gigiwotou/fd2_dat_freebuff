"""Verify format 2 parsing with layout_idx=0 for map 0"""
import struct
from pathlib import Path

fdfield_path = Path("game/FDFIELD.DAT")
data = fdfield_path.read_bytes()

# Format 2: offsets from byte 6, no count
offsets = []
pos = 6
while pos + 4 <= len(data):
    offset = struct.unpack_from('<I', data, pos)[0]
    if offset > pos and offset < len(data):
        offsets.append(offset)
    else:
        break
    pos += 4

print(f"FDFIELD.DAT format 2: {len(offsets)} resources")
print(f"First 10 offsets: {offsets[:10]}")

# Map 0: layout_idx=0, control_idx=1
layout_idx = 0
control_idx = 1

layout_start = offsets[layout_idx]
layout_end = offsets[layout_idx + 1]
control_start = offsets[control_idx]
control_end = offsets[control_idx + 1]

layout_data = data[layout_start:layout_end]
control_data = data[control_start:control_end]

print(f"\nMap 0:")
print(f"  Layout: resource {layout_idx}, offset {layout_start}-{layout_end}, size={len(layout_data)}")
print(f"  Control: resource {control_idx}, offset {control_start}-{control_end}, size={len(control_data)}")

# Parse layout
if len(layout_data) >= 4:
    w = struct.unpack_from('<H', layout_data, 0)[0]
    h = struct.unpack_from('<H', layout_data, 2)[0]
    print(f"  Layout dimensions: {w}x{h}")
    
    if 10 < w < 100 and 10 < h < 100:
        expected_size = 4 + w * h * 4
        print(f"  Expected size: {expected_size}, Actual: {len(layout_data)}")
        
        # Parse terrain IDs
        tile_data = layout_data[4:]
        print(f"\n  First 30 terrain IDs (5 rows x {w} columns):")
        for y in range(min(5, h)):
            row = []
            for x in range(min(w, 30)):
                idx = y * w + x
                b0 = tile_data[idx * 4]
                b1 = tile_data[idx * 4 + 1]
                tid = b0 | ((b1 & 0x03) << 8)
                row.append(f"{tid:3d}")
            print(f"    Row {y}: {' '.join(row)}")
    else:
        print(f"  [ERROR] Invalid dimensions")

# Parse control
if len(control_data) >= 1:
    ts_id = control_data[0]
    print(f"\n  Control: terrain_set_id = {ts_id}")
