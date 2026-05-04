#!/usr/bin/env python3
"""Verify FDOTHER.DAT offset table structure to determine correct interpretation."""

import struct

with open("game/FDOTHER.DAT", "rb") as f:
    data = f.read()

print(f"FDOTHER.DAT file size: {len(data)} bytes")
print(f"Magic: {data[0:6]}")

# Check byte 6-9
dword_at_6 = struct.unpack_from('<I', data, 6)[0]
dword_at_10 = struct.unpack_from('<I', data, 10)[0]
print(f"\nDWORD at byte 6:  {dword_at_6}")
print(f"DWORD at byte 10: {dword_at_10}")

# Interpretation A: byte 6 is count, offsets start at byte 10
# Resource 0: offset[0]=422, offset[1]=1190, size=768 (palette)
# Resource 10: offset[10]=19525, offset[11]=24648, size=5123

# Interpretation B: byte 6 is offset[0], offsets start at byte 6  
# Resource 0: offset[0]=422, offset[1]=1190, size=768
# Resource 10: offset[10]=2235, offset[11]=16689, size=14454

print("\n=== Interpretation A: count at byte 6, offsets at byte 10 ===")
count_a = dword_at_6
print(f"Count: {count_a}")
offsets_a = []
for i in range(min(15, count_a)):
    pos = 10 + 4 * i
    offset = struct.unpack_from('<I', data, pos)[0]
    offsets_a.append(offset)
for i in range(min(12, len(offsets_a))):
    if i+1 < len(offsets_a):
        size = offsets_a[i+1] - offsets_a[i]
    else:
        size = len(data) - offsets_a[i]
    print(f"  Resource {i:2d}: offset={offsets_a[i]:10d}, size={size:8d}")

print("\n=== Interpretation B: offsets start at byte 6 ===")
offsets_b = []
for i in range(15):
    pos = 6 + 4 * i
    offset = struct.unpack_from('<I', data, pos)[0]
    offsets_b.append(offset)
for i in range(12):
    if i+1 < len(offsets_b):
        size = offsets_b[i+1] - offsets_b[i]
    else:
        size = len(data) - offsets_b[i]
    print(f"  Resource {i:2d}: offset={offsets_b[i]:10d}, size={size:8d}")

# Check actual resource data to see which is correct
print("\n=== Checking resource 10 actual content ===")
# Interpretation A: offset 19525, size 5123
res_a = data[19525:19525+5123]
if len(res_a) >= 4:
    w, h = struct.unpack_from('<HH', res_a, 0)
    print(f"Interp A: width={w}, height={h}, size={len(res_a)}")
    if w == 320 and h == 200:
        print("  -> This is 320x200 (correct for resource 10)")

# Interpretation B: offset 2235, size 14454  
res_b = data[2235:2235+14454]
if len(res_b) >= 4:
    w, h = struct.unpack_from('<HH', res_b, 0)
    print(f"Interp B: width={w}, height={h}, size={len(res_b)}")
    if w == 320 and h == 200:
        print("  -> This is 320x200 (correct for resource 10)")

print("\n=== Checking resource 0 actual content ===")
# Both interpretations agree: offset 422, size 768
res0 = data[422:422+768]
print(f"Resource 0: size={len(res0)}, all bytes in 0-63 range: {all(0 <= b <= 63 for b in res0)}")
if all(0 <= b <= 63 for b in res0):
    print("  -> This looks like a palette (6-bit values 0-63)")
