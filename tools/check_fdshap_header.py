#!/usr/bin/env python3
"""Check FDSHAP.DAT header structure"""

import struct

with open("game/FDSHAP.DAT", "rb") as f:
    fdshap = f.read()

print(f"FDSHAP.DAT size: {len(fdshap)} bytes")
print(f"First 20 bytes: {fdshap[:20].hex()}")
print(f"Magic: {fdshap[:6]}")

# Check different interpretations of offset 6
val_16 = struct.unpack_from("<H", fdshap, 6)[0]
val_32 = struct.unpack_from("<I", fdshap, 6)[0]
print(f"\nOffset 6-7 (16-bit): {val_16} (0x{val_16:04x})")
print(f"Offset 6-9 (32-bit): {val_32} (0x{val_32:08x})")

# Check what's at offset 10
offset_at_10 = struct.unpack_from("<I", fdshap, 10)[0]
print(f"\nOffset 10-13 (32-bit): {offset_at_10}")

# If offset table starts at 6 (not 10), and each entry is 4 bytes
print(f"\n--- Checking offset table starting at 6 ---")
for i in range(5):
    pos = 6 + i * 4
    val = struct.unpack_from("<I", fdshap, pos)[0]
    print(f"  Entry {i} at {pos}: {val}")

# If offset table starts at 10
print(f"\n--- Checking offset table starting at 10 ---")
for i in range(5):
    pos = 10 + i * 4
    val = struct.unpack_from("<I", fdshap, pos)[0]
    print(f"  Entry {i} at {pos}: {val}")

# Check if there's a different structure
# Maybe FDSHAP has: magic (6) + data_start_offset (4) + offset_table (starting at data_start)
data_start_32 = struct.unpack_from("<I", fdshap, 6)[0]
print(f"\n--- If offset 6-9 is data_start: {data_start_32} ---")
if data_start_32 < len(fdshap) - 4:
    # At data_start, there should be an offset table
    first_offset = struct.unpack_from("<I", fdshap, data_start_32)[0]
    second_offset = struct.unpack_from("<I", fdshap, data_start_32 + 4)[0]
    third_offset = struct.unpack_from("<I", fdshap, data_start_32 + 8)[0]
    print(f"  At data_start: first={first_offset}, second={second_offset}, third={third_offset}")

# Let's check the actual bytes around offset 6-14
print(f"\n--- Bytes 6-30 ---")
for i in range(6, 30, 4):
    val = struct.unpack_from("<I", fdshap, i)[0]
    print(f"  Offset {i}: 0x{val:08x} = {val}")

# Check what's at offset 148014
print(f"\n--- Checking offset 148014 ---")
if 148014 < len(fdshap):
    print(f"Data at 148014: {fdshap[148014:148030].hex()}")
    print(f"As values: {list(fdshap[148014:148030])}")
    
    # Check if this could be a palette (768 bytes of RGB)
    # Or if the actual palette is elsewhere

# Maybe FDSHAP structure is different from FDFIELD
# Let's search for "LLLLLL" pattern to find all DAT-like structures
print(f"\n--- Searching for LLLLLL pattern ---")
import re
positions = [m.start() for m in re.finditer(b'LLLLLL', fdshap)]
print(f"Found LLLLLL at positions: {positions[:10]}")
