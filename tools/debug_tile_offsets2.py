#!/usr/bin/env python3
"""Debug FDSHAP tile offset table parsing"""

import struct

with open("game/FDSHAP.DAT", "rb") as f:
    fdshap = f.read()

# Parse FDSHAP.DAT offset table
resource_count = struct.unpack_from("<I", fdshap, 6)[0]
fdshap_offsets = []
for i in range(resource_count):
    offset = struct.unpack_from("<I", fdshap, 10 + i * 4)[0]
    fdshap_offsets.append(offset)

# Resource 1
res1_start = fdshap_offsets[1]
res1_end = fdshap_offsets[2]
res1_size = res1_end - res1_start

print(f"Resource 1: start={res1_start}, end={res1_end}, size={res1_size}")

# Parse header
tile_w = struct.unpack_from("<H", fdshap, res1_start)[0]
tile_h = struct.unpack_from("<H", fdshap, res1_start + 2)[0]
first_tile_offset = struct.unpack_from("<H", fdshap, res1_start + 4)[0]
print(f"Tile dimensions: {tile_w}x{tile_h}")
print(f"First tile offset: {first_tile_offset}")

# Analyze offset table starting at byte 6
# Let's look at the actual byte pattern
print(f"\nFirst 100 bytes of offset table:")
for i in range(0, 100, 4):
    pos = res1_start + 6 + i
    if pos + 4 > res1_start + res1_size:
        break
    b0 = fdshap[pos]
    b1 = fdshap[pos+1]
    b2 = fdshap[pos+2]
    b3 = fdshap[pos+3]
    val_16 = struct.unpack_from("<H", fdshap, pos)[0]
    zero_16 = struct.unpack_from("<H", fdshap, pos+2)[0]
    print(f"  Offset {6+i}: [{b0:02x} {b1:02x} {b2:02x} {b3:02x}] val16={val_16}, zero16={zero_16}")

# Check if the pattern is:
# [offset_low, offset_high, zero, zero] - 4 bytes per entry
# Or maybe it's a different structure

# Let's also check if first_tile_offset is actually the start of tile data
# and the offset table entries point to individual tiles

# Search for repeating patterns
print(f"\nSearching for offset table pattern...")
# If each entry is 4 bytes: [offset(2), zero(2)]
# Then valid entries have zero == 0

offset_entries = []
pos = res1_start + 6
while pos + 4 <= res1_start + res1_size:
    offset_val = struct.unpack_from("<H", fdshap, pos)[0]
    zero_val = struct.unpack_from("<H", fdshap, pos + 2)[0]
    
    if zero_val == 0:
        offset_entries.append(offset_val)
        if len(offset_entries) >= 20:
            break
    
    pos += 4

print(f"Found {len(offset_entries)} offset entries with zero=0:")
for i, off in enumerate(offset_entries):
    print(f"  Entry {i}: offset={off}")

# Now let's see if these offsets are increasing (pointing to sequential tile data)
if len(offset_entries) > 1:
    diffs = [offset_entries[i+1] - offset_entries[i] for i in range(len(offset_entries)-1)]
    print(f"\nOffset differences: {diffs[:10]}")
    print(f"Average diff: {sum(diffs) / len(diffs)}")
    
    # If diffs are consistent, it's likely a valid offset table
    # If not, the parsing is wrong
