import struct
from pathlib import Path

data = Path("game/FDFIELD.DAT").read_bytes()

print("=== FDFIELD.DAT Offset Table Analysis ===")
print(f"Magic: {data[:6]}")
print(f"Resource count: {struct.unpack_from('<I', data, 6)[0]}")

print("\n=== First 10 resources (8 bytes each: start, end) ===")
for i in range(10):
    pos = 10 + i * 8
    start, end = struct.unpack_from("<II", data, pos)
    size = end - start
    print(f"Resource {i}: start={start}, end={end}, size={size}")
    if i == 0 and size > 0:
        w, h = struct.unpack_from("<HH", data, start)
        print(f"  -> Width: {w}, Height: {h}")
