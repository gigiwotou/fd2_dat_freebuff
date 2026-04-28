#!/usr/bin/env python3
"""Analyze FDFIELD.DAT structure"""

import struct

fdfield_path = "game/FDFIELD.DAT"
with open(fdfield_path, "rb") as f:
    data = f.read()

print(f"FDFIELD.DAT size: {len(data)} bytes")
print(f"First 100 bytes: {data[:100].hex()}")
print(f"Magic: {data[:6]}")

resource_count = struct.unpack_from("<I", data, 6)[0]
print(f"Resource count at offset 6: {resource_count}")

# Try different interpretations
# 1. Offset table starts at 10, each entry is 4 bytes
print("\n--- Interpretation 1: offset table at 10, 4 bytes each ---")
offsets_4 = []
for i in range(min(20, resource_count)):
    offset = struct.unpack_from("<I", data, 10 + i * 4)[0]
    offsets_4.append(offset)
    print(f"  Resource {i}: offset={offset}")

# 2. Check if the first offset points to valid data
if offsets_4:
    first_offset = offsets_4[0]
    print(f"\nFirst resource at offset {first_offset}:")
    print(f"  Data: {data[first_offset:first_offset+20].hex()}")
    w = struct.unpack_from("<H", data, first_offset)[0]
    h = struct.unpack_from("<H", data, first_offset + 2)[0]
    print(f"  If layout: width={w}, height={h}")

# 3. Try reading resource count as different types
print("\n--- Alternative resource counts ---")
rc_16 = struct.unpack_from("<H", data, 6)[0]
print(f"  16-bit at offset 6: {rc_16}")
rc_8 = data[6]
print(f"  8-bit at offset 6: {rc_8}")
rc_10 = struct.unpack_from("<I", data, 10)[0]
print(f"  32-bit at offset 10: {rc_10}")

# 4. Look at bytes 6-10
print(f"\nBytes 6-14: {data[6:14].hex()}")
print(f"  Byte[6]={data[6]}, Byte[7]={data[7]}, Byte[8]={data[8]}, Byte[9]={data[9]}")

# 5. If resource_count is valid, check all resource offsets
print(f"\n--- All resource offsets (first 30) ---")
for i in range(min(30, resource_count)):
    offset = struct.unpack_from("<I", data, 10 + i * 4)[0]
    if offset > len(data):
        print(f"  Resource {i}: offset={offset} (INVALID - exceeds file size)")
        break
    print(f"  Resource {i}: offset={offset}")

# 6. Calculate expected resource count
# Each map has 3 resources. If there are ~100 maps, we'd expect ~300 resources
# The file is 243169 bytes. If each resource entry is 4 bytes in offset table:
# Header (10 bytes) + 300*4 bytes = 1210 bytes for offset table
# Remaining for data: 243169 - 1210 = 241959 bytes
