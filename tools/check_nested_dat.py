#!/usr/bin/env python3
"""Check nested DAT format for resource 6"""
import struct
from pathlib import Path

data = Path("game/FDOTHER.DAT").read_bytes()
res_count = struct.unpack_from("<I", data, 6)[0]
offsets = [struct.unpack_from("<I", data, 10 + i*4)[0] for i in range(res_count)]

# Resource 6 is the nested DAT
res6_start = offsets[6]
res6_end = offsets[7]
res6 = data[res6_start:res6_end]

print(f"Resource 6: start={res6_start}, size={len(res6)}")
print(f"First 40 bytes hex: {res6[:40].hex()}")
print(f"Bytes 0-5: {res6[:6]}")
print(f"Bytes 6-9 (LE uint32): {struct.unpack_from('<I', res6, 6)[0]}")
print(f"Bytes 10-13 (LE uint32): {struct.unpack_from('<I', res6, 10)[0]}")

# Check: is byte 6 the count or first offset?
val_at_6 = struct.unpack_from('<I', res6, 6)[0]
val_at_10 = struct.unpack_from('<I', res6, 10)[0]
print(f"\nIf byte 6 = count: {val_at_6} sub-resources")
print(f"If byte 6 = first offset: offset={val_at_6}")
print(f"  res6[{val_at_6}:{val_at_6+4}] = {res6[val_at_6:val_at_6+4].hex()}")

# Check what sub_16886(res6, 0) would point to
# *(DWORD*)(res6 + 6) + res6 = val_at_6 + res6
target = val_at_6
print(f"\nsub_16886(res6, 0): *(res6[6..9]) + res6 = {target} + base")
if target < len(res6):
    print(f"  res6[{target}:{target+8}] = {res6[target:target+8].hex()}")
    w, h = struct.unpack_from("<HH", res6, target)
    print(f"  If image header at {target}: {w}x{h}")

# Check what sub_16886(res6, 1) would point to
target1 = val_at_10
print(f"\nsub_16886(res6, 1): *(res6[10..13]) + res6 = {target1} + base")
if target1 < len(res6):
    w1, h1 = struct.unpack_from("<HH", res6, target1)
    print(f"  If image header at {target1}: {w1}x{h1}")
    rle = res6[target1+4:target1+4+20]
    print(f"  First 20 bytes of RLE: {rle.hex()}")

# List first 10 offsets in the nested DAT
print("\nNested DAT offset table (bytes 6+4*i):")
for i in range(min(10, (len(res6)-6)//4)):
    off = struct.unpack_from("<I", res6, 6 + i*4)[0]
    print(f"  i={i}: offset={off}, within range={off < len(res6)}")
