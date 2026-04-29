import struct
from collections import Counter

# 读取FDFIELD.DAT
with open("game/FDFIELD.DAT", "rb") as f:
    fdfield = f.read()

# 解析资源偏移
fdfield_offsets = []
pos = 6
while pos + 4 <= len(fdfield):
    offset = struct.unpack_from("<I", fdfield, pos)[0]
    if offset > pos and offset < len(fdfield):
        fdfield_offsets.append(offset)
    else:
        break
    pos += 4

print(f"FDFIELD.DAT: {len(fdfield_offsets)} resources")

# 地图0 layout
layout_start = fdfield_offsets[0]
w = struct.unpack_from("<H", fdfield, layout_start)[0]
h = struct.unpack_from("<H", fdfield, layout_start + 2)[0]
print(f"Map 0: {w}x{h}")

# 解析地形ID
tile_data = fdfield[layout_start + 4:]
terrain_ids_raw = []
pos = 0
for y in range(h):
    for x in range(w):
        if pos + 4 <= len(tile_data):
            b0 = tile_data[pos]
            b1 = tile_data[pos + 1]
            b2 = tile_data[pos + 2]
            b3 = tile_data[pos + 3]
            
            # 原始Python方式：直接读取2字节
            raw_16bit = struct.unpack_from("<H", tile_data, pos)[0]
            terrain_ids_raw.append(raw_16bit)
            pos += 4

print(f"\n原始terrain_id (16-bit直接读取):")
print(f"Range: {min(terrain_ids_raw)}-{max(terrain_ids_raw)}")
print(f"Unique: {len(set(terrain_ids_raw))}")

# 应用不同的掩码
print(f"\n不同掩码下的瓦片索引:")
for mask in [0x1F, 0x3F, 0x7F, 0xFF, 0x1FF, 0x3FF]:
    indices = [tid & mask for tid in terrain_ids_raw]
    unique = len(set(indices))
    max_idx = max(indices)
    print(f"  Mask 0x{mask:03X}: {unique} unique tiles, max index {max_idx}")

# 读取FDSHAP.DAT检查瓦片数量
with open("game/FDSHAP.DAT", "rb") as f:
    fdshap = f.read()

fdshap_rc = struct.unpack_from("<I", fdshap, 6)[0]
fdshap_offsets = []
for i in range(fdshap_rc):
    offset = struct.unpack_from("<I", fdshap, 10 + i * 4)[0]
    fdshap_offsets.append(offset)

# 资源1（瓦片集）
res1_start = fdshap_offsets[1]
tile_w, tile_h = struct.unpack_from("<HH", fdshap, res1_start)
print(f"\nFDSHAP resource 1: {tile_w}x{tile_h} tiles")

# 解析瓦片偏移表
tile_offsets = []
first_offset = struct.unpack_from("<H", fdshap, res1_start + 4)[0]
if first_offset > 0:
    tile_offsets.append(first_offset)
pos = res1_start + 6
while pos + 4 <= len(fdshap):
    offset_val = struct.unpack_from("<H", fdshap, pos)[0]
    zero_val = struct.unpack_from("<H", fdshap, pos + 2)[0]
    if zero_val == 0 and offset_val > 0:
        tile_offsets.append(offset_val)
    pos += 4
    if offset_val > len(fdshap) - 500:
        break

print(f"Total tiles in FDSHAP resource 1: {len(tile_offsets)}")

# 检查哪种掩码适合
print(f"\n掩码适配分析:")
for mask in [0x1F, 0x3F, 0x7F, 0xFF]:
    indices = [tid & mask for tid in terrain_ids_raw]
    max_idx = max(indices)
    fits = "[OK]" if max_idx < len(tile_offsets) else "[EXCEEDS]"
    print(f"  Mask 0x{mask:02X}: max index {max_idx}, fits {len(tile_offsets)} tiles? {fits}")