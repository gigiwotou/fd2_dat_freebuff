import struct
from pathlib import Path

data = Path("game/FDSHAP.DAT").read_bytes()
count = struct.unpack_from('<I', data, 6)[0]

print(f"FDSHAP.DAT: {count} resources")
print("\n=== 前15个资源 ===")

for i in range(min(15, count)):
    pos = 4 * i + 10
    offset = struct.unpack_from('<I', data, pos)[0]
    next_pos = 4 * (i + 1) + 10
    next_offset = struct.unpack_from('<I', data, next_pos)[0] if i + 1 < count else len(data)
    size = next_offset - offset
    
    print(f"Resource {i}: offset={offset}, size={size}")
    if size >= 4 and size < 2000:
        w, h = struct.unpack_from('<HH', data, offset)
        print(f"  w={w}, h={h}")
        if 5 <= w <= 50 and 5 <= h <= 50:
            print(f"  *** 可能是瓷砖图像 ***")
