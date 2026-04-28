#!/usr/bin/env python3
"""Analyze FDFIELD.DAT structure - deeper analysis"""

import struct

fdfield_path = "game/FDFIELD.DAT"
with open(fdfield_path, "rb") as f:
    data = f.read()

resource_count = struct.unpack_from("<I", data, 6)[0]
print(f"Resource count: {resource_count}")
print(f"Expected maps (3 resources each): {resource_count // 3}")

# Read all offsets
offsets = []
for i in range(resource_count):
    offset = struct.unpack_from("<I", data, 10 + i * 4)[0]
    offsets.append(offset)

# Calculate resource sizes
print("\n--- Resource sizes and first map analysis ---")
for i in range(min(12, resource_count)):
    start = offsets[i]
    end = offsets[i + 1] if i + 1 < resource_count else len(data)
    size = end - start
    print(f"Resource {i}: start={start}, size={size}")
    
    # Check if this is a layout resource (every 3rd resource starting from 0)
    if i % 3 == 0:
        if size >= 4:
            w = struct.unpack_from("<H", data, start)[0]
            h = struct.unpack_from("<H", data, start + 2)[0]
            print(f"  -> Layout: width={w}, height={h}")
            if 0 < w <= 100 and 0 < h <= 100:
                print(f"  -> VALID MAP {i // 3}")

# Let's check if map 0 (resources 0, 1, 2) is valid
print("\n--- Map 0 detailed analysis ---")
layout_start = offsets[0]
layout_end = offsets[1]
layout_size = layout_end - layout_start

print(f"Layout resource (0): offset={layout_start}, size={layout_size}")
if layout_size >= 4:
    w = struct.unpack_from("<H", data, layout_start)[0]
    h = struct.unpack_from("<H", data, layout_start + 2)[0]
    print(f"  width={w}, height={h}")
    print(f"  Tile data starts at offset {layout_start + 4}")
    print(f"  Tile data size: {layout_size - 4} bytes")
    expected_tile_data = w * h * 4
    print(f"  Expected tile data: {w} * {h} * 4 = {expected_tile_data} bytes")

control_start = offsets[1]
control_end = offsets[2]
control_size = control_end - control_start
print(f"\nControl resource (1): offset={control_start}, size={control_size}")
if control_size >= 3:
    print(f"  First 20 bytes: {data[control_start:control_start+20].hex()}")
    map_id_byte = data[control_start]
    ally_max = data[control_start + 1]
    enemy_total = data[control_start + 2]
    print(f"  Map ID byte: {map_id_byte}, Ally max: {ally_max}, Enemy total: {enemy_total}")

# Check FDSHAP.DAT structure
print("\n--- FDSHAP.DAT analysis ---")
fdshap_path = "game/FDSHAP.DAT"
with open(fdshap_path, "rb") as f:
    fdshap = f.read()

fdshap_magic = fdshap[:6]
fdshap_count = struct.unpack_from("<I", fdshap, 6)[0]
print(f"FDSHAP: magic={fdshap_magic}, resource_count={fdshap_count}")

# First resource (palette)
res0_start = struct.unpack_from("<I", fdshap, 10)[0]
res0_end = struct.unpack_from("<I", fdshap, 14)[0]
res0_size = res0_end - res0_start
print(f"Resource 0 (palette?): offset={res0_start}, size={res0_size}")

# Second resource (tile images?)
res1_start = struct.unpack_from("<I", fdshap, 14)[0]
res1_end = struct.unpack_from("<I", fdshap, 18)[0]
res1_size = res1_end - res1_start
print(f"Resource 1 (tiles?): offset={res1_start}, size={res1_size}")

if res1_size > 4:
    tw = struct.unpack_from("<H", fdshap, res1_start)[0]
    th = struct.unpack_from("<H", fdshap, res1_start + 2)[0]
    print(f"  Tile dimensions: {tw}x{th}")
    
    # Check for offset table
    print(f"  Data at offset 4: {fdshap[res1_start+4:res1_start+20].hex()}")
    
    # Parse offset table (2 bytes per tile)
    tile_offsets = []
    pos = res1_start + 4
    max_pos = res1_start + min(res1_size, 500)
    while pos < max_pos - 2:
        offset_val = struct.unpack_from('<H', fdshap, pos)[0]
        if offset_val > 0 and offset_val < res1_size:
            if not tile_offsets or offset_val > tile_offsets[-1]:
                tile_offsets.append(offset_val)
        pos += 2
    
    print(f"  Found {len(tile_offsets)} tile offsets")
    print(f"  First 10 offsets: {tile_offsets[:10]}")
