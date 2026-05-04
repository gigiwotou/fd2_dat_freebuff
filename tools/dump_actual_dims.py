#!/usr/bin/env python3
"""Dump actual resource dimensions for sub_111BA interpretation."""

import struct

with open("game/FDOTHER.DAT", "rb") as f:
    data = f.read()

print("=== FDOTHER.DAT resources (sub_111BA interpretation) ===")
print(f"{'Index':>5} {'Offset':>10} {'Size':>10} {'Width':>6} {'Height':>6}")
print("-" * 50)

for i in range(120):
    pos = 6 + 4 * i
    if pos + 8 > len(data):
        break
    offset = struct.unpack_from('<I', data, pos)[0]
    next_offset = struct.unpack_from('<I', data, pos + 4)[0]
    size = next_offset - offset
    
    # Try to read dimensions
    w, h = 0, 0
    if offset + 4 <= len(data):
        w, h = struct.unpack_from('<HH', data, offset)
    
    print(f"{i:5d} {offset:10d} {size:10d} {w:6d} {h:6d}")
