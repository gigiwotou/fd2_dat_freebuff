#!/usr/bin/env python3
"""Find which FDOTHER resources are 320x200 images using sub_111BA interpretation."""
import struct

with open("game/FDOTHER.DAT", "rb") as f:
    data = f.read()

print("=== Finding 320x200 resources with sub_111BA interpretation ===")
for a7 in range(420):
    pos = 6 + 4 * a7
    if pos + 8 > len(data):
        break
    offset = struct.unpack_from('<I', data, pos)[0]
    next_offset = struct.unpack_from('<I', data, pos + 4)[0]
    size = next_offset - offset
    
    if offset + 4 <= len(data):
        w, h = struct.unpack_from('<HH', data, offset)
        if w == 320 and h == 200:
            print(f"  a7={a7:3d}: offset={offset:8d}, size={size:6d}, dims={w}x{h}")
        elif w == 320 and h == 147:
            print(f"  a7={a7:3d}: offset={offset:8d}, size={size:6d}, dims={w}x{h}")
        elif w == 320 and h == 100:
            print(f"  a7={a7:3d}: offset={offset:8d}, size={size:6d}, dims={w}x{h}")

print("\n=== Finding 768-byte resources (palettes) ===")
for a7 in range(420):
    pos = 6 + 4 * a7
    if pos + 8 > len(data):
        break
    offset = struct.unpack_from('<I', data, pos)[0]
    next_offset = struct.unpack_from('<I', data, pos + 4)[0]
    size = next_offset - offset
    
    if size == 768:
        print(f"  a7={a7:3d}: offset={offset:8d}, size={size:4d}")
