#!/usr/bin/env python3
"""对比地形ID计算公式的差异"""
import struct

data = open("game/FDFIELD.DAT", "rb").read()

offsets = []
pos = 6
while pos < len(data) - 4:
    o = struct.unpack_from("<I", data, pos)[0]
    if o > pos and o < len(data):
        offsets.append(o)
    else:
        break
    pos += 4

layout = data[offsets[0]:offsets[1]]
print(f"Layout size: {len(layout)}")
print(f"First 16 bytes hex: {layout[:16].hex(' ')}")
print()

raw_ids = []
ida_ids = []
diff_count = 0

for i in range(4, len(layout) - 3, 4):
    b0 = layout[i]
    b1 = layout[i + 1]
    b2 = layout[i + 2]
    b3 = layout[i + 3]
    raw_16 = b0 | (b1 << 8)
    ida_id = b0 | ((b1 & 0x03) << 8)
    raw_ids.append(raw_16)
    ida_ids.append(ida_id)
    if raw_16 != ida_id:
        diff_count += 1
        if diff_count <= 10:
            tile_idx = (i - 4) // 4
            print(f"Tile {tile_idx}: b0={b0:02x} b1={b1:02x} b2={b2:02x} b3={b3:02x}, raw16={raw_16}, ida={ida_id}")

print(f"\nTotal tiles: {len(raw_ids)}")
print(f"Different IDs: {diff_count}")
print(f"Raw ID range: {min(raw_ids)} - {max(raw_ids)}")
print(f"IDA ID range: {min(ida_ids)} - {max(ida_ids)}")
print(f"Raw unique: {len(set(raw_ids))}")
print(f"IDA unique: {len(set(ida_ids))}")
