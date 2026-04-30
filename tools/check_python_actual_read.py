"""See what Python export tool actually extracts for map 0"""
import struct
from pathlib import Path

fdfield_path = Path("game/FDFIELD.DAT")
data = fdfield_path.read_bytes()

# Python tool uses format 2 parsing
offsets_v2 = []
pos = 6
while pos + 4 <= len(data):
    offset = struct.unpack_from('<I', data, pos)[0]
    if offset > pos and offset < len(data):
        offsets_v2.append(offset)
    else:
        break
    pos += 4

print(f"Python format 2 offsets: {len(offsets_v2)}")
print(f"First 10: {offsets_v2[:10]}")

# Python tool: layout_res_idx=0, control_res_idx=1
layout_start = offsets_v2[0]
layout_end = offsets_v2[1]
control_start = offsets_v2[1]
control_end = offsets_v2[2]

layout_data = data[layout_start:layout_end]
control_data = data[control_start:control_end]

print(f"\nPython reads:")
print(f"  layout: resource 0, offset {layout_start}-{layout_end}, size={len(layout_data)}")
print(f"  control: resource 1, offset {control_start}-{control_end}, size={len(control_data)}")

# Parse layout dimensions
if len(layout_data) >= 4:
    w = struct.unpack_from('<H', layout_data, 0)[0]
    h = struct.unpack_from('<H', layout_data, 2)[0]
    print(f"  Parsed layout: {w}x{h}")
    
    if 10 < w < 100 and 10 < h < 100:
        expected_size = 4 + w * h * 4
        print(f"  Expected size: {expected_size}, Actual: {len(layout_data)}")
        if abs(len(layout_data) - expected_size) < 50:
            print(f"  [OK] Valid layout!")
            
            # Extract first 20 terrain IDs
            tile_data = layout_data[4:]
            print(f"  First 20 terrain IDs:")
            for i in range(min(20, w * h)):
                b0 = tile_data[i * 4]
                b1 = tile_data[i * 4 + 1]
                tid = b0 | ((b1 & 0x03) << 8)
                print(f"    [{i:2d}] {b0:02x} {b1:02x} -> {tid:3d}", end="")
                if (i + 1) % w == 0:
                    print()
        else:
            print(f"  [ERROR] Size mismatch")
    else:
        print(f"  [ERROR] Invalid dimensions")

# Check what's at offset 410 (Python's layout offset)
print(f"\n=== Byte-level check of offset 410 ===")
offset410_data = data[410:450]
print(f"First 40 bytes at offset 410: {offset410_data.hex(' ')}")

w = offset410_data[0] | (offset410_data[1] << 8)
h = offset410_data[2] | (offset410_data[3] << 8)
print(f"Bytes 0-3: {w}x{h}")

# Check if there's a "LLLLLL" magic or other marker
print(f"\n=== Checking for markers around offset 410 ===")
for i in range(-20, 20):
    pos = 410 + i
    if 0 <= pos < len(data) and data[pos:pos+6] == b'LLLLLL':
        print(f"  Found 'LLLLLL' at offset {pos}")
