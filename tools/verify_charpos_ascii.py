#!/usr/bin/env python3
"""
Verify Map 0 character position data format - ASCII only
"""

import struct

filepath = r'd:\testworkspace\fd2_dat_freebuff\bin\FDFIELD.DAT'

with open(filepath, 'rb') as f:
    data = f.read()

# Map 0 char position data starts at 0x0E43
charpos_offset = 0x0E43
map1_layout_offset = 0x0F11

print("Map 0 Character Position Data (Part 3)")
print("=" * 60)
print("Start offset: 0x{:04X} ({})".format(charpos_offset, charpos_offset))
print("End offset:   0x{:04X} ({})".format(map1_layout_offset - 1, map1_layout_offset - 1))
print("Total size:   0x{:04X} ({}) bytes".format(map1_layout_offset - charpos_offset, map1_layout_offset - charpos_offset))
print()

# Read the data
char_data = data[charpos_offset:map1_layout_offset]

# First 2 bytes: total count
total_chars = struct.unpack_from('<H', char_data, 0)[0]
print("Total characters: {} (0x{:04X})".format(total_chars, total_chars))
print()

# Each char is 6 bytes (3 WORDs)
char_size = 6
expected_data_size = 2 + total_chars * char_size
actual_data_size = len(char_data)

print("Expected data size: 2 + {} * {} = {} bytes".format(total_chars, char_size, expected_data_size))
print("Actual data size:   {} bytes".format(actual_data_size))

if expected_data_size == actual_data_size:
    print("[OK] Size matches! Parsing character positions...")
else:
    print("[ERROR] Size mismatch! Difference: {} bytes".format(actual_data_size - expected_data_size))

print()
print("{:<4} {:<8} {:<8} {:<12} {:<15}".format("ID", "X", "Y", "Portrait", "Type"))
print("-" * 50)

for i in range(total_chars):
    offset = 2 + i * char_size
    if offset + char_size > len(char_data):
        print("Char {}: Not enough data".format(i))
        break
    
    # Parse 3 WORDs (6 bytes)
    x = struct.unpack_from('<H', char_data, offset)[0]
    y = struct.unpack_from('<H', char_data, offset + 2)[0]
    portrait = struct.unpack_from('<H', char_data, offset + 4)[0]
    
    if portrait == 0:
        char_type = "PLAYER"
    else:
        char_type = "NPC({})".format(portrait)
    
    print("{:<4} {:<8} {:<8} {:<12} {:<15}".format(i, x, y, portrait, char_type))

print()
print("=" * 60)
print("FIRST 10 CHARACTERS FROM DOCUMENTATION SCREENSHOT")
print("=" * 60)
print()
print("The screenshot shows:")
print("  Char 0: X=1, Y=0, Portrait=0 (PLAYER)")
print("  Char 1: X=0, Y=3, Portrait=0 (PLAYER)")
print("  Char 2: X=0, Y=60, Portrait=0 (PLAYER)")
print()
print("Our parsed data:")
for i in range(min(10, total_chars)):
    offset = 2 + i * char_size
    x = struct.unpack_from('<H', char_data, offset)[0]
    y = struct.unpack_from('<H', char_data, offset + 2)[0]
    portrait = struct.unpack_from('<H', char_data, offset + 4)[0]
    print("  Char {}: X={}, Y={}, Portrait={}".format(i, x, y, portrait))
