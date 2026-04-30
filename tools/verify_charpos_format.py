#!/usr/bin/env python3
"""
Verify Map 0 character position data format

According to documentation:
- Part 3 starts at 0x0E43
- First 2 bytes: total character count (0x22 = 34 in the example)
- Each character: 3 * 2 bytes = 6 bytes (AA AA BB BB CC CC)
  - AA AA: X coordinate (2 bytes, little-endian)
  - BB BB: Y coordinate (2 bytes, little-endian)  
  - CC CC: Portrait ID (2 bytes, little-endian)
  - If CC CC = 0x0000, it's a player character

But wait - the documentation shows 0x22 groups = 34 characters
And the example shows each character is 6 bytes (3 * 2-byte words)
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
print(f"Start offset: 0x{charpos_offset:04X} ({charpos_offset})")
print(f"End offset:   0x{map1_layout_offset - 1:04X} ({map1_layout_offset - 1})")
print(f"Total size:   0x{map1_layout_offset - charpos_offset:04X} ({map1_layout_offset - charpos_offset}) bytes")
print()

# Read the data
char_data = data[charpos_offset:map1_layout_offset]

# First 2 bytes: total count
total_chars = struct.unpack_from('<H', char_data, 0)[0]
print(f"Total characters: {total_chars} (0x{total_chars:04X})")
print()

# According to documentation, each char is 6 bytes (3 WORDs)
char_size = 6
expected_data_size = 2 + total_chars * char_size
actual_data_size = len(char_data)

print(f"Expected data size: 2 + {total_chars} * {char_size} = {expected_data_size} bytes")
print(f"Actual data size:   {actual_data_size} bytes")
print()

if expected_data_size == actual_data_size:
    print("✓ Size matches! Parsing character positions...")
else:
    print(f"✗ Size mismatch! Difference: {actual_data_size - expected_data_size} bytes")
    print("  Trying alternative interpretation...")

print()
print(f"{'ID':<4} {'X':<8} {'Y':<8} {'Portrait':<12} {'Type':<15}")
print("-" * 50)

for i in range(total_chars):
    offset = 2 + i * char_size
    if offset + char_size > len(char_data):
        print(f"Char {i}: Not enough data")
        break
    
    # Parse 3 WORDs (6 bytes)
    x = struct.unpack_from('<H', char_data, offset)[0]
    y = struct.unpack_from('<H', char_data, offset + 2)[0]
    portrait = struct.unpack_from('<H', char_data, offset + 4)[0]
    
    if portrait == 0:
        char_type = "PLAYER"
    else:
        char_type = f"NPC({portrait})"
    
    print(f"{i:<4} {x:<8} {y:<8} {portrait:<12} {char_type:<15}")

print()
print("=" * 60)
print("VERIFICATION AGAINST DOCUMENTATION EXAMPLE")
print("=" * 60)
print()
print("From the screenshot, first few characters should be:")
print("  Char 0: X=1, Y=0, Portrait=0 (PLAYER)")
print("  Char 1: Y=3, X=0, Portrait=0 (PLAYER) - wait, this looks wrong in screenshot")
print()
print("Actual parsed data:")
print(f"  Char 0: X={struct.unpack_from('<H', char_data, 2)[0]}, Y={struct.unpack_from('<H', char_data, 4)[0]}, Portrait={struct.unpack_from('<H', char_data, 6)[0]}")
print(f"  Char 1: X={struct.unpack_from('<H', char_data, 8)[0]}, Y={struct.unpack_from('<H', char_data, 10)[0]}, Portrait={struct.unpack_from('<H', char_data, 12)[0]}")
print(f"  Char 2: X={struct.unpack_from('<H', char_data, 14)[0]}, Y={struct.unpack_from('<H', char_data, 16)[0]}, Portrait={struct.unpack_from('<H', char_data, 18)[0]}")
