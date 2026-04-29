"""Verify which FDFIELD resource contains valid control data for map 0"""
import struct
from pathlib import Path

fdfield_path = Path("game/FDFIELD.DAT")
data = fdfield_path.read_bytes()

# Parse format 1 (count at byte 6)
count = struct.unpack_from('<I', data, 6)[0]
offsets = []
for i in range(count):
    offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(offset)

print("=== Checking resources for map 0 ===")
print("\nAccording to user: map data at 1-based indices 1,4,7,10 → 0-based: 0,3,6,9")
print("According to IDA: 3 resources per map, layout at 3*map_id")

# Check resources 0, 1, 2 (if map 0 uses 3 consecutive resources starting at 0)
print("\n=== If map 0 uses resources 0, 1, 2 ===")
for idx in range(3):
    start = offsets[idx]
    end = offsets[idx+1] if idx+1 < len(offsets) else len(data)
    size = end - start
    print(f"\nResource {idx} (size={size}):")
    print(f"  First 20 bytes: {data[start:start+20].hex(' ')}")
    if size >= 2:
        val0 = data[start]
        val1 = data[start+1]
        print(f"  byte[0] = {val0} (0x{val0:02x})")
        print(f"  byte[1] = {val1} (0x{val1:02x})")
        # If this is control data: terrain_set_id = byte[0]
        print(f"  If control: terrain_set_id = {val0}")
    # Try parsing as layout (width/height WORDs)
    if size >= 4:
        w, h = struct.unpack_from('<HH', data[start:start+4], 0)
        print(f"  If layout: width={w}, height={h}")

# Check resources 0, 3, 6, 9 (user's formula)
print("\n=== According to user's formula (every 3rd resource) ===")
for idx in [0, 3, 6, 9]:
    start = offsets[idx]
    end = offsets[idx+1] if idx+1 < len(offsets) else len(data)
    size = end - start
    print(f"\nResource {idx} (size={size}):")
    print(f"  First 20 bytes: {data[start:start+20].hex(' ')}")
    if size >= 4:
        w, h = struct.unpack_from('<HH', data[start:start+4], 0)
        print(f"  Parsed as layout: {w}x{h}")
        if 10 < w < 100 and 10 < h < 100:
            print(f"  [OK] Reasonable map dimensions!")
            # Check tile data size: should be w * h * 4 bytes
            expected_size = 4 + w * h * 4
            print(f"  Expected layout size: {expected_size} bytes (4 header + {w*h}*4 tile data)")
            if abs(size - expected_size) < 100:
                print(f"  [OK] Actual size {size} matches expected!")
            else:
                print(f"  [ERROR] Actual size {size} doesn't match")

# Now check FDSHAP.DAT to see which tileset is valid for map 0
print("\n=== FDSHAP.DAT tilesets ===")
fdshap_path = Path("game/FDSHAP.DAT")
fdshap_data = fdshap_path.read_bytes()

# Parse FDSHAP format 1
shap_count = struct.unpack_from('<I', fdshap_data, 6)[0]
shap_offsets = []
for i in range(shap_count):
    offset = struct.unpack_from('<I', fdshap_data, 10 + i * 4)[0]
    shap_offsets.append(offset)

print(f"FDSHAP.DAT has {shap_count} resources")

# Check tilesets at even indices (0, 2, 4, 6...)
for tileset_idx in [0, 2, 34, 68]:
    if tileset_idx >= shap_count:
        print(f"Tileset {tileset_idx}: out of range")
        continue
    
    start = shap_offsets[tileset_idx]
    end = shap_offsets[tileset_idx+1] if tileset_idx+1 < shap_count else len(fdshap_data)
    size = end - start
    
    if size < 6:
        print(f"Tileset {tileset_idx}: too small ({size} bytes)")
        continue
    
    tile_w = fdshap_data[start] | (fdshap_data[start+1] << 8)
    tile_h = fdshap_data[start+2] | (fdshap_data[start+3] << 8)
    tile_count = fdshap_data[start+4] | (fdshap_data[start+5] << 8)
    
    print(f"Tileset {tileset_idx}: {tile_w}x{tile_h}, {tile_count} tiles, resource size={size}")
    if tile_w == 64 and tile_h == 64:
        expected_size = 6 + tile_count * 4 + tile_count * 64 * 64 * 0.5  # rough estimate
        print(f"  [OK] Valid 64x64 tileset!")
