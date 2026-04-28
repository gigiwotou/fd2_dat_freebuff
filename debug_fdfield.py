#!/usr/bin/env python3
"""Verify Map 97 using IDA's sub_111BA loading logic."""

import struct

data = open('game/FDFIELD.DAT', 'rb').read()

def load_resource(data: bytes, index: int) -> bytes:
    """Exactly mimic IDA sub_111BA behavior."""
    pos = 4 * index + 6
    start, end = struct.unpack_from("<II", data, pos)
    size = end - start
    return data[start:start + size]

# Map 97 uses resources: 3*97=291, 292, 293
map_id = 97
layout_res = load_resource(data, 3 * map_id)
control_res = load_resource(data, 3 * map_id + 1)
spawn_res = load_resource(data, 3 * map_id + 2)

print(f"Map {map_id} resources:")
print(f"  Layout resource (index {3*map_id}): {len(layout_res)} bytes")
print(f"  Control resource (index {3*map_id+1}): {len(control_res)} bytes")
print(f"  Spawn resource (index {3*map_id+2}): {len(spawn_res)} bytes")

# Parse layout: width (2 bytes) + height (2 bytes) + tile data
if len(layout_res) >= 4:
    width = struct.unpack_from("<H", layout_res, 0)[0]
    height = struct.unpack_from("<H", layout_res, 2)[0]
    print(f"\nLayout data:")
    print(f"  Width: {width}")
    print(f"  Height: {height}")
    print(f"  Expected tile data size: {width * height * 4} bytes")
    print(f"  Actual layout size (minus header): {len(layout_res) - 4} bytes")
    
    if len(layout_res) - 4 == width * height * 4:
        print(f"  ✓ Size matches!")
    else:
        print(f"  ✗ Size mismatch!")

# Parse control: map_id (1 byte) + max_friendly (1 byte) + total_enemy_ally (1 byte) + ...
if len(control_res) >= 3:
    print(f"\nControl data:")
    print(f"  Map ID: {control_res[0]}")
    print(f"  Max friendly units: {control_res[1]}")
    print(f"  Total enemy/ally units: {control_res[2]}")
