#!/usr/bin/env python3
"""Check actual resource dimensions for failing tests."""
import struct

def check_dat(name, indices):
    print(f"\n=== {name} ===")
    try:
        with open(f"game/{name}", "rb") as f:
            data = f.read()
    except:
        print(f"  File not found")
        return

    # Read count at byte 6
    count = struct.unpack_from('<I', data, 6)[0]
    print(f"  Count: {count}, File size: {len(data)}")
    print(f"  {'Idx':>4} {'Offset':>10} {'Size':>10} {'W':>5} {'H':>5}")

    for i in indices:
        pos = 6 + 4 * i
        if pos + 8 > len(data):
            print(f"  {i:4d}: out of range")
            continue
        offset = struct.unpack_from('<I', data, pos)[0]
        next_offset = struct.unpack_from('<I', data, pos + 4)[0]
        size = next_offset - offset

        w, h = 0, 0
        if offset + 4 <= len(data):
            w, h = struct.unpack_from('<HH', data, offset)

        print(f"  {i:4d} {offset:10d} {size:10d} {w:5d} {h:5d}")

# FDMUS.DAT - check resource 0
check_dat("FDMUS.DAT", [0, 1, 2])

# FIGANI.DAT - find 11x11 resources
check_dat("FIGANI.DAT", [0, 1, 2, 3])

# FDTXT.DAT - find 24x316 resources
check_dat("FDTXT.DAT", [0, 1, 2])

# TAI.DAT - find 154x42 resources
check_dat("TAI.DAT", [0, 1, 2, 3])

# FDSHAP.DAT
check_dat("FDSHAP.DAT", [0, 1, 2])
