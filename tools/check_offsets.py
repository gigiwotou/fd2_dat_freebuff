#!/usr/bin/env python3
"""Analyze FDOTHER.DAT offset table to verify sub_111BA logic."""

import struct

with open("game/FDOTHER.DAT", "rb") as f:
    data = f.read()

print(f"FDOTHER.DAT file size: {len(data)} bytes")
print(f"Magic: {data[0:6]}")

# sub_111BA reads from byte 6, no count field
# Each entry is 4 bytes: offset
# For index N: seek to 4*N+6, read offset[N] and offset[N+1]
# size = offset[N+1] - offset[N]

print("\nOffset table (reading from byte 6, 4 bytes per entry):")
print(f"{'Index':>5} {'Offset':>10} {'Next':>10} {'Size':>10}")
print("-" * 50)

for i in range(20):
    pos = 4 * i + 6
    if pos + 8 > len(data):
        break
    offset, next_offset = struct.unpack_from('<II', data, pos)
    size = next_offset - offset
    print(f"{i:5d} {offset:10d} {next_offset:10d} {size:10d}")

# Check what resource 7 should be
print("\n--- Checking resource 7 ---")
pos7 = 4 * 7 + 6
offset7, next7 = struct.unpack_from('<II', data, pos7)
print(f"Index 7: offset={offset7}, next={next7}, size={next7 - offset7}")

# Check if maybe the count is at byte 6
count_at_6 = struct.unpack_from('<I', data, 6)[0]
print(f"\nDWORD at byte 6: {count_at_6}")
print(f"If this is count, offset table starts at byte 10")

# If count is at byte 6, offset table starts at byte 10
if count_at_6 < 10000:  # reasonable resource count
    print(f"\nOffset table starting at byte 10 (with count at byte 6):")
    print(f"{'Index':>5} {'Offset':>10} {'Next':>10} {'Size':>10}")
    print("-" * 50)
    for i in range(20):
        pos = 10 + 4 * i
        if pos + 8 > len(data):
            break
        offset, next_offset = struct.unpack_from('<II', data, pos)
        size = next_offset - offset
        print(f"{i:5d} {offset:10d} {next_offset:10d} {size:10d}")
    
    print(f"\n--- Resource 7 with this scheme ---")
    pos7 = 10 + 4 * 7
    offset7, next7 = struct.unpack_from('<II', data, pos7)
    print(f"Index 7: offset={offset7}, next={next7}, size={next7 - offset7}")
