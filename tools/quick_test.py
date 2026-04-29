"""Quick test to verify parse_dat_entries in C matches Python"""
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
        print(f"  Stopping at pos {pos}: offset {offset} > data_size {len(data)}")
        break
    offsets.append(offset)
    pos += 4
    if len(offsets) > 500:
        break

print(f"Total resources parsed: {len(offsets)}")
print(f"First 10 offsets: {offsets[:10]}")

# Check offset[0] and offset[1]
if len(offsets) >= 2:
    print(f"\nResource 0 (layout for map 0):")
    print(f"  Start: {offsets[0]}")
    print(f"  End: {offsets[1]}")
    print(f"  Size: {offsets[1] - offsets[0]}")
    print(f"  First 4 bytes: {data[offsets[0]:offsets[0]+4].hex(' ')}")
    
    if len(offsets) >= 3:
        print(f"\nResource 1 (control for map 0):")
        print(f"  Start: {offsets[1]}")
        print(f"  End: {offsets[2]}")
        print(f"  Size: {offsets[2] - offsets[1]}")
        print(f"  First 4 bytes: {data[offsets[1]:offsets[1]+4].hex(' ')}")
        print(f"  terrain_set_id = {data[offsets[1]]}")
