#!/usr/bin/env python3
"""
Analyze FDFIELD.DAT structure with the assumption that resource count 
at offset 6 might be wrong, or resource entries might have different structure.
"""

import struct

fdfield_path = "game/FDFIELD.DAT"
with open(fdfield_path, "rb") as f:
    data = f.read()

print(f"FDFIELD.DAT size: {len(data)} bytes")
print(f"First 20 bytes hex: {data[:20].hex()}")
print(f"Magic: {data[:6]}")

# According to user's documentation:
# 1.檔頭=連續6個4Ch (header = 6 bytes of 0x4C = 'LLLLLL')
# 2.各地圖資料位置：每地圖3個4 byte整數，共12 byte
#   (1)地圖構成資料位置 (2)地圖控制與寶箱資料位置 (3)人物出場位置資料位置
#
# So after the 6-byte header, each map entry is 12 bytes (3 x 4-byte offsets)
# The number of maps is NOT stored - we calculate it from file size

print("\n--- Interpretation: Each map entry is 12 bytes (3 x 4-byte offsets) ---")

# How many complete 12-byte map entries fit?
remaining = len(data) - 6  # subtract header
map_count = remaining // 12
print(f"Possible map count: {map_count}")

# Read first few map entries
for map_idx in range(min(20, map_count)):
    entry_start = 6 + map_idx * 12
    layout_offset = struct.unpack_from("<I", data, entry_start)[0]
    control_offset = struct.unpack_from("<I", data, entry_start + 4)[0]
    spawn_offset = struct.unpack_from("<I", data, entry_start + 8)[0]
    
    print(f"\nMap {map_idx}:")
    print(f"  Layout offset: {layout_offset}, Control offset: {control_offset}, Spawn offset: {spawn_offset}")
    
    # Check if layout offset is valid
    if layout_offset > 0 and layout_offset < len(data):
        print(f"  Layout data (first 8 bytes): {data[layout_offset:layout_offset+8].hex()}")
        w = struct.unpack_from("<H", data, layout_offset)[0]
        h = struct.unpack_from("<H", data, layout_offset + 2)[0]
        print(f"  If LE 16-bit: width={w}, height={h}")
        w_be = struct.unpack_from(">H", data, layout_offset)[0]
        h_be = struct.unpack_from(">H", data, layout_offset + 2)[0]
        print(f"  If BE 16-bit: width={w_be}, height={h_be}")
        
        # Check if control offset is valid
        if control_offset > 0 and control_offset < len(data):
            print(f"  Control first 3 bytes: {data[control_offset:control_offset+3].hex()}")
            map_id = data[control_offset]
            ally_max = data[control_offset + 1]
            enemy_total = data[control_offset + 2]
            print(f"  Map ID: {map_id}, Ally max: {ally_max}, Enemy total: {enemy_total}")
