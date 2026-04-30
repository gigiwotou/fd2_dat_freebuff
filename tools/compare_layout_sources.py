"""Compare terrain IDs between C code and Python tool for map 0"""
import struct
from pathlib import Path

fdfield_path = Path("game/FDFIELD.DAT")
data = fdfield_path.read_bytes()

# Parse format 1 (count at byte 6)
count = struct.unpack_from('<I', data, 6)[0]
print(f"FDFIELD.DAT format 1: count={count}")

offsets = []
for i in range(count):
    offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(offset)

print(f"Total resources: {len(offsets)}")

# Python tool uses layout_res_idx=0, control_res_idx=1 (format 2)
# But format 2 parsing filters out byte 6-9 if offset <= pos
# So Python's offset[0] = format 1's offset[0] = offsets[0]

print(f"\n=== Python tool (format 2) reads: ===")
print(f"layout_res_idx = 0, offset = {offsets[0]}, size = {offsets[1] - offsets[0]}")
print(f"control_res_idx = 1, offset = {offsets[1]}, size = {offsets[2] - offsets[1]}")

# C code uses layout_idx=2, control_idx=0 (format 1)
print(f"\n=== C code (format 1) reads: ===")
print(f"layout_idx = 2, offset = {offsets[2]}, size = {offsets[3] - offsets[2]}")
print(f"control_idx = 0, offset = {offsets[0]}, size = {offsets[1] - offsets[0]}")

# Check Resource 0 structure (what Python reads as layout)
print(f"\n=== Resource 0 (Python's layout, C's control) ===")
res0_start = offsets[0]
res0_end = offsets[1]
res0_data = data[res0_start:res0_end]
print(f"Size: {len(res0_data)}")
print(f"First 40 bytes: {res0_data[:40].hex(' ')}")

# Try parsing as layout (width/height at byte 0)
w0 = struct.unpack_from('<H', res0_data, 0)[0]
h0 = struct.unpack_from('<H', res0_data, 2)[0]
print(f"Bytes 0-3 as width/height: {w0}x{h0}")

# Try parsing as control (terrain_set_id at byte 0)
ts_id0 = res0_data[0]
print(f"Byte 0 as terrain_set_id: {ts_id0}")

# Check if Resource 0 has valid map data at some offset
# Scan for reasonable width/height pairs
print(f"\nScanning Resource 0 for valid width/height...")
for scan_offset in range(0, min(100, len(res0_data) - 4), 2):
    if scan_offset + 4 <= len(res0_data):
        w = struct.unpack_from('<H', res0_data, scan_offset)[0]
        h = struct.unpack_from('<H', res0_data, scan_offset + 2)[0]
        if 10 < w < 100 and 10 < h < 100:
            expected_size = 4 + w * h * 4
            if abs(len(res0_data) - scan_offset - expected_size) < 50:
                print(f"  Offset {scan_offset}: {w}x{h}, expected_size={expected_size}, actual_remaining={len(res0_data) - scan_offset}")
                if abs(len(res0_data) - scan_offset - expected_size) < 10:
                    print(f"    [OK] MATCH!")
                    # Extract terrain IDs
                    tile_data = res0_data[scan_offset + 4:]
                    print(f"    First 20 terrain IDs:")
                    for i in range(min(20, w * h)):
                        b0 = tile_data[i * 4]
                        b1 = tile_data[i * 4 + 1]
                        tid = b0 | ((b1 & 0x03) << 8)
                        print(f"      [{i}] byte0={b0:02x}, byte1={b1:02x}, terrain_id={tid}", end="")
                        if i < w:
                            print()
                    break

# Check Resource 2 (C's layout)
print(f"\n=== Resource 2 (C's layout) ===")
res2_start = offsets[2]
res2_end = offsets[3]
res2_data = data[res2_start:res2_end]
print(f"Size: {len(res2_data)}")
print(f"First 40 bytes: {res2_data[:40].hex(' ')}")

w2 = struct.unpack_from('<H', res2_data, 0)[0]
h2 = struct.unpack_from('<H', res2_data, 2)[0]
print(f"Bytes 0-3 as width/height: {w2}x{h2}")

if 10 < w2 < 100 and 10 < h2 < 100:
    expected_size = 4 + w2 * h2 * 4
    print(f"Expected size: {expected_size}, Actual: {len(res2_data)}")
    if abs(len(res2_data) - expected_size) < 50:
        print(f"[OK] Resource 2 is valid layout!")
        
        # Extract first few terrain IDs
        tile_data = res2_data[4:]
        print(f"First 20 terrain IDs from Resource 2:")
        for i in range(min(20, w2 * h2)):
            b0 = tile_data[i * 4]
            b1 = tile_data[i * 4 + 1]
            tid = b0 | ((b1 & 0x03) << 8)
            print(f"  [{i:2d}] {b0:02x} {b1:02x} -> {tid:3d}", end="")
            if (i + 1) % w2 == 0:
                print()
