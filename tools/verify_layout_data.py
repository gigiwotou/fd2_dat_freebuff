#!/usr/bin/env python3
"""
Verify Map 0 Part 1 (Layout Data) structure

According to documentation:
- Map dimensions: 24x24 tiles
- Each tile: 4 bytes (AA AA BB BB)
  - AA AA: Block ID (terrain ID)
  - BB BB: Event ID (treasure chest, etc.)

Layout data: 0x196 ~ 0xA99 (0x904 = 2308 bytes)
Header: 4 bytes (width + height)
Tile data: 2304 bytes = 24 * 24 * 4 bytes
"""

import struct

filepath = r'd:\testworkspace\fd2_dat_freebuff\bin\FDFIELD.DAT'

with open(filepath, 'rb') as f:
    data = f.read()

# Map 0 layout data
layout_offset = 0x0196
layout_size = 0x0A9A - 0x0196  # Should be 0x904

print("Map 0 Layout Data (Part 1)")
print("=" * 60)
print("Start offset: 0x{:04X} ({})".format(layout_offset, layout_offset))
print("End offset:   0x{:04X} ({})".format(0x0A99, 0x0A99))
print("Size: 0x{:04X} ({}) bytes".format(layout_size, layout_size))
print()

layout_data = data[layout_offset:layout_offset + layout_size]

# First 4 bytes: width and height
width = struct.unpack_from('<H', layout_data, 0)[0]
height = struct.unpack_from('<H', layout_data, 2)[0]

print("Map Dimensions:")
print("  Width:  {} tiles".format(width))
print("  Height: {} tiles".format(height))
print()

if width == 24 and height == 24:
    print("[OK] Matches documentation (24x24)")
else:
    print("[WARNING] Does not match documentation (expected 24x24)")
print()

# Verify tile data size
expected_tile_size = width * height * 4
actual_tile_size = layout_size - 4

print("Tile Data:")
print("  Expected size: {} bytes ({} * {} * 4)".format(expected_tile_size, width, height))
print("  Actual size:   {} bytes".format(actual_tile_size))

if expected_tile_size == actual_tile_size:
    print("  [OK] Size matches!")
else:
    print("  [ERROR] Size mismatch!")

print()
print("=" * 60)
print("FIRST 10 TILES")
print("=" * 60)
print()

tile_data_offset = 4
print("{:<6} {:<6} {:<10} {:<10}".format("Index", "X,Y", "Terrain", "Event"))
print("-" * 35)

for i in range(min(10, width * height)):
    offset = tile_data_offset + i * 4
    terrain = struct.unpack_from('<H', layout_data, offset)[0]
    event = struct.unpack_from('<H', layout_data, offset + 2)[0]
    
    x = i % width
    y = i // width
    
    print("{:<6} {:<6} {:<10} {:<10}".format(i, "{},{}".format(x, y), terrain, event))

print()
print("=" * 60)
print("VERIFY MAP PIXEL DIMENSIONS")
print("=" * 60)
print()

print("If tile size = 24x24 pixels:")
print("  Map pixel size: {}x{} pixels".format(width * 24, height * 24))
print("  Screen (320x200) would show ~{}x{} tiles".format(320 // 24, 200 // 24))
print()
print("If tile size = 64x64 pixels:")
print("  Map pixel size: {}x{} pixels".format(width * 64, height * 64))
print("  Screen (320x200) would show ~{}x{} tiles".format(320 // 64, 200 // 64))
print()
print("If tile size = 128x128 pixels:")
print("  Map pixel size: {}x{} pixels".format(width * 128, height * 128))
print("  Screen (320x200) would show ~{}x{} tiles".format(320 // 128, 200 // 128))
