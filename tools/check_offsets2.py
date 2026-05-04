#!/usr/bin/env python3
"""Verify which offset table interpretation is correct."""

import struct

with open("game/FDOTHER.DAT", "rb") as f:
    data = f.read()

print("=== Interpretation A: sub_111BA (offset table at byte 6) ===")
print("Resource 0: offset=422, size=768")
print("Resource 7: offset=183059, size=23377")

# Check resource 0 (offset 422, size 768) - should be palette if sub_111BA is correct
res0 = data[422:422+768]
print(f"\nBytes at offset 422 (first 24 bytes of resource 0):")
print(f"  {res0[:24].hex()}")
print(f"  Is this a palette? 768 bytes = 256 colors * 3 channels")
if len(res0) == 768:
    print(f"  Yes, 768 bytes = 256 RGB colors!")

print("\n=== Interpretation B: count at byte 6 (offset table at byte 10) ===")
print("Resource 0: offset=1190, size=2235")
print("Resource 7: offset=206436, size=768")

# Check resource 7 (offset 206436, size 768) - should be palette if count approach is correct
res7 = data[206436:206436+768]
print(f"\nBytes at offset 206436 (first 24 bytes of resource 7):")
print(f"  {res7[:24].hex()}")
if len(res7) == 768:
    print(f"  Yes, 768 bytes = 256 RGB colors!")

# Check if offset 422 contains palette-like data
print("\n=== Checking if offset 422 is valid palette data ===")
print(f"  Data at 422: {res0[:12].hex()}")
print(f"  Data at 206436: {res7[:12].hex()}")

# Both could be palettes - let's see which one the game actually loads as index 0
print("\n=== Conclusion ===")
print("If sub_111BA loads index 0 and gets 768 bytes at offset 422:")
print("  -> sub_111BA's index 0 = palette (768 bytes)")
print("If count-at-byte-6 loads index 7 and gets 768 bytes at offset 206436:")
print("  -> count approach's index 7 = palette (768 bytes)")
print("\nThe sub_111BA approach treats byte 6 as offset[0], not as count.")
print("This means resource indices are shifted by 1 compared to our current implementation.")
