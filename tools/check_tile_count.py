#!/usr/bin/env python3
"""Analyze FDSHAP resource 1 tile count correctly"""

import struct

with open("game/FDSHAP.DAT", "rb") as f:
    fdshap = f.read()

# Parse FDSHAP.DAT offset table
resource_count = struct.unpack_from("<I", fdshap, 6)[0]
fdshap_offsets = []
for i in range(resource_count):
    offset = struct.unpack_from("<I", fdshap, 10 + i * 4)[0]
    fdshap_offsets.append(offset)

# Resource 0 and 1
res0_start = fdshap_offsets[0]
res0_end = fdshap_offsets[1]
res0_size = res0_end - res0_start

res1_start = fdshap_offsets[1]
res1_end = fdshap_offsets[2]
res1_size = res1_end - res1_start

print(f"Resource 0: offset={res0_start}, size={res0_size}")
print(f"Resource 1: offset={res1_start}, size={res1_size}")

# Maybe Resource 0 and Resource 1 are a pair (palette + tiles for terrain set 0)
# Let's check if Resource 0 is a palette (768 bytes)
print(f"\nResource 0 first 20 bytes: {fdshap[res0_start:res0_start+20].hex()}")

# If Resource 0 is 1200 bytes, it's NOT just a palette
# Maybe the structure is different

# Let's check if the tile count is stored somewhere
# Or if Resource 1 is structured differently

# According to IDA, the tile resource might have:
# - Header: 4 bytes (width + height)
# - Tile count: 2 bytes?
# - Offset table: variable
# - Compressed tile data: variable

# Let's look at Resource 1 header more carefully
print(f"\nResource 1 header analysis:")
print(f"Bytes 0-1: {struct.unpack_from('<H', fdshap, res1_start)[0]} (tile width)")
print(f"Bytes 2-3: {struct.unpack_from('<H', fdshap, res1_start+2)[0]} (tile height)")
print(f"Bytes 4-5: {struct.unpack_from('<H', fdshap, res1_start+4)[0]} (first tile offset)")

# Check if bytes 6-7 might be tile count
bytes_6_7 = struct.unpack_from("<H", fdshap, res1_start+6)[0]
print(f"Bytes 6-7: {bytes_6_7}")

# Maybe the offset table entries are 2 bytes each (not 4 bytes with zero padding)
# Let's try reading 2-byte entries starting at byte 6
print(f"\nTrying 2-byte offset entries at byte 6:")
offsets_2byte = []
pos = res1_start + 6
for i in range(200):  # Limit
    if pos + 2 > res1_start + res1_size:
        break
    val = struct.unpack_from("<H", fdshap, pos)[0]
    offsets_2byte.append(val)
    pos += 2
    
    # Stop if value exceeds resource size
    if val > res1_size:
        break

print(f"Found {len(offsets_2byte)} 2-byte entries")
print(f"First 20: {offsets_2byte[:20]}")

# Check if these are valid offsets (increasing, within range)
if len(offsets_2byte) > 1:
    valid_offsets = [off for off in offsets_2byte if 0 < off < res1_size]
    print(f"Valid offsets (0 < off < {res1_size}): {len(valid_offsets)}")
    
    # Check if they're increasing
    is_increasing = all(valid_offsets[i] < valid_offsets[i+1] for i in range(min(50, len(valid_offsets)-1)))
    print(f"First 50 are increasing: {is_increasing}")
    
    if is_increasing and len(valid_offsets) > 10:
        print(f"First 10 valid offsets: {valid_offsets[:10]}")
        
        # Check differences
        diffs = [valid_offsets[i+1] - valid_offsets[i] for i in range(min(10, len(valid_offsets)-1))]
        print(f"First 10 differences: {diffs}")
        
        # If differences are consistent (~500-600 bytes per tile), this is correct
        avg_diff = sum(diffs) / len(diffs)
        print(f"Average difference: {avg_diff:.0f} bytes")
        print(f"Expected tile size: 24x24 = 576 pixels, RLE compressed ~300-600 bytes")
