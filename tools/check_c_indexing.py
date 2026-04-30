#!/usr/bin/env python3
"""Check current C code indexing logic"""

import struct

filepath = r'd:\testworkspace\fd2_dat_freebuff\bin\FDFIELD.DAT'
map_id = 32

with open(filepath, 'rb') as f:
    data = f.read()

print("FDFIELD.DAT parsing analysis:")
print(f"File size: {len(data)} bytes")
print()

# Current C code logic: read DWORDs from byte 6
print("Current C code: reads DWORDs from byte 6")
print("  layout_idx = map_id * 3 = 96")
print("  control_idx = map_id * 3 + 1 = 97")
print("  char_pos_idx = map_id * 3 + 2 = 98")
print()

# What offsets are at positions 96, 97, 98?
for idx in [96, 97, 98]:
    pos = 6 + idx * 4
    offset = struct.unpack_from('<I', data, pos)[0]
    print(f"  offset[{idx}] at byte {pos}: {offset} (0x{offset:06X})")

print()
print("Correct offsets for map 32 (from documentation):")
print(f"  Tile data:      238140 (0x03A23C)")
print(f"  Control data:   241816 (0x03B098)")
print(f"  Character pos:  242987 (0x03B52B)")
print()

# What does documentation say?
doc_offset = 6 + map_id * 12
tile_off, ctrl_off, char_off = struct.unpack_from('<III', data, doc_offset)
print(f"Documentation structure (12 bytes per map):")
print(f"  Index offset: {doc_offset}")
print(f"  Tile data:      {tile_off} (0x{tile_off:06X})")
print(f"  Control data:   {ctrl_off} (0x{ctrl_off:06X})")
print(f"  Character pos:  {char_off} (0x{char_off:06X})")
