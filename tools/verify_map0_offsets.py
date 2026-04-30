#!/usr/bin/env python3
"""
Verify Map 0 (first map) offsets from the hex dump

From the hex dump:
Offset 0x00000000: 4C 4C 4C 4C 4C 4C 96 01 00 00 9A 0A 00 00 43 0E
Offset 0x00000010: 00 00 11 0F 00 00 F1 17 00 00 84 1C 00 00 94 1D

Header: bytes 0-5 = 'LLLLLL' (6 bytes of 0x4C)

Map 0 index table starts at byte 6:
  DWORD[0] (bytes 6-9):   0x00000196 = 406 (Layout data offset)
  DWORD[1] (bytes 10-13): 0x00000A9A = 2714 (Control data offset)
  DWORD[2] (bytes 14-17): 0x00000E43 = 3651 (Character position offset)

Map 1 index table starts at byte 18:
  DWORD[0] (bytes 18-21): 0x00000F11 = 3857
  DWORD[1] (bytes 22-25): 0x000017F1 = 6129
  DWORD[2] (bytes 26-29): 0x00001C84 = 7300
"""

import struct

filepath = r'd:\testworkspace\fd2_dat_freebuff\bin\FDFIELD.DAT'

with open(filepath, 'rb') as f:
    data = f.read()

print("FDFIELD.DAT - Map 0 Offset Verification")
print("=" * 60)

# Read first 30 bytes to show header + map 0 + map 1 index entries
print("\nFirst 30 bytes (hex):")
for i in range(0, 30, 16):
    hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
    print(f"  {i:08X}: {hex_str}")

print("\n" + "=" * 60)
print("MAP 0 INDEX TABLE (bytes 6-17)")
print("=" * 60)

# Map 0 offsets
map0_layout = struct.unpack_from('<I', data, 6)[0]
map0_control = struct.unpack_from('<I', data, 10)[0]
map0_charpos = struct.unpack_from('<I', data, 14)[0]

print(f"\nLayout data offset:   0x{map0_layout:04X} ({map0_layout})")
print(f"Control data offset:  0x{map0_control:04X} ({map0_control})")
print(f"Char position offset: 0x{map0_charpos:04X} ({map0_charpos})")

print("\n" + "=" * 60)
print("VERIFY PART SIZES")
print("=" * 60)

# Part 1: Layout data (0x196 ~ 0xA99)
part1_start = map0_layout
part1_end = map0_control - 1
part1_size = part1_end - part1_start + 1

print(f"\nPart 1 (Layout):")
print(f"  Start: 0x{part1_start:04X} ({part1_start})")
print(f"  End:   0x{part1_end:04X} ({part1_end})")
print(f"  Size:  0x{part1_size:04X} ({part1_size}) bytes")
print(f"  Expected: 0x196 ~ 0xA99, size 0x904")

if part1_start == 0x196 and part1_end == 0xA99:
    print("  ✓ MATCHES expected values!")
else:
    print(f"  ✗ MISMATCH!")

# Part 2: Control data (0xA9A ~ 0xE42)
part2_start = map0_control
part2_end = map0_charpos - 1
part2_size = part2_end - part2_start + 1

print(f"\nPart 2 (Control):")
print(f"  Start: 0x{part2_start:04X} ({part2_start})")
print(f"  End:   0x{part2_end:04X} ({part2_end})")
print(f"  Size:  0x{part2_size:04X} ({part2_size}) bytes")
print(f"  Expected: 0xA9A ~ 0xE42, size 0x3A9")

if part2_start == 0xA9A and part2_end == 0xE42:
    print("  ✓ MATCHES expected values!")
else:
    print(f"  ✗ MISMATCH!")

# Part 3: Character positions (0xE43 ~ 0xF10)
# Map 1 layout offset = 0xF11, so part 3 ends at 0xF10
map1_layout = struct.unpack_from('<I', data, 18)[0]
part3_end = map1_layout - 1
part3_size = part3_end - map0_charpos + 1

print(f"\nPart 3 (Character Positions):")
print(f"  Start: 0x{map0_charpos:04X} ({map0_charpos})")
print(f"  End:   0x{part3_end:04X} ({part3_end})")
print(f"  Size:  0x{part3_size:04X} ({part3_size}) bytes")
print(f"  Expected: 0xE43 ~ 0xF10, size 0xCE")

if map0_charpos == 0xE43 and part3_end == 0xF10:
    print("  ✓ MATCHES expected values!")
else:
    print(f"  ✗ MISMATCH!")

print("\n" + "=" * 60)
print("PARSE MAP 0 CHARACTER DATA")
print("=" * 60)

# Parse character position data
char_data = data[map0_charpos:map0_charpos + part3_size]
total_chars = struct.unpack_from('<H', char_data, 0)[0]

print(f"\nTotal characters: {total_chars}")
print(f"Character data size: {part3_size} bytes")
print(f"Expected: 2 + {total_chars} * 6 = {2 + total_chars * 6} bytes")

print(f"\n{'ID':<4} {'X':<6} {'Y':<6} {'Portrait':<10} {'Type':<10}")
print("-" * 40)

for i in range(total_chars):
    offset = 2 + i * 6
    if offset + 6 > len(char_data):
        break
    x, y, portrait = struct.unpack_from('<HHH', char_data, offset)
    char_type = "PLAYER" if portrait == 0 else f"NPC({portrait})"
    print(f"{i:<4} {x:<6} {y:<6} {portrait:<10} {char_type:<10}")
