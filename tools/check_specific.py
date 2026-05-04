#!/usr/bin/env python3
import struct

with open("game/FDOTHER.DAT", "rb") as f:
    data = f.read()

print("=== Key resources (sub_111BA: offsets start at byte 6) ===")
print(f"{'Index':>5} {'Offset':>10} {'Size':>10} {'Width':>6} {'Height':>6}")
print("-" * 50)

for i in [0, 3, 10, 69, 70, 71, 72, 73, 74, 75, 76, 99, 100, 101]:
    pos = 6 + 4 * i
    if pos + 8 > len(data):
        print(f"{i:5d}: out of range")
        continue
    offset = struct.unpack_from('<I', data, pos)[0]
    next_offset = struct.unpack_from('<I', data, pos + 4)[0]
    size = next_offset - offset
    
    w, h = 0, 0
    if offset + 4 <= len(data):
        w, h = struct.unpack_from('<HH', data, offset)
    
    print(f"{i:5d} {offset:10d} {size:10d} {w:6d} {h:6d}")

print("\n=== Key resources (old: count at byte 6, offsets at byte 10) ===")
print(f"{'Index':>5} {'Offset':>10} {'Size':>10} {'Width':>6} {'Height':>6}")
print("-" * 50)

for i in [0, 3, 7, 10, 69, 70, 71, 72, 73, 74, 76, 99, 100, 101]:
    pos = 10 + 4 * i
    if pos + 8 > len(data):
        print(f"{i:5d}: out of range")
        continue
    offset = struct.unpack_from('<I', data, pos)[0]
    next_offset = struct.unpack_from('<I', data, pos + 4)[0]
    size = next_offset - offset
    
    w, h = 0, 0
    if offset + 4 <= len(data):
        w, h = struct.unpack_from('<HH', data, offset)
    
    print(f"{i:5d} {offset:10d} {size:10d} {w:6d} {h:6d}")
