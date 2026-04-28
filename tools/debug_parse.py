#!/usr/bin/env python3
"""Debug parse_fdfield"""

import struct

with open("game/FDFIELD.DAT", "rb") as f:
    data = f.read()

magic = data[:6]
print(f"Magic: {magic}")

data_start = struct.unpack_from("<I", data, 6)[0]
print(f"Data start (offset 6): {data_start}")

# Read all resource offsets from offset table (starts at 10)
resource_offsets = []
pos = 10
while pos < data_start - 4:
    offset = struct.unpack_from("<I", data, pos)[0]
    print(f"  pos={pos}, offset={offset}, valid={data_start <= offset < len(data)}")
    if offset >= data_start and offset < len(data):
        resource_offsets.append(offset)
    pos += 4
    if len(resource_offsets) >= 10:
        break

print(f"\nResource offsets found: {len(resource_offsets)}")
print(f"First 5: {resource_offsets[:5]}")
