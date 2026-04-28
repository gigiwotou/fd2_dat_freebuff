#!/usr/bin/env python3
"""
Test correct FDFIELD.DAT parsing based on analysis results
"""

import struct

with open("game/FDFIELD.DAT", "rb") as f:
    data = f.read()

print(f"FDFIELD.DAT size: {len(data)} bytes")
print(f"First 14 bytes: {data[:14].hex()}")

# Based on successful analysis:
# Offset 6-9: Value is 0x00000196 = 406 (little-endian)
# But 406 doesn't work as map count because it exceeds file bounds
# 
# From analyze_fdfield_new.py, we know:
# - Map entry table starts at offset 6
# - Each map entry is 12 bytes (3 x 4-byte offsets)
# - First map layout data starts at offset 406
# 
# So: map_entry_table_size = 406 - 6 = 400 bytes
#     map_count = 400 / 12 = 33.33 (not exact!)
#
# This means either:
# 1. The value 406 at offset 6 is the START of data, not map count
# 2. Map count calculation is different
#
# Let's verify by checking if offsets are sequential

# Read first 50 map entries assuming they start at offset 6
print("\n--- Testing: offset table starts at 6, each entry 4 bytes ---")
offsets_from_6 = []
for i in range(50):
    pos = 6 + i * 4
    if pos + 4 > len(data):
        break
    offset = struct.unpack_from("<I", data, pos)[0]
    offsets_from_6.append(offset)

print(f"First 10 offsets: {offsets_from_6[:10]}")

# Check if offset[0] = 406 points to valid layout data
if offsets_from_6 and offsets_from_6[0] < len(data):
    layout_start = offsets_from_6[0]
    w = struct.unpack_from("<H", data, layout_start)[0]
    h = struct.unpack_from("<H", data, layout_start + 2)[0]
    print(f"Offset[0]={layout_start}: width={w}, height={h}")
    
    # If w=24, h=24, then tile data size = 24*24*4 = 2304 bytes
    # Plus 4 byte header = 2308 bytes
    # Next resource should start at 406 + 2308 = 2714
    expected_next = layout_start + 4 + w * h * 4
    print(f"Expected next offset: {expected_next}")
    
    # Check if offset[1] matches
    if len(offsets_from_6) > 1:
        print(f"Actual offset[1]: {offsets_from_6[1]}")
        if offsets_from_6[1] == expected_next:
            print("MATCH! This confirms the structure")
        else:
            print(f"Difference: {offsets_from_6[1] - expected_next}")

# Now let's understand what 406 means
# Maybe it's not at offset 6, but somewhere else
# Or maybe the structure is:
# Offset 0-5: Magic
# Offset 6-9: Resource count (406 resources)
# Offset 10+: Resource offset table (406 * 4 = 1624 bytes)
# Resources start after offset table

resource_count = struct.unpack_from("<I", data, 6)[0]
print(f"\n--- Testing: resource_count={resource_count} at offset 6 ---")
offset_table_start = 10
offset_table_size = resource_count * 4
print(f"Offset table: starts at {offset_table_start}, size {offset_table_size}")

# Read resource offsets
resource_offsets = []
for i in range(min(resource_count, 50)):
    pos = offset_table_start + i * 4
    if pos + 4 > len(data):
        break
    offset = struct.unpack_from("<I", data, pos)[0]
    resource_offsets.append(offset)

print(f"First 10 resource offsets: {resource_offsets[:10]}")

# Check if resource 0 is layout for map 0
if resource_offsets:
    res0_start = resource_offsets[0]
    if res0_start < len(data) - 4:
        w = struct.unpack_from("<H", data, res0_start)[0]
        h = struct.unpack_from("<H", data, res0_start + 2)[0]
        print(f"Resource 0 at {res0_start}: width={w}, height={h}")
        
        res1_start = resource_offsets[1] if len(resource_offsets) > 1 else len(data)
        res0_size = res1_start - res0_start
        expected_size = 4 + w * h * 4
        print(f"Resource 0 size: {res0_size}, expected: {expected_size}")
