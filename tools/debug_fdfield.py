#!/usr/bin/env python3
"""Debug FDFIELD.DAT parsing"""

import struct

with open("game/FDFIELD.DAT", "rb") as f:
    fdfield = f.read()

print(f"FDFIELD.DAT size: {len(fdfield)}")
print(f"First 14 bytes: {fdfield[:14].hex()}")

# Try different parsing strategies
magic = fdfield[:6]
print(f"Magic: {magic}")

# Value at offset 6 (4 bytes)
val_at_6 = struct.unpack_from("<I", fdfield, 6)[0]
print(f"Value at offset 6 (32-bit): {val_at_6}")

# The offset table might start at 6, not 10
# Let's try: offset 6 is the start of the offset table, not a resource count
# Each resource is 4 bytes (offset value)
# Resource 0 at offset 6 points to the first resource data

# Or: offset 6 is resource count, offset table starts at 10
# Let's verify both

print("\n--- Strategy 1: offset 6 is resource count, table at 10 ---")
rc = struct.unpack_from("<I", fdfield, 6)[0]
print(f"Resource count: {rc}")
if rc > 1000:
    print("  Too many resources, this is probably wrong")

# Read first few offsets from table at 10
offsets_v1 = []
for i in range(5):
    pos = 10 + i * 4
    if pos + 4 > len(fdfield):
        break
    offset = struct.unpack_from("<I", fdfield, pos)[0]
    offsets_v1.append(offset)
    print(f"  Offset table[{i}] at {pos}: {offset}")

# Check if first offset points to valid map data
if offsets_v1:
    first_res = offsets_v1[0]
    if first_res < len(fdfield):
        w = struct.unpack_from("<H", fdfield, first_res)[0]
        h = struct.unpack_from("<H", fdfield, first_res + 2)[0]
        print(f"  Resource 0 at {first_res}: w={w}, h={h}")

print("\n--- Strategy 2: offset table starts at 6, no resource count ---")
offsets_v2 = []
for i in range(10):
    pos = 6 + i * 4
    if pos + 4 > len(fdfield):
        break
    offset = struct.unpack_from("<I", fdfield, pos)[0]
    offsets_v2.append(offset)
    print(f"  Offset[{i}] at {pos}: {offset}")

# Check if first offset points to valid map data
if offsets_v2:
    first_res = offsets_v2[0]
    if first_res < len(fdfield):
        w = struct.unpack_from("<H", fdfield, first_res)[0]
        h = struct.unpack_from("<H", fdfield, first_res + 2)[0]
        print(f"  Resource 0 at {first_res}: w={w}, h={h}")
        if 0 < w <= 100 and 0 < h <= 100:
            print("  -> This looks like a valid map!")
        else:
            print("  -> Invalid dimensions")

# Check if there's a pattern in the offset values
print("\n--- Checking for offset pattern ---")
# If offset table starts at 6, read all valid offsets
all_offsets = []
pos = 6
while pos + 4 <= len(fdfield):
    offset = struct.unpack_from("<I", fdfield, pos)[0]
    if offset > pos and offset < len(fdfield):
        all_offsets.append((pos, offset))
        if len(all_offsets) >= 50:
            break
    pos += 4

print(f"Found {len(all_offsets)} valid offsets:")
for i, (table_pos, data_pos) in enumerate(all_offsets[:20]):
    print(f"  Table[{i}] at {table_pos}: points to {data_pos}")
