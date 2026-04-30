#!/usr/bin/env python3
"""
Verify FDFIELD.DAT structure:
- 33 maps
- Each map has 3 parts (12 bytes = 3 DWORDs):
  Part 1: Map layout data offset
  Part 2: Map control data offset (character limits, treasure, events)
  Part 3: Character spawn position offset
"""

import struct

filepath = r'd:\testworkspace\fd2_dat_freebuff\bin\FDFIELD.DAT'

with open(filepath, 'rb') as f:
    data = f.read()

print(f"FDFIELD.DAT file size: {len(data)} bytes")
print(f"Header: {data[0:6]}")
print()

# Verify header
assert data[0:6] == b'LLLLLL', "Invalid header!"

print("=" * 80)
print("ALL 33 MAPS OFFSET TABLE")
print("=" * 80)
print(f"{'Map':<5} {'Layout':<12} {'Control':<12} {'CharPos':<12} {'Layout Size':<12} {'Control Size':<12}")
print("-" * 80)

for map_id in range(33):
    idx_offset = 6 + map_id * 12
    
    if idx_offset + 12 > len(data):
        print(f"Map {map_id:2d}: Index offset out of range")
        continue
    
    layout_off, control_off, charpos_off = struct.unpack_from('<III', data, idx_offset)
    
    # Calculate sizes by looking at next map's offsets
    if map_id < 32:
        next_idx = 6 + (map_id + 1) * 12
        next_layout, next_control, next_charpos = struct.unpack_from('<III', data, next_idx)
        
        # Layout size = next layout offset - current layout offset
        if next_layout > layout_off:
            layout_size = next_layout - layout_off
        else:
            layout_size = 0
    else:
        layout_size = 0  # Last map
    
    print(f"Map {map_id:2d}: {layout_off:<12} {control_off:<12} {charpos_off:<12} {layout_size:<12}")

print()
print("=" * 80)
print("DETAILED ANALYSIS OF MAP 32")
print("=" * 80)

map_id = 32
idx_offset = 6 + map_id * 12
layout_off, control_off, charpos_off = struct.unpack_from('<III', data, idx_offset)

print(f"\nLayout data at offset {layout_off} (0x{layout_off:06X}):")
width = struct.unpack_from('<H', data, layout_off)[0]
height = struct.unpack_from('<H', data, layout_off + 2)[0]
print(f"  Map dimensions: {width} x {height} tiles")
print(f"  Layout size: {width * height * 4 + 4} bytes (header + {width*height} tiles * 4 bytes)")

print(f"\nControl data at offset {control_off} (0x{control_off:06X}):")
map_num = data[control_off]
max_friendly = data[control_off + 1]
total_units = data[control_off + 2]
print(f"  Map number: {map_num}")
print(f"  Max friendly units: {max_friendly}")
print(f"  Total enemy units: {total_units}")
print(f"  Turn events: 16 * 3 bytes")
print(f"  Reserved: 16 * 2 bytes")
print(f"  Treasure data: 16 * 3 bytes")
print(f"  Character info: {total_units} * 26 bytes")

# Calculate control data size
control_header = 3
turn_events = 16 * 3
reserved = 16 * 2
treasure = 16 * 3
char_info = total_units * 26
expected_control_size = control_header + turn_events + reserved + treasure + char_info
print(f"  Expected control size: {expected_control_size} bytes")

print(f"\nCharacter position data at offset {charpos_off} (0x{charpos_off:06X}):")
total_chars = struct.unpack_from('<H', data, charpos_off)[0]
print(f"  Total characters: {total_chars}")
print(f"  Character positions: {total_chars} * 6 bytes")
print(f"  Expected size: {2 + total_chars * 6} bytes")

print("\nFirst 10 characters:")
print(f"  {'ID':<4} {'X':<6} {'Y':<6} {'Portrait':<10} {'Type':<10}")
print("  " + "-" * 36)

for i in range(min(10, total_chars)):
    pos = charpos_off + 2 + i * 6
    x, y, portrait = struct.unpack_from('<HHH', data, pos)
    char_type = "PLAYER" if portrait == 0 else f"NPC({portrait})"
    print(f"  {i:<4} {x:<6} {y:<6} {portrait:<10} {char_type:<10}")
