"""Debug FDSHAP.DAT tileset header parsing"""
import struct
from pathlib import Path

fdshap_path = Path("game/FDSHAP.DAT")
data = fdshap_path.read_bytes()

print(f"FDSHAP.DAT size: {len(data)} bytes")

# Parse format 1 (count at byte 6)
count = struct.unpack_from('<I', data, 6)[0]
print(f"Resource count: {count}")

offsets = []
for i in range(count):
    offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(offset)

# Check tilesets for terrain_set_id=0 (tileset_idx=0)
print(f"\n=== Tileset 0 (for terrain_set_id=0) ===")
for tileset_idx in [0, 1]:
    start = offsets[tileset_idx]
    end = offsets[tileset_idx + 1] if tileset_idx + 1 < count else len(data)
    size = end - start
    
    print(f"\nTileset index {tileset_idx}: offset={start}, size={size}")
    print(f"  First 30 bytes: {data[start:start+30].hex(' ')}")
    
    if size >= 6:
        tile_w = data[start] | (data[start+1] << 8)
        tile_h = data[start+2] | (data[start+3] << 8)
        tile_count = data[start+4] | (data[start+5] << 8)
        print(f"  Parsed header: {tile_w}x{tile_h}, {tile_count} tiles")
        
        # Check what Python export tool uses
        # Python uses format 2, so let's see what it would parse
        pos = 6
        python_offsets = []
        while pos < len(data) - 4:
            offset = struct.unpack_from('<I', data, pos)[0]
            if offset > pos and offset < len(data):
                python_offsets.append(offset)
            else:
                break
            pos += 4
        
        print(f"\nPython format 2 parsing:")
        print(f"  Python would parse {len(python_offsets)} offsets")
        if tileset_idx < len(python_offsets):
            py_start = python_offsets[tileset_idx]
            py_end = python_offsets[tileset_idx + 1] if tileset_idx + 1 < len(python_offsets) else len(data)
            print(f"  Python tileset {tileset_idx}: offset={py_start}-{py_end}, size={py_end - py_start}")
            print(f"  First 30 bytes: {data[py_start:py_start+30].hex(' ')}")
