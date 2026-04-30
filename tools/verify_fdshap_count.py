"""Verify FDSHAP.DAT actual resource count and check map 32 tileset index"""
import struct

data = open('../bin/FDSHAP.DAT', 'rb').read()
print(f"FDSHAP.DAT file size: {len(data)} bytes")

# Format 2 parsing
offsets = []
pos = 6
while pos + 4 <= len(data):
    offset = struct.unpack('<I', data[pos:pos+4])[0]
    if offset > len(data):
        break
    offsets.append(offset)
    pos += 4

print(f"\nFormat 2 parsing: {len(offsets)} resources found")
print(f"First 5 offsets: {offsets[:5]}")
print(f"Last 5 offsets: {offsets[-5:]}")

# Check byte 6-9 value
byte6_val = struct.unpack('<I', data[6:10])[0]
print(f"\nByte 6-9 value: {byte6_val}")

# For map 32 with terrain_set_id=32, tileset index would be 64
print(f"\nTileset index needed for terrain_set=32: {32 * 2}")
print(f"Max valid index: {len(offsets) - 1}")
if 32 * 2 >= len(offsets):
    print(f"*** ERROR: Index 64 is OUT OF RANGE (max={len(offsets)-1}) ***")
else:
    print(f"Index 64 is valid")
