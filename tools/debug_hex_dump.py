#!/usr/bin/env python3
"""
Debug: Compare actual hex data with documentation screenshot
"""

import struct

filepath = r'd:\testworkspace\fd2_dat_freebuff\bin\FDFIELD.DAT'

with open(filepath, 'rb') as f:
    data = f.read()

# From documentation screenshot:
# 00000E40: 00 00 00 22 00 01 00 03 00 60 00  02 00 01 00 60
# 00000E50: 00 04 00 01 00 60 00 06 00 00 00  00 00 01 00 15

print("Actual data from FDFIELD.DAT at offset 0x0E40:")
print("=" * 60)

# Show hex dump from 0x0E40 to 0x0E70
for i in range(0x0E40, 0x0E70, 16):
    hex_bytes = data[i:i+16]
    hex_str = ' '.join('{:02X}'.format(b) for b in hex_bytes)
    print("0x{:06X}: {}".format(i, hex_str))

print()
print("=" * 60)
print("DOCUMENTATION SCREENSHOT COMPARISON")
print("=" * 60)
print()
print("Documentation shows at 0x0E40:")
print("  00 00 00 22 00 01 00 03 00 60 00  02 00 01 00 60")
print()

# Compare
print("Actual data at 0x0E40:")
actual_16 = data[0x0E40:0x0E50]
actual_hex = ' '.join('{:02X}'.format(b) for b in actual_16)
print("  " + actual_hex)

print()
if actual_hex == "00 00 00 22 00 01 00 03 00 60 00 02 00 01 00 60":
    print("[OK] Data matches documentation screenshot!")
else:
    print("[ERROR] Data does NOT match!")

print()
print("=" * 60)
print("RE-PARSE WITH CORRECT OFFSET")
print("=" * 60)
print()

# The data starts at 0x0E43
charpos_offset = 0x0E43
char_data = data[charpos_offset:charpos_offset+206]

print("First 20 bytes from 0x0E43:")
hex_str = ' '.join('{:02X}'.format(b) for b in char_data[:20])
print("  " + hex_str)
print()

# Parse according to documentation
# Byte 0-1: total count
total = struct.unpack_from('<H', char_data, 0)[0]
print("Total characters: {} (0x{:04X})".format(total, total))
print()

# Each character: 6 bytes (X:2, Y:2, Portrait:2)
print("{:<4} {:<8} {:<8} {:<12}".format("ID", "X", "Y", "Portrait"))
print("-" * 35)

for i in range(min(10, total)):
    offset = 2 + i * 6
    x = struct.unpack_from('<H', char_data, offset)[0]
    y = struct.unpack_from('<H', char_data, offset + 2)[0]
    portrait = struct.unpack_from('<H', char_data, offset + 4)[0]
    print("{:<4} {:<8} {:<8} {:<12}".format(i, x, y, portrait))

print()
print("=" * 60)
print("DOCUMENTATION INTERPRETATION")
print("=" * 60)
print()
print("From screenshot, the interpretation is:")
print("  Char 0: X=1 (00 01), Y=3 (00 03), Portrait=0x60=96 (00 60)")
print("  Char 1: X=2 (00 02), Y=1 (00 01), Portrait=0x60=96 (00 60)")
print("  Char 2: X=4 (00 04), Y=1 (00 01), Portrait=0x60=96 (00 60)")
print()
print("Our parsed data:")
print("  Char 0: X={}, Y={}, Portrait={}".format(
    struct.unpack_from('<H', char_data, 2)[0],
    struct.unpack_from('<H', char_data, 4)[0],
    struct.unpack_from('<H', char_data, 6)[0]))
print("  Char 1: X={}, Y={}, Portrait={}".format(
    struct.unpack_from('<H', char_data, 8)[0],
    struct.unpack_from('<H', char_data, 10)[0],
    struct.unpack_from('<H', char_data, 12)[0]))
print("  Char 2: X={}, Y={}, Portrait={}".format(
    struct.unpack_from('<H', char_data, 14)[0],
    struct.unpack_from('<H', char_data, 16)[0],
    struct.unpack_from('<H', char_data, 18)[0]))
