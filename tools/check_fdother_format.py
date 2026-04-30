"""Check FDOTHER.DAT format"""
import struct
from pathlib import Path

fdother_path = Path("game/FDOTHER.DAT")
data = fdother_path.read_bytes()

print(f"FDOTHER.DAT size: {len(data)} bytes")
print(f"Magic (0-6): {data[0:6]}")

# Format 1: count at byte 6
count = struct.unpack_from('<I', data, 6)[0]
print(f"\nIf format 1 (byte 6-9 = count): count = {count}")

# Format 2: offsets from byte 6
offset0 = struct.unpack_from('<I', data, 6)[0]
offset1 = struct.unpack_from('<I', data, 10)[0]
print(f"\nIf format 2 (offsets from byte 6):")
print(f"  offset[0] = {offset0}")
print(f"  offset[1] = {offset1}")

# Check resource 0 for palette
if count < 5000 and count > 0:
    # Format 1
    offset0_f1 = struct.unpack_from('<I', data, 10)[0]
    offset1_f1 = struct.unpack_from('<I', data, 14)[0]
    size = offset1_f1 - offset0_f1
    print(f"\nFormat 1 - Resource 0: offset={offset0_f1}, size={size}")
    print(f"  First 16 bytes: {data[offset0_f1:offset0_f1+16].hex(' ')}")
    if size >= 768:
        print(f"  [OK] Has enough data for 768-byte palette!")
    else:
        print(f"  [ERROR] Not enough data for palette")
else:
    # Format 2
    size = offset1 - offset0
    print(f"\nFormat 2 - Resource 0: offset={offset0}, size={size}")
    print(f"  First 16 bytes: {data[offset0:offset0+16].hex(' ')}")
    if size >= 768:
        print(f"  [OK] Has enough data for 768-byte palette!")
    else:
        print(f"  [ERROR] Not enough data for palette")
