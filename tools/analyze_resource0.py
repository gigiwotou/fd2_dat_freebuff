#!/usr/bin/env python3
"""Analyze FDSHAP Resource 0 structure"""

import struct

with open("game/FDSHAP.DAT", "rb") as f:
    fdshap = f.read()

# Parse offset table
resource_count = struct.unpack_from("<I", fdshap, 6)[0]
offsets = []
for i in range(resource_count):
    offset = struct.unpack_from("<I", fdshap, 10 + i * 4)[0]
    offsets.append(offset)

# Resource 0: 1200 bytes
res0_start = offsets[0]
res0_end = offsets[1]
res0_size = res0_end - res0_start

print(f"Resource 0: offset={res0_start}, size={res0_size}")
print(f"Total bytes: {res0_size}")

# Check different entry sizes
for entry_size in [3, 4, 6, 8, 12]:
    if res0_size % entry_size == 0:
        num_entries = res0_size // entry_size
        print(f"\n  {entry_size}-byte entries: {num_entries} entries")
        
        # Show first 10 entries
        for i in range(min(10, num_entries)):
            entry = fdshap[res0_start + i*entry_size:res0_start + (i+1)*entry_size]
            print(f"    Entry {i}: {entry.hex()} = {list(entry)}")

# The pattern shows: 00 00 04 00 repeating
# This is little-endian 32-bit: 0x00040000
# Byte breakdown: [0, 0, 4, 0]
#   - byte 0: 0
#   - byte 1: 0 or 1 (bit flag?)
#   - byte 2: 4, 5, etc (could be palette index?)
#   - byte 3: 0

# If byte 2 is a palette index or tile reference
print("\n\nAnalyzing byte 2 values (potential palette/tile index):")
byte2_values = []
for i in range(res0_size):
    if i % 4 == 2:  # byte 2 of each 4-byte entry
        val = fdshap[res0_start + i]
        byte2_values.append(val)

from collections import Counter
counter = Counter(byte2_values)
print(f"Unique byte 2 values: {len(counter)}")
print(f"Most common:")
for val, count in counter.most_common(20):
    print(f"  Value {val}: {count} times")

# Check if byte 1 is a flag
print("\n\nAnalyzing byte 1 values (potential flags):")
byte1_values = []
for i in range(res0_size):
    if i % 4 == 1:
        val = fdshap[res0_start + i]
        byte1_values.append(val)

counter1 = Counter(byte1_values)
print(f"Unique byte 1 values: {len(counter1)}")
for val, count in counter1.most_common():
    print(f"  Value {val}: {count} times")

# Let's also check Resource 1's offset table more carefully
res1_start = offsets[1]
res1_end = offsets[2]
res1_size = res1_end - res1_start

print(f"\n\nResource 1: offset={res1_start}, size={res1_size}")

# First 4 bytes: tile dimensions
tile_w = struct.unpack_from("<H", fdshap, res1_start)[0]
tile_h = struct.unpack_from("<H", fdshap, res1_start + 2)[0]
print(f"Tile dimensions: {tile_w}x{tile_h}")

# Check bytes 4-5: could be tile count
tile_count_16 = struct.unpack_from("<H", fdshap, res1_start + 4)[0]
print(f"Bytes 4-5 as uint16: {tile_count_16}")

# The offset table might start at byte 6
# Each entry could be 4 bytes (2 bytes offset + 2 bytes size)
print(f"\nChecking offset table starting at byte 6:")
for i in range(5):
    pos = res1_start + 6 + i * 4
    entry_offset = struct.unpack_from("<H", fdshap, pos)[0]
    entry_size = struct.unpack_from("<H", fdshap, pos + 2)[0]
    print(f"  Entry {i}: offset={entry_offset}, size={entry_size}")

# Or each entry is 6 bytes: 2 bytes offset + 2 bytes size + 2 bytes zero
print(f"\nChecking 6-byte entries starting at byte 4:")
tile_entries = []
pos = res1_start + 4
for i in range(20):
    if pos + 6 > res1_start + res1_size:
        break
    entry_off = struct.unpack_from("<H", fdshap, pos)[0]
    entry_size = struct.unpack_from("<H", fdshap, pos + 2)[0]
    entry_zero = struct.unpack_from("<H", fdshap, pos + 4)[0]
    tile_entries.append((entry_off, entry_size, entry_zero))
    print(f"  Entry {i}: offset={entry_off}, size={entry_size}, zero={entry_zero}")
    pos += 6
    
    if entry_zero != 0:
        break

print(f"\nFound {len(tile_entries)} entries with zero=0")
