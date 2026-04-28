#!/usr/bin/env python3
"""Analyze Resource 0 as tile index mapping table"""

import struct

with open("game/FDSHAP.DAT", "rb") as f:
    fdshap = f.read()

resource_count = struct.unpack_from("<I", fdshap, 6)[0]
offsets = []
for i in range(resource_count):
    offset = struct.unpack_from("<I", fdshap, 10 + i * 4)[0]
    offsets.append(offset)

# Resource 0: 1200 bytes
res0_start = offsets[0]
res0_end = offsets[1]
res0_size = res0_end - res0_start

print(f"Resource 0: start={res0_start}, size={res0_size}")

# Hypothesis 1: First 768 bytes are palette, remaining 432 bytes are tile mapping
palette_data = fdshap[res0_start:res0_start+768]
mapping_data = fdshap[res0_start+768:res0_start+1200]

print(f"\nFirst 10 palette entries:")
for i in range(10):
    r = palette_data[i*3]
    g = palette_data[i*3+1]
    b = palette_data[i*3+2]
    print(f"  Color {i}: RGB=({r},{g},{b})")

# Hypothesis 2: The entire 1200 bytes is a mapping table
# 300 entries × 4 bytes = 1200 bytes
# Each entry maps terrain_id -> tile_index

print(f"\n\n=== Analyzing as 4-byte mapping entries ===")
num_entries = res0_size // 4
print(f"Number of 4-byte entries: {num_entries}")

tile_mapping = []
for i in range(num_entries):
    pos = res0_start + i * 4
    # Format might be: [byte0, byte1, tile_index, byte3]
    # or [tile_index, 0, 0, 0]
    entry = struct.unpack_from("<I", fdshap, pos)[0]
    byte0 = fdshap[pos]
    byte1 = fdshap[pos+1]
    byte2 = fdshap[pos+2]
    byte3 = fdshap[pos+3]
    
    tile_mapping.append({
        "raw": entry,
        "bytes": [byte0, byte1, byte2, byte3],
        "byte2": byte2
    })

print(f"First 20 entries:")
for i in range(20):
    entry = tile_mapping[i]
    print(f"  Entry {i}: raw=0x{entry['raw']:08x}, bytes={entry['bytes']}, byte2={entry['byte2']}")

# Check if byte2 is the tile index
byte2_values = [e['byte2'] for e in tile_mapping]
unique_byte2 = set(byte2_values)
print(f"\nUnique byte2 values: {len(unique_byte2)}")
print(f"Byte2 range: {min(byte2_values)}-{max(byte2_values)}")

# Check the pattern: does byte2 increment sequentially?
print(f"\nByte2 sequence (first 50):")
for i in range(0, 50, 5):
    chunk = byte2_values[i:i+5]
    print(f"  {i:3d}-{i+4:3d}: {chunk}")

# Alternative: maybe the mapping is byte0 + byte1*256 -> tile_index
print(f"\n=== Checking byte0+byte1 as terrain index ===")
for i in range(20):
    entry = tile_mapping[i]
    terrain_idx = entry['bytes'][0] + entry['bytes'][1] * 256
    tile_idx = entry['bytes'][2]
    print(f"  Terrain {terrain_idx} -> Tile {tile_idx}")
