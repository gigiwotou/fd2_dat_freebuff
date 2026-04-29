"""Check if resources 0,3,6,9 are actually Control or Layout data"""
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

print("=== Checking resources 0, 1, 2, 3 (map 0 area) ===\n")

for i in range(6):
    start = offsets[i]
    end = offsets[i+1] if i+1 < count else len(data)
    size = end - start
    print(f"Resource {i} (size={size}):")
    print(f"  Bytes: {data[start:start+30].hex(' ')}")
    
    # Try parsing as Control data (byte[0] = terrain_set_id, byte[1] = ally_max, byte[2] = enemy_total)
    if size >= 3:
        terrain_set_id = data[start]
        ally_max = data[start+1]
        enemy_total = data[start+2]
        print(f"  If Control: terrain_set_id={terrain_set_id}, ally_max={ally_max}, enemy_total={enemy_total}")
    
    # Try parsing as Layout data (width, height, then 4 bytes per tile)
    if size >= 4:
        w = data[start] | (data[start+1] << 8)
        h = data[start+2] | (data[start+3] << 8)
        print(f"  If Layout (bytes 0-3): {w}x{h}")
        
        # Check if remaining bytes match 4 bytes per tile
        if w > 0 and h > 0 and w < 100 and h < 100:
            expected_size = 4 + w * h * 4
            print(f"    Expected size: {expected_size} (4 + {w}*{h}*4)")
            if abs(size - expected_size) < 50:
                print(f"    [OK] Size matches!")
            else:
                print(f"    [ERROR] Actual size {size} doesn't match")
    print()

# Check resource 2 (should be spawn or map data)
print("=== Resource 2 detailed analysis ===")
start = offsets[2]
end = offsets[3] if 3 < count else len(data)
size = end - start
res2_data = data[start:start+size]

# Check byte patterns
if size >= 4:
    w = res2_data[0] | (res2_data[1] << 8)
    h = res2_data[2] | (res2_data[3] << 8)
    print(f"First 4 bytes as WORDs: {w}x{h}")
    if w > 0 and h > 0 and w < 100 and h < 100:
        expected_size = 4 + w * h * 4
        print(f"  Expected: {expected_size}, Actual: {size}")
        if abs(size - expected_size) < 100:
            print(f"  [OK] Resource 2 is Layout!")

# Try resource 0 as layout with different dimensions
print("\n=== Resource 0 detailed analysis ===")
start = offsets[0]
end = offsets[1]
size = end - start
res0_data = data[start:start+size]

print(f"Size: {size}")
print(f"First 40 bytes: {res0_data[:40].hex(' ')}")

# Try: first 2 bytes = width, next 2 bytes = height
w = res0_data[0] | (res0_data[1] << 8)
h = res0_data[2] | (res0_data[3] << 8)
print(f"  Bytes 0-1: {w} (0x{w:04x})")
print(f"  Bytes 2-3: {h} (0x{h:04x})")

# Try: maybe width/height are at different offsets?
for offset in [0, 2, 4]:
    if offset + 4 <= len(res0_data):
        w_test = res0_data[offset] | (res0_data[offset+1] << 8)
        h_test = res0_data[offset+2] | (res0_data[offset+3] << 8)
        print(f"  Offset {offset}: {w_test}x{h_test}")
