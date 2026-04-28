import struct

with open("game/FDFIELD.DAT", "rb") as f:
    data = f.read()

map_count = struct.unpack_from("<I", data, 6)[0]
print(f"Map count at offset 6: {map_count} (0x{map_count:08x})")
print(f"First 14 bytes: {data[:14].hex()}")

# The value is 0x00000196 = 406
# But maybe the actual count should be derived differently
# Let's check byte 6 specifically
print(f"Byte 6: {data[6]} (0x{data[6]:02x})")
print(f"Byte 7: {data[7]} (0x{data[7]:02x})")

# 0x96 = 150 in decimal
# Could the actual map count be different?
# Let's calculate based on file size
# Header: 6 bytes
# Map count field: 4 bytes
# Each map entry: 12 bytes
# Data starts after map entries

# If map_count = 406, map table size = 406 * 12 = 4872 bytes
# Data would start at offset 6 + 4 + 4872 = 4882
# But actual map 0 layout starts at offset 406 (which is the map_count value!)

# This suggests the structure might be:
# Offset 0-5: Magic (6 bytes)
# Offset 6-9: First map's layout offset (4 bytes)
# No explicit map count - we calculate from file size

# Let's try: offset 6 is actually the first map's layout offset
first_layout = struct.unpack_from("<I", data, 6)[0]
print(f"\nIf offset 6 is first layout offset: {first_layout}")
if first_layout < len(data):
    w = struct.unpack_from("<H", data, first_layout)[0]
    h = struct.unpack_from("<H", data, first_layout + 2)[0]
    print(f"  Width: {w}, Height: {h}")
