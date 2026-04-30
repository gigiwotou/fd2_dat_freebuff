"""
Check portrait icon pixel data to see if they're transparent.
"""
import struct

# Check FDICON.B24 structure
with open('game/FDICON.B24', 'rb') as f:
    data = f.read()

print(f"FDICON.B24: {len(data)} bytes")

# First 4 bytes: unknown
magic = struct.unpack_from('<I', data, 0)[0]
print(f"Header: 0x{magic:08X}")

# Parse icon headers (each icon has header)
# Based on the C code, icons have segments
# Let's check the icon cache structure

# Actually, let's check if portrait 68/69 icons exist and have valid data
# The C code loads them via fd2_icon_get()

# Print first 100 bytes for debugging
print("\nFirst 100 bytes:")
for i in range(0, 100, 16):
    hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
    print(f"  {i:04x}: {hex_str}")

# Check icon 48, 66, 68, 69
# Based on the log, these are the portraits used
print("\nPortraits used in map 32:")
print("  48: Enemy 0")
print("  66: Enemy 1")
print("  68: Enemies 5-12")
print("  69: Enemies 13-20")
print("\nNeed to verify these icons have non-zero pixel data after decoding")
